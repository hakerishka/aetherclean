"""
Orphaned AppData and ProgramData Scanner.
Detects abandoned directories left behind by previously uninstalled applications.
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Callable, Tuple
from core.models import ScanItem, FileEntry, RiskLevel, Category
from core.registry_analyzer import RegistryAnalyzer
from .base_scanner import BaseScanner


class OrphanedAppDataScanner(BaseScanner):
    """Scans %LOCALAPPDATA%, %APPDATA%, %PROGRAMDATA% for orphaned application folders."""

    # Well-known essential top-level system folders in AppData/ProgramData to skip immediately
    SYSTEM_IGNORE_FOLDERS = {
        "microsoft", "windows", "temp", "packages", "system", "microsoft help",
        "windows defender", "windows security", "system32", "syswow64", "elevateddiagnostics",
        "crypto", "identitycrl", "regid.1991-06.com.microsoft", "usoshared", "ssh",
        "pip", "npm", "yarn", "docker", "git", "vscode", "github", "jetbrainstoolbox"
    }

    def __init__(self, registry_analyzer: Optional[RegistryAnalyzer] = None, settings: Optional[dict] = None):
        super().__init__(registry_analyzer, settings)
        self.min_days = self.settings.get("heuristics", {}).get("orphaned_appdata_min_days", 30)

    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        if not self.registry:
            self.registry = RegistryAnalyzer()
            self.registry.load()

        scan_roots = [
            ("AppData Local", os.environ.get("LOCALAPPDATA")),
            ("AppData Roaming", os.environ.get("APPDATA")),
            ("ProgramData", os.environ.get("PROGRAMDATA")),
        ]

        orphaned_items: List[ScanItem] = []
        cutoff_date = datetime.now() - timedelta(days=self.min_days)

        total_roots = len([r for r in scan_roots if r[1] and os.path.isdir(r[1])])
        current_root_idx = 0

        for label, root_path in scan_roots:
            if self.is_cancelled:
                break

            if not root_path or not os.path.isdir(root_path):
                continue

            current_root_idx += 1
            if progress_callback:
                progress_callback(f"Поиск остатков программ в {label}...", int((current_root_idx / total_roots) * 100))

            try:
                entries = list(os.scandir(root_path))
            except (OSError, PermissionError):
                continue

            for entry in entries:
                if self.is_cancelled:
                    break

                if not entry.is_dir() or entry.is_symlink():
                    continue

                folder_name = entry.name
                if folder_name.lower() in self.SYSTEM_IGNORE_FOLDERS:
                    continue

                # Check if this top-level folder is orphaned
                is_orphan, reason = self.registry.is_folder_orphaned(folder_name)

                if is_orphan:
                    # Deep check contents and last modification date
                    total_size, file_count, latest_mtime, sample_files = self._inspect_folder(entry.path)

                    if total_size == 0 and file_count == 0:
                        continue

                    # Determine risk level based on recency
                    is_recent = latest_mtime and latest_mtime > cutoff_date
                    risk = RiskLevel.HIGH if is_recent else RiskLevel.MEDIUM

                    recency_text = f"Последняя активность: {latest_mtime.strftime('%Y-%m-%d')}" if latest_mtime else "Дата изменения неизвестна"
                    safety_text = "Внимание: программа не найдена в реестре. Проверьте список файлов." if not is_recent else "Внимание: файлы изменялись недавно! Проверьте перед удалением."

                    detailed_reason = (
                        f"В каталоге {label} найдена папка '{folder_name}'. "
                        f"{reason}. {recency_text}."
                    )

                    orphaned_items.append(
                        ScanItem(
                            id=f"orphan_{label.lower().replace(' ', '_')}_{folder_name.lower()}",
                            title=f"Остатки {folder_name} ({label})",
                            category=Category.ORPHANED_APPDATA,
                            risk_level=risk,
                            safety_label=safety_text,
                            description=f"Оставшиеся файлы и конфигурация удаленного приложения '{folder_name}'.",
                            reason=detailed_reason,
                            total_size=total_size,
                            file_count=file_count,
                            paths=[entry.path],
                            files=sample_files,
                            is_selected=False,  # Unselected by default for user safety review
                            metadata={
                                "folder_name": folder_name,
                                "latest_mtime": latest_mtime.isoformat() if latest_mtime else None,
                                "root_type": label
                            }
                        )
                    )

        # Sort by total size descending
        orphaned_items.sort(key=lambda item: item.total_size, reverse=True)
        return orphaned_items

    def _inspect_folder(self, folder_path: str) -> Tuple[int, int, Optional[datetime], List[FileEntry]]:
        total_size = 0
        file_count = 0
        latest_mtime: Optional[datetime] = None
        sample_files: List[FileEntry] = []

        try:
            for root, dirs, files in os.walk(folder_path):
                if self.is_cancelled:
                    break
                for f in files:
                    full_p = os.path.join(root, f)
                    try:
                        stat = os.stat(full_p)
                        size = stat.st_size
                        mtime = datetime.fromtimestamp(stat.st_mtime)

                        total_size += size
                        file_count += 1

                        if latest_mtime is None or mtime > latest_mtime:
                            latest_mtime = mtime

                        if len(sample_files) < 150:
                            sample_files.append(
                                FileEntry(
                                    path=full_p,
                                    size=size,
                                    mtime=mtime,
                                    is_dir=False,
                                    details="Оставшийся файл программы"
                                )
                            )
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass

        return total_size, file_count, latest_mtime, sample_files
