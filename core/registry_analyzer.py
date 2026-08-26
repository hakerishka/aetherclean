"""
Registry and Installed Software Analyzer for Windows 11.
Extracts registered applications, publishers, install directories and MSI package identifiers
to cross-reference against filesystem directories and find orphaned leftovers.
"""

import os
import re
import winreg
import subprocess
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class InstalledAppInfo:
    name: str
    publisher: str
    version: str
    install_location: str
    uninstall_string: str
    registry_key: str
    source: str  # "HKLM_64", "HKLM_32", "HKCU", "UWP"


class RegistryAnalyzer:
    """Reads installed application info from Windows registry and AppX manifest."""

    UNINSTALL_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_WOW64_64KEY, "HKLM_64"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_WOW64_32KEY, "HKLM_32"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, "HKCU"),
    ]

    # Essential system publishers and keywords that must never be treated as orphaned
    SYSTEM_WHITELIST_KEYWORDS = {
        "microsoft", "windows", "nvidia", "intel", "amd", "realtek", "lenovo",
        "dell", "asus", "hp", "acer", "logitech", "synaptics", "vmware",
        "google", "mozilla", "brave", "telegram", "discord", "steam", "valve",
        "epic games", "spotify", "adobe", "jetbrains", "git", "python",
        "docker", "vlc", "7-zip", "winrar", "notepad++", "obs studio",
        "dotnet", "vcredist", "directx", "windows defender"
    }

    def __init__(self):
        self._installed_apps: List[InstalledAppInfo] = []
        self._known_app_names: Set[str] = set()
        self._known_publishers: Set[str] = set()
        self._known_install_dirs: Set[str] = set()
        self._known_tokens: Set[str] = set()
        self._msi_package_paths: Set[str] = set()
        self._is_loaded = False

    def load(self, include_uwp: bool = True):
        """Loads installed apps from registry and cached MSI records."""
        if self._is_loaded:
            return

        self._load_registry_apps()
        if include_uwp:
            self._load_uwp_apps()
        self._load_msi_registered_packages()
        self._build_token_index()
        self._is_loaded = True

    def _load_registry_apps(self):
        for root_key, sub_key, access_flag, source_label in self.UNINSTALL_PATHS:
            try:
                flags = winreg.KEY_READ | access_flag if access_flag else winreg.KEY_READ
                with winreg.OpenKey(root_key, sub_key, 0, flags) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as app_key:
                                display_name = self._safe_reg_query(app_key, "DisplayName")
                                if not display_name:
                                    # Fallback to subkey name if it's not a GUID
                                    if not subkey_name.startswith("{"):
                                        display_name = subkey_name
                                    else:
                                        continue

                                publisher = self._safe_reg_query(app_key, "Publisher")
                                version = self._safe_reg_query(app_key, "DisplayVersion")
                                install_loc = self._safe_reg_query(app_key, "InstallLocation")
                                uninstall_str = self._safe_reg_query(app_key, "UninstallString")

                                app_info = InstalledAppInfo(
                                    name=display_name.strip(),
                                    publisher=publisher.strip() if publisher else "",
                                    version=version.strip() if version else "",
                                    install_location=install_loc.strip() if install_loc else "",
                                    uninstall_string=uninstall_str.strip() if uninstall_str else "",
                                    registry_key=subkey_name,
                                    source=source_label
                                )
                                self._installed_apps.append(app_info)
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

    def _load_uwp_apps(self):
        """Loads Windows Store UWP packages from registry repository."""
        uwp_path = r"Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppModel\Repository\Packages"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, uwp_path, 0, winreg.KEY_READ) as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    try:
                        pkg_name = winreg.EnumKey(key, i)
                        # Extract friendly name from package family (e.g., Microsoft.WindowsCalculator_8wekyb3d8bbwe)
                        clean_name = pkg_name.split("_")[0] if "_" in pkg_name else pkg_name
                        self._installed_apps.append(
                            InstalledAppInfo(
                                name=clean_name,
                                publisher="Microsoft Store / UWP",
                                version="",
                                install_location="",
                                uninstall_string="",
                                registry_key=pkg_name,
                                source="UWP"
                            )
                        )
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass

    def _load_msi_registered_packages(self):
        """
        Reads registered MSI local package filepaths from:
        HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Installer\\UserData\\S-1-5-18\\Products
        and Patches.
        """
        base_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData\S-1-5-18"
        for sub_branch in ["Products", "Patches"]:
            full_branch = f"{base_path}\\{sub_branch}"
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, full_branch, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as root_key:
                    num_subkeys = winreg.QueryInfoKey(root_key)[0]
                    for i in range(num_subkeys):
                        try:
                            prod_id = winreg.EnumKey(root_key, i)
                            # For Products, LocalPackage is in InstallProperties
                            sub_path = f"{full_branch}\\{prod_id}\\InstallProperties" if sub_branch == "Products" else f"{full_branch}\\{prod_id}"
                            try:
                                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as prop_key:
                                    local_pkg = self._safe_reg_query(prop_key, "LocalPackage")
                                    if local_pkg and os.path.isabs(local_pkg):
                                        self._msi_package_paths.add(os.path.normpath(local_pkg).lower())
                            except (OSError, PermissionError):
                                continue
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

    def _build_token_index(self):
        """Indexes app names, publishers and install paths into searchable token sets."""
        for app in self._installed_apps:
            if app.name:
                self._known_app_names.add(app.name.lower())
                for token in self._tokenize(app.name):
                    if len(token) >= 3:
                        self._known_tokens.add(token)

            if app.publisher:
                self._known_publishers.add(app.publisher.lower())
                for token in self._tokenize(app.publisher):
                    if len(token) >= 3:
                        self._known_tokens.add(token)

            if app.install_location and os.path.isdir(app.install_location):
                self._known_install_dirs.add(os.path.normpath(app.install_location).lower())

    def is_folder_orphaned(self, folder_name: str, parent_vendor_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Determines if an AppData / ProgramData folder belongs to an uninstalled / dead application.
        Returns (is_orphaned, reason).
        """
        if not self._is_loaded:
            self.load()

        norm_folder = folder_name.lower().strip()
        tokens = self._tokenize(norm_folder)

        # Check vendor if available (e.g. AppData/Local/VendorName/AppName)
        if parent_vendor_name:
            norm_vendor = parent_vendor_name.lower().strip()
            if norm_vendor in self.SYSTEM_WHITELIST_KEYWORDS or any(kw in norm_vendor for kw in self.SYSTEM_WHITELIST_KEYWORDS):
                return False, f"Родительский разработчик '{parent_vendor_name}' находится в белом списке системы"

        # Check against system whitelist keywords
        for kw in self.SYSTEM_WHITELIST_KEYWORDS:
            if kw in norm_folder or norm_folder in kw:
                return False, f"Соответствует системному или активному компоненту '{kw}'"

        # Check against full app names
        for known_app in self._known_app_names:
            if norm_folder == known_app or (len(norm_folder) > 4 and norm_folder in known_app):
                return False, f"Найдена установленная программа: '{known_app}'"

        # Check token matches
        matching_tokens = [t for t in tokens if t in self._known_tokens and len(t) >= 4]
        if matching_tokens:
            return False, f"Совпадает с компонентом установленного ПО (токены: {', '.join(matching_tokens)})"

        return True, f"Не найдено связанных установленных программ или служб для '{folder_name}'"

    def is_msi_package_registered(self, msi_full_path: str) -> bool:
        """Returns True if the MSI/MSP file in C:\\Windows\\Installer is currently registered in Windows."""
        if not self._is_loaded:
            self.load()
        return os.path.normpath(msi_full_path).lower() in self._msi_package_paths

    def get_registered_msi_count(self) -> int:
        return len(self._msi_package_paths)

    def get_installed_apps_count(self) -> int:
        return len(self._installed_apps)

    @staticmethod
    def _safe_reg_query(key, value_name: str) -> Optional[str]:
        try:
            val, _ = winreg.QueryValueEx(key, value_name)
            return str(val) if val else None
        except (OSError, PermissionError):
            return None

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Split text into lowercase alphanumeric tokens."""
        clean = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ]", " ", text.lower())
        return [w for w in clean.split() if w]
