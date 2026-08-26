# Contributing to AetherClean

Thank you for your interest in contributing to **AetherClean**!

---

## 🛠️ How to Add Rules for New Applications

Most applications can be supported without writing Python code, simply by defining a declarative YAML rule in `config/rules/`:

1. Open or create a YAML file in `config/rules/` (e.g. `config/rules/app_caches.yaml`).
2. Add the application rule specification:
   ```yaml
   - id: "my_app_cache"
     name: "My Application Cache"
     category: "app_cache"
     risk_level: "safe"
     safety_label: "Safe: temporary application cache"
     description: "Thumbnail, GPU and media cache for My Application."
     paths:
       - "%LOCALAPPDATA%\\MyApp\\Cache"
       - "%LOCALAPPDATA%\\MyApp\\GPUCache"
   ```
3. Verify your rule by running tests: `pytest tests/`.

---

## 🧪 Running the Test Suite

Before submitting a Pull Request, ensure that all automated tests pass:

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## 📜 Code Style & Safety Guidelines

- Follow **PEP 8** conventions.
- Provide type annotations for all public methods and functions.
- Never add critical Windows system directories (`C:\Windows\System32`, `WinSxS`, etc.) to automated deletion targets.
- Ensure all new UI strings are added to `core/i18n.py` for both English and Russian.
