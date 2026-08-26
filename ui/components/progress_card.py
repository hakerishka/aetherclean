"""
Live scan progress widget for AetherClean.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton
from PySide6.QtCore import Qt, Signal


class ProgressCard(QFrame):
    """Card displaying current scan progress, percentage, and cancel button."""

    cancelled_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("detailCard")
        self.setProperty("class", "CardFrame")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Status text & cancel button row
        top_row = QHBoxLayout()
        self.status_label = QLabel("Подготовка к сканированию...")
        self.status_label.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 13px;")

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.setFixedHeight(26)
        self.cancel_btn.clicked.connect(self.cancelled_signal.emit)

        top_row.addWidget(self.status_label)
        top_row.addStretch()
        top_row.addWidget(self.cancel_btn)
        layout.addLayout(top_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        layout.addWidget(self.progress_bar)

    def set_progress(self, message: str, percentage: int):
        self.status_label.setText(message)
        self.progress_bar.setValue(percentage)
