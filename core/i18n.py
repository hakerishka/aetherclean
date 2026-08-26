"""
Internationalization (i18n) and localization subsystem for AetherClean.
Supports English (en) and Russian (ru).
"""

from typing import Dict, Any


class I18nManager:
    """Manages bilingual localization dictionary and language switching."""

    _current_lang = "en"

    TRANSLATIONS: Dict[str, Dict[str, str]] = {
        # App Info & Headers
        "app_title": {
            "en": "🛡️ AetherClean",
            "ru": "🛡️ AetherClean",
        },
        "app_subtitle": {
            "en": "Intelligent Storage, Orphaned AppData & System Debris Analyzer for Windows 11",
            "ru": "Интеллектуальный анализатор и безопасная очистка диска Windows 11",
        },
        "system_drive_title": {
            "en": "💾 System Drive (C:)",
            "ru": "💾 Системный диск (C:)",
        },
        "free_total_fmt": {
            "en": "Free: {free} / Total: {total}",
            "ru": "Свободно: {free} / Всего: {total}",
        },
        "legend_used": {
            "en": "■ Used: {size}",
            "ru": "■ Занято: {size}",
        },
        "legend_cleanable": {
            "en": "■ Selected for Cleanup: {size}",
            "ru": "■ Выбрано к очистке: {size}",
        },
        "legend_free": {
            "en": "■ Free: {size}",
            "ru": "■ Свободно: {size}",
        },

        # Top Buttons
        "btn_restore_point": {
            "en": "🛡️ Create Restore Point",
            "ru": "🛡️ Точка восстановления",
        },
        "btn_quarantine": {
            "en": "📦 Quarantine",
            "ru": "📦 Карантин",
        },
        "btn_settings": {
            "en": "⚙️ Settings",
            "ru": "⚙️ Настройки",
        },

        # Action Toolbar
        "btn_start_scan": {
            "en": "🔍 Start Smart Scan",
            "ru": "🔍 Начать умный анализ",
        },
        "btn_stop_scan": {
            "en": "⏹️ Stop Scan",
            "ru": "⏹️ Остановить анализ",
        },
        "btn_safe_only": {
            "en": "🟢 Safe Items Only",
            "ru": "🟢 Только безопасные",
        },
        "btn_select_all": {
            "en": "Select All",
            "ru": "Выбрать всё",
        },
        "btn_unselect_all": {
            "en": "Deselect All",
            "ru": "Снять всё",
        },
        "lbl_action_target": {
            "en": "Action Target:",
            "ru": "Куда удалять:",
        },
        "action_recycle_bin": {
            "en": "🗑️ Windows Recycle Bin",
            "ru": "🗑️ Корзина Windows",
        },
        "action_quarantine": {
            "en": "📦 AetherClean Quarantine (1-Click Undo)",
            "ru": "📦 Карантин с откатом в 1 клик",
        },
        "action_permanent": {
            "en": "⚠️ Permanent Delete",
            "ru": "⚠️ Безвозвратно",
        },
        "btn_clean_selected": {
            "en": "🧹 Clean Selected ({size})",
            "ru": "🧹 Очистить выбранное ({size})",
        },

        # Tree Headers
        "tree_col_category": {
            "en": "Category / Item",
            "ru": "Категория / Элемент",
        },
        "tree_col_risk": {
            "en": "Risk Level",
            "ru": "Уровень риска",
        },
        "tree_col_size": {
            "en": "Size",
            "ru": "Размер",
        },
        "tree_col_files": {
            "en": "Files",
            "ru": "Файлов",
        },

        # Risk Badges
        "risk_safe": {
            "en": "🟢 SAFE",
            "ru": "🟢 БЕЗОПАСНО",
        },
        "risk_medium": {
            "en": "🟡 REVIEW",
            "ru": "🟡 ВНИМАНИЕ",
        },
        "risk_high": {
            "en": "🔴 HIGH RISK",
            "ru": "🔴 ВЫСОКИЙ РИСК",
        },

        # Category Names
        "cat_app_cache": {
            "en": "Application Caches",
            "ru": "Кэши приложений",
        },
        "cat_orphaned_appdata": {
            "en": "Orphaned AppData Leftovers",
            "ru": "Остатки удаленных программ (AppData)",
        },
        "cat_system_junk": {
            "en": "System Junk & Crash Dumps",
            "ru": "Системный мусор и дампы",
        },
        "cat_installer_cache": {
            "en": "Orphaned Windows Installers",
            "ru": "Неиспользуемые установщики Windows",
        },
        "cat_drivers": {
            "en": "Driver Store & Unpacked Drivers",
            "ru": "Хранилище драйверов",
        },
        "cat_large_dormant": {
            "en": "Large Dormant Files (>500MB)",
            "ru": "Забытые тяжелые файлы (>500MB)",
        },
        "cat_dism_component": {
            "en": "WinSxS Component Store",
            "ru": "Хранилище компонентов WinSxS",
        },
        "cat_registry_junk": {
            "en": "Orphaned Windows Registry Keys",
            "ru": "Остатки в реестре Windows (Реестр)",
        },

        # Inspector Panel
        "detail_empty_title": {
            "en": "Select an item to inspect",
            "ru": "Выберите элемент для анализа",
        },
        "detail_empty_desc": {
            "en": "Safety recommendations, risk rating, and file lists will be shown here.",
            "ru": "Здесь отображаются рекомендации по безопасности и список файлов.",
        },
        "detail_btn_explorer": {
            "en": "📁 Open in Explorer",
            "ru": "📁 Открыть в Проводнике",
        },
        "detail_files_title": {
            "en": "Discovered Files List:",
            "ru": "Список обнаруженных файлов:",
        },
        "table_col_path": {
            "en": "File Path",
            "ru": "Путь к файлу",
        },
        "table_col_size": {
            "en": "Size",
            "ru": "Размер",
        },
        "table_col_mtime": {
            "en": "Modified Date",
            "ru": "Дата изменения",
        },
        "detail_why_label": {
            "en": "💡 Why this was flagged:",
            "ru": "💡 Почему это здесь:",
        },
        "detail_total_label": {
            "en": "Total size: {size} ({count} files)",
            "ru": "Общий объем: {size} ({count} файлов)",
        },

        # Status & Progress
        "status_ready": {
            "en": "Ready. Click 'Start Smart Scan' to analyze system drives.",
            "ru": "Готов к работе. Нажмите «Начать умный анализ» для проверки системного диска.",
        },
        "status_scanning_init": {
            "en": "Initializing registry and specialized scanners...",
            "ru": "Инициализация реестра и сканеров...",
        },
        "status_scan_complete_fmt": {
            "en": "Scan completed. Found {size} of recoverable space across {count} categories.",
            "ru": "Анализ завершен. Найдено категорий мусора на {size}.",
        },

        # Cleaning Dialog
        "clean_dlg_title": {
            "en": "System Cleaning — AetherClean",
            "ru": "Очистка системы — AetherClean",
        },
        "clean_dlg_header_active": {
            "en": "🧹 Safe Disk Cleaning in Progress",
            "ru": "🧹 Выполняется безопасная очистка",
        },
        "clean_dlg_header_finished": {
            "en": "✅ Cleaning Successfully Completed!",
            "ru": "✅ Очистка успешно завершена!",
        },
        "clean_dlg_metric_freed": {
            "en": "💾 Freed Space:",
            "ru": "💾 Освобождено:",
        },
        "clean_dlg_metric_items": {
            "en": "📁 Categories Processed:",
            "ru": "📁 Обработано категорий:",
        },
        "clean_dlg_metric_skipped": {
            "en": "ℹ️ Locked Files Skipped:",
            "ru": "ℹ️ Занятых файлов:",
        },
        "clean_dlg_log_title": {
            "en": "Real-time Operations Log:",
            "ru": "Журнал операций в реальном времени:",
        },
        "clean_dlg_btn_stop": {
            "en": "⏹️ Stop Cleaning",
            "ru": "⏹️ Остановить очистку",
        },
        "clean_dlg_btn_close": {
            "en": "Close",
            "ru": "Закрыть",
        },

        # Quarantine Dialog
        "quar_dlg_title": {
            "en": "Quarantine & Rollback Manager",
            "ru": "Карантин и восстановление файлов",
        },
        "quar_dlg_header": {
            "en": "📦 Quarantine Management",
            "ru": "📦 Управление Карантином",
        },
        "quar_dlg_desc": {
            "en": "Isolated backup snapshots created during cleaning sessions. You can restore any session with 1 click.",
            "ru": "Здесь хранятся резервные копии файлов, перемещенных в Карантин. Вы можете восстановить их в 1 клик.",
        },
        "quar_col_id": {
            "en": "Session ID",
            "ru": "ID Сессии",
        },
        "quar_col_date": {
            "en": "Date & Time",
            "ru": "Дата и время",
        },
        "quar_col_size": {
            "en": "Size",
            "ru": "Объем",
        },
        "quar_col_items": {
            "en": "Files",
            "ru": "Файлов",
        },
        "quar_col_status": {
            "en": "Status",
            "ru": "Статус",
        },
        "quar_status_restored": {
            "en": "Restored",
            "ru": "Восстановлено",
        },
        "quar_status_in_quar": {
            "en": "In Quarantine",
            "ru": "В карантине",
        },
        "quar_btn_restore": {
            "en": "↩️ Restore Selected Session",
            "ru": "↩️ Восстановить выбранную сессию",
        },
        "quar_btn_delete": {
            "en": "🗑️ Delete Permanently",
            "ru": "🗑️ Удалить навсегда",
        },

        # Settings Dialog
        "set_dlg_title": {
            "en": "AetherClean Settings",
            "ru": "Настройки AetherClean",
        },
        "set_dlg_header": {
            "en": "⚙️ Analysis & Safety Parameters",
            "ru": "⚙️ Параметры анализа и безопасности",
        },
        "set_lbl_language": {
            "en": "Interface Language / Язык интерфейса:",
            "ru": "Язык интерфейса / Interface Language:",
        },
        "set_lbl_default_action": {
            "en": "Default Cleaning Action:",
            "ru": "Действие по умолчанию:",
        },
        "set_chk_restore_point": {
            "en": "Create Windows System Restore Point before deep cleaning",
            "ru": "Создавать точку восстановления Windows перед системной очисткой",
        },
        "set_chk_safe_only": {
            "en": "Auto-select 100% safe items by default",
            "ru": "Выбирать по умолчанию только 100% безопасные категории (Safe)",
        },
        "set_grp_heuristics": {
            "en": "Heuristic Age Thresholds",
            "ru": "Эвристические пороги",
        },
        "set_lbl_appdata_days": {
            "en": "Minimum idle time for Orphaned AppData:",
            "ru": "Минимальный простой для остатков AppData:",
        },
        "set_lbl_dormant_days": {
            "en": "Minimum age for dormant files:",
            "ru": "Минимальный возраст забытых файлов:",
        },
        "set_lbl_dormant_size": {
            "en": "Dormant file size threshold:",
            "ru": "Порог размера забытых файлов:",
        },
        "btn_save": {
            "en": "Save",
            "ru": "Сохранить",
        },
        "btn_cancel": {
            "en": "Cancel",
            "ru": "Отмена",
        },
    }

    @classmethod
    def get_lang(cls) -> str:
        return cls._current_lang

    @classmethod
    def set_lang(cls, lang: str):
        if lang in ["en", "ru"]:
            cls._current_lang = lang

    @classmethod
    def t(cls, key: str, **kwargs) -> str:
        """Translate key into the current language, formatting kwargs if provided."""
        translations = cls.TRANSLATIONS.get(key, {})
        text = translations.get(cls._current_lang, translations.get("en", key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


# Helper alias
t = I18nManager.t
