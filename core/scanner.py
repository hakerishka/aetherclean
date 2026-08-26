"""
Master Scan Orchestrator for AetherClean.
Coordinates multiple scanner modules, aggregates findings, and manages thread execution.
"""

import os
import psutil
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from .models import ScanResult, ScanItem, RiskLevel, Category
from .registry_analyzer import RegistryAnalyzer
from .i18n import t
from scanners.base_scanner import BaseScanner
from scanners.app_cache_scanner import AppCacheScanner
from scanners.orphaned_appdata_scanner import OrphanedAppDataScanner
from scanners.installer_scanner import InstallerCacheScanner
from scanners.driver_store_scanner import DriverStoreScanner
from scanners.system_junk_scanner import SystemJunkScanner
from scanners.large_dormant_scanner import LargeDormantScanner
from scanners.dism_analyzer import DismAnalyzer
from scanners.registry_junk_scanner import RegistryJunkScanner


class DiskInfo:
    @staticmethod
    def get_drive_stats(drive_letter: str = "C:"):
        try:
            path = (drive_letter + "\\") if os.name == "nt" else "/"
            usage = psutil.disk_usage(path)
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            }
        except Exception:
            return {"total": 100 * (1024**3), "used": 40 * (1024**3), "free": 60 * (1024**3), "percent": 40.0}


class MasterScanner:
    """Orchestrates all specialized scanners and aggregates results."""

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        self.settings = settings or {}
        self.registry = RegistryAnalyzer()
        self.is_cancelled = False
        self._active_scanners: List[BaseScanner] = []

    def run_full_scan(
        self,
        target_drive: str = "C:",
        progress_callback: Optional[Callable[[str, int], None]] = None,
        item_found_callback: Optional[Callable[[ScanItem], None]] = None
    ) -> ScanResult:
        """
        Executes a complete scan across all categories.
        progress_callback: accepts (status_message, percentage_0_to_100)
        item_found_callback: invoked whenever a new ScanItem is discovered
        """
        self.is_cancelled = False
        self._active_scanners.clear()

        # Step 1: Pre-load Registry ground truth
        if progress_callback:
            progress_callback(t("status_scanning_init"), 5)
        self.registry.load()

        # Define scanner pipeline
        scanner_classes = [
            (t("cat_system_junk"), SystemJunkScanner),
            (t("cat_app_cache"), AppCacheScanner),
            (t("cat_orphaned_appdata"), OrphanedAppDataScanner),
            (t("cat_installer_cache"), InstallerCacheScanner),
            (t("cat_drivers"), DriverStoreScanner),
            (t("cat_large_dormant"), LargeDormantScanner),
            (t("cat_dism_component"), DismAnalyzer),
            (t("cat_registry_junk"), RegistryJunkScanner),
        ]

        all_items: List[ScanItem] = []
        errors: List[str] = []

        total_scanners = len(scanner_classes)

        for idx, (scanner_name, scanner_cls) in enumerate(scanner_classes):
            if self.is_cancelled:
                break

            base_pct = int(10 + (idx / total_scanners) * 85)
            if progress_callback:
                progress_callback(f"Scanning: {scanner_name}...", base_pct)

            try:
                scanner_instance = scanner_cls(self.registry, self.settings)
                self._active_scanners.append(scanner_instance)

                def sub_progress(msg: str, sub_pct: int):
                    if progress_callback:
                        adjusted_pct = min(99, int(base_pct + (sub_pct / 100) * (85 / total_scanners)))
                        progress_callback(msg, adjusted_pct)

                found_items = scanner_instance.scan(progress_callback=sub_progress)

                for item in found_items:
                    all_items.append(item)
                    if item_found_callback:
                        item_found_callback(item)

            except Exception as e:
                errors.append(f"Error in {scanner_name}: {str(e)}")

        if progress_callback:
            progress_callback("Scan completed!", 100)

        result = ScanResult(
            target_drive=target_drive,
            timestamp=datetime.now(),
            items=all_items,
            errors=errors
        )
        result.recalculate_totals()
        return result

    def cancel(self):
        """Cancels all active scanners."""
        self.is_cancelled = True
        for scanner in self._active_scanners:
            scanner.cancel()
