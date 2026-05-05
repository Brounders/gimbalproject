from __future__ import annotations

from pathlib import Path

import cv2
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
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
)


class TrainingDeskDialog(QDialog):
    """DTS: compact operator annotation review desk."""

    def __init__(self, root: Path, parent=None):
        super().__init__(parent)
        self.root = Path(root)
        self.log_dir = self.root / 'runs' / 'operator_annotations'
        self.state_path = self.root / 'runs' / 'operator_annotations' / 'dts_review_state.json'
        self.records: list[AnnotationRecord] = []
        self.filtered: list[AnnotationRecord] = []
        self.current_status_filter = 'all'
        self.current_record_id: str | None = None
        self.show_bbox = True
        self.zoom = 1.0

        self.setWindowTitle('DTS — Training Desk')
        self.resize(1280, 820)
        self.setMinimumSize(1120, 740)
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel('DTS')
        title.setObjectName('ActiveTargetId')
        subtitle = QLabel('очередь operator-разметки')
        subtitle.setObjectName('ActiveTargetSub')
        self.counts_label = QLabel('new 0 · accepted 0 · rejected 0 · staged 0')
        self.counts_label.setObjectName('MetricVal')
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch(1)
        header.addWidget(self.counts_label)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(10)
        root.addLayout(body, 1)

        left = QFrame()
        left.setObjectName('GlassPanel')
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)
        left_title = QLabel('Очередь')
        left_title.setObjectName('RailSectionTitle')
        left_layout.addWidget(left_title)
        self.filter_buttons: dict[str, QPushButton] = {}
        for status, label in (
            ('all', 'Все'),
            (STATUS_NEW, 'Новые'),
            (STATUS_ACCEPTED, 'Принятые'),
            (STATUS_REJECTED, 'Отклонённые'),
            (STATUS_STAGED, 'Готовые'),
        ):
            btn = QPushButton(label)
            btn.setObjectName('ModeBtn')
            btn.clicked.connect(lambda checked=False, s=status: self._set_filter(s))
            self.filter_buttons[status] = btn
            left_layout.addWidget(btn)
        left_layout.addStretch(1)
        self.reload_btn = QPushButton('Обновить')
        self.reload_btn.clicked.connect(self.reload)
        left_layout.addWidget(self.reload_btn)
        body.addWidget(left, 0)

        center = QFrame()
        center.setObjectName('GlassPanel')
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(12, 12, 12, 12)
        center_layout.setSpacing(8)
        self.preview_label = QLabel('Нет выбранной разметки')
        self.preview_label.setObjectName('VideoSurface')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(620, 420)
        center_layout.addWidget(self.preview_label, 1)
        preview_tools = QHBoxLayout()
        self.prev_btn = QPushButton('Предыдущий')
        self.next_btn = QPushButton('Следующий')
        self.zoom_out_btn = QPushButton('Zoom -')
        self.zoom_in_btn = QPushButton('Zoom +')
        self.toggle_bbox_btn = QPushButton('BBox on')
        self.prev_btn.clicked.connect(lambda: self._move_selection(-1))
        self.next_btn.clicked.connect(lambda: self._move_selection(1))
        self.zoom_out_btn.clicked.connect(lambda: self._set_zoom(max(0.5, self.zoom - 0.25)))
        self.zoom_in_btn.clicked.connect(lambda: self._set_zoom(min(3.0, self.zoom + 0.25)))
        self.toggle_bbox_btn.clicked.connect(self._toggle_bbox)
        for btn in (self.prev_btn, self.next_btn, self.zoom_out_btn, self.zoom_in_btn, self.toggle_bbox_btn):
            preview_tools.addWidget(btn)
        preview_tools.addStretch(1)
        center_layout.addLayout(preview_tools)
        body.addWidget(center, 1)

        right = QFrame()
        right.setObjectName('GlassPanel')
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)
        right_title = QLabel('Разметка')
        right_title.setObjectName('RailSectionTitle')
        self.detail_label = QLabel('Выберите запись')
        self.detail_label.setObjectName('InspectorValue')
        self.detail_label.setWordWrap(True)
        right_layout.addWidget(right_title)
        right_layout.addWidget(self.detail_label, 1)
        self.accept_btn = QPushButton('Принять')
        self.reject_btn = QPushButton('Отклонить')
        self.stage_btn = QPushButton('В training pack')
        self.accept_btn.clicked.connect(lambda: self._set_current_status(STATUS_ACCEPTED))
        self.reject_btn.clicked.connect(lambda: self._set_current_status(STATUS_REJECTED))
        self.stage_btn.clicked.connect(lambda: self._set_current_status(STATUS_STAGED))
        for btn in (self.accept_btn, self.reject_btn, self.stage_btn):
            right_layout.addWidget(btn)
        body.addWidget(right, 0)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['Статус', 'Клип', 'Кадр', 'BBox', 'ID', 'Источник'])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_table_selection)
        root.addWidget(self.table, 0)

        footer = QHBoxLayout()
        self.find_dupes_btn = QPushButton('Найти дубли')
        self.export_btn = QPushButton('Экспорт YOLO')
        self.pack_btn = QPushButton('Собрать training pack')
        self.report_btn = QPushButton('Отчёт качества')
        self.export_btn.clicked.connect(lambda: self._info('Экспорт', 'Используй accepted/staged записи через export_operator_annotations_to_yolo.py. Автообучение здесь не запускается.'))
        self.pack_btn.clicked.connect(lambda: self._info('Training pack', 'Следующий слой: stage_operator_training_pack.py соберёт кадры и labels из accepted/staged.'))
        self.report_btn.clicked.connect(self._show_quality_report)
        self.find_dupes_btn.clicked.connect(self._show_duplicate_report)
        for btn in (self.find_dupes_btn, self.export_btn, self.pack_btn, self.report_btn):
            footer.addWidget(btn)
        footer.addStretch(1)
        root.addLayout(footer)

    def reload(self) -> None:
        self.records = load_annotation_records(self.log_dir, state_path=self.state_path)
        self._refresh_counts()
        self._refresh_table()

    def _set_filter(self, status: str) -> None:
        self.current_status_filter = status
        self._refresh_table()

    def _refresh_counts(self) -> None:
        counts = status_counts(self.records)
        self.counts_label.setText(
            f"new {counts.get(STATUS_NEW, 0)} · "
            f"accepted {counts.get(STATUS_ACCEPTED, 0)} · "
            f"rejected {counts.get(STATUS_REJECTED, 0)} · "
            f"staged {counts.get(STATUS_STAGED, 0)}"
        )

    def _refresh_table(self) -> None:
        if self.current_status_filter == 'all':
            self.filtered = list(self.records)
        else:
            self.filtered = [record for record in self.records if record.status == self.current_status_filter]
        self.table.setRowCount(len(self.filtered))
        for row, record in enumerate(self.filtered):
            values = [
                record.status,
                record.clip_name,
                str(record.frame_index),
                record.bbox_size,
                str(record.active_id if record.active_id is not None else '-'),
                record.source,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, record.record_id)
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()
        if self.filtered:
            self.table.selectRow(0)
        else:
            self.current_record_id = None
            self.preview_label.setText('Нет записей')
            self.detail_label.setText('Нет записей для выбранного фильтра')

    def _selected_record(self) -> AnnotationRecord | None:
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
        self._render_current()

    def _toggle_bbox(self) -> None:
        self.show_bbox = not self.show_bbox
        self.toggle_bbox_btn.setText('BBox on' if self.show_bbox else 'BBox off')
        self._render_current()

    def _set_current_status(self, status: str) -> None:
        record = self._selected_record()
        if record is None:
            return
        set_record_status(self.records, record.record_id, status)
        save_review_state(self.records, self.state_path)
        self._refresh_counts()
        self._refresh_table()

    def _render_current(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        self.detail_label.setText(
            f"Статус: {record.status}\n"
            f"Клип: {record.clip_name}\n"
            f"Кадр: {record.frame_index}\n"
            f"BBox: {record.bbox_size}\n"
            f"Source: {record.source}\n"
            f"Log: {Path(record.log_path).name}:{record.line_number}\n"
            f"Reason: {record.reason or '-'}"
        )
        pixmap = self._preview_pixmap(record)
        if pixmap is None:
            self.preview_label.setText('Кадр недоступен\n' + record.source)
            self.preview_label.setPixmap(QPixmap())
            return
        size = self.preview_label.size()
        target_size = QSize(max(1, int(size.width() * self.zoom)), max(1, int(size.height() * self.zoom)))
        self.preview_label.setPixmap(pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _preview_pixmap(self, record: AnnotationRecord) -> QPixmap | None:
        if not record.source or record.bbox_xyxy is None:
            return None
        source = Path(record.source)
        if not source.exists():
            return None
        cap = cv2.VideoCapture(str(source))
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(record.frame_index)))
            ok, frame = cap.read()
        finally:
            cap.release()
        if not ok or frame is None:
            return None
        if self.show_bbox:
            x1, y1, x2, y2 = record.bbox_xyxy
            cv2.rectangle(frame, (x1, y1), (x2, y2), (92, 203, 120), 2)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        return QPixmap.fromImage(image)

    def _show_quality_report(self) -> None:
        counts = status_counts(self.records)
        total = sum(counts.values())
        small = 0
        for record in self.records:
            if record.bbox_xyxy is None:
                continue
            x1, y1, x2, y2 = record.bbox_xyxy
            if (x2 - x1) * (y2 - y1) < 64:
                small += 1
        self._info('Отчёт качества', f'Всего: {total}\nМаленькие bbox: {small}\nReview state: {self.state_path}')

    def _show_duplicate_report(self) -> None:
        seen: dict[tuple[str, int, tuple[int, int, int, int] | None], int] = {}
        dupes = 0
        for record in self.records:
            key = (record.source, record.frame_index, record.bbox_xyxy)
            seen[key] = seen.get(key, 0) + 1
            if seen[key] == 2:
                dupes += 1
        self._info('Дубли', f'Найдено групп дублей: {dupes}')

    def _info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)
