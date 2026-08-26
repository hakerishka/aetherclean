"""
Disk space visualization widget for AetherClean with i18n support.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QBrush
from core.models import format_bytes
from core.i18n import t


class DiskGaugeWidget(QFrame):
    """Visualizes disk capacity, current usage, and potential recoverable space."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("detailCard")
        self.setProperty("class", "CardFrame")

        self.total_bytes = 1
        self.used_bytes = 0
        self.free_bytes = 0
        self.cleanable_bytes = 0

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Header row
        header_layout = QHBoxLayout()
        self.drive_label = QLabel(t("system_drive_title"))
        self.drive_label.setObjectName("sectionTitle")

        self.stats_label = QLabel(t("free_total_fmt", free="--", total="--"))
        self.stats_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")

        header_layout.addWidget(self.drive_label)
        header_layout.addStretch()
        header_layout.addWidget(self.stats_label)
        layout.addLayout(header_layout)

        # Custom Segmented Bar
        self.bar = DiskUsageBar()
        layout.addWidget(self.bar)

        # Bottom info row
        info_layout = QHBoxLayout()

        self.legend_used = QLabel(t("legend_used", size="0 GB"))
        self.legend_used.setStyleSheet("color: #78909C; font-size: 12px; font-weight: 500;")

        self.legend_cleanable = QLabel(t("legend_cleanable", size="0 GB"))
        self.legend_cleanable.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: 600;")

        self.legend_free = QLabel(t("legend_free", size="0 GB"))
        self.legend_free.setStyleSheet("color: #90A4AE; font-size: 12px; font-weight: 500;")

        info_layout.addWidget(self.legend_used)
        info_layout.addSpacing(20)
        info_layout.addWidget(self.legend_cleanable)
        info_layout.addSpacing(20)
        info_layout.addWidget(self.legend_free)
        info_layout.addStretch()

        layout.addLayout(info_layout)

    def update_stats(self, total: int, used: int, free: int, cleanable: int = 0):
        self.total_bytes = max(1, total)
        self.used_bytes = used
        self.free_bytes = free
        self.cleanable_bytes = cleanable

        self.drive_label.setText(t("system_drive_title"))
        self.stats_label.setText(t("free_total_fmt", free=format_bytes(free), total=format_bytes(total)))
        self.legend_used.setText(t("legend_used", size=format_bytes(max(0, used - cleanable))))
        self.legend_cleanable.setText(t("legend_cleanable", size=format_bytes(cleanable)))
        self.legend_free.setText(t("legend_free", size=format_bytes(free)))

        self.bar.set_values(total, used, cleanable)


class DiskUsageBar(QWidget):
    """Custom painted multi-segment disk usage bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self.total = 100
        self.used = 0
        self.cleanable = 0

    def set_values(self, total: int, used: int, cleanable: int):
        self.total = max(1, total)
        self.used = max(0, used)
        self.cleanable = max(0, cleanable)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        radius = 6

        # Background (Free space)
        painter.setBrush(QBrush(QColor("#2d3238")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, width, height, radius, radius)

        # Used space (excluding cleanable)
        pure_used = max(0, self.used - self.cleanable)
        used_width = int((pure_used / self.total) * width)
        if used_width > 0:
            painter.setBrush(QBrush(QColor("#0078D4")))
            painter.drawRoundedRect(0, 0, used_width, height, radius, radius)

        # Cleanable space segment (green highlight)
        cleanable_width = int((self.cleanable / self.total) * width)
        if cleanable_width > 0:
            painter.setBrush(QBrush(QColor("#4CAF50")))
            painter.drawRoundedRect(used_width, 0, cleanable_width, height, radius, radius)
