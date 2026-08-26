<div align="center">

# 🛡️ AetherClean (Windows 11 Edition)

**Интеллектуальный анализатор и безопасный менеджер глубокой очистки системного диска для Windows 11.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-brightgreen.svg)](https://pypi.org/project/PySide6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011%20%2F%2010-0078D4.svg)](https://www.microsoft.com/windows)
[![Tests](https://img.shields.io/badge/PyTest-10%20passed-success.svg)](tests/)
[![AI-Ready](https://img.shields.io/badge/AI%20Skill-Ready-purple.svg)](AI_SKILL.md)

[English / AI Skill Reference](AI_SKILL.md) | [Полная техническая документация](DOCUMENTATION.md) | [Участие в проекте](CONTRIBUTING.md)

</div>

---

## 🌟 Почему AetherClean, а не обычные чистильщики?

Стандартные утилиты (CCleaner, BleachBit) работают вслепую по жестким путям и удаляют только папку `Temp` и историю браузера. При этом **сотни гигабайт** на диске `C:` занимают совсем другие вещи:

- **Папки-сироты в AppData**: удаленные полгода назад игры и программы оставляют гигабайты забытых кэшей.
- **Мертвый кэш Windows Installer**: десятки гигабайт неиспользуемых `.msi` и `.msp` обновлений в `C:\Windows\Installer`.
- **Забытые инсталляторы драйверов**: распакованные пакеты NVIDIA/AMD/Intel, о которых Windows забывает.
- **Тяжелые спящие файлы**: забытые ISO-образы, виртуальные диски и видеозаписи >500МБ в пользовательских папках.

**AetherClean** объединяет сверку с реестром Windows, эвристику возраста файлов, декларативные правила YAML и многоуровневый стек безопасности.

---

## ⚡ Ключевые возможности

- 🧠 **Поиск папок-сирот в AppData / ProgramData**: автоматическая сверка с 64/32-битным реестром и базой Windows Store UWP для нахождения мусора удаленных программ.
- 📦 **Безопасный аудит Windows Installer Cache**: алгоритмическая проверка активных пакетов (как в PatchCleaner).
- 🔌 **Очистка кэша драйверов**: удаление распакованных архивов инсталляторов NVIDIA, AMD и Intel.
- ⚙️ **Системный мусор и дампы WER**: очистка дампов аварийного завершения программ (*.dmp) и кэша Delivery Optimization.
- 🌐 **Декларативная база YAML-правил**: кэши Chromium, Electron, Telegram Desktop, Discord, Slack, Spotify, Steam и DirectX шейдеров.
- 🐘 **Поиск спящих файлов (>500MB)**: выявление забытых тяжелых файлов без активности более 90 дней.
- 🛡️ **Полная безопасность и 1-клик откат**:
  - Цветовые бейджи рисков (🟢 *Безопасно*, 🟡 *Внимание*, 🔴 *Высокий риск*).
  - Понятные подсказки: *"кэш, удаление безопасно и не навредит"*, *"остатки удаленного приложения"*.
  - Выделенный **Карантин со структурированными сессиями и восстановлением в 1 клик**.
  - Интеграция с системными **Точками восстановления Windows (System Restore)**.
  - **Асинхронный поток CleanWorker**: интерфейс никогда не зависает, отображая консольный журнал операций в реальном времени.

---

## 🚀 Быстрый старт

### 1. Требования
- Windows 10 / Windows 11 (64-бит)
- Python 3.10 или новее

### 2. Установка
```bash
git clone https://github.com/your-username/aetherclean.git
cd aetherclean
pip install -r requirements.txt
```

### 3. Запуск
- **Способ 1**: Дважды кликните по [`run.bat`](run.bat)
- **Способ 2**: В командной строке:
  ```bash
  python main.py
  ```

---

## 📂 Структура репозитория

```
├── config/
│   ├── rules/                   # Декларативные YAML-правила для кэшей
│   │   ├── app_caches.yaml      # Браузеры, Electron, Discord, Telegram, Spotify
│   │   ├── system_junk.yaml     # Дампы WER, Delivery Optimization, Temp
│   │   └── driver_rules.yaml    # Распакованные драйверы
│   └── settings.yaml            # Настройки порогов, путей и белых списков
├── core/
│   ├── models.py                # Модели данных (ScanItem, RiskLevel, Category)
│   ├── registry_analyzer.py     # Анализатор реестра и белых списков
│   ├── rule_engine.py           # Движок парсинга YAML правил
│   ├── quarantine_manager.py    # Менеджер карантина и отката в 1 клик
│   ├── restore_point.py         # Создание точек восстановления Windows
│   └── scanner.py               # Оркестратор многопоточного сканирования
├── scanners/                    # Модули специализированных сканеров
│   ├── orphaned_appdata_scanner.py
│   ├── installer_scanner.py
│   ├── driver_store_scanner.py
│   ├── system_junk_scanner.py
│   ├── app_cache_scanner.py
│   ├── large_dormant_scanner.py
│   └── dism_analyzer.py
├── ui/                          # Интерфейс на PySide6 (Windows 11 Fluent Dark)
│   ├── main_window.py           # Главное окно с неблокирующими потоками
│   ├── theme.py                 # Dark QSS стили
│   └── components/              # Виджеты (диалог очистки, инспектор, дерево, диаграмма)
├── tests/                       # 10 автоматизированных тестов PyTest
├── AI_SKILL.md                  # Руководство и системный скилл для нейросетей
├── DOCUMENTATION.md             # Полная техническая документация
├── CONTRIBUTING.md              # Руководство по контрибьютингу
├── LICENSE                      # MIT Лицензия
├── run.bat                      # Скрипт быстрого запуска
└── main.py                      # Точка входа
```

---

## 🤖 Поддержка нейросетей и AI-агентов

В проект включен файл [`AI_SKILL.md`](AI_SKILL.md), позволяющий AI-ассистентам (Google Antigravity, Claude, GPT-4, Cursor) анализировать систему, добавлять новые правила и расширять сканеры в автономном режиме.

---

## 📜 Лицензия

Проект распространяется под открытой лицензией [MIT](LICENSE).
