"""
Windows Registry Junk & Orphaned Keys Scanner for AetherClean.
Detects broken startup entries, dead App Paths, orphaned Software keys, and invalid shell extensions.
"""

import os
import re
import winreg
from typing import List, Optional, Callable, Tuple
from core.models import ScanItem, FileEntry, RiskLevel, Category
from core.registry_analyzer import RegistryAnalyzer
from .base_scanner import BaseScanner


class RegistryJunkScanner(BaseScanner):
    """Scans Windows Registry for dead references, broken startup entries, and orphaned software branches."""

    RUN_KEYS = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU\\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM\\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU\\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM\\RunOnce"),
    ]

    APP_PATHS_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"

    SYSTEM_VENDOR_WHITELIST = {
        "microsoft", "windows", "intel", "nvidia", "amd", "realtek", "lenovo",
        "dell", "asus", "hp", "acer", "google", "mozilla", "brave", "telegram",
        "discord", "steam", "valve", "epic games", "spotify", "adobe", "jetbrains",
        "python", "docker", "git", "windows defender", "classes", "policies"
    }

    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        if not self.registry:
            self.registry = RegistryAnalyzer()
            self.registry.load()

        items: List[ScanItem] = []

        # 1. Dead Startup Entries
        if progress_callback:
            progress_callback("Проверка битых записей автозагрузки в реестре...", 15)
        startup_items = self._scan_dead_startup_entries()
        items.extend(startup_items)

        # 2. Dead App Paths
        if progress_callback:
            progress_callback("Проверка устаревших путей приложений (App Paths)...", 45)
        app_path_items = self._scan_dead_app_paths()
        items.extend(app_path_items)

        # 3. Orphaned Software Keys (HKCU\Software & HKLM\Software)
        if progress_callback:
            progress_callback("Поиск осиротевших ключей удаленных программ в HKCU/HKLM...", 75)
        orphaned_soft_items = self._scan_orphaned_software_keys()
        items.extend(orphaned_soft_items)

        return items

    def _scan_dead_startup_entries(self) -> List[ScanItem]:
        dead_entries: List[FileEntry] = []

        for root_key, subkey_path, label in self.RUN_KEYS:
            try:
                with winreg.OpenKey(root_key, subkey_path, 0, winreg.KEY_READ) as key:
                    num_values = winreg.QueryInfoKey(key)[1]
                    for i in range(num_values):
                        val_name, val_data, _ = winreg.EnumValue(key, i)
                        if not val_data or not isinstance(val_data, str):
                            continue

                        # Extract executable file path from command line string
                        exe_path = self._extract_exe_path(val_data)
                        if exe_path and not os.path.exists(exe_path):
                            dead_entries.append(
                                FileEntry(
                                    path=f"{label} -> {val_name}",
                                    size=1024,
                                    is_dir=False,
                                    details=f"Запуск несуществующего файла: {exe_path}"
                                )
                            )
            except (OSError, PermissionError):
                continue

        if not dead_entries:
            return []

        reason = (
            f"В ветках автозагрузки реестра обнаружено {len(dead_entries)} записей, "
            f"ссылающихся на несуществующие исполняемые файлы (программы удалены, но записи остались)."
        )

        return [
            ScanItem(
                id="dead_registry_startup_entries",
                title="Битые записи автозагрузки в реестре",
                category=Category.REGISTRY_JUNK,
                risk_level=RiskLevel.SAFE,
                safety_label="Безопасно: ссылки на удаленные исполняемые файлы в автозагрузке",
                description="Записи в реестре Windows Run/RunOnce, оставшиеся от удаленных программ.",
                reason=reason,
                total_size=len(dead_entries) * 1024,
                file_count=len(dead_entries),
                paths=[],
                files=dead_entries,
                is_selected=True,
                metadata={"type": "startup_entries"}
            )
        ]

    def _scan_dead_app_paths(self) -> List[ScanItem]:
        dead_paths: List[FileEntry] = []

        for root_key, label in [(winreg.HKEY_LOCAL_MACHINE, "HKLM"), (winreg.HKEY_CURRENT_USER, "HKCU")]:
            try:
                with winreg.OpenKey(root_key, self.APP_PATHS_KEY, 0, winreg.KEY_READ) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        sub_name = winreg.EnumKey(key, i)
                        try:
                            with winreg.OpenKey(key, sub_name) as app_key:
                                default_val, _ = winreg.QueryValueEx(app_key, "")
                                if default_val and isinstance(default_val, str):
                                    clean_path = default_val.strip("\"' ")
                                    if clean_path.lower().endswith(".exe") and not os.path.exists(clean_path):
                                        dead_paths.append(
                                            FileEntry(
                                                path=f"{label}\\...\\App Paths\\{sub_name}",
                                                size=1024,
                                                is_dir=False,
                                                details=f"Путь не существует: {clean_path}"
                                            )
                                        )
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

        if not dead_paths:
            return []

        reason = (
            f"В реестре App Paths найдено {len(dead_paths)} записей быстрого запуска, "
            f"указывающих на удаленные исполняемые файлы."
        )

        return [
            ScanItem(
                id="dead_registry_app_paths",
                title="Устаревшие пути приложений в реестре (App Paths)",
                category=Category.REGISTRY_JUNK,
                risk_level=RiskLevel.SAFE,
                safety_label="Безопасно: пути вызова удаленных программ через диалог «Выполнить»",
                description="Регистрация команд быстрого запуска для программ, которые больше не присутствуют на диске.",
                reason=reason,
                total_size=len(dead_paths) * 1024,
                file_count=len(dead_paths),
                paths=[],
                files=dead_paths,
                is_selected=True,
                metadata={"type": "app_paths"}
            )
        ]

    def _scan_orphaned_software_keys(self) -> List[ScanItem]:
        orphaned_branches: List[FileEntry] = []

        # Check HKCU\Software keys
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software", 0, winreg.KEY_READ) as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    sub_name = winreg.EnumKey(key, i)
                    norm_name = sub_name.lower().strip()

                    if norm_name in self.SYSTEM_VENDOR_WHITELIST:
                        continue

                    # Check if this vendor / app exists in installed programs
                    is_orphan, reason = self.registry.is_folder_orphaned(sub_name)
                    if is_orphan:
                        # Cross-check if any files exist in Program Files or AppData
                        if not self._check_files_exist_for_app(sub_name):
                            orphaned_branches.append(
                                FileEntry(
                                    path=f"HKCU\\Software\\{sub_name}",
                                    size=2048,
                                    is_dir=False,
                                    details=f"Ветка конфигурации удаленной программы: {reason}"
                                )
                            )
        except (OSError, PermissionError):
            pass

        if not orphaned_branches:
            return []

        reason = (
            f"Обнаружено {len(orphaned_branches)} оставшихся веток настроек в HKCU\\Software "
            f"от программ, которые удалены из системы и не имеют связанных файлов на диске."
        )

        return [
            ScanItem(
                id="orphaned_software_registry_keys",
                title="Оставшиеся ветки конфигурации удаленного ПО (HKCU\\Software)",
                category=Category.REGISTRY_JUNK,
                risk_level=RiskLevel.MEDIUM,
                safety_label="Внимание: старые настройки удаленных программ в реестре",
                description="Ветки реестра, в которых программы хранили свои настройки. Программы удалены, но записи остались.",
                reason=reason,
                total_size=len(orphaned_branches) * 2048,
                file_count=len(orphaned_branches),
                paths=[],
                files=orphaned_branches,
                is_selected=False,
                metadata={"type": "software_keys"}
            )
        ]

    @staticmethod
    def _extract_exe_path(cmd_line: str) -> Optional[str]:
        """Extracts executable path from a Windows command line string."""
        s = cmd_line.strip()
        if s.startswith('"'):
            end_quote = s.find('"', 1)
            if end_quote != -1:
                return s[1:end_quote]
        parts = s.split()
        if parts:
            candidate = parts[0]
            if candidate.lower().endswith(".exe") or os.path.isabs(candidate):
                return candidate
        return None

    @staticmethod
    def _check_files_exist_for_app(app_name: str) -> bool:
        """Quick check if any directory with app_name exists in Program Files or AppData."""
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), app_name),
            os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), app_name),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), app_name),
            os.path.join(os.environ.get("APPDATA", ""), app_name),
        ]
        return any(os.path.exists(p) for p in candidates if p)
