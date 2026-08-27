"""
Windows System Junk and Crash Dumps Scanner for AetherClean.
"""

import os
import yaml
from typing import List, Optional, Callable
from core.models import ScanItem, RiskLevel, Category
from core.rule_engine import RuleEngine
from core.path_utils import get_config_path
from .base_scanner import BaseScanner


class SystemJunkScanner(BaseScanner):
    """Scans for WER dumps, Windows Temp, Delivery Optimization and update caches."""

    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        items: List[ScanItem] = []
        junk_rules_path = get_config_path(os.path.join("config", "rules", "system_junk.yaml"))

        rule_engine = RuleEngine()
        if os.path.exists(junk_rules_path):
            try:
                with open(junk_rules_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "rules" in data:
                        rules = data["rules"]
                        total_rules = len(rules)
                        for idx, rule in enumerate(rules):
                            if self.is_cancelled:
                                break
                            if progress_callback:
                                pct = int((idx / total_rules) * 100)
                                progress_callback(f"Scanning system junk: {rule.get('name', '')}...", pct)

                            item = rule_engine.scan_rule(rule)
                            if item:
                                item.category = Category.SYSTEM_JUNK
                                items.append(item)
            except Exception as e:
                print(f"[SystemJunkScanner] Error reading system rules: {e}")

        return items
