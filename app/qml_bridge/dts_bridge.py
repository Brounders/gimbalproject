from __future__ import annotations

import hashlib
import json
import csv
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _battle_models_arg(baseline_path: Path, candidate_path: Path) -> str:
    return f"baseline={baseline_path},candidate={candidate_path}"


def _regression_pack_paths(scope: str) -> dict[str, Path]:
    if scope == "smoke":
        return {
            "day": ROOT / "configs" / "regression_pack_day.csv",
            "night": ROOT / "configs" / "regression_pack_problem_night.csv",
            "ir": ROOT / "configs" / "regression_pack_problem_ir.csv",
        }
    return {
        "day": ROOT / "configs" / "regression_pack_day.csv",
        "night": ROOT / "configs" / "regression_pack_night.csv",
        "ir": ROOT / "configs" / "regression_pack_ir.csv",
    }

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    QByteArray,
    QProcess,
    QProcessEnvironment,
    QSize,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from app.dts_candidate_gate import (
    CandidateGateError,
    accept_candidate_model,
    write_gate_decision,
)
from app.dts_diagnostics import build_compare_diagnostics_md
from app.dts_training_loop import TrainingLoopSnapshot, training_loop_state
from app.training_desk_data import (
    STATUS_ACCEPTED,
    STATUS_HARD_NEGATIVE,
    STATUS_NEW,
    STATUS_REJECTED,
    STATUS_STAGED,
    AnnotationRecord,
    load_annotation_records,
    save_review_state,
    set_record_status,
    status_counts,
    training_candidate_records,
)
from app.training_desk_quality import (
    DuplicateLink,
    QualityReport,
    _frame_size,
    duplicate_summary,
    evaluate_record_quality,
    find_duplicates,
)


ROOT = Path(__file__).resolve().parents[2]


def _write_compare_diagnostics(result_dir: Path) -> None:
    """Write diagnostics.md next to the compare results. Silent on any error."""
    try:
        gate_decision: dict = {}
        decision_file = result_dir / "candidate_gate_decision.json"
        if decision_file.exists():
            try:
                gate_decision = json.loads(decision_file.read_text(encoding="utf-8"))
            except Exception:
                gate_decision = {}

        telemetry: dict | None = None
        telemetry_file = result_dir / "telemetry_report.json"
        if telemetry_file.exists():
            try:
                telemetry = json.loads(telemetry_file.read_text(encoding="utf-8"))
            except Exception:
                telemetry = None

        summary_rows: list[dict] | None = None
        summary_csv = result_dir / "summary.csv"
        if summary_csv.exists():
            try:
                with summary_csv.open("r", encoding="utf-8", newline="") as f:
                    summary_rows = list(csv.DictReader(f))
            except Exception:
                summary_rows = None

        md = build_compare_diagnostics_md(gate_decision, telemetry, summary_rows)
        (result_dir / "diagnostics.md").write_text(md, encoding="utf-8")
    except Exception:
        pass


class DtsFrameProvider(QQuickImageProvider):
    """Render selected DTS source frame with bbox into image://dtsFrames/<record_id>/<rev>."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)
        self._lock = threading.RLock()
        self._records: dict[str, AnnotationRecord] = {}
        self._blank = QImage(960, 540, QImage.Format_RGB32)
        self._blank.fill(0x050810)

    def set_records(self, records: list[AnnotationRecord]) -> None:
        with self._lock:
            self._records = {record.record_id: record for record in records}

    def requestImage(self, id_: str, size: QSize, requested_size: QSize) -> QImage:
        record_id = id_.split("/", 1)[0].split("?", 1)[0]
        with self._lock:
            record = self._records.get(record_id)
        image = self._render_record(record) if record is not None else self._blank.copy()
        if requested_size.isValid() and requested_size.width() > 0 and requested_size.height() > 0:
            image = image.scaled(requested_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        size.setWidth(image.width())
        size.setHeight(image.height())
        return image

    def _render_record(self, record: AnnotationRecord) -> QImage:
        if not record.source or record.bbox_xyxy is None:
            return self._blank.copy()
        source = Path(record.source)
        if not source.exists():
            return self._blank.copy()
        try:
            import cv2  # type: ignore
        except Exception:
            return self._blank.copy()

        cap = cv2.VideoCapture(str(source))
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(record.frame_index)))
            ok, frame = cap.read()
        finally:
            cap.release()
        if not ok or frame is None:
            return self._blank.copy()

        x1, y1, x2, y2 = record.bbox_xyxy
        cv2.rectangle(frame, (x1, y1), (x2, y2), (95, 217, 126), 2)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = rgb.shape[:2]
        return QImage(rgb.data, width, height, rgb.strides[0], QImage.Format_RGB888).copy()


class DtsRecordsModel(QAbstractListModel):
    RecordIdRole = Qt.UserRole + 1
    ShortIdRole = Qt.UserRole + 2
    StatusRole = Qt.UserRole + 3
    FrameRole = Qt.UserRole + 4
    ClipRole = Qt.UserRole + 5
    BboxRole = Qt.UserRole + 6
    EventRole = Qt.UserRole + 7
    SourceRole = Qt.UserRole + 8
    ReasonRole = Qt.UserRole + 9
    DuplicateRole = Qt.UserRole + 10

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._records: list[AnnotationRecord] = []
        self._filtered: list[AnnotationRecord] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._filtered)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._filtered):
            return None
        record = self._filtered[index.row()]
        if role == self.RecordIdRole:
            return record.record_id
        if role == self.ShortIdRole:
            return record.record_id[:8]
        if role == self.StatusRole:
            return record.status.upper()
        if role == self.FrameRole:
            return int(record.frame_index)
        if role == self.ClipRole:
            return record.clip_name
        if role == self.BboxRole:
            return record.bbox_size
        if role == self.EventRole:
            return record.event
        if role == self.SourceRole:
            return record.source
        if role == self.ReasonRole:
            return record.reason
        if role == self.DuplicateRole:
            return False
        return None

    def roleNames(self) -> dict[int, QByteArray]:
        return {
            self.RecordIdRole: QByteArray(b"recordId"),
            self.ShortIdRole: QByteArray(b"shortId"),
            self.StatusRole: QByteArray(b"status"),
            self.FrameRole: QByteArray(b"frame"),
            self.ClipRole: QByteArray(b"clip"),
            self.BboxRole: QByteArray(b"bbox"),
            self.EventRole: QByteArray(b"event"),
            self.SourceRole: QByteArray(b"source"),
            self.ReasonRole: QByteArray(b"reason"),
            self.DuplicateRole: QByteArray(b"hasDuplicate"),
        }

    def set_records(self, records: list[AnnotationRecord], filtered: list[AnnotationRecord]) -> None:
        self.beginResetModel()
        self._records = records
        self._filtered = filtered
        self.endResetModel()

    def filtered_record(self, row: int) -> AnnotationRecord | None:
        if row < 0 or row >= len(self._filtered):
            return None
        return self._filtered[row]


class DtsBridge(QObject):
    """QML bridge for DTS review data, quality checks, export and pack staging."""

    changed = Signal()
    selectedChanged = Signal()
    lastMessageChanged = Signal()
    previewChanged = Signal()

    def __init__(self, frame_provider: DtsFrameProvider, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.log_dir = ROOT / "runs" / "operator_annotations"
        self.state_path = self.log_dir / "dts_review_state.json"
        self.exports_dir = ROOT / "runs" / "dts_exports"
        self.packs_dir = ROOT / "runs" / "operator_training_packs"
        self._frame_provider = frame_provider
        self.model = DtsRecordsModel(self)
        self._records: list[AnnotationRecord] = []
        self._filtered: list[AnnotationRecord] = []
        self._duplicate_links: dict[str, list[DuplicateLink]] = {}
        self._quality_cache: dict[str, QualityReport] = {}
        self._filter = STATUS_NEW
        self._search = ""
        self._selected_index = -1
        self._last_message = "DTS готов"
        self._operation_status_title = "Готов к работе"
        self._operation_status_body = "Примите кадры, соберите pack и создайте candidate job."
        self._operation_status_tone = "idle"
        self._last_pack_dir = ""
        self._last_pack_ok = 0
        self._last_candidate_name = ""
        self._last_candidate_job_dir = ""
        self._last_accepted_candidate_dir = ""
        self._training_process: QProcess | None = None
        self._training_running = False
        self._training_expected_best = ""
        self._training_log_tail = ""
        self._training_log_lines: list[str] = []
        self._training_exit_code: int = -999
        self._training_cancelled: bool = False
        self._compare_process: QProcess | None = None
        self._compare_running = False
        self._compare_result_dir = ""
        self._compare_summary = "Сравнение не запускалось"
        # structured compare result (Task 1)
        self._compare_status = "NOT_RUN"
        self._compare_baseline_pass = 0
        self._compare_baseline_total = 0
        self._compare_candidate_pass = 0
        self._compare_candidate_total = 0
        self._compare_contexts_json = "[]"
        # live progress (Task 2)
        self._compare_step = 0
        self._compare_total = 0
        self._compare_context_label = ""
        # human-readable compare result (Task 097)
        self._compare_human_title = "Сравнение не запускалось"
        self._compare_human_summary = ""
        self._compare_reject_reason = ""
        self._compare_decision_ready = False
        self._compare_decision_missing = False
        self._preview_revision = 0
        self._last_reload_time = 0.0
        self._restore_candidate_context()
        self._load_latest_compare_summary()
        self.reload()

    @Property(QObject, constant=True)
    def recordsModel(self) -> QObject:
        return self.model

    @Property(str, notify=lastMessageChanged)
    def lastMessage(self) -> str:
        return self._last_message

    @Property(str, notify=changed)
    def operationStatusTitle(self) -> str:
        return self._operation_status_title

    @Property(str, notify=changed)
    def operationStatusBody(self) -> str:
        return self._operation_status_body

    @Property(str, notify=changed)
    def operationStatusTone(self) -> str:
        return self._operation_status_tone

    @Property(bool, notify=changed)
    def candidateModelReady(self) -> bool:
        return self._candidate_model_path() is not None

    @Property(bool, notify=changed)
    def trainingRunning(self) -> bool:
        return bool(self._training_running)

    @Property(str, notify=changed)
    def activeRunName(self) -> str:
        return self._last_candidate_name

    @Property(str, notify=changed)
    def trainingExpectedBest(self) -> str:
        return self._training_expected_best

    @Property(str, notify=changed)
    def trainingLogTail(self) -> str:
        return self._training_log_tail

    @Property(int, notify=changed)
    def trainingExitCode(self) -> int:
        return self._training_exit_code

    @Property(bool, notify=changed)
    def trainingCanCancel(self) -> bool:
        return bool(self._training_running and self._training_process is not None)

    @Property(int, notify=changed)
    def totalCount(self) -> int:
        return len(self._records)

    @Property(int, notify=changed)
    def filteredCount(self) -> int:
        return len(self._filtered)

    @Property(int, notify=selectedChanged)
    def selectedIndex(self) -> int:
        return self._selected_index

    @Property(str, notify=changed)
    def currentFilter(self) -> str:
        return self._filter.upper()

    @Property(str, notify=selectedChanged)
    def selectedRecordId(self) -> str:
        record = self._selected_record()
        return record.record_id if record else ""

    @Property(str, notify=selectedChanged)
    def selectedShortId(self) -> str:
        record = self._selected_record()
        return record.record_id[:10] if record else "—"

    @Property(str, notify=selectedChanged)
    def selectedStatus(self) -> str:
        record = self._selected_record()
        return record.status.upper() if record else "—"

    @Property(str, notify=selectedChanged)
    def selectedClip(self) -> str:
        record = self._selected_record()
        return record.clip_name if record else "—"

    @Property(str, notify=selectedChanged)
    def selectedFrame(self) -> str:
        record = self._selected_record()
        return str(record.frame_index) if record else "—"

    @Property(str, notify=selectedChanged)
    def selectedBbox(self) -> str:
        record = self._selected_record()
        return record.bbox_size if record else "—"

    @Property(str, notify=selectedChanged)
    def selectedMeta(self) -> str:
        record = self._selected_record()
        if record is None:
            return "Выберите запись"
        parts = [
            f"EVENT  {record.event}",
            f"FRAME  {record.frame_index}",
            f"BBOX   {record.bbox_size}",
            f"SOURCE {record.clip_name}",
            f"LOG    {Path(record.log_path).name}:{record.line_number}",
        ]
        if record.active_id is not None:
            parts.append(f"ACTIVE {record.active_id}")
        if record.reason:
            parts.append(f"REASON {record.reason}")
        return "\n".join(parts)

    @Property(str, notify=selectedChanged)
    def selectedQuality(self) -> str:
        record = self._selected_record()
        if record is None:
            return "—"
        report = self._quality(record)
        return f"{report.warnings} WARN · {report.fails} FAIL"

    @Property(str, notify=selectedChanged)
    def selectedQualityRows(self) -> str:
        record = self._selected_record()
        if record is None:
            return "[]"
        report = self._quality(record)
        return json.dumps(
            [
                {"name": row.name, "state": row.state, "value": row.value, "note": row.note}
                for row in report.rows
            ],
            ensure_ascii=False,
        )

    @Property(str, notify=selectedChanged)
    def selectedDuplicates(self) -> str:
        record = self._selected_record()
        if record is None:
            return "—"
        links = self._duplicate_links.get(record.record_id, [])
        if not links:
            return "—"
        lines = [
            f"{link.kind:<7} f{link.other_frame_index} IoU {link.iou:.2f} · {link.other_record_id[:8]}"
            for link in links[:6]
        ]
        if len(links) > 6:
            lines.append(f"... ещё {len(links) - 6}")
        return "\n".join(lines)

    @Property(str, notify=selectedChanged)
    def selectedDuplicateCount(self) -> str:
        record = self._selected_record()
        if record is None:
            return "0"
        return str(len(self._duplicate_links.get(record.record_id, [])))

    @Property(int, notify=changed)
    def candidateFrameCount(self) -> int:
        return len(self._selected_for_training())

    @Property(str, notify=changed)
    def candidateSummary(self) -> str:
        items = self._selected_for_training()
        if not items:
            return "ready 0 · pack не готов"
        quality = [self._quality(record) for record in items]
        warns = sum(report.warnings for report in quality)
        fails = sum(report.fails for report in quality)
        sources = len({record.source for record in items})
        duplicates = sum(1 for record in items if self._duplicate_links.get(record.record_id))
        state = "готов" if fails == 0 else "нужна чистка"
        return f"ready {len(items)} · sources {sources} · warn {warns} · fail {fails} · dup {duplicates} · {state}"

    @Property(str, notify=changed)
    def candidatePackDir(self) -> str:
        return self._last_pack_dir

    @Property(int, notify=changed)
    def candidatePackOkCount(self) -> int:
        return int(self._last_pack_ok)

    @Property(str, notify=changed)
    def trainingLoopStage(self) -> str:
        return self._training_loop().stage

    @Property(str, notify=changed)
    def trainingLoopNextAction(self) -> str:
        return self._training_loop().next_action

    @Property(bool, notify=changed)
    def compareRunning(self) -> bool:
        return bool(self._compare_running)

    @Property(str, notify=changed)
    def compareSummary(self) -> str:
        return self._compare_summary

    @Property(str, notify=changed)
    def compareResultDir(self) -> str:
        return self._compare_result_dir

    # -- structured compare properties (Task 1) --

    @Property(str, notify=changed)
    def compareStatus(self) -> str:
        return self._compare_status

    @Property(int, notify=changed)
    def compareBaselinePassN(self) -> int:
        return self._compare_baseline_pass

    @Property(int, notify=changed)
    def compareBaselineTotalN(self) -> int:
        return self._compare_baseline_total

    @Property(int, notify=changed)
    def compareCandidatePassN(self) -> int:
        return self._compare_candidate_pass

    @Property(int, notify=changed)
    def compareCandidateTotalN(self) -> int:
        return self._compare_candidate_total

    @Property(str, notify=changed)
    def compareContextsJson(self) -> str:
        return self._compare_contexts_json

    # -- live progress properties (Task 2) --

    @Property(int, notify=changed)
    def compareStep(self) -> int:
        return self._compare_step

    @Property(int, notify=changed)
    def compareTotal(self) -> int:
        return self._compare_total

    @Property(str, notify=changed)
    def compareContextLabel(self) -> str:
        return self._compare_context_label

    # -- human-readable compare result (Task 097) --

    @Property(str, notify=changed)
    def compareHumanTitle(self) -> str:
        return self._compare_human_title

    @Property(str, notify=changed)
    def compareHumanSummary(self) -> str:
        return self._compare_human_summary

    @Property(str, notify=changed)
    def compareRejectReason(self) -> str:
        return self._compare_reject_reason

    @Property(bool, notify=changed)
    def compareDecisionReady(self) -> bool:
        return self._compare_decision_ready

    @Property(bool, notify=changed)
    def compareDecisionMissing(self) -> bool:
        return self._compare_decision_missing

    @Property(str, notify=changed)
    def candidateStatusLabel(self) -> str:
        if self._training_running:
            return "обучение идёт"
        if self._compare_running:
            return "сравнение идёт"
        if self._last_accepted_candidate_dir:
            return "candidate принят"
        if self._compare_decision_ready:
            if self._compare_status == "PASS":
                return "compare PASS"
            if self._compare_status == "RETUNE":
                return "compare RETUNE"
            return "compare FAIL"
        if self._compare_result_dir:
            return "compare не пройден"
        if self._candidate_model_path() is not None:
            return "best.pt готов"
        if self._last_pack_dir:
            return "pack собран"
        if self._selected_for_training():
            return "данные готовы"
        return "нет данных"

    @Property(str, notify=previewChanged)
    def previewSource(self) -> str:
        record = self._selected_record()
        if record is None:
            return ""
        return f"image://dtsFrames/{record.record_id}/{self._preview_revision}"

    @Slot()
    def reload(self) -> None:
        now = time.monotonic()
        if now - self._last_reload_time < 0.35:
            return
        self._last_reload_time = now
        self._records = load_annotation_records(self.log_dir, state_path=self.state_path)
        self._duplicate_links = find_duplicates(self._records)
        self._quality_cache.clear()
        self._frame_provider.set_records(self._records)
        self._apply_filter(keep_selected=True)
        self._set_message(f"DTS перезагружен: {len(self._records)} записей")
        if not self._selected_for_training():
            self._set_operation_status(
                "Ждем кадры",
                "Кликните цель на видео и примите записи в DTS.",
                "idle",
            )
        self.changed.emit()

    @Slot(str)
    def setFilter(self, status: str) -> None:
        normalized = status.strip().lower()
        self._filter = "all" if normalized in {"", "all", "все"} else normalized
        self._apply_filter(keep_selected=False)
        self.changed.emit()

    @Slot(str)
    def setSearch(self, query: str) -> None:
        self._search = query.strip()
        self._apply_filter(keep_selected=False)
        self.changed.emit()

    @Slot(int)
    def selectIndex(self, index: int) -> None:
        if not self._filtered:
            self._selected_index = -1
        else:
            self._selected_index = max(0, min(int(index), len(self._filtered) - 1))
        self._preview_revision += 1
        self.selectedChanged.emit()
        self.previewChanged.emit()

    @Slot(str)
    def setSelectedStatus(self, status: str) -> None:
        record = self._selected_record()
        normalized = status.strip().lower()
        if record is None or normalized not in {STATUS_ACCEPTED, STATUS_HARD_NEGATIVE, STATUS_NEW, STATUS_REJECTED, STATUS_STAGED}:
            return
        previous_index = self._selected_index
        if set_record_status(self._records, record.record_id, normalized):
            save_review_state(self._records, self.state_path)
            preferred_index = previous_index + 1 if self._filter in {"all", normalized} else previous_index
            self._apply_filter(keep_selected=False, preferred_index=preferred_index)
            self._set_message(f"Статус {record.record_id[:8]}: {normalized.upper()}")
            self.changed.emit()

    @Slot(result=str)
    def exportYolo(self) -> str:
        items = self._selected_for_training()
        if not items:
            return self._set_message("Нет accepted/staged записей для экспорта")

        ts = time.strftime("%Y%m%d_%H%M%S")
        out_dir = self.exports_dir / ts
        labels_dir = out_dir / "labels"
        labels_dir.mkdir(parents=True, exist_ok=True)
        selected_jsonl = out_dir / "selected_operator_annotations.jsonl"
        skipped: list[str] = []
        with selected_jsonl.open("w", encoding="utf-8") as out_f:
            for record in items:
                try:
                    src_path = Path(record.log_path)
                    if not src_path.exists():
                        skipped.append(f"log missing: {record.log_path}")
                        continue
                    with src_path.open("r", encoding="utf-8") as src_f:
                        for idx, line in enumerate(src_f, start=1):
                            if idx == record.line_number:
                                out_f.write(line if line.endswith("\n") else line + "\n")
                                break
                except Exception as exc:
                    skipped.append(f"{record.record_id}: {exc}")

        first_size = None
        for record in items:
            first_size = _frame_size(record.source)
            if first_size is not None:
                break
        if first_size is None:
            return self._set_message("Экспорт остановлен: не удалось определить размер кадра")
        fw, fh = first_size
        cmd = [
            sys.executable,
            str(ROOT / "python_scripts" / "export_operator_annotations_to_yolo.py"),
            "--input",
            str(selected_jsonl),
            "--output-dir",
            str(labels_dir),
            "--manifest-dir",
            str(out_dir),
            "--frame-width",
            str(fw),
            "--frame-height",
            str(fh),
        ]
        try:
            result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=120)
            output = (result.stdout + "\n" + result.stderr).strip()
        except Exception as exc:
            return self._set_message(f"Ошибка экспорта YOLO: {exc}")
        suffix = f" · skipped {len(skipped)}" if skipped else ""
        cmd_text = " ".join(shlex.quote(p) for p in cmd)
        state = "готов" if result.returncode == 0 else f"код {result.returncode}"
        short_output = output[:500].replace("\n", " | ") if output else "без вывода"
        return self._set_message(f"YOLO export {state}: {out_dir.relative_to(ROOT)}{suffix} · {cmd_text} · {short_output}")

    @Slot(result=str)
    def buildPack(self) -> str:
        items = self._selected_for_training()
        if not items:
            self._set_operation_status(
                "Pack не собран",
                "Нет принятых кадров. Сначала примите записи в DTS.",
                "warn",
            )
            return self._set_message("Нет accepted/staged записей для сборки pack")
        failed = [
            (record, self._quality(record))
            for record in items
            if self._quality(record).fails > 0
        ]
        if failed:
            self._set_operation_status(
                "Pack заблокирован",
                f"Есть accepted-записи с ошибками качества: {len(failed)}. Исправьте или отклоните их.",
                "error",
            )
            return self._set_message(
                f"Pack заблокирован: {len(failed)} accepted записей с FAIL. Отклоните или исправьте их перед сборкой"
            )
        ts = time.strftime("%Y%m%d_%H%M%S")
        pack_dir = self.packs_dir / f"pack_{ts}"
        cmd = [
            sys.executable,
            str(ROOT / "python_scripts" / "stage_operator_training_pack.py"),
            "--state-file",
            str(self.state_path),
            "--log-dir",
            str(self.log_dir),
            "--output-dir",
            str(pack_dir),
        ]
        try:
            result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=300)
            output = (result.stdout + "\n" + result.stderr).strip()
        except Exception as exc:
            self._set_operation_status("Ошибка сборки", str(exc), "error")
            return self._set_message(f"Ошибка сборки pack: {exc}")
        manifest_path = pack_dir / "manifest.json"
        ok_count = 0
        skipped_frame = 0
        skipped_source = 0
        skipped_invalid = 0
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            counts = manifest.get("counts", {}) if isinstance(manifest, dict) else {}
            ok_count = int(counts.get("ok", 0) or 0)
            skipped_frame = int(counts.get("skipped_frame", 0) or 0)
            skipped_source = int(counts.get("skipped_source", 0) or 0)
            skipped_invalid = int(counts.get("skipped_invalid", 0) or 0)
        except Exception as exc:
            self._set_operation_status("Pack требует проверки", "Manifest создан, но не читается.", "warn")
            return self._set_message(f"Pack создан, но manifest не прочитан: {exc}")
        if result.returncode == 0 and ok_count <= 0:
            self._set_operation_status("Pack пустой", "Manifest создан, но пригодных кадров нет.", "warn")
            return self._set_message("Pack заблокирован: manifest создан, но ok=0")
        self._last_pack_dir = str(pack_dir.relative_to(ROOT))
        self._last_pack_ok = ok_count
        self._set_operation_status(
            "Pack собран",
            f"Готово кадров: {ok_count}. Теперь создайте candidate job кнопкой ОБУЧИТЬ.",
            "success" if result.returncode == 0 else "warn",
        )
        self.changed.emit()
        state = "готов" if result.returncode == 0 else f"код {result.returncode}"
        short_output = output[:700].replace("\n", " | ") if output else "без вывода"
        return self._set_message(
            f"Training pack {state}: {pack_dir.relative_to(ROOT)} · ok {ok_count} · "
            f"skipped frame/source/invalid {skipped_frame}/{skipped_source}/{skipped_invalid} · {short_output}"
        )

    @Slot(result=str)
    def assembleCandidate(self) -> str:
        return self.buildPack()

    @Slot(result=str)
    def trainCandidate(self) -> str:
        if self._training_running:
            self._set_operation_status(
                "Обучение идет",
                "Дождитесь завершения. После появления best.pt станет доступно сравнение.",
                "progress",
            )
            return self._set_message("Обучение уже идет")
        pack_dir = self._current_pack_dir()
        if pack_dir is None:
            self._set_operation_status(
                "Обучение недоступно",
                "Сначала соберите pack с пригодными кадрами.",
                "warn",
            )
            return self._set_message("Сначала соберите pack: кнопка СОБРАТЬ должна дать ok > 0")
        data_yaml = pack_dir / "data.yaml"
        if not data_yaml.exists():
            self._set_operation_status(
                "Обучение заблокировано",
                "В pack нет data.yaml. Соберите pack заново.",
                "error",
            )
            return self._set_message(f"Обучение заблокировано: нет data.yaml в {pack_dir.relative_to(ROOT)}")

        ts = time.strftime("%Y%m%d_%H%M%S")
        run_name = f"dts_{pack_dir.name}_{ts}"
        job_dir = ROOT / "runs" / "dts_candidate_jobs" / run_name
        job_dir.mkdir(parents=True, exist_ok=True)
        project_dir = ROOT / "runs" / "dts_candidate_training"
        base_model = self._base_model_path()
        cmd = [
            str(ROOT / "tracker_env" / "bin" / "python"),
            str(ROOT / "python_scripts" / "train_yolo_from_yaml.py"),
            "--data", str(data_yaml),
            "--model", str(base_model),
            "--project", str(project_dir),
            "--name", run_name,
            "--device", "mps",
            "--imgsz", "960",
            "--batch", "4",
            "--workers", "2",
            "--epochs", "80",
            "--patience", "20",
            "--cache", "disk",
            "--val",
        ]
        env_prefix = f"cd {shlex.quote(str(ROOT))}\nexport PYTHONPATH=src\n"
        shell_text = env_prefix + " ".join(shlex.quote(part) for part in cmd) + "\n"
        script_path = job_dir / "train_candidate.sh"
        script_path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + shell_text, encoding="utf-8")
        script_path.chmod(script_path.stat().st_mode | 0o111)
        manifest_json = pack_dir / "manifest.json"
        if not manifest_json.exists():
            self._set_operation_status(
                "Обучение заблокировано",
                "В pack нет manifest.json — audit chain нарушен. Соберите pack заново.",
                "error",
            )
            return self._set_message(f"Обучение заблокировано: нет manifest.json в {pack_dir.relative_to(ROOT)}")
        job = {
            "type": "dts_candidate_training",
            "created_at": ts,
            "pack_dir": str(pack_dir),
            "data_yaml": str(data_yaml),
            "base_model": str(base_model),
            "project_dir": str(project_dir),
            "run_name": run_name,
            "expected_best": str(project_dir / run_name / "weights" / "best.pt"),
            "command": cmd,
            "base_model_sha256": _file_sha256(base_model) if base_model.exists() else "",
            "pack_manifest_sha256": _file_sha256(manifest_json),
            "data_yaml_sha256": _file_sha256(data_yaml),
        }
        (job_dir / "job.json").write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
        self._last_candidate_name = run_name
        self._last_candidate_job_dir = str(job_dir.relative_to(ROOT))
        self._training_expected_best = str((project_dir / run_name / "weights" / "best.pt").relative_to(ROOT))
        self._set_operation_status(
            "Обучение запускается",
            "Создан training job. Запускаю обучение candidate в фоне.",
            "progress",
        )
        self.changed.emit()

        process = QProcess(self)
        process.setWorkingDirectory(str(ROOT))
        process.setProgram(cmd[0])
        process.setArguments(cmd[1:])
        env = QProcessEnvironment.systemEnvironment()
        existing_pythonpath = env.value("PYTHONPATH", "")
        env.insert("PYTHONPATH", "src" if not existing_pythonpath else f"src:{existing_pythonpath}")
        process.setProcessEnvironment(env)
        process.readyReadStandardOutput.connect(lambda: self._on_training_output(process, stderr=False))
        process.readyReadStandardError.connect(lambda: self._on_training_output(process, stderr=True))
        process.finished.connect(
            lambda exit_code, exit_status: self._on_training_finished(
                exit_code,
                exit_status,
                Path(job["expected_best"]),
            )
        )
        process.errorOccurred.connect(lambda error: self._on_training_error(error))

        self._training_process = process
        self._training_running = True
        self._training_log_tail = ""
        self._training_log_lines = []
        self._training_exit_code = -999
        self._training_cancelled = False
        self.changed.emit()
        process.start()
        if not process.waitForStarted(3000):
            self._training_running = False
            self._training_process = None
            self._set_operation_status("Обучение не стартовало", "Процесс training не запустился.", "error")
            self.changed.emit()
            return self._set_message("Ошибка запуска обучения candidate")
        return self._set_message(
            f"Обучение запущено: {run_name}. Ожидаемый best.pt: {Path(job['expected_best']).relative_to(ROOT)}"
        )

    @Slot(result=str)
    def cancelTraining(self) -> str:
        if not self._training_running or self._training_process is None:
            return "Обучение не запущено — нечего останавливать"
        self._training_cancelled = True
        process = self._training_process
        process.terminate()
        if not process.waitForFinished(3000):
            process.kill()
        self._set_operation_status(
            "Обучение остановлено",
            "Запуск можно повторить после проверки pack.",
            "warn",
        )
        return self._set_message("Обучение остановлено оператором")

    @Slot(result=str)
    def compareCandidate(self) -> str:
        if self._compare_running:
            self._set_operation_status(
                "Сравнение идет",
                self._compare_context_label or "Дождитесь завершения текущего прохода.",
                "progress",
            )
            return self._set_message("Сравнение уже идет: дождитесь завершения текущего прохода")
        model_path = self._candidate_model_path()
        if model_path is None:
            self._set_operation_status(
                "Сравнение недоступно",
                "Candidate best.pt не найден. Обучение еще не завершено или не запускалось.",
                "warn",
            )
            return self._set_message("Сравнение заблокировано: candidate best.pt не найден. Сначала запустите training job и дождитесь весов")
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_dir = ROOT / "runs" / "dts_candidate_comparisons"
        tag = f"dts_{ts}"
        baseline_path = self._base_model_path()
        scope = "smoke"
        args = [
            str(ROOT / "python_scripts" / "run_model_battle.py"),
            "--models", _battle_models_arg(baseline_path, model_path),
            "--scope", scope,
            "--contexts", "day,night,ir",
            "--max-frames", "180",
            "--preview-frames", "0",
            "--no-preview",
            "--out-dir", str(out_dir),
            "--tag", tag,
        ]

        process = QProcess(self)
        process.setWorkingDirectory(str(ROOT))
        process.setProgram(sys.executable)
        process.setArguments(args)
        process.finished.connect(
            lambda exit_code, exit_status: self._on_compare_finished(
                exit_code, exit_status, out_dir, tag, model_path, baseline_path, scope
            )
        )
        process.errorOccurred.connect(lambda error: self._on_compare_error(error))
        process.readyReadStandardOutput.connect(lambda: self._on_compare_stdout(process))

        self._compare_process = process
        self._compare_running = True
        self._compare_result_dir = ""
        self._compare_summary = (
            "Идет сравнение: baseline против candidate · smoke day/night/ir · "
            "лимит 180 кадров на контекст"
        )
        self._compare_status = "RUNNING"
        self._compare_step = 0
        self._compare_total = 0
        self._compare_context_label = ""
        self._compare_human_title = "Сравнение идет"
        self._compare_human_summary = "Baseline и candidate проверяются."
        self._compare_reject_reason = ""
        self._compare_decision_ready = False
        self._compare_decision_missing = False
        self.changed.emit()
        self._set_operation_status(
            "Сравнение идет",
            "Baseline и candidate проверяются на day/night/ir.",
            "progress",
        )
        self._set_message("Сравнение запущено в фоне: интерфейс можно продолжать использовать")
        process.start()
        if not process.waitForStarted(3000):
            self._compare_running = False
            self._compare_summary = "Сравнение не стартовало: QProcess не запустился"
            self._compare_process = None
            self._set_operation_status("Сравнение не стартовало", "Процесс сравнения не запустился.", "error")
            self.changed.emit()
            return self._set_message("Ошибка сравнения candidate: процесс не стартовал")
        return self._last_message

    @Slot(result=str)
    def acceptCandidate(self) -> str:
        model_path = self._candidate_model_path()
        if model_path is None:
            self._set_operation_status(
                "Принятие недоступно",
                "Candidate best.pt не найден.",
                "warn",
            )
            return self._set_message("Принятие заблокировано: candidate best.pt не найден")
        if not self._compare_result_dir:
            self._set_operation_status(
                "Принятие заблокировано",
                "Сначала выполните СРАВНИТЬ и получите PASS.",
                "warn",
            )
            return self._set_message("Принятие заблокировано: сначала выполните СРАВНИТЬ и получите PASS")
        compare_dir = ROOT / self._compare_result_dir
        try:
            manifest_path = accept_candidate_model(
                model_path,
                compare_dir,
                output_root=ROOT / "models" / "candidates" / "accepted",
                training_job_dir=ROOT / self._last_candidate_job_dir if self._last_candidate_job_dir else None,
                pack_dir=ROOT / self._last_pack_dir if self._last_pack_dir else None,
            )
        except CandidateGateError as exc:
            self._set_operation_status("Принятие заблокировано", str(exc), "error")
            return self._set_message(f"Принятие заблокировано: {exc}")
        self._last_accepted_candidate_dir = str(manifest_path.parent.relative_to(ROOT))
        self._set_operation_status(
            "Candidate принят",
            "Модель сохранена безопасно. Production-модель не заменялась.",
            "success",
        )
        self.changed.emit()
        return self._set_message(
            f"Candidate принят безопасно: {self._last_accepted_candidate_dir} · текущая модель не заменялась"
        )

    @Slot(str, result=int)
    def countStatus(self, status: str) -> int:
        normalized = status.strip().lower()
        if normalized == "all":
            return len(self._records)
        if normalized in {"fail", "accepted_fail"}:
            return sum(
                1
                for record in self._records
                if record.status == STATUS_ACCEPTED and self._quality(record).fails > 0
            )
        counts = status_counts(self._records)
        return int(counts.get(normalized, 0))

    def _set_message(self, message: str) -> str:
        self._last_message = message
        self.lastMessageChanged.emit()
        return message

    def _set_operation_status(self, title: str, body: str, tone: str = "idle") -> None:
        self._operation_status_title = title
        self._operation_status_body = body
        self._operation_status_tone = tone
        self.changed.emit()

    def _on_compare_error(self, error: QProcess.ProcessError) -> None:
        self._compare_running = False
        self._compare_status = "FAIL"
        self._compare_summary = f"Сравнение остановлено: ошибка процесса {int(error)}"
        self._compare_process = None
        self._compare_human_title = "Сравнение не завершилось"
        self._compare_human_summary = f"Ошибка процесса {int(error)}."
        self._compare_reject_reason = f"process error {int(error)}"
        self._compare_decision_ready = False
        self._compare_decision_missing = False
        self._set_operation_status("Сравнение остановлено", f"Ошибка процесса {int(error)}.", "error")
        self.changed.emit()
        self._set_message(self._compare_summary)

    def _on_training_output(self, process: QProcess, *, stderr: bool) -> None:
        raw = process.readAllStandardError() if stderr else process.readAllStandardOutput()
        text = bytes(raw).decode("utf-8", "replace")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return
        self._training_log_lines.extend(lines)
        if len(self._training_log_lines) > 8:
            self._training_log_lines = self._training_log_lines[-8:]
        self._training_log_tail = "\n".join(self._training_log_lines)
        last = lines[-1]
        if "Epoch" in last or "epoch" in last:
            body = last[-160:]
        elif self._training_expected_best:
            body = f"Ждем {self._training_expected_best}"
        else:
            body = "Ждем best.pt"
        self._set_operation_status("Обучение идет", body, "progress")
        self.changed.emit()

    def _on_training_error(self, error: QProcess.ProcessError) -> None:
        self._training_running = False
        self._training_process = None
        self._set_operation_status("Обучение остановлено", f"Ошибка процесса {int(error)}.", "error")
        self.changed.emit()
        self._set_message(f"Обучение остановлено: ошибка процесса {int(error)}")

    def _on_training_finished(
        self,
        exit_code: int,
        _exit_status: QProcess.ExitStatus,
        expected_best: Path,
    ) -> None:
        process = self._training_process
        if process is not None:
            tail = (
                bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
                + "\n"
                + bytes(process.readAllStandardError()).decode("utf-8", "replace")
            ).strip()
            if tail:
                new_lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
                self._training_log_lines.extend(new_lines)
                if len(self._training_log_lines) > 8:
                    self._training_log_lines = self._training_log_lines[-8:]
                self._training_log_tail = "\n".join(self._training_log_lines)

        self._training_exit_code = exit_code
        cancelled = self._training_cancelled
        self._training_running = False
        self._training_process = None
        self._training_cancelled = False

        if cancelled:
            self._set_operation_status(
                "Обучение остановлено",
                "Запуск можно повторить после проверки pack.",
                "warn",
            )
            self.changed.emit()
            self._set_message("Обучение остановлено оператором")
            return

        if expected_best.exists():
            self._set_operation_status(
                "best.pt готов",
                "Обучение завершено. Теперь можно нажать СРАВНИТЬ.",
                "success",
            )
            self.changed.emit()
            self._set_message(f"Обучение завершено: {expected_best.relative_to(ROOT)}")
            return

        if exit_code == 0:
            self._set_operation_status(
                "best.pt не найден",
                "Обучение завершилось, но weights/best.pt не появился.",
                "warn",
            )
        else:
            tail_line = self._training_log_tail.splitlines()[-1][-160:] if self._training_log_tail else f"Процесс завершился с кодом {exit_code}."
            self._set_operation_status("Обучение упало", tail_line, "error")
        self.changed.emit()
        self._set_message(f"Обучение завершилось без best.pt: код {exit_code}")

    def _on_compare_stdout(self, process: QProcess) -> None:
        data = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
        changed = False
        for line in data.splitlines():
            line = line.strip()
            if not line.startswith("PROGRESS"):
                continue
            parts = dict(p.split("=", 1) for p in line.split() if "=" in p)
            try:
                self._compare_step = int(parts.get("step", self._compare_step))
                self._compare_total = int(parts.get("total", self._compare_total))
                self._compare_context_label = parts.get("context", self._compare_context_label)
                changed = True
            except (ValueError, KeyError):
                pass
        if changed:
            self.changed.emit()

    def _on_compare_finished(
        self,
        exit_code: int,
        _exit_status: QProcess.ExitStatus,
        out_dir: Path,
        tag: str,
        model_path: Path,
        baseline_path: Path | None = None,
        scope: str = "smoke",
    ) -> None:
        process = self._compare_process
        stdout = ""
        stderr = ""
        if process is not None:
            stdout = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
            stderr = bytes(process.readAllStandardError()).decode("utf-8", "replace")

        result_dir = self._find_compare_result_dir(out_dir, tag)
        if result_dir is not None:
            self._compare_result_dir = str(result_dir.relative_to(ROOT))
            self._compare_summary = self._summarize_compare_dir(result_dir)
            data = self._apply_compare_structured(result_dir)
            decision_ready = False
            decision_missing = False
            regression_packs = _regression_pack_paths(scope)
            try:
                write_gate_decision(
                    result_dir,
                    model_path,
                    data,
                    baseline_model_path=baseline_path,
                    regression_pack_paths=regression_packs,
                )
                decision_ready = True
                _write_compare_diagnostics(result_dir)
            except CandidateGateError as exc:
                decision_missing = True
                self._compare_status = "FAIL"
                self._compare_summary = f"{self._compare_summary} · gate decision не сохранен: {exc}"
            self._build_human_compare_fields(data, decision_ready=decision_ready, decision_missing=decision_missing)
        else:
            output = (stdout + "\n" + stderr).strip().replace("\n", " | ")
            short_output = output[:420] if output else "summary.csv не найден"
            self._compare_result_dir = ""
            self._compare_summary = f"Сравнение завершилось без summary.csv · код {exit_code} · {short_output}"
            self._compare_status = "FAIL"
            empty: dict = {"status": "FAIL", "candidate_pass": 0, "candidate_total": 0, "contexts": []}
            self._build_human_compare_fields(empty, decision_ready=False, decision_missing=True)

        self._compare_running = False
        self._compare_process = None
        self._compare_step = 0
        self._compare_total = 0
        self._compare_context_label = ""
        self.changed.emit()

        state = "готово" if exit_code == 0 else f"код {exit_code}"
        model_label = model_path.relative_to(ROOT) if model_path.is_relative_to(ROOT) else model_path
        if self._compare_status == "PASS":
            self._set_operation_status("Сравнение PASS", "Candidate прошел smoke gate. Можно нажать ПРИНЯТЬ.", "success")
        elif self._compare_status == "RETUNE":
            self._set_operation_status("Нужна доработка", "Candidate прошел не все контексты. Лучше собрать больше данных.", "warn")
        else:
            self._set_operation_status("Сравнение FAIL", "Candidate нельзя принимать. Смотрите результат сравнения.", "error")
        self._set_message(f"Сравнение {state}: {self._compare_result_dir or out_dir.relative_to(ROOT)} · model {model_label}")

    def _load_latest_compare_summary(self) -> None:
        base_dir = ROOT / "runs" / "dts_candidate_comparisons"
        candidates = [
            path.parent
            for path in base_dir.glob("*/summary.csv")
            if path.is_file()
        ]
        if not candidates:
            return
        latest = max(candidates, key=lambda path: path.stat().st_mtime)
        self._compare_result_dir = str(latest.relative_to(ROOT))
        self._compare_summary = self._summarize_compare_dir(latest)
        data = self._apply_compare_structured(latest)
        decision_ready = (latest / "candidate_gate_decision.json").exists()
        if decision_ready:
            try:
                gd = json.loads((latest / "candidate_gate_decision.json").read_text(encoding="utf-8"))
                if not gd.get("accept_allowed", False):
                    decision_ready = False
                elif gd.get("candidate_model_sha256"):
                    current_best = self._candidate_model_path()
                    if current_best is None or _file_sha256(current_best) != gd["candidate_model_sha256"]:
                        decision_ready = False
            except Exception:
                decision_ready = False
        decision_missing = not decision_ready
        self._build_human_compare_fields(data, decision_ready=decision_ready, decision_missing=decision_missing)

    def _build_human_compare_fields(self, data: dict, *, decision_ready: bool, decision_missing: bool) -> None:
        status = data.get("status", "FAIL")
        candidate_pass = int(data.get("candidate_pass", 0) or 0)
        candidate_total = int(data.get("candidate_total", 0) or 0)
        contexts = data.get("contexts", [])
        if not isinstance(contexts, list):
            contexts = []

        self._compare_decision_ready = decision_ready
        self._compare_decision_missing = decision_missing

        if decision_missing:
            self._compare_human_title = "Результат неполный"
            self._compare_human_summary = "Решение gate не сохранено. Повторите сравнение."
            self._compare_reject_reason = "gate decision не сохранен"
            return

        if candidate_total == 0:
            self._compare_human_title = "Результат неполный"
            self._compare_human_summary = "Candidate строки не найдены в summary.csv."
            self._compare_reject_reason = "candidate строки не найдены"
            return

        failed = [str(ctx.get("name", "?")) for ctx in contexts if not ctx.get("passed", False)]
        summary = f"Прошел {candidate_pass}/{candidate_total} контекстов."
        if status == "PASS":
            self._compare_human_title = "Candidate PASS"
            self._compare_human_summary = summary
            self._compare_reject_reason = ""
        elif status == "RETUNE":
            self._compare_human_title = "Нужна доработка"
            self._compare_human_summary = summary
            self._compare_reject_reason = (", ".join(failed) + " FAIL") if failed else f"candidate {candidate_pass}/{candidate_total}"
        else:
            self._compare_human_title = "Candidate отклонен"
            self._compare_human_summary = summary
            self._compare_reject_reason = (", ".join(failed) + " FAIL") if failed else f"candidate {candidate_pass}/{candidate_total}"

    def _find_compare_result_dir(self, out_dir: Path, tag: str) -> Path | None:
        candidates = [path for path in out_dir.glob(f"{tag}_*") if (path / "summary.csv").exists()]
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime)

    def _summarize_compare_dir(self, result_dir: Path) -> str:
        summary_csv = result_dir / "summary.csv"
        try:
            with summary_csv.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
        except Exception as exc:
            return f"Результат есть, но summary.csv не прочитан: {exc}"
        if not rows:
            return "Результат есть, но summary.csv пустой"

        baseline_rows = [row for row in rows if row.get("model") == "baseline"]
        candidate_rows = [row for row in rows if row.get("model") != "baseline"]
        if not candidate_rows:
            return "Результат есть, но строки candidate не найдены"

        candidate_pass = sum(1 for row in candidate_rows if self._csv_bool(row.get("passed", "")))
        baseline_pass = sum(1 for row in baseline_rows if self._csv_bool(row.get("passed", "")))
        contexts = []
        baseline_by_context = {row.get("context", ""): row for row in baseline_rows}
        for row in candidate_rows:
            context = row.get("context", "unknown")
            passed = "PASS" if self._csv_bool(row.get("passed", "")) else "FAIL"
            presence = self._csv_float(row.get("active_presence_rate", ""))
            false_lock = self._csv_float(row.get("false_lock_rate", ""))
            id_changes = self._csv_float(row.get("active_id_changes_per_min", ""))
            base = baseline_by_context.get(context)
            delta_presence = ""
            if base is not None:
                delta = presence - self._csv_float(base.get("active_presence_rate", ""))
                delta_presence = f" Δpres {delta:+.2f}"
            contexts.append(
                f"{context}: {passed}, pres {presence:.2f}{delta_presence}, false {false_lock:.2f}, id/min {id_changes:.1f}"
            )

        decision = "PASS" if candidate_pass == len(candidate_rows) and candidate_rows else "FAIL/RETUNE"
        return (
            f"{decision} · candidate {candidate_pass}/{len(candidate_rows)} контекстов · "
            f"baseline {baseline_pass}/{len(baseline_rows)} · "
            + " · ".join(contexts)
        )

    def _csv_bool(self, value: object) -> bool:
        return str(value).strip().lower() in {"1", "true", "yes", "pass", "passed"}

    def _csv_float(self, value: object) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0

    def _parse_compare_structured(self, result_dir: Path) -> dict:
        """Parse summary.csv into a structured dict for QML display (Task 1)."""
        empty: dict = {
            "status": "FAIL",
            "baseline_pass": 0, "baseline_total": 0,
            "candidate_pass": 0, "candidate_total": 0,
            "contexts": [],
        }
        summary_csv = result_dir / "summary.csv"
        try:
            with summary_csv.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
        except Exception:
            return empty
        if not rows:
            return empty
        baseline_rows = [r for r in rows if r.get("model") == "baseline"]
        candidate_rows = [r for r in rows if r.get("model") != "baseline"]
        if not candidate_rows:
            return empty
        candidate_pass = sum(1 for r in candidate_rows if self._csv_bool(r.get("passed", "")))
        baseline_pass = sum(1 for r in baseline_rows if self._csv_bool(r.get("passed", "")))
        baseline_by_ctx = {r.get("context", ""): r for r in baseline_rows}
        contexts = []
        for row in candidate_rows:
            ctx = row.get("context", "?")
            passed = self._csv_bool(row.get("passed", ""))
            presence = self._csv_float(row.get("active_presence_rate", ""))
            false_lock = self._csv_float(row.get("false_lock_rate", ""))
            id_changes = self._csv_float(row.get("active_id_changes_per_min", ""))
            base = baseline_by_ctx.get(ctx)
            delta_presence = (
                presence - self._csv_float(base.get("active_presence_rate", ""))
                if base is not None else 0.0
            )
            contexts.append({
                "name": ctx,
                "passed": passed,
                "presence": round(presence, 3),
                "delta_presence": round(delta_presence, 3),
                "false_lock": round(false_lock, 3),
                "id_changes": round(id_changes, 2),
            })
        all_pass = candidate_pass == len(candidate_rows)
        some_pass = candidate_pass > 0
        status = "PASS" if all_pass else ("RETUNE" if some_pass else "FAIL")
        return {
            "status": status,
            "baseline_pass": baseline_pass,
            "baseline_total": len(baseline_rows),
            "candidate_pass": candidate_pass,
            "candidate_total": len(candidate_rows),
            "contexts": contexts,
        }

    def _apply_compare_structured(self, result_dir: Path) -> dict:
        data = self._parse_compare_structured(result_dir)
        self._compare_status = data["status"]
        self._compare_baseline_pass = data["baseline_pass"]
        self._compare_baseline_total = data["baseline_total"]
        self._compare_candidate_pass = data["candidate_pass"]
        self._compare_candidate_total = data["candidate_total"]
        self._compare_contexts_json = json.dumps(data["contexts"], ensure_ascii=False)
        return data

    def _selected_record(self) -> AnnotationRecord | None:
        return self.model.filtered_record(self._selected_index)

    def _restore_candidate_context(self) -> None:
        """Restore _last_candidate_* fields from the newest valid job.json on startup."""
        jobs_root = ROOT / "runs" / "dts_candidate_jobs"
        if not jobs_root.exists():
            return
        candidates: list[tuple[str, Path]] = []
        for job_file in jobs_root.glob("*/job.json"):
            try:
                data = json.loads(job_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            created_at = str(data.get("created_at", ""))
            expected_best = str(data.get("expected_best", ""))
            pack_dir_str = str(data.get("pack_dir", ""))
            run_name = str(data.get("run_name", ""))
            if not (expected_best and pack_dir_str and run_name):
                continue
            best_path = Path(expected_best)
            if not best_path.exists():
                continue
            pack_path = Path(pack_dir_str)
            if not pack_path.exists() or not (pack_path / "manifest.json").exists():
                continue
            candidates.append((created_at, job_file))
        if not candidates:
            return
        _ts, best_job = sorted(candidates)[-1]
        try:
            data = json.loads(best_job.read_text(encoding="utf-8"))
        except Exception:
            return
        job_dir = best_job.parent
        best_path = Path(str(data["expected_best"]))
        pack_path = Path(str(data["pack_dir"]))
        run_name = str(data["run_name"])
        try:
            self._last_candidate_job_dir = str(job_dir.relative_to(ROOT))
            self._last_pack_dir = str(pack_path.relative_to(ROOT))
        except ValueError:
            self._last_candidate_job_dir = str(job_dir)
            self._last_pack_dir = str(pack_path)
        self._last_candidate_name = run_name
        try:
            self._training_expected_best = str(best_path.relative_to(ROOT))
        except ValueError:
            self._training_expected_best = str(best_path)

    def _base_model_path(self) -> Path:
        for path in (
            ROOT / "models" / "checkpoints" / "rtx_latest_best.pt",
            ROOT / "models" / "baseline.pt",
            ROOT / "models" / "yolo11n.pt",
        ):
            if path.exists():
                return path
        return ROOT / "models" / "yolo11n.pt"

    def _current_pack_dir(self) -> Path | None:
        if self._last_pack_dir:
            pack_dir = ROOT / self._last_pack_dir
            if pack_dir.exists() and (pack_dir / "manifest.json").exists():
                return pack_dir
        candidates = []
        for manifest in self.packs_dir.glob("pack_*/manifest.json"):
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                ok_count = int((data.get("counts", {}) or {}).get("ok", 0) or 0)
            except Exception:
                ok_count = 0
            if ok_count > 0:
                candidates.append((manifest.parent.stat().st_mtime, manifest.parent, ok_count))
        if not candidates:
            return None
        _mtime, pack_dir, ok_count = sorted(candidates)[-1]
        self._last_pack_dir = str(pack_dir.relative_to(ROOT))
        self._last_pack_ok = int(ok_count)
        return pack_dir

    def _candidate_model_path(self) -> Path | None:
        names = []
        if self._last_candidate_name:
            names.append(self._last_candidate_name)
        pack_dir = self._current_pack_dir()
        if pack_dir is not None:
            names.extend(
                p.name
                for p in sorted((ROOT / "runs" / "dts_candidate_training").glob(f"dts_{pack_dir.name}_*"))
                if p.is_dir()
            )
        names = list(dict.fromkeys(names))
        for name in reversed(names):
            path = ROOT / "runs" / "dts_candidate_training" / name / "weights" / "best.pt"
            if path.exists():
                return path
        return None

    def _quality(self, record: AnnotationRecord) -> QualityReport:
        if record.record_id not in self._quality_cache:
            self._quality_cache[record.record_id] = evaluate_record_quality(record)
        return self._quality_cache[record.record_id]

    def _apply_filter(
        self,
        *,
        keep_selected: bool,
        selected_id: str | None = None,
        preferred_index: int | None = None,
    ) -> None:
        current_id = selected_id
        if current_id is None and keep_selected:
            current = self._selected_record()
            current_id = current.record_id if current else None

        query = self._search.lower()
        if self._filter == "all":
            base = self._sorted_records(self._records)
        elif self._filter in {"fail", "accepted_fail"}:
            base = self._sorted_records(
                [
                    record
                    for record in self._records
                    if record.status == STATUS_ACCEPTED and self._quality(record).fails > 0
                ]
            )
        else:
            base = self._sorted_records([record for record in self._records if record.status == self._filter])
        if query:
            self._filtered = [
                record
                for record in base
                if query in record.record_id.lower()
                or query in record.clip_name.lower()
                or query in str(record.frame_index)
                or query in record.source.lower()
                or query in record.event.lower()
            ]
        else:
            self._filtered = base
        self.model.set_records(self._records, self._filtered)

        if not self._filtered:
            self._selected_index = -1
        elif preferred_index is not None:
            self._selected_index = max(0, min(int(preferred_index), len(self._filtered) - 1))
        elif current_id is not None:
            self._selected_index = next(
                (i for i, record in enumerate(self._filtered) if record.record_id == current_id),
                0,
            )
        else:
            self._selected_index = 0
        self._preview_revision += 1
        self.selectedChanged.emit()
        self.previewChanged.emit()

    @staticmethod
    def _sorted_records(records: list[AnnotationRecord]) -> list[AnnotationRecord]:
        return sorted(
            records,
            key=lambda record: (
                record.source.lower(),
                int(record.frame_index),
                int(record.line_number),
                record.record_id,
            ),
        )

    def _selected_for_training(self) -> list[AnnotationRecord]:
        return training_candidate_records(self._records)

    def _training_loop(self):
        candidate_model = self._candidate_model_path()
        return training_loop_state(
            TrainingLoopSnapshot(
                ready_frames=len(self._selected_for_training()),
                pack_ok=int(self._last_pack_ok),
                pack_dir=str(self._last_pack_dir),
                training_job_dir=str(self._last_candidate_job_dir),
                candidate_model_path=str(candidate_model) if candidate_model is not None else "",
                compare_status=str(self._compare_status),
                compare_result_dir=str(self._compare_result_dir),
                accepted_candidate_dir=str(self._last_accepted_candidate_dir),
            )
        )

    @Property(str, notify=changed)
    def duplicateSummary(self) -> str:
        summary = duplicate_summary(self._duplicate_links)
        return (
            f"{summary.get('records_with_duplicates', 0)} records · "
            f"exact {summary.get('exact', 0)} · overlap {summary.get('overlap', 0)} · near {summary.get('near', 0)}"
        )
