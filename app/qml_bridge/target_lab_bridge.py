from __future__ import annotations

import csv
import json
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, QProcess, QProcessEnvironment, Signal, Slot

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class GtFileSummary:
    name: str
    path: str
    rows: int
    visible_rows: int
    invisible_rows: int
    clips: int
    scene: str
    modified_at: float

    def to_qml(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "rows": self.rows,
            "visible_rows": self.visible_rows,
            "invisible_rows": self.invisible_rows,
            "clips": self.clips,
            "scene": self.scene,
            "modified_at": self.modified_at,
        }


def _gt_generated_dir() -> Path:
    return ROOT / "configs" / "gt_minipack" / "generated"


def _truthy_visible(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _classify_scene(*parts: str) -> str:
    text = " ".join(parts).lower()
    normalized = text.replace("\\", "/")
    negative = any(token in text for token in ("bird", "airplane", "plane", "negative", "false"))
    if "infrared" in text or "_ir" in text or "ir_" in text or text.startswith("ir") or "/ir/" in normalized:
        return "IR_NEGATIVE" if negative else "IR"
    if "night" in text:
        return "NIGHT_NEGATIVE" if negative else "NIGHT"
    if "_eo" in text or " eo" in text or "rgb" in text or "day" in text or "/eo/" in normalized:
        return "EO_NEGATIVE" if negative else "EO"
    return "NEGATIVE" if negative else "UNKNOWN"


def _human_scene(scene: str) -> str:
    return "ДРУГОЕ" if scene == "UNKNOWN" else scene


def _scan_gt_files() -> tuple[list[GtFileSummary], Counter[str], int, int, int, set[str], list[str]]:
    files: list[GtFileSummary] = []
    scene_counts: Counter[str] = Counter()
    total_rows = 0
    total_visible = 0
    total_invisible = 0
    clips: set[str] = set()
    warnings: list[str] = []
    generated = _gt_generated_dir()
    if not generated.exists():
        return files, scene_counts, total_rows, total_visible, total_invisible, clips, warnings

    for path in sorted(generated.glob("*.csv"), key=lambda item: item.stat().st_mtime, reverse=True):
        rows = 0
        visible_rows = 0
        invisible_rows = 0
        file_sources: set[str] = set()
        try:
            with path.open("r", encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    rows += 1
                    source = str(row.get("source", "")).strip()
                    if source:
                        file_sources.add(source)
                        clips.add(source)
                    if _truthy_visible(row.get("visible", "")):
                        visible_rows += 1
                    else:
                        invisible_rows += 1
        except Exception as exc:
            warnings.append(f"{path.name}: {exc}")
            continue

        scene = _classify_scene(path.name, " ".join(sorted(file_sources)))
        files.append(
            GtFileSummary(
                name=path.name,
                path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                rows=rows,
                visible_rows=visible_rows,
                invisible_rows=invisible_rows,
                clips=len(file_sources),
                scene=scene,
                modified_at=float(path.stat().st_mtime),
            )
        )
        if file_sources:
            scene_counts.update({scene: len(file_sources)})
        else:
            scene_counts.update({scene: 1})
        total_rows += rows
        total_visible += visible_rows
        total_invisible += invisible_rows

    return files, scene_counts, total_rows, total_visible, total_invisible, clips, warnings


class TargetLabBridge(QObject):
    """Read-only coordinator for the unified Target Lab view."""

    changed = Signal()

    def __init__(
        self,
        dts_bridge: object | None = None,
        gt_assist_bridge: object | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._dts_bridge = dts_bridge
        self._gt_assist_bridge = gt_assist_bridge
        self._gt_files: list[GtFileSummary] = []
        self._scene_counts: Counter[str] = Counter()
        self._gt_rows = 0
        self._gt_visible_rows = 0
        self._gt_invisible_rows = 0
        self._gt_clips: set[str] = set()
        self._warnings: list[str] = []
        self._gt_diagnostics_process: QProcess | None = None
        self._gt_diagnostics_running = False
        self._gt_diagnostics_title = "GT диагностика не запускалась"
        self._gt_diagnostics_body = "Разметьте или проверьте GT базу, затем запустите проверку трекера."
        self._gt_diagnostics_tone = "idle"
        self._gt_diagnostics_result_dir = ""
        self._gt_diagnostics_log_lines: list[str] = []
        self._gt_diagnostics_log_tail = ""
        self._diagnostic_rows: list[dict[str, Any]] = []
        self._diagnostic_risks: list[str] = []

        changed_signal = getattr(dts_bridge, "changed", None)
        if changed_signal is not None:
            try:
                changed_signal.connect(self.changed.emit)
            except Exception:
                pass

        exported_signal = getattr(gt_assist_bridge, "exported", None)
        if exported_signal is not None:
            try:
                exported_signal.connect(self.refresh)
            except Exception:
                pass

        self.refresh()

    @Slot()
    def refresh(self) -> None:
        (
            self._gt_files,
            self._scene_counts,
            self._gt_rows,
            self._gt_visible_rows,
            self._gt_invisible_rows,
            self._gt_clips,
            self._warnings,
        ) = _scan_gt_files()
        if not self._gt_diagnostics_running:
            self._load_latest_diagnostics()
        self.changed.emit()

    @Property(int, notify=changed)
    def gtFileCount(self) -> int:
        return len(self._gt_files)

    @Property(int, notify=changed)
    def gtClipCount(self) -> int:
        return len(self._gt_clips)

    @Property(int, notify=changed)
    def gtRowCount(self) -> int:
        return int(self._gt_rows)

    @Property(int, notify=changed)
    def gtVisibleRowCount(self) -> int:
        return int(self._gt_visible_rows)

    @Property(int, notify=changed)
    def gtInvisibleRowCount(self) -> int:
        return int(self._gt_invisible_rows)

    @Property(str, notify=changed)
    def gtFilesJson(self) -> str:
        return json.dumps([item.to_qml() for item in self._gt_files[:40]], ensure_ascii=False)

    @Property(str, notify=changed)
    def gtSceneSummary(self) -> str:
        if not self._scene_counts:
            return "нет GT"
        order = ("IR", "IR_NEGATIVE", "EO", "EO_NEGATIVE", "NIGHT", "NIGHT_NEGATIVE", "NEGATIVE", "UNKNOWN")
        parts = [f"{key}:{self._scene_counts[key]}" for key in order if self._scene_counts.get(key, 0)]
        return " · ".join(parts)

    @Property(str, notify=changed)
    def gtSummaryText(self) -> str:
        if not self._gt_files:
            return "GT база пуста"
        return (
            f"{len(self._gt_files)} CSV · {len(self._gt_clips)} клипов · "
            f"{self._gt_rows} кадров · visible {self._gt_visible_rows} · invisible {self._gt_invisible_rows}"
        )

    @Property(str, notify=changed)
    def gtWarningText(self) -> str:
        return " · ".join(self._warnings[:3])

    def _dts_count(self, status: str) -> int:
        bridge = self._dts_bridge
        if bridge is None:
            return 0
        try:
            if status == "all":
                return int(getattr(bridge, "totalCount", 0))
            return int(bridge.countStatus(status))  # type: ignore[attr-defined]
        except Exception:
            return 0

    @Property(int, notify=changed)
    def dtsTotalCount(self) -> int:
        return self._dts_count("all")

    @Property(int, notify=changed)
    def dtsNewCount(self) -> int:
        return self._dts_count("new")

    @Property(int, notify=changed)
    def dtsAcceptedCount(self) -> int:
        return self._dts_count("accepted")

    @Property(int, notify=changed)
    def dtsNegativeCount(self) -> int:
        return self._dts_count("hard_negative")

    @Property(int, notify=changed)
    def dtsRejectedCount(self) -> int:
        return self._dts_count("rejected")

    @Property(int, notify=changed)
    def candidateFrameCount(self) -> int:
        try:
            return int(getattr(self._dts_bridge, "candidateFrameCount", 0))
        except Exception:
            return 0

    @Property(str, notify=changed)
    def candidateStatusLabel(self) -> str:
        try:
            return str(getattr(self._dts_bridge, "candidateStatusLabel", "нет данных"))
        except Exception:
            return "нет данных"

    @Property(str, notify=changed)
    def labSummaryText(self) -> str:
        return (
            f"DTS {self.dtsTotalCount} · NEW {self.dtsNewCount} · ACCEPTED {self.dtsAcceptedCount} · "
            f"NEG {self.dtsNegativeCount} · GT {self.gtFileCount} CSV · {self.gtClipCount} клипов"
        )

    def _scene_order(self) -> tuple[str, ...]:
        return ("IR", "IR_NEGATIVE", "EO", "EO_NEGATIVE", "NIGHT", "NIGHT_NEGATIVE", "NEGATIVE", "UNKNOWN")

    def _material_groups(self) -> list[dict[str, Any]]:
        groups: dict[str, dict[str, Any]] = {}
        for item in self._gt_files:
            group = groups.setdefault(
                item.scene,
                {
                    "scene": item.scene,
                    "clips": 0,
                    "frames": 0,
                    "visible_frames": 0,
                    "invisible_frames": 0,
                    "role": "фон / не цель" if "NEGATIVE" in item.scene else "проверка",
                },
            )
            group["clips"] += max(1, int(item.clips))
            group["frames"] += int(item.rows)
            group["visible_frames"] += int(item.visible_rows)
            group["invisible_frames"] += int(item.invisible_rows)
        order = {name: idx for idx, name in enumerate(self._scene_order())}
        return sorted(groups.values(), key=lambda row: (order.get(str(row["scene"]), 99), str(row["scene"])))

    @Property(str, notify=changed)
    def materialTitle(self) -> str:
        clip_word = "клип" if self.gtClipCount == 1 else "клипа" if 2 <= self.gtClipCount <= 4 else "клипов"
        frame_word = "кадр" if self.gtRowCount == 1 else "кадра" if 2 <= self.gtRowCount <= 4 else "кадров"
        return f"{self.gtClipCount} {clip_word} · {self.gtRowCount} {frame_word}"

    @Property(str, notify=changed)
    def materialSubtitle(self) -> str:
        groups = self._material_groups()
        if not groups:
            return "Материал не собран"
        return " · ".join(f"{_human_scene(str(row['scene']))}:{row['clips']}" for row in groups)

    @Property(str, notify=changed)
    def materialCardsJson(self) -> str:
        return json.dumps(self._material_groups(), ensure_ascii=False)

    def _diagnostic_groups(self) -> list[dict[str, Any]]:
        if not self._diagnostic_rows:
            return []
        groups: dict[str, dict[str, Any]] = {}
        for row in self._diagnostic_rows:
            scene = str(row.get("scene") or _classify_scene(str(row.get("source", "")), str(row.get("clip", ""))))
            sampled = max(1, int(row.get("sampled_frames", 0) or 0))
            group = groups.setdefault(
                scene,
                {
                    "scene": scene,
                    "clips": 0,
                    "frames": 0,
                    "_recall_sum": 0.0,
                    "_false_sum": 0.0,
                    "_fps_sum": 0.0,
                    "_jitter_max": 0.0,
                    "_weight": 0,
                },
            )
            group["clips"] += 1
            group["frames"] += sampled
            group["_weight"] += sampled
            group["_recall_sum"] += float(row.get("recall_iou_01", 0.0) or 0.0) * sampled
            group["_false_sum"] += float(row.get("false_lock_rate_sampled", 0.0) or 0.0) * sampled
            group["_fps_sum"] += float(row.get("avg_fps", 0.0) or 0.0) * sampled
            group["_jitter_max"] = max(group["_jitter_max"], float(row.get("bbox_scale_step_p95", 0.0) or 0.0))

        cards: list[dict[str, Any]] = []
        for group in groups.values():
            weight = max(1, int(group["_weight"]))
            recall = float(group["_recall_sum"]) / weight
            false_lock = float(group["_false_sum"]) / weight
            fps = float(group["_fps_sum"]) / weight
            jitter = float(group["_jitter_max"])
            if recall < 0.65 or false_lock > 0.25 or jitter > 0.60:
                status = "слабое место"
                tone = "warn"
            elif recall >= 0.78 and false_lock <= 0.15:
                status = "держится"
                tone = "success"
            else:
                status = "наблюдать"
                tone = "idle"
            cards.append(
                {
                    "scene": group["scene"],
                    "clips": int(group["clips"]),
                    "frames": int(group["frames"]),
                    "recall_pct": int(round(recall * 100)),
                    "false_lock_pct": int(round(false_lock * 100)),
                    "fps": int(round(fps)),
                    "jitter": round(jitter, 2),
                    "status": status,
                    "tone": tone,
                }
            )
        order = {name: idx for idx, name in enumerate(self._scene_order())}
        return sorted(cards, key=lambda row: (0 if row["status"] == "слабое место" else 1, order.get(str(row["scene"]), 99)))

    @Property(str, notify=changed)
    def checkCardsJson(self) -> str:
        return json.dumps(self._diagnostic_groups(), ensure_ascii=False)

    @Property(str, notify=changed)
    def checkTitle(self) -> str:
        cards = self._diagnostic_groups()
        if self._gt_diagnostics_running:
            return "Проверка идет"
        if not cards:
            return "Проверка не запускалась"
        weak = sum(1 for item in cards if item["status"] == "слабое место")
        return f"{len(cards)} сцен · {weak} слабых"

    @Property(str, notify=changed)
    def checkSubtitle(self) -> str:
        if self._gt_diagnostics_running:
            return self._gt_diagnostics_body
        if not self._diagnostic_rows:
            return "Запустите проверку, чтобы увидеть recall, промахи трекера и FPS по сценам."
        return self._gt_diagnostics_body

    def _weakest_scene(self) -> dict[str, Any] | None:
        weak = [card for card in self._diagnostic_groups() if card["status"] == "слабое место"]
        if not weak:
            return None
        return min(weak, key=lambda card: (int(card.get("recall_pct", 100)), -int(card.get("false_lock_pct", 0))))

    @Property(str, notify=changed)
    def nextActionTitle(self) -> str:
        if self._gt_diagnostics_running:
            return "Подождать результат"
        if not self._gt_files and not self._diagnostic_rows:
            return "Собрать материал"
        if not self._diagnostic_rows:
            return "Проверить трекер"
        weak = self._weakest_scene()
        if weak is None:
            return "База годится для сравнения"
        scene = str(weak["scene"])
        if "NEGATIVE" in scene or scene == "NEGATIVE":
            return "Усилить защиту"
        return f"Улучшить {scene}"

    @Property(str, notify=changed)
    def nextActionBody(self) -> str:
        if self._gt_diagnostics_running:
            return self._gt_diagnostics_body
        if not self._gt_files and not self._diagnostic_rows:
            return "Откройте видео и разметьте цель. После этого появится первая проверочная база."
        if not self._diagnostic_rows:
            return "Запустите проверку на размеченной базе. Это покажет, где трекер слабый."
        weak = self._weakest_scene()
        if weak is None:
            return "Слабых сцен не найдено. Можно использовать базу для сравнения candidate."
        scene = str(weak["scene"])
        recall = int(weak["recall_pct"])
        false_lock = int(weak["false_lock_pct"])
        if "NEGATIVE" in scene or scene == "NEGATIVE":
            return f"{scene}: трекер держит фон {false_lock}%. Нужны hard negatives и проверка candidate."
        return f"{scene}: трекер видит {recall}% и держит не там {false_lock}%. Соберите улучшение по этой сцене."

    @Property(str, notify=changed)
    def nextActionTone(self) -> str:
        if self._gt_diagnostics_running:
            return "progress"
        if not self._gt_files and not self._diagnostic_rows:
            return "idle"
        if not self._diagnostic_rows:
            return "progress"
        return "warn" if self._weakest_scene() is not None else "success"

    @Property(str, notify=changed)
    def primaryActionLabel(self) -> str:
        if self._gt_diagnostics_running:
            return "ИДЕТ ПРОВЕРКА"
        if not self._gt_files and not self._diagnostic_rows:
            return "РАЗМЕТИТЬ ВИДЕО"
        if not self._diagnostic_rows:
            return "ПРОВЕРИТЬ ТРЕКЕР"
        if self._weakest_scene() is not None:
            return "СОБРАТЬ УЛУЧШЕНИЕ"
        return "СРАВНИТЬ КАНДИДАТ"

    @Property(bool, notify=changed)
    def gtDiagnosticsRunning(self) -> bool:
        return bool(self._gt_diagnostics_running)

    @Property(bool, notify=changed)
    def gtDiagnosticsCanRun(self) -> bool:
        return bool(self._gt_files and not self._gt_diagnostics_running)

    @Property(str, notify=changed)
    def gtDiagnosticsTitle(self) -> str:
        return self._gt_diagnostics_title

    @Property(str, notify=changed)
    def gtDiagnosticsBody(self) -> str:
        return self._gt_diagnostics_body

    @Property(str, notify=changed)
    def gtDiagnosticsTone(self) -> str:
        return self._gt_diagnostics_tone

    @Property(str, notify=changed)
    def gtDiagnosticsResultDir(self) -> str:
        return self._gt_diagnostics_result_dir

    @Property(str, notify=changed)
    def gtDiagnosticsLogTail(self) -> str:
        return self._gt_diagnostics_log_tail

    def _gt_diagnostics_command(self) -> tuple[str, list[str]]:
        return (
            sys.executable,
            [
                str(ROOT / "python_scripts" / "run_tracking_gt_diagnostics.py"),
                str(_gt_generated_dir()),
                "--preset",
                "tracking_live_auto",
                "--scene-aware",
                "--render-errors",
                "--max-error-samples",
                "4",
                "--device",
                "mps",
                "--tag",
                "target_lab",
            ],
        )

    def _set_gt_diagnostics_status(self, title: str, body: str, tone: str = "idle") -> None:
        self._gt_diagnostics_title = title
        self._gt_diagnostics_body = body
        self._gt_diagnostics_tone = tone
        self.changed.emit()

    @Slot(result=str)
    def runGtDiagnostics(self) -> str:
        if self._gt_diagnostics_running:
            return "GT диагностика уже идет"
        self.refresh()
        if not self._gt_files:
            self._set_gt_diagnostics_status(
                "GT база пуста",
                "Сначала разметьте хотя бы один клип во вкладке РАЗМЕТКА GT.",
                "warn",
            )
            return "GT диагностика заблокирована: нет CSV"

        program, args = self._gt_diagnostics_command()
        process = QProcess(self)
        process.setWorkingDirectory(str(ROOT))
        process.setProgram(program)
        process.setArguments(args)
        env = QProcessEnvironment.systemEnvironment()
        existing_pythonpath = env.value("PYTHONPATH", "")
        env.insert("PYTHONPATH", "src" if not existing_pythonpath else f"src:{existing_pythonpath}")
        process.setProcessEnvironment(env)
        process.readyReadStandardOutput.connect(lambda: self._on_gt_diagnostics_output(process, stderr=False))
        process.readyReadStandardError.connect(lambda: self._on_gt_diagnostics_output(process, stderr=True))
        process.finished.connect(
            lambda exit_code, exit_status: self._on_gt_diagnostics_finished(
                exit_code,
                exit_status,
                self._find_latest_gt_diagnostics_dir(),
            )
        )
        process.errorOccurred.connect(lambda error: self._on_gt_diagnostics_error(int(error)))

        self._gt_diagnostics_process = process
        self._gt_diagnostics_running = True
        self._gt_diagnostics_log_lines = []
        self._gt_diagnostics_log_tail = ""
        self._gt_diagnostics_result_dir = ""
        self._diagnostic_rows = []
        self._diagnostic_risks = []
        self._set_gt_diagnostics_status(
            "GT диагностика идет",
            f"Проверяю {self.gtFileCount} CSV / {self.gtClipCount} клипов на текущем трекере.",
            "progress",
        )
        process.start()
        if not process.waitForStarted(3000):
            self._gt_diagnostics_running = False
            self._gt_diagnostics_process = None
            self._set_gt_diagnostics_status("GT диагностика не стартовала", "QProcess не запустился.", "error")
            return "GT диагностика не стартовала"
        return "GT диагностика запущена"

    @Slot(result=str)
    def cancelGtDiagnostics(self) -> str:
        if not self._gt_diagnostics_running or self._gt_diagnostics_process is None:
            return "GT диагностика не запущена"
        process = self._gt_diagnostics_process
        process.terminate()
        if not process.waitForFinished(3000):
            process.kill()
        self._gt_diagnostics_running = False
        self._gt_diagnostics_process = None
        self._set_gt_diagnostics_status("GT диагностика остановлена", "Проверку можно запустить заново.", "warn")
        return "GT диагностика остановлена"

    def _on_gt_diagnostics_output(self, process: QProcess, *, stderr: bool) -> None:
        raw = process.readAllStandardError() if stderr else process.readAllStandardOutput()
        text = bytes(raw).decode("utf-8", "replace")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return
        self._gt_diagnostics_log_lines.extend(lines)
        if len(self._gt_diagnostics_log_lines) > 10:
            self._gt_diagnostics_log_lines = self._gt_diagnostics_log_lines[-10:]
        self._gt_diagnostics_log_tail = "\n".join(self._gt_diagnostics_log_lines)
        last = lines[-1]
        if last.startswith("[tracking-gt] out_dir="):
            out_dir = Path(last.split("=", 1)[1].strip())
            self._gt_diagnostics_result_dir = str(out_dir.relative_to(ROOT)) if out_dir.is_relative_to(ROOT) else str(out_dir)
        elif last.startswith("[tracking-gt]"):
            self._gt_diagnostics_body = last.replace("[tracking-gt]", "").strip()
        self.changed.emit()

    def _find_latest_gt_diagnostics_dir(self) -> Path | None:
        base = ROOT / "runs" / "evaluations" / "tracking_gt_diagnostics"
        if not base.exists():
            return None
        items = [path for path in base.glob("target_lab_*") if path.is_dir()]
        if not items:
            return None
        return max(items, key=lambda path: path.stat().st_mtime)

    def _load_latest_diagnostics(self) -> bool:
        result_dir = self._find_latest_gt_diagnostics_dir()
        if result_dir is None:
            return False
        summary_path = result_dir / "summary.json"
        if not summary_path.exists():
            return False
        return self._apply_diagnostics_summary(result_dir, summary_path, prefix="Последняя проверка")

    def _apply_diagnostics_summary(self, result_dir: Path, summary_path: Path, *, prefix: str) -> bool:
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            rows = data.get("rows", [])
            risks = data.get("risks", [])
            self._diagnostic_rows = list(rows) if isinstance(rows, list) else []
            self._diagnostic_risks = list(risks) if isinstance(risks, list) else []
            self._gt_diagnostics_result_dir = (
                str(result_dir.relative_to(ROOT)) if result_dir.is_relative_to(ROOT) else str(result_dir)
            )
            clip_n = len(rows) if isinstance(rows, list) else 0
            risk_n = len(risks) if isinstance(risks, list) else 0
            tone = "warn" if risk_n else "success"
            risk_word = "риск" if risk_n == 1 else "рисков"
            self._gt_diagnostics_title = "GT диагностика готова"
            self._gt_diagnostics_body = (
                f"{prefix}: {clip_n} клипов · {risk_n} {risk_word} · "
                "«мимо» означает bbox трекера вне вашей разметки."
            )
            self._gt_diagnostics_tone = tone
            return True
        except Exception as exc:
            self._gt_diagnostics_title = "GT диагностика не прочитана"
            self._gt_diagnostics_body = f"summary.json не разобран: {exc}"
            self._gt_diagnostics_tone = "warn"
            return False

    def _on_gt_diagnostics_error(self, error: int) -> None:
        self._gt_diagnostics_running = False
        self._gt_diagnostics_process = None
        self._set_gt_diagnostics_status("GT диагностика остановлена", f"Ошибка процесса {error}.", "error")

    def _on_gt_diagnostics_finished(
        self,
        exit_code: int,
        _exit_status: object,
        result_dir: Path | None,
    ) -> None:
        process = self._gt_diagnostics_process
        if process is not None:
            tail = (
                bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
                + "\n"
                + bytes(process.readAllStandardError()).decode("utf-8", "replace")
            ).strip()
            if tail:
                self._gt_diagnostics_log_lines.extend([line.strip() for line in tail.splitlines() if line.strip()])
                if len(self._gt_diagnostics_log_lines) > 10:
                    self._gt_diagnostics_log_lines = self._gt_diagnostics_log_lines[-10:]
                self._gt_diagnostics_log_tail = "\n".join(self._gt_diagnostics_log_lines)

        self._gt_diagnostics_running = False
        self._gt_diagnostics_process = None

        if exit_code != 0:
            self._set_gt_diagnostics_status(
                "GT диагностика упала",
                f"Процесс завершился с кодом {exit_code}. Проверьте лог.",
                "error",
            )
            return

        if result_dir is None:
            self._set_gt_diagnostics_status(
                "GT диагностика без отчета",
                "Процесс завершился, но папка результата не найдена.",
                "warn",
            )
            return

        self._gt_diagnostics_result_dir = (
            str(result_dir.relative_to(ROOT)) if result_dir.is_relative_to(ROOT) else str(result_dir)
        )
        summary_path = result_dir / "summary.json"
        if not summary_path.exists():
            self._set_gt_diagnostics_status(
                "GT диагностика завершена",
                f"Отчет: {self._gt_diagnostics_result_dir}",
                "success",
            )
            return

        if self._apply_diagnostics_summary(result_dir, summary_path, prefix="Проверка готова"):
            self.changed.emit()
        else:
            self._set_gt_diagnostics_status(
                "GT диагностика завершена",
                f"Отчет создан, но summary.json не разобран: {self._gt_diagnostics_body}",
                "warn",
            )
