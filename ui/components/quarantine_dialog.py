"""
Quarantine and Rollback management dialog for AetherClean with i18n support.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from core.quarantine_manager import QuarantineManager
from core.models import format_bytes
from core.i18n import t


class QuarantineDialog(QDialog):
    """Dialog allowing users to inspect quarantine backups and perform 1-click rollbacks."""

    def __init__(self, quarantine_manager: QuarantineManager, parent=None):
        super().__init__(parent)
        self.qm = quarantine_manager
        self.setWindowTitle(t("quar_dlg_title"))
        self.resize(750, 480)
        self._init_ui()
        self._load_sessions()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        title = QLabel(t("quar_dlg_header"))
        title.setObjectName("headerTitle")
        layout.addWidget(title)

        desc = QLabel(t("quar_dlg_desc"))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        layout.addWidget(desc)

        # Sessions Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            t("quar_col_id"),
            t("quar_col_date"),
            t("quar_col_size"),
            t("quar_col_items"),
            t("quar_col_status")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        # Action Buttons
        btn_layout = QHBoxLayout()

        self.restore_btn = QPushButton(t("quar_btn_restore"))
        self.restore_btn.setObjectName("primaryButton")
        self.restore_btn.clicked.connect(self._restore_selected)

        self.delete_btn = QPushButton(t("quar_btn_delete"))
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.clicked.connect(self._delete_selected)

        self.close_btn = QPushButton(t("clean_dlg_btn_close"))
        self.close_btn.setObjectName("secondaryButton")
        self.close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.restore_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _load_sessions(self):
        self.table.setRowCount(0)
        sessions = self.qm.list_sessions()

        if not sessions:
            self.restore_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return

        self.restore_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

        for s in sessions:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(s.session_id))
            self.table.setItem(row, 1, QTableWidgetItem(s.timestamp.replace("T", " ")[:19]))
            self.table.setItem(row, 2, QTableWidgetItem(format_bytes(s.total_bytes)))
            self.table.setItem(row, 3, QTableWidgetItem(str(s.item_count)))

            status_text = t("quar_status_restored") if s.is_restored else t("quar_status_in_quar")
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(Qt.green if s.is_restored else Qt.yellow)
            self.table.setItem(row, 4, status_item)

        self.table.selectRow(0)

    def _get_selected_session_id(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        return self.table.item(row, 0).text()

    def _restore_selected(self):
        session_id = self._get_selected_session_id()
        if not session_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Undo / Восстановление",
            f"Restore all files from session '{session_id}' to their original locations?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            count, errors = self.qm.restore_session(session_id)
            if errors:
                QMessageBox.warning(
                    self,
                    "Warnings during restore",
                    f"Restored objects: {count}.\nErrors:\n" + "\n".join(errors[:5])
                )
            else:
                QMessageBox.information(
                    self,
                    "Restore Successful",
                    f"All objects ({count}) successfully restored to original paths!"
                )
            self._load_sessions()

    def _delete_selected(self):
        session_id = self._get_selected_session_id()
        if not session_id:
            return

        reply = QMessageBox.warning(
            self,
            "Delete Quarantine Session",
            f"Are you sure you want to permanently delete session '{session_id}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.qm.delete_session(session_id):
                QMessageBox.information(self, "Deleted", "Quarantine session deleted.")
                self._load_sessions()
            else:
                QMessageBox.critical(self, "Error", "Could not delete session directory.")
