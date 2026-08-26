"""
Unit tests for Declarative Rule Engine.
"""

import os
import tempfile
import pytest
from core.rule_engine import RuleEngine
from core.models import RiskLevel, Category


def test_rule_engine_loading():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rules_dir = os.path.join(base_dir, "config", "rules")

    engine = RuleEngine(rules_dir)
    count = engine.load_rules()
    assert count > 0, "Should load at least one rule from config/rules"


def test_rule_scanning_with_temp_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy cache files
        cache_dir = os.path.join(tmpdir, "DummyApp", "Cache")
        os.makedirs(cache_dir, exist_ok=True)

        file1 = os.path.join(cache_dir, "data1.bin")
        file2 = os.path.join(cache_dir, "data2.bin")

        with open(file1, "wb") as f:
            f.write(b"0" * 1024)
        with open(file2, "wb") as f:
            f.write(b"0" * 2048)

        engine = RuleEngine()
        rule = {
            "id": "dummy_cache_rule",
            "name": "Dummy App Cache",
            "category": "app_cache",
            "risk_level": "safe",
            "safety_label": "Безопасно",
            "description": "Тестовый кэш",
            "paths": [os.path.join(tmpdir, "DummyApp", "Cache")]
        }

        item = engine.scan_rule(rule)
        assert item is not None
        assert item.total_size == 3072
        assert item.file_count == 2
        assert item.risk_level == RiskLevel.SAFE
        assert item.category == Category.APP_CACHE
