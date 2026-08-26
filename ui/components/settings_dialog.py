"""
Settings dialog for AetherClean with bilingual i18n support.
"""

import os
import yaml
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QComboBox, QCheckBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt
from core.i18n import I18nManager, t


class SettingsDialog(QDialog):
    """Settings modal dialog for configuring thresholds, language, and safety options."""

    def __init__(self, settings_path: str, parent=None):
        super().__init__(parent)
        self.settings_path = settings_path
        self.settings = {}
        self._load_settings()
        self.setWindowTitle(t("set_dlg_title"))
        self.resize(560, 440)
        self._init_ui()

    def _load_settings(self):
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    self.settings = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading settings: {e}")

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel(t("set_dlg_header"))
        title.setObjectName("headerTitle")
        layout.addWidget(title)

        # General & Safety Group
        safety_group = QGroupBox("General & Safety / Безопасность")
        safety_layout = QFormLayout(safety_group)

        # Language combo
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English (US)", "en")
        self.lang_combo.addItem("Русский (Russian)", "ru")

        current_lang = self.settings.get("general", {}).get("language", I18nManager.get_lang())
        idx = self.lang_combo.findData(current_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        safety_layout.addRow(t("set_lbl_language"), self.lang_combo)

        # Default action
        self.action_combo = QComboBox()
        self.action_combo.addItem(t("action_recycle_bin"), "recycle_bin")
        self.action_combo.addItem(t("action_quarantine"), "quarantine")
        self.action_combo.addItem(t("action_permanent"), "permanent_delete")

        current_action = self.settings.get("general", {}).get("default_action", "recycle_bin")
        idx = self.action_combo.findData(current_action)
        if idx >= 0:
            self.action_combo.setCurrentIndex(idx)

        safety_layout.addRow(t("set_lbl_default_action"), self.action_combo)

        self.restore_pt_chk = QCheckBox(t("set_chk_restore_point"))
        self.restore_pt_chk.setChecked(self.settings.get("general", {}).get("create_restore_point", True))
        safety_layout.addRow(self.restore_pt_chk)

        self.safe_only_chk = QCheckBox(t("set_chk_safe_only"))
        self.safe_only_chk.setChecked(self.settings.get("general", {}).get("auto_select_safe_only", True))
        safety_layout.addRow(self.safe_only_chk)

        layout.addWidget(safety_group)

        # Heuristics Group
        heuristics_group = QGroupBox(t("set_grp_heuristics"))
        heuristics_layout = QFormLayout(heuristics_group)

        heuristics = self.settings.get("heuristics", {})

        self.appdata_days_spin = QSpinBox()
        self.appdata_days_spin.setRange(7, 365)
        self.appdata_days_spin.setValue(heuristics.get("orphaned_appdata_min_days", 30))
        self.appdata_days_spin.setSuffix(" days / дн.")
        heuristics_layout.addRow(t("set_lbl_appdata_days"), self.appdata_days_spin)

        self.dormant_days_spin = QSpinBox()
        self.dormant_days_spin.setRange(14, 730)
        self.dormant_days_spin.setValue(heuristics.get("dormant_large_file_min_days", 90))
        self.dormant_days_spin.setSuffix(" days / дн.")
        heuristics_layout.addRow(t("set_lbl_dormant_days"), self.dormant_days_spin)

        self.dormant_size_spin = QSpinBox()
        self.dormant_size_spin.setRange(100, 10000)
        self.dormant_size_spin.setValue(heuristics.get("dormant_large_file_min_size_mb", 500))
        self.dormant_size_spin.setSuffix(" MB / МБ")
        heuristics_layout.addRow(t("set_lbl_dormant_size"), self.dormant_size_spin)

        layout.addWidget(heuristics_group)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(t("btn_save"))
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_and_close)

        cancel_btn = QPushButton(t("btn_cancel"))
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _save_and_close(self):
        if "general" not in self.settings:
            self.settings["general"] = {}
        if "heuristics" not in self.settings:
            self.settings["heuristics"] = {}

        selected_lang = self.lang_combo.currentData()
        self.settings["general"]["language"] = selected_lang
        I18nManager.set_lang(selected_lang)

        self.settings["general"]["default_action"] = self.action_combo.currentData()
        self.settings["general"]["create_restore_point"] = self.restore_pt_chk.isChecked()
        self.settings["general"]["auto_select_safe_only"] = self.safe_only_chk.isChecked()

        self.settings["heuristics"]["orphaned_appdata_min_days"] = self.appdata_days_spin.value()
        self.settings["heuristics"]["dormant_large_file_min_days"] = self.dormant_days_spin.value()
        self.settings["heuristics"]["dormant_large_file_min_size_mb"] = self.dormant_size_spin.value()

        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                yaml.dump(self.settings, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"Error saving settings: {e}")

        self.accept()
