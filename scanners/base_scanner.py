"""
Base Scanner Interface for AetherClean.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Callable
from core.models import ScanItem, FileEntry, RiskLevel, Category
from core.registry_analyzer import RegistryAnalyzer


class BaseScanner(ABC):
    """Abstract base class for all disk and system cleanup scanners."""

    def __init__(self, registry_analyzer: Optional[RegistryAnalyzer] = None, settings: Optional[dict] = None):
        self.registry = registry_analyzer
        self.settings = settings or {}
        self.is_cancelled = False

    @abstractmethod
    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        """
        Executes scanner logic and returns a list of ScanItem objects.
        progress_callback: Optional function accepting (status_text: str, percentage: int)
        """
        pass

    def cancel(self):
        """Signals the scanner to abort execution cleanly."""
        self.is_cancelled = True
