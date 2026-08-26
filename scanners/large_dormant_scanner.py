"""
Large and Dormant Files Scanner for AetherClean.
Identifies huge files (>500MB) untouched for months in Downloads, Videos, and user directories.
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Callable
from core.models import ScanItem, FileEntry, RiskLevel, Category
from .base_scanner import BaseScanner


class LargeDormantScanner(BaseScanner):
    """Scans for giant files (>500MB) that have not been modified or accessed in >90 days."""

    DORMANT_EXTENSIONS = {
        ".iso", ".img", ".vmdk", ".vdi", ".vhdx", ".zip", ".rar", ".7z",
        ".tar", ".gz", ".exe", ".msi", ".mp4", ".mkv", ".mov", ".avi", ".dmp"
    }

    def __init__(self, registry_analyzer=None, settings=None):
        super().__init__(registry_analyzer, settings)
        heuristics = self.settings.get("heuristics", {})
        self.min_size_bytes = heuristics.get("dormant_large_file_min_size_mb", 500) * 1024 * 1024
        self.min_days = heuristics.get("dormant_large_file_min_days", 90)

    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        user_profile = os.environ.get("USERPROFILE")
        if not user_profile:
            return []

        search_dirs = [
            os.path.join(user_profile, "Downloads"),
            os.path.join(user_profile, "Videos"),
            os.path.join(user_profile, "Documents"),
            os.path.join(user_profile, "Desktop"),
        ]

        found_files: List[FileEntry] = []
        cutoff_date = datetime.now() - timedelta(days=self.min_days)

        for s_dir in search_dirs:
            if self.is_cancelled:
                break
            if not os.path.isdir(s_dir):
                continue

            if progress_callback:
                progress_callback(f"Поиск забытых тяжелых файлов в {os.path.basename(s_dir)}...", 40)

            try:
                for root, dirs, files in os.walk(s_dir):
                    if self.is_cancelled:
                        break
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        full_p = os.path.join(root, f)
                        try:
                            stat = os.stat(full_p)
                            if stat.st_size >= self.min_size_bytes:
                                mtime = datetime.fromtimestamp(stat.st_mtime)
                                if mtime <= cutoff_date or ext in self.DORMANT_EXTENSIONS:
                                    days_old = (datetime.now() - mtime).days
                                    found_files.append(
                                        FileEntry(
                                            path=full_p,
                                            size=stat.st_size,
                                            mtime=mtime,
                                            is_dir=False,
                                            details=f"Файл не изменялся {days_old} дн."
                                        )
                                    )
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

        if not found_files:
            return []

        # Sort by size descending
        found_files.sort(key=lambda f: f.size, reverse=True)
        total_size = sum(f.size for f in found_files)

        reason = (
            f"Обнаружено {len(found_files)} файлов размером более {self.min_size_bytes / (1024**2):.0f} МБ, "
            f"к которым не обращались длительное время (ISO образы, старые архивы, установщики)."
        )

        item = ScanItem(
            id="large_dormant_user_files",
            title="Забытые тяжелые файлы пользователя (>500MB)",
            category=Category.LARGE_DORMANT,
            risk_level=RiskLevel.HIGH,
            safety_label="Высокий риск: личные файлы пользователя (ISO, архивы, установщики). Удалять только вручную",
            description="Крупные файлы в папках Загрузки, Документы, Видео, которые не изменялись месяцами.",
            reason=reason,
            total_size=total_size,
            file_count=len(found_files),
            paths=[f.path for f in found_files],
            files=found_files,
            is_selected=False,  # High risk -> never auto-selected
            metadata={"file_count": len(found_files)}
        )

        return [item]
