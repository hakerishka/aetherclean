"""
Driver Store and Unpacked Drivers Scanner.
Identifies redundant driver installation files and old OEM driver packages.
"""

import os
import subprocess
from datetime import datetime
from typing import List, Optional, Callable
from core.models import ScanItem, FileEntry, RiskLevel, Category
from core.rule_engine import RuleEngine
from .base_scanner import BaseScanner


class DriverStoreScanner(BaseScanner):
    """Scans for redundant driver packages and unpacked driver installation directories."""

    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        items: List[ScanItem] = []

        if progress_callback:
            progress_callback("Поиск распакованных дистрибутивов драйверов (NVIDIA / AMD / Intel)...", 20)

        # Load driver declarative rules
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        driver_rules_path = os.path.join(base_dir, "config", "rules", "driver_rules.yaml")

        rule_engine = RuleEngine()
        if os.path.exists(driver_rules_path):
            import yaml
            try:
                with open(driver_rules_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "rules" in data:
                        for rule in data["rules"]:
                            if self.is_cancelled:
                                break
                            item = rule_engine.scan_rule(rule)
                            if item:
                                item.category = Category.DRIVERS
                                items.append(item)
            except Exception as e:
                print(f"[DriverStoreScanner] Error reading driver rules: {e}")

        # Check DriverStore FileRepository summary
        if progress_callback:
            progress_callback("Анализ хранилища драйверов Windows (DriverStore)...", 60)

        ds_path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "DriverStore", "FileRepository")
        if os.path.isdir(ds_path):
            ds_size, ds_count = self._calc_folder_stats(ds_path)
            if ds_size > 2 * (1024 ** 3):  # If larger than 2 GB
                items.append(
                    ScanItem(
                        id="driverstore_filerepository_info",
                        title="Хранилище пакетов драйверов (DriverStore)",
                        category=Category.DRIVERS,
                        risk_level=RiskLevel.HIGH,
                        safety_label="Высокий риск: системные драйверы. Очистка только через специализированный инструмент",
                        description=f"Папка FileRepository занимает {ds_size / (1024**3):.2f} ГБ. Windows хранит в ней резервные копии всех когда-либо установленных версий драйверов.",
                        reason=f"Обнаружено {ds_count} пакетов драйверов. Для безопасного удаления устаревших версий рекомендуется использовать утилиту pnputil или DriverStore Explorer.",
                        total_size=ds_size,
                        file_count=ds_count,
                        paths=[ds_path],
                        is_selected=False,
                        metadata={"is_informational_only": True}
                    )
                )

        return items

    @staticmethod
    def _calc_folder_stats(folder_path: str):
        total_size = 0
        count = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                        count += 1
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
        return total_size, count
