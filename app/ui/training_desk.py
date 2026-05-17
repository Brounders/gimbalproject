"""DTS — Training Desk dialog (operator annotation review station).

Maximised window over the operator UI; Esc closes.

Layout (matches HTML reference):

    HEAD: title · counters (new/accepted/rejected/staged) · path · time · reload · close
    BODY:
      LEFT  — filters + search + events table
      CENTER — frame preview (with bbox overlay) + crop preview + zoom/bbox toolbar
      RIGHT — record card (status, meta, real quality, real duplicates) + actions
    FOOT: accept/reject/stage hints + export YOLO + build training pack + output path

The DTS uses real quality calculations (``training_desk_quality.evaluate_record_quality``)
and real duplicate detection (``find_duplicates``).  Export and pack staging are
wired to existing python_scripts via subprocess so the DTS does not start training
automatically — it only writes label/pack artifacts to disk.
"""
from __future__ import annotations

import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.training_desk_data import (
    STATUS_ACCEPTED,
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
    QUALITY_FAIL,
    QUALITY_NA,
    QUALITY_OK,
    QUALITY_WARN,
    DuplicateLink,
    QualityReport,
    aggregate_quality,
    duplicate_summary,
    evaluate_record_quality,
    find_duplicates,
)
from app.ui.theme import refresh_widget_style


_FILTERS: list[tuple[str, str]] = [
    ('all', 'Все'),
    (STATUS_NEW, 'Новые'),
    (STATUS_ACCEPTED, 'Принятые'),
    (STATUS_REJECTED, 'Отклонённые'),
    (STATUS_STAGED, 'В pack'),
]


class TrainingDeskDialog(QDialog):
    """DTS Training Desk: real quality + dedup + export wiring."""

    def __init__(self, root: Path, parent=None):
        super().__init__(parent)
        self.setObjectName('TrainingDeskDialog')
        self.root = Path(root)
        self.log_dir = self.root / 'runs' / 'operator_annotations'
        self.state_path = self.log_dir / 'dts_review_state.json'
        self.exports_dir = self.root / 'runs' / 'dts_exports'
        self.packs_dir = self.root / 'runs' / 'operator_training_packs'

        self.records: list[AnnotationRecord] = []
        self.filtered: list[AnnotationRecord] = []
        self.current_status_filter: str = 'all'
        self.current_record_id: Optional[str] = None
        self.show_bbox: bool = True
        self.zoom: float = 1.0
        self._duplicate_links: dict[str, list[DuplicateLink]] = {}
        self._quality_cache: dict[str, QualityReport] = {}

        self.setWindowTitle('DTS — Training Desk')
        self.setStyleSheet('QDialog#TrainingDeskDialog { background: #1A222C; }')
        self._build_ui()

        self._esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._esc_shortcut.activated.connect(self.close)

    # ── UI build ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_left_sidebar(), 0)
        body.addWidget(self._build_center_preview(), 1)
        body.addWidget(self._build_right_record(), 0)
        root.addLayout(body, 1)

        root.addWidget(self._build_footer())

    def _build_header(self) -> QFrame:
        head = QFrame()
        head.setObjectName('DtsHeader')
        layout = QHBoxLayout(head)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(14)

        brand = QLabel('DTS')
        brand.setObjectName('DtsTitle')
        layout.addWidget(brand)
        sub = QLabel('— Training Desk')
        sub.setObjectName('DtsSubtitle')
        layout.addWidget(sub)
        layout.addStretch(1)

        self.cnt_new = QLabel('● NEW 0')
        self.cnt_new.setObjectName('DtsCounterPill')
        self.cnt_new.setProperty('tone', 'new')
        self.cnt_acc = QLabel('● ACC 0')
        self.cnt_acc.setObjectName('DtsCounterPill')
        self.cnt_acc.setProperty('tone', 'accepted')
        self.cnt_rej = QLabel('● REJ 0')
        self.cnt_rej.setObjectName('DtsCounterPill')
        self.cnt_rej.setProperty('tone', 'rejected')
        self.cnt_stg = QLabel('● STG 0')
        self.cnt_stg.setObjectName('DtsCounterPill')
        self.cnt_stg.setProperty('tone', 'staged')
        for w in (self.cnt_new, self.cnt_acc, self.cnt_rej, self.cnt_stg):
            layout.addWidget(w)

        layout.addSpacing(12)
        self.path_label = QLabel(str(self.log_dir.relative_to(self.root)))
        self.path_label.setObjectName('DtsSubtitle')
        layout.addWidget(self.path_label)

        self.clock_label = QLabel(time.strftime('%H:%M:%S'))
        self.clock_label.setObjectName('DtsSubtitle')
        layout.addWidget(self.clock_label)

        self.reload_btn = QPushButton('⟳')
        self.reload_btn.setObjectName('DtsExport')
        self.reload_btn.setToolTip('Перезагрузить annotation logs')
        self.reload_btn.clicked.connect(self.reload)
        layout.addWidget(self.reload_btn)

        self.close_btn = QPushButton('✕')
        self.close_btn.setObjectName('DtsExport')
        self.close_btn.setToolTip('Закрыть DTS (Esc)')
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(
            lambda: self.clock_label.setText(time.strftime('%H:%M:%S'))
        )
        self._clock_timer.start(1000)
        return head

    def _build_left_sidebar(self) -> QFrame:
        side = QFrame()
        side.setObjectName('DtsSidebar')
        side.setFixedWidth(300)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Filters + search in padded sub-container
        filters_frame = QFrame()
        filters_layout = QVBoxLayout(filters_frame)
        filters_layout.setContentsMargins(9, 9, 9, 7)
        filters_layout.setSpacing(5)

        chips_row = QHBoxLayout()
        chips_row.setContentsMargins(0, 0, 0, 0)
        chips_row.setSpacing(4)
        self.filter_buttons: dict[str, QPushButton] = {}
        for status, label in _FILTERS:
            btn = QPushButton(label)
            btn.setObjectName('DtsFilterBtn')
            btn.clicked.connect(lambda checked=False, s=status: self._set_filter(s))
            self.filter_buttons[status] = btn
            chips_row.addWidget(btn)
        chips_row.addStretch(1)
        filters_layout.addLayout(chips_row)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('ID, кадр, путь…')
        self.search_edit.textChanged.connect(self._refresh_table)
        filters_layout.addWidget(self.search_edit)
        layout.addWidget(filters_frame)

        events_title = QLabel('ANNOTATION EVENTS')
        events_title.setObjectName('DtsPanelLabel')
        events_container = QFrame()
        events_container_layout = QVBoxLayout(events_container)
        events_container_layout.setContentsMargins(0, 7, 0, 0)
        events_container_layout.setSpacing(0)
        events_title_padded = QFrame()
        events_title_layout = QHBoxLayout(events_title_padded)
        events_title_layout.setContentsMargins(12, 0, 12, 6)
        events_title_layout.addWidget(events_title)
        events_container_layout.addWidget(events_title_padded)
        layout.addWidget(events_container)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName('DtsEventsTable')
        self.table.setHorizontalHeaderLabels(['STATUS', 'ID', 'FRAME', 'CLIP', 'BBOX'])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_table_selection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, 1)

        self._set_filter_active(self.current_status_filter)
        return side

    def _build_center_preview(self) -> QFrame:
        center = QFrame()
        center.setObjectName('DtsCenter')
        layout = QVBoxLayout(center)
        layout.setContentsMargins(16, 9, 16, 10)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        self.preview_meta_label = QLabel('—')
        self.preview_meta_label.setObjectName('DtsPanelLabel')
        top_row.addWidget(self.preview_meta_label)
        top_row.addStretch(1)
        self.preview_index_label = QLabel('—')
        self.preview_index_label.setObjectName('DtsPanelLabel')
        top_row.addWidget(self.preview_index_label)
        layout.addLayout(top_row)

        previews = QHBoxLayout()
        previews.setSpacing(10)
        self.preview_label = QLabel('Нет выбранной разметки')
        self.preview_label.setObjectName('DtsPreviewSurface')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(560, 380)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        previews.addWidget(self.preview_label, 3)

        self.crop_label = QLabel('CROP')
        self.crop_label.setObjectName('DtsCropSurface')
        self.crop_label.setAlignment(Qt.AlignCenter)
        self.crop_label.setMinimumSize(220, 380)
        self.crop_label.setMaximumWidth(280)
        previews.addWidget(self.crop_label, 1)
        layout.addLayout(previews, 1)

        tools = QHBoxLayout()
        self.zoom_out_btn = QPushButton('−')
        self.zoom_in_btn = QPushButton('+')
        self.zoom_label = QLabel('×1.0')
        self.zoom_label.setObjectName('DtsPanelLabel')
        self.toggle_bbox_btn = QPushButton('● BBOX')
        self.prev_btn = QPushButton('◀')
        self.next_btn = QPushButton('▶')
        for btn in (self.zoom_out_btn, self.zoom_in_btn, self.toggle_bbox_btn,
                    self.prev_btn, self.next_btn):
            btn.setObjectName('DtsExport')

        self.zoom_out_btn.clicked.connect(lambda: self._set_zoom(max(0.5, self.zoom - 0.25)))
        self.zoom_in_btn.clicked.connect(lambda: self._set_zoom(min(3.0, self.zoom + 0.25)))
        self.toggle_bbox_btn.clicked.connect(self._toggle_bbox)
        self.prev_btn.clicked.connect(lambda: self._move_selection(-1))
        self.next_btn.clicked.connect(lambda: self._move_selection(1))

        tools.addWidget(self.zoom_out_btn)
        tools.addWidget(self.zoom_label)
        tools.addWidget(self.zoom_in_btn)
        tools.addSpacing(12)
        tools.addWidget(self.toggle_bbox_btn)
        tools.addStretch(1)
        tools.addWidget(self.prev_btn)
        tools.addWidget(self.next_btn)
        layout.addLayout(tools)
        return center

    def _build_right_record(self) -> QFrame:
        outer = QFrame()
        outer.setObjectName('DtsRecordPanel')
        outer.setFixedWidth(320)
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer_layout.addWidget(scroll, 1)

        panel = QWidget()
        scroll.setWidget(panel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        head_row = QHBoxLayout()
        self.record_id_label = QLabel('—')
        self.record_id_label.setObjectName('DtsRecordHeading')
        head_row.addWidget(self.record_id_label)
        head_row.addStretch(1)
        self.record_class_label = QLabel('—')
        self.record_class_label.setObjectName('DtsRecordClass')
        head_row.addWidget(self.record_class_label)
        layout.addLayout(head_row)

        self.record_status_label = QLabel('СТАТУС: —')
        self.record_status_label.setObjectName('DtsRecordVal')
        layout.addWidget(self.record_status_label)

        self.record_meta_label = QLabel('—')
        self.record_meta_label.setObjectName('DtsRecordVal')
        self.record_meta_label.setWordWrap(True)
        layout.addWidget(self.record_meta_label)

        # Quality block
        q_title_row = QHBoxLayout()
        q_title = QLabel('QUALITY')
        q_title.setObjectName('DtsPanelLabel')
        q_title_row.addWidget(q_title)
        self.quality_summary_label = QLabel('—')
        self.quality_summary_label.setObjectName('DtsPanelLabel')
        q_title_row.addStretch(1)
        q_title_row.addWidget(self.quality_summary_label)
        layout.addLayout(q_title_row)

        self.quality_rows_layout = QVBoxLayout()
        self.quality_rows_layout.setContentsMargins(0, 0, 0, 0)
        self.quality_rows_layout.setSpacing(4)
        layout.addLayout(self.quality_rows_layout)

        # Duplicates block
        d_title_row = QHBoxLayout()
        d_title = QLabel('ДУБЛИКАТЫ')
        d_title.setObjectName('DtsPanelLabel')
        d_title_row.addWidget(d_title)
        self.dup_summary_label = QLabel('0')
        self.dup_summary_label.setObjectName('DtsPanelLabel')
        d_title_row.addStretch(1)
        d_title_row.addWidget(self.dup_summary_label)
        layout.addLayout(d_title_row)

        self.dup_list_label = QLabel('—')
        self.dup_list_label.setObjectName('DtsRecordVal')
        self.dup_list_label.setWordWrap(True)
        layout.addWidget(self.dup_list_label)

        layout.addStretch(1)

        # Action buttons
        self.stage_btn = QPushButton('● В TRAINING PACK')
        self.stage_btn.setObjectName('DtsStage')
        self.stage_btn.clicked.connect(lambda: self._set_current_status(STATUS_STAGED))
        layout.addWidget(self.stage_btn)

        action_row = QHBoxLayout()
        self.accept_btn = QPushButton('✓ ПРИНЯТЬ')
        self.accept_btn.setObjectName('DtsAccept')
        self.accept_btn.clicked.connect(lambda: self._set_current_status(STATUS_ACCEPTED))
        self.reject_btn = QPushButton('✕ ОТКЛОНИТЬ')
        self.reject_btn.setObjectName('DtsReject')
        self.reject_btn.clicked.connect(lambda: self._set_current_status(STATUS_REJECTED))
        action_row.addWidget(self.accept_btn)
        action_row.addWidget(self.reject_btn)
        layout.addLayout(action_row)
        return outer

    def _build_footer(self) -> QFrame:
        foot = QFrame()
        foot.setObjectName('DtsFooter')
        layout = QHBoxLayout(foot)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        self.foot_stats_label = QLabel('ACCEPTED 0 · STAGED 0')
        self.foot_stats_label.setObjectName('DtsPanelLabel')
        layout.addWidget(self.foot_stats_label)
        layout.addStretch(1)

        self.foot_path_label = QLabel('—')
        self.foot_path_label.setObjectName('DtsPanelLabel')
        layout.addWidget(self.foot_path_label)

        self.export_btn = QPushButton('↓ ЭКСПОРТ YOLO')
        self.export_btn.setObjectName('DtsExport')
        self.export_btn.clicked.connect(self._do_export_yolo)
        layout.addWidget(self.export_btn)

        self.pack_btn = QPushButton('○ СОБРАТЬ PACK')
        self.pack_btn.setObjectName('DtsExport')
        self.pack_btn.setProperty('primary', 'true')
        self.pack_btn.clicked.connect(self._do_build_pack)
        layout.addWidget(self.pack_btn)
        return foot

    # ── Reload + filters ───────────────────────────────────────────────────

    def reload(self) -> None:
        self.records = load_annotation_records(self.log_dir, state_path=self.state_path)
        self._duplicate_links = find_duplicates(self.records)
        self._quality_cache.clear()
        self._refresh_counts()
        self._refresh_table()

    def _set_filter(self, status: str) -> None:
        self.current_status_filter = status
        self._set_filter_active(status)
        self._refresh_table()

    def _set_filter_active(self, status: str) -> None:
        for key, btn in self.filter_buttons.items():
            btn.setProperty('active', 'true' if key == status else 'false')
            refresh_widget_style(btn)

    def _refresh_counts(self) -> None:
        counts = status_counts(self.records)
        self.cnt_new.setText(f"● NEW {counts.get(STATUS_NEW, 0)}")
        self.cnt_acc.setText(f"● ACC {counts.get(STATUS_ACCEPTED, 0)}")
        self.cnt_rej.setText(f"● REJ {counts.get(STATUS_REJECTED, 0)}")
        self.cnt_stg.setText(f"● STG {counts.get(STATUS_STAGED, 0)}")
        self.foot_stats_label.setText(
            f"ACCEPTED {counts.get(STATUS_ACCEPTED, 0)} · "
            f"STAGED {counts.get(STATUS_STAGED, 0)}"
        )

    def _matches_search(self, record: AnnotationRecord, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        return (
            q in record.record_id.lower()
            or q in record.clip_name.lower()
            or q in str(record.frame_index)
            or q in record.source.lower()
            or q in record.event.lower()
        )

    def _refresh_table(self) -> None:
        query = self.search_edit.text().strip() if hasattr(self, 'search_edit') else ''
        if self.current_status_filter == 'all':
            base = list(self.records)
        else:
            base = [r for r in self.records if r.status == self.current_status_filter]
        self.filtered = [r for r in base if self._matches_search(r, query)]

        self.table.setRowCount(len(self.filtered))
        for row, record in enumerate(self.filtered):
            dup_marker = ''
            if record.record_id in self._duplicate_links:
                dup_marker = ' ⊕'
            values = [
                record.status,
                record.record_id[:8] + dup_marker,
                str(record.frame_index),
                record.clip_name,
                record.bbox_size,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, record.record_id)
                self.table.setItem(row, col, item)

        if self.filtered:
            self.table.selectRow(0)
        else:
            self.current_record_id = None
            self.preview_label.setText('Нет записей для выбранного фильтра')
            self.crop_label.setText('—')
            self._set_record_card(None)

    # ── Selection handling ────────────────────────────────────────────────

    def _selected_record(self) -> Optional[AnnotationRecord]:
        if self.current_record_id is None:
            return None
        for record in self.records:
            if record.record_id == self.current_record_id:
                return record
        return None

    def _on_table_selection(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            return
        record_id = selected[0].data(Qt.UserRole)
        self.current_record_id = str(record_id)
        self._render_current()

    def _move_selection(self, delta: int) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        next_row = max(0, min(self.table.rowCount() - 1, row + delta))
        self.table.selectRow(next_row)

    def _set_zoom(self, zoom: float) -> None:
        self.zoom = float(zoom)
        self.zoom_label.setText(f'×{self.zoom:.1f}')
        self._render_current()

    def _toggle_bbox(self) -> None:
        self.show_bbox = not self.show_bbox
        self.toggle_bbox_btn.setText('● BBOX' if self.show_bbox else '○ BBOX')
        self._render_current()

    def _set_current_status(self, status: str) -> None:
        record = self._selected_record()
        if record is None:
            return
        set_record_status(self.records, record.record_id, status)
        save_review_state(self.records, self.state_path)
        self._refresh_counts()
        self._refresh_table()

    # ── Render ────────────────────────────────────────────────────────────

    def _render_current(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        self._set_record_card(record)
        pixmap, crop_pixmap = self._render_pixmaps(record)
        if pixmap is None:
            self.preview_label.setText('Кадр недоступен\n' + (record.source or '—'))
            self.preview_label.setPixmap(QPixmap())
            self.crop_label.setText('—')
            self.crop_label.setPixmap(QPixmap())
            return
        size = self.preview_label.size()
        target = QSize(max(1, int(size.width() * self.zoom)),
                       max(1, int(size.height() * self.zoom)))
        self.preview_label.setPixmap(pixmap.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if crop_pixmap is not None:
            crop_size = self.crop_label.size()
            self.crop_label.setPixmap(crop_pixmap.scaled(crop_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.crop_label.setText('—')

    def _render_pixmaps(self, record: AnnotationRecord) -> tuple[Optional[QPixmap], Optional[QPixmap]]:
        if not record.source or record.bbox_xyxy is None:
            return None, None
        source = Path(record.source)
        if not source.exists():
            return None, None
        cap = cv2.VideoCapture(str(source))
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(record.frame_index)))
            ok, frame = cap.read()
        finally:
            cap.release()
        if not ok or frame is None:
            return None, None
        h, w = frame.shape[:2]
        # Update preview meta line.
        self.preview_meta_label.setText(
            f'{record.clip_name} · кадр {record.frame_index} · {w}×{h}'
        )
        x1, y1, x2, y2 = record.bbox_xyxy
        crop = None
        cx1 = max(0, x1)
        cy1 = max(0, y1)
        cx2 = min(w, x2)
        cy2 = min(h, y2)
        if cx2 > cx1 and cy2 > cy1:
            crop = frame[cy1:cy2, cx1:cx2].copy()
        if self.show_bbox:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (95, 217, 126), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
        pix = QPixmap.fromImage(image)

        crop_pix = None
        if crop is not None and crop.size > 0:
            ch, cw = crop.shape[:2]
            crgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            cimg = QImage(crgb.data, cw, ch, 3 * cw, QImage.Format_RGB888).copy()
            crop_pix = QPixmap.fromImage(cimg)
        return pix, crop_pix

    def _set_record_card(self, record: Optional[AnnotationRecord]) -> None:
        # Clear old quality rows
        while self.quality_rows_layout.count():
            child = self.quality_rows_layout.takeAt(0)
            w = child.widget()
            if w is not None:
                w.deleteLater()

        if record is None:
            self.record_id_label.setText('—')
            self.record_class_label.setText('—')
            self.record_status_label.setText('СТАТУС: —')
            self.record_meta_label.setText('Выберите запись')
            self.quality_summary_label.setText('—')
            self.dup_summary_label.setText('0')
            self.dup_list_label.setText('—')
            self.preview_index_label.setText('—')
            return

        # Header
        self.record_id_label.setText(record.record_id[:10])
        cls_text = record.event.upper().replace('_', ' ')
        self.record_class_label.setText(cls_text)
        self.record_status_label.setText(f'СТАТУС: ● {record.status.upper()}')

        # Meta
        meta_parts = [
            f'FRAME  {record.frame_index}',
            f'BBOX   {record.bbox_size}',
            f'SOURCE {record.clip_name}',
            f'LOG    {Path(record.log_path).name}:{record.line_number}',
        ]
        if record.active_id is not None:
            meta_parts.append(f'ACTIVE {record.active_id}')
        if record.reason:
            meta_parts.append(f'REASON {record.reason}')
        self.record_meta_label.setText('\n'.join(meta_parts))

        # Quality (cache to avoid re-opening videos)
        if record.record_id not in self._quality_cache:
            self._quality_cache[record.record_id] = evaluate_record_quality(record)
        report = self._quality_cache[record.record_id]
        self.quality_summary_label.setText(
            f'{report.warnings} WARN · {report.fails} FAIL'
        )
        for row in report.rows:
            row_widget = self._build_quality_row_widget(row.name, row.state, row.value, row.note)
            self.quality_rows_layout.addWidget(row_widget)

        # Duplicates
        links = self._duplicate_links.get(record.record_id, [])
        if not links:
            self.dup_summary_label.setText('0')
            self.dup_list_label.setText('—')
        else:
            self.dup_summary_label.setText(str(len(links)))
            lines = []
            for link in links[:6]:
                lines.append(
                    f'{link.kind:<7} f{link.other_frame_index} '
                    f'IoU {link.iou:.2f} · {link.other_record_id[:8]}'
                )
            if len(links) > 6:
                lines.append(f'… ещё {len(links) - 6}')
            self.dup_list_label.setText('\n'.join(lines))

        # Preview index "x / N" (within current filtered list)
        if self.filtered and self.current_record_id is not None:
            try:
                idx = next(i for i, r in enumerate(self.filtered) if r.record_id == self.current_record_id)
                self.preview_index_label.setText(f'Запись {idx + 1} / {len(self.filtered)}')
            except StopIteration:
                self.preview_index_label.setText('—')

    def _build_quality_row_widget(self, name: str, state: str, value: str, note: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(8)
        marker_map = {
            QUALITY_OK: '●',
            QUALITY_WARN: '●',
            QUALITY_FAIL: '●',
            QUALITY_NA: '○',
        }
        marker = QLabel(marker_map.get(state, '·'))
        marker.setObjectName('DtsQualityState')
        marker.setProperty('state', state)
        refresh_widget_style(marker)
        marker.setFixedWidth(14)
        layout.addWidget(marker)
        name_label = QLabel(name)
        name_label.setObjectName('DtsQualityRow')
        layout.addWidget(name_label)
        layout.addStretch(1)
        text = value
        if note:
            text = f'{value} · {note}' if value else note
        val_label = QLabel(text or '—')
        val_label.setObjectName('DtsQualityValue')
        layout.addWidget(val_label)
        return row

    # ── Export / Pack actions ──────────────────────────────────────────────

    def _selected_for_training(self) -> list[AnnotationRecord]:
        return training_candidate_records(self.records)

    def _do_export_yolo(self) -> None:
        items = self._selected_for_training()
        if not items:
            QMessageBox.information(
                self,
                'Экспорт YOLO',
                'Нет записей со статусом accepted/staged. Сначала примите или отметьте разметку.',
            )
            return
        ts = time.strftime('%Y%m%d_%H%M%S')
        out_dir = self.exports_dir / ts
        labels_dir = out_dir / 'labels'
        labels_dir.mkdir(parents=True, exist_ok=True)

        # Write a filtered jsonl with only the selected lines (preserving
        # the original JSON line where possible).
        selected_jsonl = out_dir / 'selected_operator_annotations.jsonl'
        manifest_skipped: list[str] = []
        with selected_jsonl.open('w', encoding='utf-8') as out_f:
            for record in items:
                try:
                    src_path = Path(record.log_path)
                    if not src_path.exists():
                        manifest_skipped.append(f'log missing: {record.log_path}')
                        continue
                    with src_path.open('r', encoding='utf-8') as src_f:
                        for idx, line in enumerate(src_f, start=1):
                            if idx == record.line_number:
                                out_f.write(line if line.endswith('\n') else line + '\n')
                                break
                except Exception as exc:
                    manifest_skipped.append(f'{record.record_id}: {exc}')

        # Try to infer frame size from first accepted source video.
        from app.training_desk_quality import _frame_size  # internal helper, intentional
        first_size = None
        for record in items:
            sz = _frame_size(record.source)
            if sz is not None:
                first_size = sz
                break

        if first_size is None:
            QMessageBox.warning(
                self,
                'Экспорт YOLO',
                'Не удалось определить размер кадра по исходным видео. '
                'Экспорт остановлен — bbox без размера дал бы неверную нормализацию.',
            )
            return
        fw, fh = first_size

        # Run the existing exporter as a subprocess against the filtered jsonl.
        cmd = [
            sys.executable,
            str(self.root / 'python_scripts' / 'export_operator_annotations_to_yolo.py'),
            '--input', str(selected_jsonl),
            '--output-dir', str(labels_dir),
            '--manifest-dir', str(out_dir),
            '--frame-width', str(fw),
            '--frame-height', str(fh),
        ]
        try:
            result = subprocess.run(cmd, cwd=str(self.root), capture_output=True, text=True, timeout=120)
            output = (result.stdout + '\n' + result.stderr).strip()
        except Exception as exc:
            QMessageBox.critical(self, 'Экспорт YOLO',
                                 f'Не удалось запустить export_operator_annotations_to_yolo.py:\n{exc}')
            return

        self.foot_path_label.setText(str(out_dir.relative_to(self.root)))
        msg = f'Экспортировано {len(items)} записей.\nПапка: {out_dir}\n\n'
        if manifest_skipped:
            msg += 'Пропущено:\n' + '\n'.join(manifest_skipped[:5]) + '\n\n'
        msg += 'Команда:\n' + ' '.join(shlex.quote(p) for p in cmd) + '\n\n'
        msg += 'Вывод:\n' + (output[:1500] or '—')
        QMessageBox.information(self, 'Экспорт YOLO', msg)

    def _do_build_pack(self) -> None:
        items = self._selected_for_training()
        if not items:
            QMessageBox.information(
                self,
                'Training pack',
                'Нет записей для сборки. Отметьте accepted/staged и попробуйте снова.',
            )
            return
        ts = time.strftime('%Y%m%d_%H%M%S')
        pack_dir = self.packs_dir / f'pack_{ts}'

        cmd = [
            sys.executable,
            str(self.root / 'python_scripts' / 'stage_operator_training_pack.py'),
            '--state-file', str(self.state_path),
            '--log-dir', str(self.log_dir),
            '--output-dir', str(pack_dir),
        ]
        try:
            result = subprocess.run(cmd, cwd=str(self.root), capture_output=True, text=True, timeout=300)
            output = (result.stdout + '\n' + result.stderr).strip()
            ok = result.returncode == 0
        except Exception as exc:
            QMessageBox.critical(self, 'Training pack',
                                 f'Не удалось запустить stage_operator_training_pack.py:\n{exc}')
            return

        self.foot_path_label.setText(str(pack_dir.relative_to(self.root)))
        title = 'Training pack' if ok else 'Training pack — ошибка'
        msg = f'Папка: {pack_dir}\n\n'
        msg += 'Команда:\n' + ' '.join(shlex.quote(p) for p in cmd) + '\n\n'
        msg += 'Вывод:\n' + (output[:1800] or '—')
        QMessageBox.information(self, title, msg)
