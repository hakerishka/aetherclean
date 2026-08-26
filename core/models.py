"""
Data models and enumerations for AetherClean with i18n support.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from .i18n import t


class RiskLevel(str, Enum):
    SAFE = "safe"          # 🟢 Safe to remove, zero impact on applications
    MEDIUM = "medium"      # 🟡 Low/Medium risk: orphaned files or rollback data
    HIGH = "high"          # 🔴 Review required: system component or large user data

    @property
    def badge_text(self) -> str:
        if self == RiskLevel.SAFE:
            return t("risk_safe")
        elif self == RiskLevel.MEDIUM:
            return t("risk_medium")
        else:
            return t("risk_high")

    @property
    def color_hex(self) -> str:
        if self == RiskLevel.SAFE:
            return "#4CAF50"
        elif self == RiskLevel.MEDIUM:
            return "#FFA726"
        else:
            return "#EF5350"


class Category(str, Enum):
    APP_CACHE = "app_cache"
    ORPHANED_APPDATA = "orphaned_appdata"
    SYSTEM_JUNK = "system_junk"
    INSTALLER_CACHE = "installer_cache"
    DRIVERS = "drivers"
    LARGE_DORMANT = "large_dormant"
    DISM_COMPONENT = "dism_component"
    REGISTRY_JUNK = "registry_junk"

    @property
    def display_name(self) -> str:
        key_map = {
            Category.APP_CACHE: "cat_app_cache",
            Category.ORPHANED_APPDATA: "cat_orphaned_appdata",
            Category.SYSTEM_JUNK: "cat_system_junk",
            Category.INSTALLER_CACHE: "cat_installer_cache",
            Category.DRIVERS: "cat_drivers",
            Category.LARGE_DORMANT: "cat_large_dormant",
            Category.DISM_COMPONENT: "cat_dism_component",
            Category.REGISTRY_JUNK: "cat_registry_junk",
        }
        return t(key_map.get(self, "cat_app_cache"))

    @property
    def icon_name(self) -> str:
        icons = {
            Category.APP_CACHE: "🌐",
            Category.ORPHANED_APPDATA: "🗑️",
            Category.SYSTEM_JUNK: "⚙️",
            Category.INSTALLER_CACHE: "📦",
            Category.DRIVERS: "🔌",
            Category.LARGE_DORMANT: "🐘",
            Category.DISM_COMPONENT: "🧩",
            Category.REGISTRY_JUNK: "📑",
        }
        return icons.get(self, "📁")


class CleanAction(str, Enum):
    RECYCLE_BIN = "recycle_bin"
    QUARANTINE = "quarantine"
    PERMANENT_DELETE = "permanent_delete"


@dataclass
class FileEntry:
    """Represents a single file or subdirectory inside a ScanItem."""
    path: str
    size: int
    mtime: Optional[datetime] = None
    is_dir: bool = False
    details: str = ""


@dataclass
class ScanItem:
    """Represents a logical cleanable item (e.g. a specific app's cache or an orphaned folder)."""
    id: str
    title: str
    category: Category
    risk_level: RiskLevel
    safety_label: str
    description: str
    reason: str
    total_size: int = 0
    file_count: int = 0
    paths: List[str] = field(default_factory=list)
    files: List[FileEntry] = field(default_factory=list)
    is_selected: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def format_size(self) -> str:
        return format_bytes(self.total_size)


@dataclass
class CategoryGroup:
    category: Category
    items: List[ScanItem] = field(default_factory=list)
    total_size: int = 0
    selected_size: int = 0

    def recalculate(self):
        self.total_size = sum(item.total_size for item in self.items)
        self.selected_size = sum(item.total_size for item in self.items if item.is_selected)


@dataclass
class ScanResult:
    target_drive: str
    timestamp: datetime
    items: List[ScanItem] = field(default_factory=list)
    total_bytes: int = 0
    selected_bytes: int = 0
    scanned_folders: int = 0
    errors: List[str] = field(default_factory=list)

    def recalculate_totals(self):
        self.total_bytes = sum(i.total_size for i in self.items)
        self.selected_bytes = sum(i.total_size for i in self.items if i.is_selected)

    def get_by_category(self) -> Dict[Category, CategoryGroup]:
        groups: Dict[Category, CategoryGroup] = {}
        for cat in Category:
            groups[cat] = CategoryGroup(category=cat)

        for item in self.items:
            if item.category in groups:
                groups[item.category].items.append(item)

        # Recalculate sizes and remove empty categories
        result = {}
        for cat, group in groups.items():
            if group.items:
                group.recalculate()
                result[cat] = group
        return result


def format_bytes(byte_count: int) -> str:
    """Format bytes to human readable string (KB, MB, GB)."""
    if byte_count < 0:
        return "0 B"
    if byte_count < 1024:
        return f"{byte_count} B"
    elif byte_count < 1024 ** 2:
        return f"{byte_count / 1024:.1f} KB"
    elif byte_count < 1024 ** 3:
        return f"{byte_count / (1024 ** 2):.2f} MB"
    else:
        return f"{byte_count / (1024 ** 3):.2f} GB"
