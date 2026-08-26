# 🤖 AI Agent Skill & Integration Guide: AetherClean

This document defines the **AI Skill** specifications and instructions for LLMs, autonomous coding agents (Google Antigravity, Claude Engineer, OpenAI GPT-4/o, Cursor, Windsurf, Devin), and CLI automation scripts interacting with the **AetherClean** codebase.

---

## 🎯 Skill Purpose & Capabilities

When equipped with this skill, an AI Agent can:
1. **Audit Windows Disks**: Perform fast, intelligent scans of Windows 11 drives to detect system bloat, orphaned `AppData`, obsolete `DriverStore` packages, dead `MSI/MSP` installers, and heavy application caches.
2. **Extend Declarative Rules**: Add or modify YAML cleanup rules for newly installed or obscure applications without writing boilerplate code.
3. **Develop New Scanner Plugins**: Create specialized scanners (e.g. Docker VHDX trimmer, WSL uncompacted disk cleaner, package manager cache sweepers) by extending `BaseScanner`.
4. **Automate Disk Hygiene**: Safely trigger non-destructive scans, generate structured markdown reports, and manage quarantine sessions.

---

## 🏗️ Codebase Architecture Quick-Reference

| Component | Path | Responsibility |
|---|---|---|
| **Models & Enums** | [`core/models.py`](file:///d:/Программы/My_own_cleaner/core/models.py) | `ScanItem`, `RiskLevel` (`SAFE`, `MEDIUM`, `HIGH`), `Category`, `CleanAction`, `FileEntry` |
| **Registry Ground Truth** | [`core/registry_analyzer.py`](file:///d:/Программы/My_own_cleaner/core/registry_analyzer.py) | Enumerates 64/32-bit `Uninstall` keys, UWP packages, and MSI GUIDs to verify active vs orphaned folders |
| **YAML Rule Engine** | [`core/rule_engine.py`](file:///d:/Программы/My_own_cleaner/core/rule_engine.py) | Resolves environment variables, globs, file age filters, and content-only options |
| **Quarantine & Safety** | [`core/quarantine_manager.py`](file:///d:/Программы/My_own_cleaner/core/quarantine_manager.py) | Non-blocking execution, session isolation with `manifest.json`, 1-click restore, and Recycle Bin routing |
| **Restore Point** | [`core/restore_point.py`](file:///d:/Программы/My_own_cleaner/core/restore_point.py) | Calls PowerShell / WMI to create a Windows System Restore Point |
| **Master Orchestrator** | [`core/scanner.py`](file:///d:/Программы/My_own_cleaner/core/scanner.py) | Coordinates all scanner plugins, aggregates results, and reports progress |
| **UI Layer** | [`ui/`](file:///d:/Программы/My_own_cleaner/ui/) | PySide6 Windows 11 Fluent dark interface (`main_window.py`, `cleaning_dialog.py`, `disk_gauge.py`, `category_tree.py`) |

---

## 🛠️ Instructions for AI Agents

### 1. How to run a CLI diagnostic / dry-run scan
When asked by the user to analyze the system or check what is taking up space, run:

```bash
python -c "from core.scanner import MasterScanner; from core.models import format_bytes; s = MasterScanner(); res = s.run_full_scan(); print('Total recoverable:', format_bytes(res.total_bytes)); [print(f'[{i.risk_level.value.upper()}] {i.title}: {i.format_size()} - {i.safety_label}') for i in res.items]"
```

### 2. How to add a new YAML cleaning rule
To add rules for a new application (e.g. OBS Studio, Blender, DaVinci Resolve), create or edit a file in [`config/rules/`](file:///d:/Программы/My_own_cleaner/config/rules/):

```yaml
- id: "obs_studio_logs_cache"
  name: "OBS Studio Crash Dumps & Old Logs"
  category: "app_cache"
  risk_level: "safe"
  safety_label: "Безопасно: устаревшие журналы записи и дампы"
  description: "Старые текстовые логи и дампы работы OBS Studio."
  paths:
    - "%APPDATA%\\obs-studio\\crashes"
    - "%APPDATA%\\obs-studio\\logs\\*.log"
  options:
    min_age_hours: 24
```

### 3. How to create a new Scanner Plugin
Create a new file in `scanners/` implementing `BaseScanner`:

```python
from typing import List, Optional, Callable
from core.models import ScanItem, FileEntry, RiskLevel, Category
from scanners.base_scanner import BaseScanner

class CustomDevCacheScanner(BaseScanner):
    def scan(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ScanItem]:
        items: List[ScanItem] = []
        if progress_callback:
            progress_callback("Scanning custom dev caches...", 50)
        
        # Implement discovery logic here
        # Return ScanItem with appropriate RiskLevel and Category
        return items
```

Register your new scanner class in `scanner_classes` inside [`core/scanner.py`](file:///d:/Программы/My_own_cleaner/core/scanner.py).

### 4. Safety Guardrails for AI Agents
1. **Never hardcode permanent delete without user consent**: Default to `CleanAction.RECYCLE_BIN` or `CleanAction.QUARANTINE`.
2. **Preserve Whitelists**: Ensure paths matching `C:\Windows\System32`, `C:\Windows\WinSxS`, or active service binaries are never deleted.
3. **Run Unit Tests**: Always verify tests with `python -m pytest tests/` after modifying any scanner or core module.
