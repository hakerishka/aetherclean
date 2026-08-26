"""
Main Application Window for AetherClean.
Modern Windows 11 Fluent Dark UI with real-time non-blocking scan and clean progress, safety inspectors, and bilingual i18n support.
"""

import os
import yaml
from datetime import datetime
from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSplitter, QComboBox, QMessageBox, QFrame,
    QStatusBar, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QIcon, QFont

from core.models import ScanResult, ScanItem, CleanAction, RiskLevel, format_bytes
from core.scanner import MasterScanner, DiskInfo
from core.quarantine_manager import QuarantineManager
from core.restore_point import RestorePointManager
from core.i18n import I18nManager, t
from ui.theme import DARK_THEME_QSS
from ui.components.disk_gauge import DiskGaugeWidget
from ui.components.category_tree import CategoryTreeWidget
from ui.components.item_detail_view import ItemDetailView
from ui.components.progress_card import ProgressCard
from ui.components.quarantine_dialog import QuarantineDialog
from ui.components.settings_dialog import SettingsDialog
from ui.components.cleaning_dialog import CleaningProgressDialog


class ScanWorker(QThread):
    """Background worker thread for non-blocking disk scan execution."""

    progress_signal = Signal(str, int)
    item_found_signal = Signal(object)
    finished_signal = Signal(object)
    error_signal = Signal(str)

    def __init__(self, scanner: MasterScanner, target_drive: str):
        super().__init__()
        self.scanner = scanner
        self.target_drive = target_drive

    def run(self):
        try:
            result = self.scanner.run_full_scan(
                target_drive=self.target_drive,
                progress_callback=self.progress_signal.emit,
                item_found_callback=self.item_found_signal.emit
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class CleanWorker(QThread):
    """Background worker thread for non-blocking clean/quarantine execution with live activity logging."""

    progress_signal = Signal(int, int, str, str, int)  # current_idx, total_items, item_title, current_path, percent
    log_signal = Signal(str, str)  # message, level: 'info'|'ok'|'warn'|'err'
    finished_signal = Signal(int, int, list)  # freed_bytes, count, errors
    error_signal = Signal(str)

    def __init__(self, quarantine_mgr: QuarantineManager, items: List[ScanItem], action: CleanAction):
        super().__init__()
        self.quarantine_mgr = quarantine_mgr
        self.items = items
        self.action = action

    def run(self):
        try:
            freed, count, errs = self.quarantine_mgr.execute_cleaning(
                items_to_clean=self.items,
                action=self.action,
                progress_callback=self.progress_signal.emit,
                log_callback=self.log_signal.emit
            )
            self.finished_signal.emit(freed, count, errs)
        except Exception as e:
            self.error_signal.emit(str(e))


class MainWindow(QMainWindow):
    """Main Application Window for AetherClean."""

    def __init__(self):
        super().__init__()
        # Paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.settings_path = os.path.join(base_dir, "config", "settings.yaml")
        self.settings = self._load_settings()

        # Set configured language
        lang = self.settings.get("general", {}).get("language", "en")
        I18nManager.set_lang(lang)

        self.setWindowTitle(f"AetherClean — {t('app_subtitle')}")
        self.resize(1180, 780)
        self.setMinimumSize(950, 600)

        # Core engines
        self.scanner = MasterScanner(self.settings)
        quar_dir = self.settings.get("general", {}).get("quarantine_dir")
        self.quarantine_mgr = QuarantineManager(quar_dir)

        self.current_scan_result: Optional[ScanResult] = None
        self.scan_worker: Optional[ScanWorker] = None
        self.clean_worker: Optional[CleanWorker] = None

        self._init_ui()
        self._refresh_disk_stats()
        self.setStyleSheet(DARK_THEME_QSS)

    def _load_settings(self) -> dict:
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {}

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 16, 18, 12)
        main_layout.setSpacing(12)

        # 1. Top Header Bar
        header_layout = QHBoxLayout()

        title_col = QVBoxLayout()
        app_title = QLabel(t("app_title"))
        app_title.setObjectName("headerTitle")
        app_sub = QLabel(t("app_subtitle"))
        app_sub.setObjectName("headerSubtitle")
        title_col.addWidget(app_title)
        title_col.addWidget(app_sub)
        header_layout.addLayout(title_col)

        header_layout.addStretch()

        # Quick utility buttons
        self.restore_pt_btn = QPushButton(t("btn_restore_point"))
        self.restore_pt_btn.setObjectName("secondaryButton")
        self.restore_pt_btn.clicked.connect(self._create_restore_point)

        self.quarantine_btn = QPushButton(t("btn_quarantine"))
        self.quarantine_btn.setObjectName("secondaryButton")
        self.quarantine_btn.clicked.connect(self._open_quarantine)

        self.settings_btn = QPushButton(t("btn_settings"))
        self.settings_btn.setObjectName("secondaryButton")
        self.settings_btn.clicked.connect(self._open_settings)

        header_layout.addWidget(self.restore_pt_btn)
        header_layout.addWidget(self.quarantine_btn)
        header_layout.addWidget(self.settings_btn)

        main_layout.addLayout(header_layout)

        # 2. Disk Space Gauge
        self.disk_gauge = DiskGaugeWidget()
        main_layout.addWidget(self.disk_gauge)

        # 3. Action Toolbar (Scan, Quick Filters, Clean)
        action_bar = QFrame()
        action_bar.setObjectName("detailCard")
        action_bar.setProperty("class", "CardFrame")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(12, 8, 12, 8)
        action_layout.setSpacing(10)

        # Big Scan Button
        self.scan_btn = QPushButton(t("btn_start_scan"))
        self.scan_btn.setObjectName("primaryButton")
        self.scan_btn.setMinimumWidth(180)
        self.scan_btn.clicked.connect(self._start_or_stop_scan)
        action_layout.addWidget(self.scan_btn)

        action_layout.addSpacing(10)

        # Selection helpers
        self.safe_only_btn = QPushButton(t("btn_safe_only"))
        self.safe_only_btn.setObjectName("secondaryButton")
        self.safe_only_btn.clicked.connect(self._select_safe_only)
        self.safe_only_btn.setEnabled(False)

        self.select_all_btn = QPushButton(t("btn_select_all"))
        self.select_all_btn.setObjectName("secondaryButton")
        self.select_all_btn.clicked.connect(lambda: self.tree.select_all(True))
        self.select_all_btn.setEnabled(False)

        self.unselect_all_btn = QPushButton(t("btn_unselect_all"))
        self.unselect_all_btn.setObjectName("secondaryButton")
        self.unselect_all_btn.clicked.connect(lambda: self.tree.select_all(False))
        self.unselect_all_btn.setEnabled(False)

        action_layout.addWidget(self.safe_only_btn)
        action_layout.addWidget(self.select_all_btn)
        action_layout.addWidget(self.unselect_all_btn)

        action_layout.addStretch()

        # Action mode combo
        action_layout.addWidget(QLabel(t("lbl_action_target")))
        self.action_mode_combo = QComboBox()
        self.action_mode_combo.addItem(t("action_recycle_bin"), CleanAction.RECYCLE_BIN)
        self.action_mode_combo.addItem(t("action_quarantine"), CleanAction.QUARANTINE)
        self.action_mode_combo.addItem(t("action_permanent"), CleanAction.PERMANENT_DELETE)
        action_layout.addWidget(self.action_mode_combo)

        # Big Clean Button
        self.clean_btn = QPushButton(t("btn_clean_selected", size="0 B"))
        self.clean_btn.setObjectName("primaryButton")
        self.clean_btn.setStyleSheet("""
            QPushButton#primaryButton {
                background-color: #2E7D32;
                border-color: #388E3C;
                font-weight: bold;
                padding: 8px 18px;
            }
            QPushButton#primaryButton:hover {
                background-color: #388E3C;
            }
        """)
        self.clean_btn.setEnabled(False)
        self.clean_btn.clicked.connect(self._execute_clean)
        action_layout.addWidget(self.clean_btn)

        main_layout.addWidget(action_bar)

        # 4. Progress Card (Hidden by default)
        self.progress_card = ProgressCard()
        self.progress_card.setVisible(False)
        self.progress_card.cancelled_signal.connect(self._cancel_scan)
        main_layout.addWidget(self.progress_card)

        # 5. Main Splitter: Tree on left, Detail Inspector on right
        splitter = QSplitter(Qt.Horizontal)

        self.tree = CategoryTreeWidget()
        self.tree.selection_changed_signal.connect(self._on_tree_selection_changed)
        self.tree.item_focused_signal.connect(self._on_item_focused)
        splitter.addWidget(self.tree)

        self.detail_view = ItemDetailView()
        splitter.addWidget(self.detail_view)

        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        main_layout.addWidget(splitter, 1)

        # 6. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(t("status_ready"))

    def _refresh_disk_stats(self, cleanable: int = 0):
        stats = DiskInfo.get_drive_stats("C:")
        self.disk_gauge.update_stats(
            total=stats["total"],
            used=stats["used"],
            free=stats["free"],
            cleanable=cleanable
        )

    def _start_or_stop_scan(self):
        if self.scan_worker and self.scan_worker.isRunning():
            self._cancel_scan()
            return

        # Start Scan
        self.scan_btn.setText(t("btn_stop_scan"))
        self.scan_btn.setObjectName("dangerButton")
        self.scan_btn.setStyle(self.scan_btn.style())
        self.progress_card.setVisible(True)
        self.progress_card.set_progress(t("status_scanning_init"), 5)
        self.clean_btn.setEnabled(False)
        self.safe_only_btn.setEnabled(False)
        self.select_all_btn.setEnabled(False)
        self.unselect_all_btn.setEnabled(False)

        target_drive = self.settings.get("general", {}).get("target_drive", "C:")
        self.scan_worker = ScanWorker(self.scanner, target_drive)
        self.scan_worker.progress_signal.connect(self._on_scan_progress)
        self.scan_worker.finished_signal.connect(self._on_scan_finished)
        self.scan_worker.error_signal.connect(self._on_scan_error)
        self.scan_worker.start()

    def _cancel_scan(self):
        if self.scanner:
            self.scanner.cancel()
        self.progress_card.set_progress("Stopping scan...", 99)

    @Slot(str, int)
    def _on_scan_progress(self, message: str, percentage: int):
        self.progress_card.set_progress(message, percentage)
        self.status_bar.showMessage(message)

    @Slot(object)
    def _on_scan_finished(self, result: ScanResult):
        self.current_scan_result = result
        self.scan_btn.setText(t("btn_start_scan"))
        self.scan_btn.setObjectName("primaryButton")
        self.scan_btn.setStyle(self.scan_btn.style())
        self.progress_card.setVisible(False)

        # Populate Category Tree
        category_groups = result.get_by_category()
        self.tree.populate(category_groups)

        self.safe_only_btn.setEnabled(True)
        self.select_all_btn.setEnabled(True)
        self.unselect_all_btn.setEnabled(True)

        self._on_tree_selection_changed()

        msg = t("status_scan_complete_fmt", size=format_bytes(result.total_bytes), count=len(category_groups))
        self.status_bar.showMessage(msg)

    @Slot(str)
    def _on_scan_error(self, err_msg: str):
        self.scan_btn.setText(t("btn_start_scan"))
        self.scan_btn.setObjectName("primaryButton")
        self.scan_btn.setStyle(self.scan_btn.style())
        self.progress_card.setVisible(False)
        QMessageBox.critical(self, "Scan Error", f"An error occurred:\n{err_msg}")

    def _on_tree_selection_changed(self):
        selected_items = self.tree.get_selected_items()
        selected_bytes = sum(item.total_size for item in selected_items)

        self.clean_btn.setText(t("btn_clean_selected", size=format_bytes(selected_bytes)))
        self.clean_btn.setEnabled(len(selected_items) > 0 and selected_bytes > 0)

        self._refresh_disk_stats(cleanable=selected_bytes)

    def _on_item_focused(self, item: ScanItem):
        if item:
            self.detail_view.display_item(item)

    def _select_safe_only(self):
        self.tree.select_all_safe()

    def _create_restore_point(self):
        self.status_bar.showMessage("Creating Windows System Restore Point...")
        success, msg = RestorePointManager.create_restore_point("AetherClean Manual Restore Point")
        if success:
            QMessageBox.information(self, "Restore Point", msg)
            self.status_bar.showMessage("System Restore Point ready.")
        else:
            QMessageBox.warning(self, "Restore Point", msg)
            self.status_bar.showMessage("Failed to create restore point.")

    def _open_quarantine(self):
        dlg = QuarantineDialog(self.quarantine_mgr, self)
        dlg.exec()

    def _open_settings(self):
        dlg = SettingsDialog(self.settings_path, self)
        if dlg.exec() == QDialog.Accepted:
            self.settings = self._load_settings()
            self.scanner.settings = self.settings
            # Update UI labels
            self.setWindowTitle(f"AetherClean — {t('app_subtitle')}")
            self._init_ui()
            if self.current_scan_result:
                self.tree.populate(self.current_scan_result.get_by_category())
                self._on_tree_selection_changed()

    def _execute_clean(self):
        selected_items = self.tree.get_selected_items()
        if not selected_items:
            return

        selected_bytes = sum(i.total_size for i in selected_items)
        action = self.action_mode_combo.currentData()

        # Check for High Risk items
        has_high_risk = any(i.risk_level == RiskLevel.HIGH for i in selected_items)
        has_medium_risk = any(i.risk_level == RiskLevel.MEDIUM for i in selected_items)

        action_names = {
            CleanAction.RECYCLE_BIN: "moved to Windows Recycle Bin",
            CleanAction.QUARANTINE: "isolated in AetherClean Quarantine (with 1-click restore)",
            CleanAction.PERMANENT_DELETE: "PERMANENTLY DELETED",
        }

        warning_notes = []
        if has_high_risk:
            warning_notes.append("⚠️ HIGH RISK items (user data / system files) are selected.")
        if has_medium_risk:
            warning_notes.append("ℹ️ Orphaned application remnants (AppData) are selected.")

        warning_text = "\n".join(warning_notes) + "\n\n" if warning_notes else ""

        confirm_msg = (
            f"Selected items: {len(selected_items)} ({format_bytes(selected_bytes)}).\n\n"
            f"Files will be {action_names.get(action)}.\n\n"
            f"{warning_text}"
            f"Are you sure you want to proceed with cleaning?"
        )

        reply = QMessageBox.question(
            self,
            "Confirm Cleaning",
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        # Create Restore point if enabled and system items are present
        if self.settings.get("general", {}).get("create_restore_point", True) and (has_high_risk or has_medium_risk):
            self.status_bar.showMessage("Creating Restore Point before cleanup...")
            RestorePointManager.create_restore_point("AetherClean Auto Restore Point")

        # Open non-blocking live progress dialog
        progress_dlg = CleaningProgressDialog(total_items_count=len(selected_items), parent=self)

        self.clean_worker = CleanWorker(self.quarantine_mgr, selected_items, action)
        self.clean_worker.progress_signal.connect(progress_dlg.update_progress)
        self.clean_worker.log_signal.connect(progress_dlg.append_log)
        self.clean_worker.finished_signal.connect(
            lambda freed, count, errs: progress_dlg.set_cleaning_finished(freed, count, errs)
        )
        self.clean_worker.error_signal.connect(
            lambda err: progress_dlg.append_log(f"Critical error: {err}", "err")
        )
        progress_dlg.cancel_requested.connect(self.quarantine_mgr.cancel)

        # Start clean worker thread
        self.clean_worker.start()

        # Run dialog modal event loop
        progress_dlg.exec()

        self._refresh_disk_stats(cleanable=0)

        # Automatically re-run scan to reflect freed space
        self._start_or_stop_scan()
