"""
Unit tests for Registry and Installed Software Analyzer.
"""

import pytest
from core.registry_analyzer import RegistryAnalyzer, InstalledAppInfo


def test_registry_tokenization():
    analyzer = RegistryAnalyzer()
    tokens = analyzer._tokenize("Telegram Desktop (x64) v4.8.1")
    assert "telegram" in tokens
    assert "desktop" in tokens
    assert "x64" in tokens


def test_whitelist_matching():
    analyzer = RegistryAnalyzer()
    # Microsoft and NVIDIA should be recognized as non-orphaned by whitelist
    is_orphan, reason = analyzer.is_folder_orphaned("Microsoft", parent_vendor_name=None)
    assert not is_orphan

    is_orphan, reason = analyzer.is_folder_orphaned("NVIDIA Corporation", parent_vendor_name=None)
    assert not is_orphan


def test_custom_app_matching():
    analyzer = RegistryAnalyzer()
    # Inject a simulated installed app
    analyzer._installed_apps.append(
        InstalledAppInfo(
            name="SuperCustomCoolApp 2026",
            publisher="CoolVendor Ltd",
            version="1.0.0",
            install_location=r"C:\Program Files\SuperCustomCoolApp",
            uninstall_string="",
            registry_key="SuperCustomCoolApp",
            source="HKLM_64"
        )
    )
    analyzer._build_token_index()
    analyzer._is_loaded = True

    # Folder matching installed app
    is_orphan, reason = analyzer.is_folder_orphaned("SuperCustomCoolApp")
    assert not is_orphan

    # Completely unknown folder
    is_orphan, reason = analyzer.is_folder_orphaned("CompletelyUnknownOldGame2012")
    assert is_orphan
