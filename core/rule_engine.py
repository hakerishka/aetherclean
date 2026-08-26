"""
Declarative YAML/JSON Rule Engine for AetherClean.
Loads, parses, and resolves declarative file/folder rules with environment variables and wildcards.
"""

import os
import glob
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .models import ScanItem, FileEntry, RiskLevel, Category


class RuleEngine:
    """Manages loading and matching of declarative file/folder cleanup rules."""

    def __init__(self, rules_dir: Optional[str] = None):
        if rules_dir is None:
            # Default to config/rules inside the project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rules_dir = os.path.join(base_dir, "config", "rules")
        self.rules_dir = rules_dir
        self.rules: List[Dict[str, Any]] = []

    def load_rules(self) -> int:
        """Loads all YAML/JSON rule files from the rules directory."""
        self.rules.clear()
        if not os.path.isdir(self.rules_dir):
            return 0

        for file_path in glob.glob(os.path.join(self.rules_dir, "*.yaml")) + glob.glob(os.path.join(self.rules_dir, "*.yml")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "rules" in data:
                        for rule in data["rules"]:
                            self.rules.append(rule)
            except Exception as e:
                print(f"[RuleEngine] Error loading {file_path}: {e}")

        return len(self.rules)

    def scan_rule(self, rule: Dict[str, Any], whitelist: Optional[List[str]] = None) -> Optional[ScanItem]:
        """Evaluates a single rule and returns a ScanItem if matches are found."""
        rule_id = rule.get("id", "unknown_rule")
        name = rule.get("name", "Unknown Item")
        cat_str = rule.get("category", "app_cache")
        risk_str = rule.get("risk_level", "safe")
        safety_label = rule.get("safety_label", "Безопасно для удаления")
        description = rule.get("description", "")
        paths_patterns = rule.get("paths", [])
        options = rule.get("options", {})

        category = Category(cat_str) if cat_str in [c.value for c in Category] else Category.APP_CACHE
        risk_level = RiskLevel(risk_str) if risk_str in [r.value for r in RiskLevel] else RiskLevel.SAFE

        matched_files: List[FileEntry] = []
        matched_roots: List[str] = []
        total_size = 0

        min_age_hours = options.get("min_age_hours", 0)
        delete_contents_only = options.get("delete_contents_only", False)
        cutoff_time = datetime.now() - timedelta(hours=min_age_hours) if min_age_hours > 0 else None

        for pattern in paths_patterns:
            resolved_patterns = self.resolve_path(pattern)
            for resolved_path in resolved_patterns:
                for matched_path in glob.glob(resolved_path):
                    if whitelist and self._is_whitelisted(matched_path, whitelist):
                        continue

                    if not os.path.exists(matched_path):
                        continue

                    matched_roots.append(matched_path)

                    if os.path.isfile(matched_path):
                        size = self._safe_file_size(matched_path)
                        mtime = self._safe_file_mtime(matched_path)
                        if cutoff_time and mtime and mtime > cutoff_time:
                            continue
                        total_size += size
                        matched_files.append(
                            FileEntry(
                                path=matched_path,
                                size=size,
                                mtime=mtime,
                                is_dir=False,
                                details="Файл по правилу"
                            )
                        )
                    elif os.path.isdir(matched_path):
                        # Walk directory
                        dir_size, dir_files = self._scan_directory(
                            matched_path,
                            cutoff_time=cutoff_time,
                            whitelist=whitelist
                        )
                        total_size += dir_size
                        matched_files.extend(dir_files)

        if not matched_files and total_size == 0:
            return None

        reason = f"Обнаружен кэш/временные данные по правилу '{name}'. Найдено {len(matched_files)} файлов."

        return ScanItem(
            id=rule_id,
            title=name,
            category=category,
            risk_level=risk_level,
            safety_label=safety_label,
            description=description,
            reason=reason,
            total_size=total_size,
            file_count=len(matched_files),
            paths=list(set(matched_roots)),
            files=matched_files[:1000],  # Keep preview list manageable
            is_selected=(risk_level == RiskLevel.SAFE),
            metadata={"rule_id": rule_id, "options": options}
        )

    def _scan_directory(self, dir_path: str, cutoff_time: Optional[datetime] = None, whitelist: Optional[List[str]] = None):
        total_size = 0
        file_entries: List[FileEntry] = []

        try:
            for root, dirs, files in os.walk(dir_path):
                if whitelist and self._is_whitelisted(root, whitelist):
                    continue

                for f in files:
                    full_p = os.path.join(root, f)
                    try:
                        stat = os.stat(full_p)
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        if cutoff_time and mtime > cutoff_time:
                            continue
                        size = stat.st_size
                        total_size += size
                        file_entries.append(
                            FileEntry(
                                path=full_p,
                                size=size,
                                mtime=mtime,
                                is_dir=False,
                                details="Вложенный файл кэша"
                            )
                        )
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass

        return total_size, file_entries

    @staticmethod
    def resolve_path(path_template: str) -> List[str]:
        """Expands Windows environment variables like %LOCALAPPDATA%, %APPDATA%, %TEMP%."""
        expanded = os.path.expandvars(path_template)
        return [expanded]

    @staticmethod
    def _is_whitelisted(path: str, whitelist: List[str]) -> bool:
        norm = os.path.normpath(path).lower()
        for w in whitelist:
            if norm.startswith(os.path.normpath(w).lower()):
                return True
        return False

    @staticmethod
    def _safe_file_size(path: str) -> int:
        try:
            return os.path.getsize(path)
        except (OSError, PermissionError):
            return 0

    @staticmethod
    def _safe_file_mtime(path: str) -> Optional[datetime]:
        try:
            return datetime.fromtimestamp(os.path.getmtime(path))
        except (OSError, PermissionError):
            return None
