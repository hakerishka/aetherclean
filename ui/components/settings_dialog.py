"""
Settings dialog for AetherClean.
"""

import os
import yaml
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QComboBox, QCheckBox, QLineEdit, QFileDialog, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    """Settings modal dialog for configuring thresholds and safety options."""

    def __init__(self, settings_path: str, parent=None):
        super().__init__(parent)
        self.settings_path = settings_path
        self.settings = {}
        self.setWindowTitle("Настройки AetherClean")
        self.resize(550, 420)
        self._load_settings()
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

        title = QLabel("⚙️ Параметры анализа и безопасности")
        title.setObjectName("headerTitle")
        layout.addWidget(title)

        # Safety & Actions Group
        safety_group = QGroupBox("Безопасность и очистка")
        safety_layout = QFormLayout(safety_group)

        self.action_combo = QComboBox()
        self.action_combo.addItem("Корзина Windows (Рекомендуется)", "recycle_bin")
        self.action_combo.addItem("Карантин AetherClean (с откатом в 1 клик)", "quarantine")
        self.action_combo.addItem("Безвозвратное удаление", "permanent_delete")

        current_action = self.settings.get("general", {}).get("default_action", "recycle_bin")
        idx = self.action_combo.findData(current_action)
        if idx >= 0:
            self.action_combo.setCurrentIndex(idx)

        safety_layout.addRow("Действие по умолчанию:", self.action_combo)

        self.restore_pt_chk = QCheckBox("Создавать точку восстановления Windows перед системной очисткой")
        self.restore_pt_chk.setChecked(self.settings.get("general", {}).get("create_restore_point", True))
        safety_layout.addRow(self.restore_pt_chk)

        self.safe_only_chk = QCheckBox("Выбирать по умолчанию только 100% безопасные категории (Safe)")
        self.safe_only_chk.setChecked(self.settings.get("general", {}).get("auto_select_safe_only", True))
        safety_layout.addRow(self.safe_only_chk)

        layout.addWidget(safety_group)

        # Heuristics Group
        heuristics_group = QGroupBox("Эвристические пороги")
        heuristics_layout = QFormLayout(heuristics_group)

        heuristics = self.settings.get("heuristics", {})

        self.appdata_days_spin = QSpinBox()
        self.appdata_days_spin.setRange(7, 365)
        self.appdata_days_spin.setValue(heuristics.get("orphaned_appdata_min_days", 30))
        self.appdata_days_spin.setSuffix(" дней")
        heuristics_layout.addRow("Минимальный простой для остатков AppData:", self.appdata_days_spin)

        self.dormant_days_spin = QSpinBox()
        self.dormant_days_spin.setRange(14, 730)
        self.dormant_days_spin.setValue(heuristics.get("dormant_large_file_min_days", 90))
        self.dormant_days_spin.setSuffix(" дней")
        heuristics_layout.addRow("Минимальный возраст забытых файлов:", self.dormant_days_spin)

        self.dormant_size_spin = QSpinBox()
        self.dormant_size_spin.setRange(100, 10000)
        self.dormant_size_spin.setValue(heuristics.get("dormant_large_file_min_size_mb", 500))
        self.dormant_size_spin.setSuffix(" МБ")
        heuristics_layout.addRow("Порог размера забытых файлов:", self.dormant_size_spin)

        layout.addWidget(heuristics_group)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_and_close)

        cancel_btn = QPushButton("Отмена")
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
