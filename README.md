<div align="center">

# 🛡️ AetherClean

**Next-Generation Storage, Orphaned AppData & System Debris Analyzer for Windows 11 & 10.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-brightgreen.svg)](https://pypi.org/project/PySide6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011%20%2F%2010-0078D4.svg)](https://www.microsoft.com/windows)
[![Tests](https://img.shields.io/badge/PyTest-11%20passed-success.svg)](tests/)
[![AI-Ready](https://img.shields.io/badge/AI%20Skill-Ready-purple.svg)](AI_SKILL.md)
[![i18n](https://img.shields.io/badge/Language-English%20%7C%20Русский-orange.svg)](core/i18n.py)

[Technical Architecture](DOCUMENTATION.md) | [AI Agent Skill Specification](AI_SKILL.md) | [Contributing](CONTRIBUTING.md) | [License](LICENSE)

</div>

---

## 🌟 Why AetherClean?

Traditional disk cleaners (such as CCleaner or BleachBit) rely on rigid, hardcoded path rules—typically wiping only your browser history and `%TEMP%` folder. Yet on modern Windows 11 machines, **hundreds of gigabytes** are silently consumed by deep architectural debris:

- **Orphaned AppData remnants**: Uninstalled games, IDEs, and Electron applications leave gigabytes of abandoned databases, CEF caches, and configs in `%LOCALAPPDATA%` and `%APPDATA%`.
- **Dead Windows Installer packages**: Obsolete `.msi` and `.msp` patch files piling up in `C:\Windows\Installer` that no longer map to any active application.
- **Unpurged GPU Shader Caches**: GPU drivers (NVIDIA, AMD, DirectX) compile shaders for every game you run. When games are uninstalled, drivers **never** delete their shaders, hoarding 10–30 GB over years.
- **Unpacked driver redistributables**: Abandoned extraction directories (`C:\NVIDIA`, `C:\AMD`, `C:\Intel`).
- **Dead Registry leftovers**: Stale `Run`/`RunOnce` auto-start entries and dead `App Paths` pointing to non-existent binaries.
- **Large dormant user files**: Forgotten ISO disk images, virtual disks (`.vhdx`), and setup archives (>500MB) untouched for 90+ days.

**AetherClean** bridges the gap: it cross-references filesystem structures against the Windows Registry, Windows Store UWP databases, and file activity heuristics to identify true debris with **zero risk of system damage**.

---

## ⚡ Key Highlights

- 🧠 **Orphaned AppData Scanner**: Cross-references `%LOCALAPPDATA%`, `%APPDATA%`, and `%PROGRAMDATA%` against 64-bit/32-bit registry uninstallation records and UWP package repositories.
- 📦 **Windows Installer Cache Validator**: Uses registry MSI/MSP verification (inspired by *PatchCleaner*) to isolate unreferenced installer packages safely.
- 🔌 **DriverStore & Package Inspector**: Detects uncleaned driver extraction folders and evaluates the health of `DriverStore\FileRepository`.
- 📑 **Registry Debris Scanner**: Identifies broken startup entries, dead `App Paths`, and orphaned `HKCU\Software` vendor keys via physical path validation.
- ⚙️ **Windows System Debris & Crash Dumps**: Cleans Windows Error Reporting (WER) memory dumps (`*.dmp`), Delivery Optimization P2P caches, and old Windows installations (`Windows.old`).
- 🌐 **Declarative YAML Rule Engine**: Extensible rule files for Chromium/Electron caches, Telegram Desktop media, Discord, Spotify, Steam, and DirectX shader caches.
- 🐘 **Large Dormant Files Finder**: Locates abandoned files (>500MB) without activity for 90+ days in user directories.
- 🛡️ **Comprehensive Safety & 1-Click Rollback**:
  - Clear risk grading: 🟢 **Safe**, 🟡 **Review Recommended**, 🔴 **High Risk**.
  - **1-Click Undo Quarantine**: Moves files into structured session archives with JSON manifests for instantaneous rollback.
  - Native **Windows System Restore Point** creation before deep cleaning.
  - **Non-blocking asynchronous thread architecture (`CleanWorker`)**: Smooth 60 FPS UI with a real-time operations console log.
  - **Bilingual Interface**: Seamlessly switch between **English** and **Русский** in settings.

---

## 🚀 Quick Start

### Prerequisites
- Windows 10 / Windows 11 (64-bit)
- Python 3.10+

### Installation
```bash
git clone https://github.com/hakerishka/aetherclean.git
cd aetherclean
pip install -r requirements.txt
```

### Launch
- **GUI Launch**:
  ```bash
  python main.py
  ```
  *(or double-click [`run.bat`](run.bat))*

- **CLI Diagnostic Scan**:
  ```bash
  python -c "from core.scanner import MasterScanner; from core.models import format_bytes; s = MasterScanner(); res = s.run_full_scan(); print('Total recoverable:', format_bytes(res.total_bytes)); [print(f'[{i.risk_level.value.upper()}] {i.title}: {i.format_size()}') for i in res.items]"
  ```

---

## 🏗️ Architecture Overview

```
aetherclean/
├── config/
│   ├── rules/                   # Declarative YAML cleanup rules
│   │   ├── app_caches.yaml      # Browsers, Electron, Discord, Telegram, Spotify
│   │   ├── system_junk.yaml     # WER dumps, Delivery Optimization, Temp
│   │   └── driver_rules.yaml    # Unpacked GPU drivers
│   └── settings.yaml            # Thresholds, whitelist paths, and preferences
├── core/
│   ├── i18n.py                  # Bilingual localization manager (EN / RU)
│   ├── models.py                # Core data models (ScanItem, RiskLevel, Category)
│   ├── registry_analyzer.py     # Registry & UWP ground-truth analyzer
│   ├── rule_engine.py           # YAML rule evaluator with env variable expansion
│   ├── quarantine_manager.py    # Non-blocking isolation engine & 1-click restore
│   ├── restore_point.py         # Windows System Restore Point integration
│   └── scanner.py               # Master multi-threaded scanner orchestrator
├── scanners/                    # Specialized discovery plugins
│   ├── orphaned_appdata_scanner.py
│   ├── installer_scanner.py
│   ├── driver_store_scanner.py
│   ├── registry_junk_scanner.py
│   ├── system_junk_scanner.py
│   ├── app_cache_scanner.py
│   ├── large_dormant_scanner.py
│   └── dism_analyzer.py
├── ui/                          # PySide6 Windows 11 Fluent Dark UI
│   ├── main_window.py           # Main window with async QThread workers
│   ├── theme.py                 # Windows 11 Mica-style dark QSS stylesheet
│   └── components/              # Live cleaning dialog, disk gauge, tree, detail view
├── tests/                       # 11 comprehensive automated PyTest tests
├── .github/workflows/ci.yml     # Automated GitHub Actions CI workflow
├── AI_SKILL.md                  # Autonomous AI Agent skill specification
├── DOCUMENTATION.md             # In-depth technical & algorithmic reference
├── CONTRIBUTING.md              # Open-source contribution guidelines
├── pyproject.toml               # PEP 621 Python package configuration
└── LICENSE                      # MIT License
```

---

## 🤖 AI Agent Skill & Integration

AetherClean is built with an **AI-First architecture**. The included [`AI_SKILL.md`](AI_SKILL.md) file enables autonomous AI agents (Google Antigravity, Claude, OpenAI GPT-4, Cursor, Windsurf, Devin) to perform system audits, add new YAML rules, and create custom scanner plugins while adhering to strict safety guardrails.

---

## 🧪 Testing

Run the automated test suite:
```bash
pytest tests/ -v
```

All 11 unit and integration tests verify registry token matching, quarantine manifest serialization, 1-click restoration cycles, and scanner safety.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
