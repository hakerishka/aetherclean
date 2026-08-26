# Руководство по участию в разработке (Contributing to AetherClean)

Спасибо за интерес к развитию проекта **AetherClean**!

---

## 🛠️ Как добавить правила для новых программ

Большинство новых программ можно поддержать без написания кода, просто добавив декларативное правило в каталог `config/rules/`:

1. Откройте или создайте YAML файл в `config/rules/` (например, `config/rules/app_caches.yaml`).
2. Добавьте описание нового приложения:
   ```yaml
   - id: "my_app_cache"
     name: "My Application Cache"
     category: "app_cache"
     risk_level: "safe"
     safety_label: "Безопасно: временный кэш приложения"
     description: "Кэш миниатюр и логов My Application."
     paths:
       - "%LOCALAPPDATA%\\MyApp\\Cache"
   ```
3. Проверьте работоспособность: запустите `pytest tests/`.

---

## 🧪 Запуск тестов

Перед отправкой Pull Request убедитесь, что все тесты проходят:

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## 📜 Стиль кода

- Соблюдайте PEP 8.
- Добавляйте аннотации типов для всех публичных методов.
- Обеспечивайте безопасность и не допускайте добавления системных путей Windows в автоматическую очистку.
