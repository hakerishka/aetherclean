"""
Driver Store and Unpacked Drivers Scanner for AetherClean.
Identifies redundant driver installation files and old OEM driver packages.
"""

import os
import yaml
from typing import List, Optional, Callable
from core.models import ScanItem, FileEntry, RiskLevel, Category
from core.rule_engine import RuleEngine
from core.path_utils import get_config_path
from .base_scanner import BaseScanner


class DriverStoreScanner(BaseScanner):
    """Scans for redundant driver packages and unpacked driver installation directories."""

    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        items: List[ScanItem] = []

        if progress_callback:
            progress_callback("Scanning unpacked driver setup packages...", 20)

        # Load driver declarative rules
        driver_rules_path = get_config_path(os.path.join("config", "rules", "driver_rules.yaml"))

        rule_engine = RuleEngine()
        if os.path.exists(driver_rules_path):
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
            progress_callback("Analyzing Windows DriverStore repository...", 60)

        ds_path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "DriverStore", "FileRepository")
        if os.path.isdir(ds_path):
            ds_size, ds_count = self._calc_folder_stats(ds_path)
            if ds_size > 2 * (1024 ** 3):  # If larger than 2 GB
                items.append(
                    ScanItem(
                        id="driverstore_filerepository_info",
                        title="Windows DriverStore Repository",
                        category=Category.DRIVERS,
                        risk_level=RiskLevel.HIGH,
                        safety_label="High risk: active system drivers. Safe removal requires pnputil",
                        description=f"FileRepository folder takes {ds_size / (1024**3):.2f} GB. Windows stores backup copies of all installed driver versions.",
                        reason=f"Found {ds_count} driver packages. Obsolete versions can be safely cleaned using pnputil or DriverStore Explorer.",
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
