**Проект**: Короткий FastAPI сервис для получения пользователей, постов и действий (feed).

**Основные файлы**:
- **app**: [finalproject1/app.py](finalproject1/app.py#L1-L80) — маршруты FastAPI.
- **database**: [finalproject1/database.py](finalproject1/database.py#L1-L6) — настройка SQLAlchemy и URL БД.
- **schemas**: [finalproject1/schema.py](finalproject1/schema.py#L1-L40) — Pydantic модели (ответы API).
- **tables**: [finalproject1/table_user.py](finalproject1/table_user.py), [finalproject1/table_post.py](finalproject1/table_post.py), [finalproject1/table_feed.py](finalproject1/table_feed.py) — SQLAlchemy модели.
- **deps**: [finalproject1/requirements.txt](finalproject1/requirements.txt) — список зависимостей.

**Требования**:
- Установлен Python 3.8+.

**Установка (Windows PowerShell, в папке `finalproject1`)**:
```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install "uvicorn[standard]"
```

**Запуск**:
- Из папки `finalproject1` запустите сервер:
```powershell
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```
- Откройте в браузере: `http://127.0.0.1:8000/docs` для Swagger UI.

**Основные API эндпоинты** (см. [app.py](finalproject1/app.py#L1-L120)):
- `GET /` — проверка доступности сервиса (возвращает "Привет!").
- `GET /user/{user_id}` — получить информацию о пользователе.
	- path-параметр: `user_id` (int).
	- ответ: `UserGet`.
- `GET /post/{post_id}` — получить информацию о посте.
	- path-параметр: `post_id` (int).
	- ответ: `PostGet`.
- `GET /user/{user_id}/feed?limit=10` — лента пользователя.
	- path-параметр: `user_id` (int).
	- query-параметр: `limit` (int, 1–100, по умолчанию 10).
	- ответ: список `FeedGet`.
- `GET /post/{post_id}/feed?limit=10` — лента по посту.
	- path-параметр: `post_id` (int).
	- query-параметр: `limit` (int, 1–100, по умолчанию 10).
	- ответ: список `FeedGet`.
- `GET /post/recommendations/?user_id=<user_id>&limit=10` — рекомендации постов.
	- query-параметры: `user_id` (int), `limit` (int, 1–100).
	- ответ: список `PostGet`.

Примеры:

```powershell
# лента пользователя 42 (до 20 записей)
curl "http://127.0.0.1:8000/user/42/feed?limit=20"

# рекомендации для пользователя 42 (до 10)
curl "http://127.0.0.1:8000/post/recommendations/?user_id=42&limit=10"
```

**База данных**:
- По умолчанию URL БД задан в [finalproject1/database.py](finalproject1/database.py#L1-L6).
