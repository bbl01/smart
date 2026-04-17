# 🤝 Руководство по участию в проекте

Спасибо за интерес к AttendAI! Мы рады любому вкладу.

## Содержание

- [Кодекс поведения](#кодекс-поведения)
- [Как начать](#как-начать)
- [Процесс разработки](#процесс-разработки)
- [Стандарты кода](#стандарты-кода)
- [Отправка изменений](#отправка-изменений)

---

## Кодекс поведения

Мы придерживаемся уважительного общения. Оскорбления и дискриминация недопустимы.

## Как начать

### 1. Форк и клон

```bash
# Форкните репозиторий на GitHub, затем:
git clone https://github.com/YOUR_USERNAME/attendai.git
cd attendai
git remote add upstream https://github.com/your-org/attendai.git
```

### 2. Настройка окружения разработчика

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend
cd ../frontend
npm install

# Запуск инфраструктуры (БД, Redis)
docker compose up -d postgres redis minio
```

### 3. Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

Это автоматически запускает линтеры перед каждым коммитом.

## Процесс разработки

### Ветки

| Ветка | Назначение |
|-------|-----------|
| `main` | Production-ready код |
| `develop` | Активная разработка |
| `feature/*` | Новые функции |
| `fix/*` | Исправления багов |
| `docs/*` | Обновление документации |

### Создание ветки

```bash
git checkout develop
git pull upstream develop
git checkout -b feature/awesome-feature
```

## Стандарты кода

### Backend (Python)

```bash
# Форматирование
black app/ tests/
isort app/ tests/

# Линтинг
flake8 app/ --max-line-length=100
mypy app/ --ignore-missing-imports

# Тесты
pytest tests/ -v --cov=app
```

Следуем PEP 8. Строки не длиннее 100 символов. Документируем публичные функции.

### Frontend (TypeScript/React)

```bash
# Линтинг
npm run lint

# Тайпчек
npm run type-check

# Тесты
npm test
```

Используем функциональные компоненты с хуками. TypeScript строгий режим.

### Коммиты (Conventional Commits)

```
feat: add face recognition for group sessions
fix: correct timezone handling in attendance records
docs: update camera setup guide
refactor: extract face service into separate module
test: add unit tests for analytics endpoints
chore: upgrade insightface to 0.7.3
```

Типы: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

## Отправка изменений

### 1. Проверьте перед PR

```bash
# Backend
cd backend
pytest tests/ --cov=app --cov-fail-under=80
flake8 app/
mypy app/

# Frontend
cd frontend
npm run lint
npm run type-check
npm test -- --run
npm run build
```

### 2. Создайте Pull Request

Заполните шаблон PR:
- Описание изменений
- Связанный Issue (если есть): `Closes #123`
- Скриншоты (для UI-изменений)
- Чек-лист: тесты написаны, документация обновлена

### 3. Code Review

- Минимум 1 апрув перед мержем
- CI/CD должен проходить
- Конфликты разрешены

---

## Типы вкладов

### 🐛 Баги

Создайте Issue с:
- Описанием проблемы
- Шагами воспроизведения
- Ожидаемым и фактическим поведением
- Версией системы

### 💡 Новые функции

1. Создайте Issue с тегом `enhancement`
2. Обсудите дизайн в комментариях
3. Получите апрув мейнтейнеров
4. Реализуйте и отправьте PR

### 📖 Документация

Правки в `docs/` приветствуются без предварительного обсуждения.

---

## Вопросы?

- 💬 [GitHub Discussions](https://github.com/your-org/attendai/discussions)
- 📧 dev@attendai.edu
