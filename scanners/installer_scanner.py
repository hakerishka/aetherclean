"""
Windows Installer (C:\\Windows\\Installer) Cache Validator.
Cross-references .msi and .msp files against registry records to detect orphaned installers.
"""

import os
from datetime import datetime
from typing import List, Optional, Callable
from core.models import ScanItem, FileEntry, RiskLevel, Category
from core.registry_analyzer import RegistryAnalyzer
from .base_scanner import BaseScanner


class InstallerCacheScanner(BaseScanner):
    """Audits C:\\Windows\\Installer against Windows Registry MSI/MSP registrations."""

    INSTALLER_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Installer")

    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        if not self.registry:
            self.registry = RegistryAnalyzer()
            self.registry.load()

        if not os.path.isdir(self.INSTALLER_DIR):
            return []

        if progress_callback:
            progress_callback("Анализ кэша установщиков C:\\Windows\\Installer...", 10)

        orphaned_files: List[FileEntry] = []
        total_orphaned_bytes = 0
        total_files_scanned = 0

        try:
            entries = [
                os.path.join(self.INSTALLER_DIR, f)
                for f in os.listdir(self.INSTALLER_DIR)
                if f.lower().endswith((".msi", ".msp"))
            ]
        except (OSError, PermissionError):
            return []

        total_count = len(entries)
        if total_count == 0:
            return []

        for idx, file_path in enumerate(entries):
            if self.is_cancelled:
                break

            total_files_scanned += 1
            if progress_callback and idx % 20 == 0:
                pct = int((idx / total_count) * 100)
                progress_callback(f"Проверка MSI/MSP пакетов ({idx}/{total_count})...", pct)

            # Check if this MSI/MSP is registered in Windows registry
            is_registered = self.registry.is_msi_package_registered(file_path)

            if not is_registered:
                try:
                    stat = os.stat(file_path)
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime)

                    total_orphaned_bytes += size
                    orphaned_files.append(
                        FileEntry(
                            path=file_path,
                            size=size,
                            mtime=mtime,
                            is_dir=False,
                            details="Неиспользуемый MSI/MSP пакет (отсутствует в реестре)"
                        )
                    )
                except (OSError, PermissionError):
                    continue

        if not orphaned_files:
            return []

        registered_count = self.registry.get_registered_msi_count()
        reason = (
            f"В папке C:\\Windows\\Installer обнаружено {len(orphaned_files)} пакетов (.msi/.msp), "
            f"которые больше не привязаны ни к одной установленной программе. "
            f"Действующих пакетов в реестре: {registered_count}."
        )

        item = ScanItem(
            id="orphaned_windows_installers",
            title="Неиспользуемые пакеты Windows Installer (.msi / .msp)",
            category=Category.INSTALLER_CACHE,
            risk_level=RiskLevel.MEDIUM,
            safety_label="Внимание: старые дистрибутивы обновлений, отсутствующие в реестре",
            description="Пакеты установки и обновления программ, которые больше не зарегистрированы в системе. Рекомендуется переместить в Карантин.",
            reason=reason,
            total_size=total_orphaned_bytes,
            file_count=len(orphaned_files),
            paths=[f.path for f in orphaned_files],
            files=orphaned_files,
            is_selected=False,  # Unselected by default for safety
            metadata={
                "orphaned_count": len(orphaned_files),
                "registered_count": registered_count
            }
        )

        return [item]
