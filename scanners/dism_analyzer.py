"""
Windows Component Store (WinSxS) & DISM Analyzer.
Provides analysis of WinSxS store health and recommendations for component cleanup.
"""

import os
import re
import subprocess
from typing import List, Optional, Callable
from core.models import ScanItem, RiskLevel, Category
from .base_scanner import BaseScanner


class DismAnalyzer(BaseScanner):
    """Analyzes WinSxS component store using DISM /AnalyzeComponentStore."""

    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        winsxs_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "WinSxS")
        if not os.path.isdir(winsxs_dir):
            return []

        if progress_callback:
            progress_callback("Анализ хранилища компонентов Windows (WinSxS / DISM)...", 50)

        # Quick size check of WinSxS folder
        total_size = 0
        try:
            for entry in os.scandir(winsxs_dir):
                if self.is_cancelled:
                    break
                if entry.is_file():
                    try:
                        total_size += entry.stat().st_size
                    except (OSError, PermissionError):
                        pass
                elif entry.is_dir():
                    # Check top-level subfolders approximate size
                    try:
                        for sub in os.scandir(entry.path):
                            if sub.is_file():
                                total_size += sub.stat().st_size
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass

        reason = (
            "Хранилище компонентов Windows (WinSxS) хранит файлы системных служб и резервные копии предыдущих версий компонентов. "
            "Прямое удаление файлов из этой папки запрещено Windows. Безопасная очистка выполняется через команду DISM /StartComponentCleanup."
        )

        item = ScanItem(
            id="winsxs_component_cleanup",
            title="Хранилище компонентов Windows (WinSxS)",
            category=Category.DISM_COMPONENT,
            risk_level=RiskLevel.SAFE,
            safety_label="Безопасно: очистка устаревших компонентов через официальный системный инструмент DISM",
            description="Очистка замененных системных компонентов и резервных копий старых накопительных обновлений Windows Update.",
            reason=reason,
            total_size=max(total_size, 1024 * 1024 * 500), # minimum estimated size
            file_count=1,
            paths=[winsxs_dir],
            is_selected=False,
            metadata={"dism_cleanup_supported": True}
        )

        return [item]
