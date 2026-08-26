"""
Unit tests for Scanners and Master Scanner Orchestrator.
"""

import pytest
from core.models import RiskLevel, Category
from core.scanner import MasterScanner, DiskInfo
from scanners.app_cache_scanner import AppCacheScanner
from scanners.system_junk_scanner import SystemJunkScanner
from scanners.dism_analyzer import DismAnalyzer
from scanners.registry_junk_scanner import RegistryJunkScanner


def test_disk_info():
    stats = DiskInfo.get_drive_stats("C:")
    assert stats["total"] > 0
    assert stats["free"] > 0


def test_dism_analyzer():
    analyzer = DismAnalyzer()
    items = analyzer.scan()
    assert len(items) >= 0  # Should run without crashing


def test_registry_junk_scanner():
    scanner = RegistryJunkScanner()
    items = scanner.scan()
    assert isinstance(items, list)
    for item in items:
        assert item.category == Category.REGISTRY_JUNK


def test_master_scanner_instantiation():
    master = MasterScanner()
    assert master is not None
    assert master.registry is not None
