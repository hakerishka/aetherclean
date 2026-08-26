"""
Real-time Cleaning Progress Modal Dialog for AetherClean with i18n support.
Shows non-blocking live deletion progress, real-time activity log, live bytes counter, and summary.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QTextEdit, QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QTextCursor
from core.models import format_bytes
from core.i18n import t


class CleaningProgressDialog(QDialog):
    """Modern modal dialog displaying live cleaning activity, detailed logs, and metrics."""

    cancel_requested = Signal()

    def __init__(self, total_items_count: int, parent=None):
        super().__init__(parent)
        self.total_items_count = total_items_count
        self.is_finished = False
        self.freed_bytes = 0
        self.skipped_count = 0

        self.setWindowTitle(t("clean_dlg_title"))
        self.resize(720, 520)
        self.setMinimumSize(600, 420)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header Title
        self.header_title = QLabel(t("clean_dlg_header_active"))
        self.header_title.setObjectName("headerTitle")
        self.header_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(self.header_title)

        # Current Item & File Label
        self.item_label = QLabel(f"Preparing to clean {self.total_items_count} items...")
        self.item_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #60CDFF;")
        self.item_label.setWordWrap(True)
        layout.addWidget(self.item_label)

        self.file_label = QLabel("")
        self.file_label.setStyleSheet("font-size: 11px; color: #888888;")
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(14)
        layout.addWidget(self.progress_bar)

        # Live Metrics Cards
        metrics_frame = QFrame()
        metrics_frame.setObjectName("detailCard")
        metrics_frame.setProperty("class", "CardFrame")
        metrics_layout = QGridLayout(metrics_frame)
        metrics_layout.setContentsMargins(12, 10, 12, 10)

        self.metric_freed = QLabel("0 B")
        self.metric_freed.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        lbl_freed = QLabel(t("clean_dlg_metric_freed"))
        lbl_freed.setStyleSheet("color: #AAAAAA; font-size: 12px;")

        self.metric_items = QLabel(f"0 / {self.total_items_count}")
        self.metric_items.setStyleSheet("font-size: 16px; font-weight: bold; color: #60CDFF;")
        lbl_items = QLabel(t("clean_dlg_metric_items"))
        lbl_items.setStyleSheet("color: #AAAAAA; font-size: 12px;")

        self.metric_skipped = QLabel("0")
        self.metric_skipped.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFA726;")
        lbl_skipped = QLabel(t("clean_dlg_metric_skipped"))
        lbl_skipped.setStyleSheet("color: #AAAAAA; font-size: 12px;")

        metrics_layout.addWidget(lbl_freed, 0, 0)
        metrics_layout.addWidget(self.metric_freed, 1, 0)

        metrics_layout.addWidget(lbl_items, 0, 1)
        metrics_layout.addWidget(self.metric_items, 1, 1)

        metrics_layout.addWidget(lbl_skipped, 0, 2)
        metrics_layout.addWidget(self.metric_skipped, 1, 2)

        layout.addWidget(metrics_frame)

        # Console Log Feed
        log_title = QLabel(t("clean_dlg_log_title"))
        log_title.setStyleSheet("color: #AAAAAA; font-size: 11px; font-weight: bold;")
        layout.addWidget(log_title)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                color: #CCCCCC;
                font-family: 'Consolas', 'Cascadia Code', monospace;
                font-size: 12px;
                padding: 6px;
            }
        """)
        layout.addWidget(self.log_text)

        # Bottom Button Row
        btn_layout = QHBoxLayout()
        self.action_btn = QPushButton(t("clean_dlg_btn_stop"))
        self.action_btn.setObjectName("secondaryButton")
        self.action_btn.clicked.connect(self._on_action_clicked)

        btn_layout.addStretch()
        btn_layout.addWidget(self.action_btn)
        layout.addLayout(btn_layout)

    @Slot(int, int, str, str, int)
    def update_progress(self, current_idx: int, total_items: int, item_title: str, current_path: str, percent: int):
        self.progress_bar.setValue(percent)
        self.item_label.setText(f"[{current_idx}/{total_items}] {item_title}")

        if current_path:
            display_path = current_path if len(current_path) < 75 else "..." + current_path[-72:]
            self.file_label.setText(f"File: {display_path}")
        else:
            self.file_label.setText("")

        self.metric_items.setText(f"{current_idx} / {total_items}")

    @Slot(str, str)
    def append_log(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")

        if level == "ok":
            color = "#81C784"
            prefix = "[OK]"
        elif level == "warn":
            color = "#FFD54F"
            prefix = "[SKIP]"
            self.skipped_count += 1
            self.metric_skipped.setText(str(self.skipped_count))
        elif level == "err":
            color = "#E57373"
            prefix = "[ERR]"
        else:
            color = "#90CAF9"
            prefix = "[INFO]"

        html_line = f"<span style='color: #666666;'>[{timestamp}]</span> <span style='color: {color}; font-weight: bold;'>{prefix}</span> <span style='color: #E0E0E0;'>{message}</span>"
        self.log_text.append(html_line)
        self.log_text.moveCursor(QTextCursor.End)

    def set_cleaning_finished(self, freed_bytes: int, processed_count: int, errors: list):
        self.is_finished = True
        self.freed_bytes = freed_bytes

        self.progress_bar.setValue(100)
        self.header_title.setText(t("clean_dlg_header_finished"))
        self.header_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #81C784;")

        self.item_label.setText(f"Processed items: {processed_count}")
        self.file_label.setText(f"Total space freed: {format_bytes(freed_bytes)}")

        self.metric_freed.setText(format_bytes(freed_bytes))
        self.metric_items.setText(f"{processed_count} / {self.total_items_count}")

        self.action_btn.setText(t("clean_dlg_btn_close"))
        self.action_btn.setObjectName("primaryButton")
        self.action_btn.setStyle(self.action_btn.style())

    def _on_action_clicked(self):
        if self.is_finished:
            self.accept()
        else:
            self.action_btn.setEnabled(False)
            self.action_btn.setText("Stopping...")
            self.cancel_requested.emit()

    def closeEvent(self, event):
        if not self.is_finished:
            self.cancel_requested.emit()
            event.ignore()
        else:
            event.accept()
