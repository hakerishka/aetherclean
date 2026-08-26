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
            usage = psutil.disk_usage(drive_letter + "\\")
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            }
        except Exception:
            return {"total": 0, "used": 0, "free": 0, "percent": 0}


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
            progress_callback("Анализ установленных программ Windows и реестра...", 5)
        self.registry.load()

        # Define scanner pipeline
        scanner_classes = [
            ("Системный мусор и дампы", SystemJunkScanner),
            ("Кэши приложений", AppCacheScanner),
            ("Остатки удаленных программ", OrphanedAppDataScanner),
            ("Кэш установщиков Windows", InstallerCacheScanner),
            ("Хранилище драйверов", DriverStoreScanner),
            ("Забытые тяжелые файлы", LargeDormantScanner),
            ("Хранилище компонентов", DismAnalyzer),
            ("Остатки в реестре Windows", RegistryJunkScanner),
        ]

        all_items: List[ScanItem] = []
        errors: List[str] = []

        total_scanners = len(scanner_classes)

        for idx, (scanner_name, scanner_cls) in enumerate(scanner_classes):
            if self.is_cancelled:
                break

            base_pct = int(10 + (idx / total_scanners) * 85)
            if progress_callback:
                progress_callback(f"Запуск: {scanner_name}...", base_pct)

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
                errors.append(f"Ошибка в {scanner_name}: {str(e)}")

        if progress_callback:
            progress_callback("Сканирование завершено!", 100)

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
