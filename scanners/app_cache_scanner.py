"""
Application Cache Scanner for AetherClean.
Discovers browser caches, electron app caches, messenger media caches, and shader caches.
"""

import os
from typing import List, Optional, Callable
from core.models import ScanItem, RiskLevel, Category
from core.rule_engine import RuleEngine
from .base_scanner import BaseScanner


class AppCacheScanner(BaseScanner):
    """Scans application caches defined in YAML rule files."""

    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        items: List[ScanItem] = []
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cache_rules_path = os.path.join(base_dir, "config", "rules", "app_caches.yaml")

        rule_engine = RuleEngine()
        if os.path.exists(cache_rules_path):
            import yaml
            try:
                with open(cache_rules_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "rules" in data:
                        rules = data["rules"]
                        total_rules = len(rules)
                        for idx, rule in enumerate(rules):
                            if self.is_cancelled:
                                break
                            if progress_callback:
                                pct = int((idx / total_rules) * 100)
                                progress_callback(f"Поиск кэша: {rule.get('name', '')}...", pct)

                            item = rule_engine.scan_rule(rule)
                            if item:
                                item.category = Category.APP_CACHE
                                items.append(item)
            except Exception as e:
                print(f"[AppCacheScanner] Error reading cache rules: {e}")

        return items
