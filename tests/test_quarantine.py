"""
Unit tests for Quarantine Manager and 1-Click Rollback.
"""

import os
import tempfile
import pytest
from core.quarantine_manager import QuarantineManager
from core.models import ScanItem, CleanAction, RiskLevel, Category


def test_quarantine_and_restore_cycle():
    with tempfile.TemporaryDirectory() as base_tmp:
        quarantine_dir = os.path.join(base_tmp, "quarantine_store")
        source_dir = os.path.join(base_tmp, "app_data_folder")
        os.makedirs(source_dir, exist_ok=True)

        test_file = os.path.join(source_dir, "test_orphan.dat")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("important dummy data")

        assert os.path.exists(test_file)

        qm = QuarantineManager(quarantine_dir)

        item = ScanItem(
            id="test_orphan_item",
            title="Test Orphan",
            category=Category.ORPHANED_APPDATA,
            risk_level=RiskLevel.MEDIUM,
            safety_label="Внимание",
            description="Тестовый сирота",
            reason="Тест",
            total_size=len("important dummy data"),
            file_count=1,
            paths=[source_dir],
            is_selected=True
        )

        # 1. Clean to Quarantine
        freed, count, errors = qm.execute_cleaning([item], action=CleanAction.QUARANTINE)
        assert count == 1
        assert not errors
        assert not os.path.exists(source_dir) # Should be moved out of source

        # 2. Check Session was created
        sessions = qm.list_sessions()
        assert len(sessions) == 1
        session = sessions[0]
        assert session.item_count == 1
        assert not session.is_restored

        # 3. Restore session
        restored, restore_errs = qm.restore_session(session.session_id)
        assert restored == 1
        assert not restore_errs

        # 4. Verify file is back in place with original content
        assert os.path.exists(test_file)
        with open(test_file, "r", encoding="utf-8") as f:
            assert f.read() == "important dummy data"


def test_cleaning_progress_and_logging():
    with tempfile.TemporaryDirectory() as base_tmp:
        quarantine_dir = os.path.join(base_tmp, "quarantine_store")
        source_dir = os.path.join(base_tmp, "cache_folder")
        os.makedirs(source_dir, exist_ok=True)

        for i in range(5):
            with open(os.path.join(source_dir, f"cache_{i}.tmp"), "w", encoding="utf-8") as f:
                f.write(f"cache data {i}")

        qm = QuarantineManager(quarantine_dir)

        item = ScanItem(
            id="test_cache",
            title="Test App Cache",
            category=Category.APP_CACHE,
            risk_level=RiskLevel.SAFE,
            safety_label="Безопасно",
            description="Тестовый кэш",
            reason="Тест прогресса",
            total_size=100,
            file_count=5,
            paths=[source_dir],
            is_selected=True,
            metadata={"options": {"delete_contents_only": True}}
        )

        progress_calls = []
        log_messages = []

        def on_prog(curr, total, title, cur_p, pct):
            progress_calls.append((curr, total, title, pct))

        def on_log(msg, lvl):
            log_messages.append((msg, lvl))

        freed, count, errs = qm.execute_cleaning(
            [item],
            action=CleanAction.PERMANENT_DELETE,
            progress_callback=on_prog,
            log_callback=on_log
        )

        assert freed > 0
        assert count == 5
        assert len(progress_calls) > 0
        assert len(log_messages) > 0
        # Source directory itself should still exist because delete_contents_only was set
        assert os.path.exists(source_dir)
        # But files inside should be cleaned
        assert len(os.listdir(source_dir)) == 0
