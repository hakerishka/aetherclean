"""
Detailed Inspector Pane for selected ScanItem with i18n support.
"""

import os
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from core.models import ScanItem, RiskLevel, format_bytes
from core.i18n import t


class ItemDetailView(QFrame):
    """Right-side inspector showing full safety analysis and file preview for selected item."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("detailCard")
        self.setProperty("class", "CardFrame")
        self._current_item: ScanItem = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title & Category
        self.title_label = QLabel(t("detail_empty_title"))
        self.title_label.setObjectName("headerTitle")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Safety Banner
        self.safety_banner = QFrame()
        self.safety_banner.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-left: 4px solid #0078D4;
                border-radius: 4px;
                padding: 8px 12px;
            }
        """)
        banner_layout = QVBoxLayout(self.safety_banner)
        banner_layout.setContentsMargins(8, 4, 8, 4)

        self.risk_badge_label = QLabel(f"{t('tree_col_risk')}: --")
        self.risk_badge_label.setFont(QFont("Segoe UI", 10, QFont.Bold))

        self.safety_advice_label = QLabel(t("detail_empty_desc"))
        self.safety_advice_label.setWordWrap(True)
        self.safety_advice_label.setStyleSheet("color: #E0E0E0; font-size: 12px;")

        banner_layout.addWidget(self.risk_badge_label)
        banner_layout.addWidget(self.safety_advice_label)
        layout.addWidget(self.safety_banner)

        # Reason & Description Card
        self.desc_label = QLabel("")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #CCCCCC; font-size: 13px;")
        layout.addWidget(self.desc_label)

        self.reason_label = QLabel("")
        self.reason_label.setWordWrap(True)
        self.reason_label.setStyleSheet("color: #90CAF9; font-size: 12px; background-color: #1a2530; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.reason_label)

        # Stats and Action Buttons Row
        stats_row = QHBoxLayout()
        self.size_label = QLabel(t("table_col_size") + ": --")
        self.size_label.setFont(QFont("Segoe UI", 10, QFont.Bold))

        self.open_explorer_btn = QPushButton(t("detail_btn_explorer"))
        self.open_explorer_btn.setObjectName("secondaryButton")
        self.open_explorer_btn.clicked.connect(self._open_in_explorer)
        self.open_explorer_btn.setEnabled(False)

        stats_row.addWidget(self.size_label)
        stats_row.addStretch()
        stats_row.addWidget(self.open_explorer_btn)
        layout.addLayout(stats_row)

        # Files Preview Table
        files_title = QLabel(t("detail_files_title"))
        files_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        files_title.setStyleSheet("color: #AAAAAA;")
        layout.addWidget(files_title)

        self.files_table = QTableWidget()
        self.files_table.setColumnCount(3)
        self.files_table.setHorizontalHeaderLabels([
            t("table_col_path"),
            t("table_col_size"),
            t("table_col_mtime")
        ])
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.files_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.files_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.files_table)

    def display_item(self, item: ScanItem):
        self._current_item = item
        self.title_label.setText(f"{item.category.icon_name} {item.title}")
        self.desc_label.setText(item.description)
        self.reason_label.setText(f"{t('detail_why_label')} {item.reason}")
        self.size_label.setText(t("detail_total_label", size=item.format_size(), count=item.file_count))

        # Update Safety Banner
        if item.risk_level == RiskLevel.SAFE:
            border_color = "#4CAF50"
            bg_color = "#122a1b"
        elif item.risk_level == RiskLevel.MEDIUM:
            border_color = "#FFA726"
            bg_color = "#2a2210"
        else:
            border_color = "#EF5350"
            bg_color = "#2b1416"

        self.safety_banner.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-left: 5px solid {border_color};
                border-radius: 4px;
                padding: 8px 12px;
            }}
        """)
        self.risk_badge_label.setText(f"{item.risk_level.badge_text}")
        self.risk_badge_label.setStyleSheet(f"color: {item.risk_level.color_hex}; font-size: 13px; font-weight: bold;")
        self.safety_advice_label.setText(item.safety_label)

        # Enable explorer button if paths exist
        self.open_explorer_btn.setEnabled(bool(item.paths and os.path.exists(item.paths[0])))

        # Populate Files Table
        self.files_table.setRowCount(0)
        display_files = item.files if item.files else []

        if not display_files and item.paths:
            for p in item.paths:
                row = self.files_table.rowCount()
                self.files_table.insertRow(row)
                self.files_table.setItem(row, 0, QTableWidgetItem(p))
                self.files_table.setItem(row, 1, QTableWidgetItem(item.format_size()))
                self.files_table.setItem(row, 2, QTableWidgetItem("--"))
        else:
            for f in display_files:
                row = self.files_table.rowCount()
                self.files_table.insertRow(row)
                self.files_table.setItem(row, 0, QTableWidgetItem(f.path))
                self.files_table.setItem(row, 1, QTableWidgetItem(format_bytes(f.size)))
                mtime_str = f.mtime.strftime("%Y-%m-%d %H:%M") if f.mtime else "--"
                self.files_table.setItem(row, 2, QTableWidgetItem(mtime_str))

    def _open_in_explorer(self):
        if not self._current_item or not self._current_item.paths:
            return
        target = self._current_item.paths[0]
        if os.path.exists(target):
            try:
                if os.path.isfile(target):
                    subprocess.run(["explorer", f"/select,{os.path.normpath(target)}"])
                else:
                    subprocess.run(["explorer", os.path.normpath(target)])
            except Exception as e:
                print(f"Error opening explorer: {e}")
