"""
Quarantine and Rollback Engine for AetherClean.
Manages safe isolation of files/folders, session manifests, detailed progress logging, and 1-click restore.
"""

import os
import json
import shutil
import send2trash
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict

from .models import ScanItem, CleanAction, format_bytes


@dataclass
class QuarantineFileRecord:
    original_path: str
    quarantine_path: str
    is_dir: bool
    size: int
    category: str


@dataclass
class QuarantineSession:
    session_id: str
    timestamp: str
    total_bytes: int
    item_count: int
    records: List[QuarantineFileRecord]
    is_restored: bool = False


class QuarantineManager:
    """Manages moving items to quarantine, tracking manifests, and restoring."""

    def __init__(self, base_quarantine_dir: Optional[str] = None):
        if not base_quarantine_dir:
            base_quarantine_dir = os.path.join(os.environ.get("SystemDrive", "C:"), "AetherClean_Quarantine")
        self.base_dir = base_quarantine_dir
        self.is_cancelled = False
        os.makedirs(self.base_dir, exist_ok=True)

    def cancel(self):
        """Signals the cleaning engine to stop execution."""
        self.is_cancelled = True

    def execute_cleaning(
        self,
        items_to_clean: List[ScanItem],
        action: CleanAction,
        progress_callback: Optional[Callable[[int, int, str, str, int], None]] = None,
        log_callback: Optional[Callable[[str, str], None]] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Executes cleaning of selected items in background.
        progress_callback: (current_idx, total_items, item_title, current_path, percentage)
        log_callback: (message, log_level: 'info'|'ok'|'warn'|'err')
        Returns (freed_bytes, processed_items_count, errors_list).
        """
        self.is_cancelled = False
        freed_bytes = 0
        cleaned_count = 0
        errors: List[str] = []

        active_items = [i for i in items_to_clean if i.is_selected]
        total_items = len(active_items)

        if total_items == 0:
            return 0, 0, []

        session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.base_dir, session_id)
        records: List[QuarantineFileRecord] = []

        if action == CleanAction.QUARANTINE:
            os.makedirs(session_dir, exist_ok=True)
            if log_callback:
                log_callback(f"📦 Создана сессия карантина: {session_id}", "info")

        for idx, item in enumerate(active_items):
            if self.is_cancelled:
                if log_callback:
                    log_callback("⏹️ Очистка остановлена пользователем.", "warn")
                break

            pct = int((idx / total_items) * 100)
            if progress_callback:
                progress_callback(idx + 1, total_items, item.title, "", pct)

            if log_callback:
                log_callback(f"Начало обработки: {item.title} ({item.format_size()})", "info")

            # Check if this item is marked to delete contents only (e.g. %TEMP% or %WINDIR%\Temp)
            delete_contents_only = item.metadata.get("options", {}).get("delete_contents_only", False)

            paths_to_remove = item.paths if item.paths else [f.path for f in item.files]

            for target_path in paths_to_remove:
                if self.is_cancelled:
                    break

                if not os.path.exists(target_path):
                    continue

                if progress_callback:
                    progress_callback(idx + 1, total_items, item.title, target_path, pct)

                try:
                    is_dir = os.path.isdir(target_path)

                    if delete_contents_only and is_dir:
                        # Clean inner contents only (leaving folder intact)
                        dir_freed, dir_cleaned, dir_errs = self._clean_directory_contents(
                            target_path,
                            action,
                            session_dir,
                            records,
                            item.category.value,
                            log_callback
                        )
                        freed_bytes += dir_freed
                        cleaned_count += dir_cleaned
                        errors.extend(dir_errs)
                    else:
                        # Process target directly
                        item_size = self._calc_path_size(target_path)

                        if action == CleanAction.RECYCLE_BIN:
                            send2trash.send2trash(target_path)
                            freed_bytes += item_size
                            cleaned_count += 1
                            if log_callback:
                                log_callback(f"✔ Отправлено в Корзину: {target_path} ({format_bytes(item_size)})", "ok")

                        elif action == CleanAction.QUARANTINE:
                            rel_id = f"item_{len(records) + 1}_{os.path.basename(target_path)}"
                            dest_path = os.path.join(session_dir, rel_id)
                            shutil.move(target_path, dest_path)

                            record = QuarantineFileRecord(
                                original_path=target_path,
                                quarantine_path=dest_path,
                                is_dir=is_dir,
                                size=item_size,
                                category=item.category.value
                            )
                            records.append(record)
                            freed_bytes += item_size
                            cleaned_count += 1
                            if log_callback:
                                log_callback(f"📦 Изолировано в карантин: {target_path} ({format_bytes(item_size)})", "ok")

                        elif action == CleanAction.PERMANENT_DELETE:
                            if is_dir:
                                shutil.rmtree(target_path, ignore_errors=False)
                            else:
                                os.remove(target_path)
                            freed_bytes += item_size
                            cleaned_count += 1
                            if log_callback:
                                log_callback(f"🗑️ Удалено: {target_path} ({format_bytes(item_size)})", "ok")

                except (PermissionError, OSError) as e:
                    msg = f"Файл/папка занята процессом: {target_path}"
                    errors.append(msg)
                    if log_callback:
                        log_callback(f"ℹ️ Пропущено (занято процессом): {os.path.basename(target_path)}", "warn")
                except Exception as e:
                    msg = f"Ошибка при обработке '{target_path}': {str(e)}"
                    errors.append(msg)
                    if log_callback:
                        log_callback(f"❌ {msg}", "err")

        # Save session manifest if quarantine was used
        if action == CleanAction.QUARANTINE and records:
            self._save_session_manifest(session_dir, session_id, freed_bytes, records)

        if progress_callback:
            progress_callback(total_items, total_items, "Готово", "", 100)

        if log_callback:
            log_callback(f"✨ Очистка завершена! Всего освобождено: {format_bytes(freed_bytes)}", "ok")

        return freed_bytes, cleaned_count, errors

    def _clean_directory_contents(
        self,
        dir_path: str,
        action: CleanAction,
        session_dir: str,
        records: List[QuarantineFileRecord],
        category_name: str,
        log_callback: Optional[Callable[[str, str], None]] = None
    ) -> Tuple[int, int, List[str]]:
        freed = 0
        cleaned = 0
        errors = []

        try:
            entries = list(os.scandir(dir_path))
        except (OSError, PermissionError):
            return 0, 0, []

        for entry in entries:
            if self.is_cancelled:
                break
            try:
                item_size = self._calc_path_size(entry.path)

                if action == CleanAction.RECYCLE_BIN:
                    send2trash.send2trash(entry.path)
                    freed += item_size
                    cleaned += 1
                elif action == CleanAction.QUARANTINE:
                    rel_id = f"item_{len(records) + 1}_{os.path.basename(entry.path)}"
                    dest_path = os.path.join(session_dir, rel_id)
                    shutil.move(entry.path, dest_path)
                    records.append(
                        QuarantineFileRecord(
                            original_path=entry.path,
                            quarantine_path=dest_path,
                            is_dir=entry.is_dir(),
                            size=item_size,
                            category=category_name
                        )
                    )
                    freed += item_size
                    cleaned += 1
                elif action == CleanAction.PERMANENT_DELETE:
                    if entry.is_dir():
                        shutil.rmtree(entry.path, ignore_errors=True)
                    else:
                        os.remove(entry.path)
                    freed += item_size
                    cleaned += 1

            except (PermissionError, OSError):
                # Locked temp file (very common in %TEMP%)
                pass
            except Exception as e:
                errors.append(str(e))

        return freed, cleaned, errors

    def list_sessions(self) -> List[QuarantineSession]:
        """Returns all recorded quarantine sessions."""
        sessions: List[QuarantineSession] = []
        if not os.path.exists(self.base_dir):
            return sessions

        for entry in os.scandir(self.base_dir):
            if entry.is_dir():
                manifest_path = os.path.join(entry.path, "manifest.json")
                if os.path.isfile(manifest_path):
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            records = [QuarantineFileRecord(**r) for r in data.get("records", [])]
                            sessions.append(
                                QuarantineSession(
                                    session_id=data.get("session_id", entry.name),
                                    timestamp=data.get("timestamp", ""),
                                    total_bytes=data.get("total_bytes", 0),
                                    item_count=len(records),
                                    records=records,
                                    is_restored=data.get("is_restored", False)
                                )
                            )
                    except Exception as e:
                        print(f"[Quarantine] Error loading manifest {manifest_path}: {e}")

        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        return sessions

    def restore_session(self, session_id: str) -> Tuple[int, List[str]]:
        """Restores all items in a quarantine session back to original paths."""
        session_dir = os.path.join(self.base_dir, session_id)
        manifest_path = os.path.join(session_dir, "manifest.json")

        if not os.path.isfile(manifest_path):
            return 0, [f"Манифест сессии '{session_id}' не найден."]

        restored_count = 0
        errors: List[str] = []

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            records = data.get("records", [])
            for rec in records:
                orig_p = rec["original_path"]
                quar_p = rec["quarantine_path"]

                if not os.path.exists(quar_p):
                    errors.append(f"Файл в карантине '{quar_p}' отсутствует.")
                    continue

                try:
                    parent_dir = os.path.dirname(orig_p)
                    if parent_dir:
                        os.makedirs(parent_dir, exist_ok=True)

                    if os.path.exists(orig_p):
                        if os.path.isdir(orig_p):
                            shutil.rmtree(orig_p)
                        else:
                            os.remove(orig_p)

                    shutil.move(quar_p, orig_p)
                    restored_count += 1
                except Exception as e:
                    errors.append(f"Не удалось восстановить '{orig_p}': {e}")

            # Update manifest status
            data["is_restored"] = True
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            errors.append(f"Ошибка при чтении манифеста: {e}")

        return restored_count, errors

    def delete_session(self, session_id: str) -> bool:
        """Permanently removes a quarantine session directory."""
        session_dir = os.path.join(self.base_dir, session_id)
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir)
                return True
            except Exception:
                return False
        return False

    def _save_session_manifest(self, session_dir: str, session_id: str, total_bytes: int, records: List[QuarantineFileRecord]):
        manifest_path = os.path.join(session_dir, "manifest.json")
        data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "total_bytes": total_bytes,
            "is_restored": False,
            "records": [asdict(r) for r in records]
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _calc_path_size(path: str) -> int:
        if os.path.isfile(path):
            try:
                return os.path.getsize(path)
            except (OSError, PermissionError):
                return 0
        total = 0
        try:
            for root, dirs, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
        return total
