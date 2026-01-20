# website_backend

Асинхронный сервис на FastAPI + MongoDB.

## Запуск через Docker (рекомендуется)

1) Скопируйте пример окружения:

```bash
cp .env.example .env
```

2) Заполните `.env` (см. описание ниже).

3) Запустите контейнеры:

```bash
docker compose -f ../infra/docker-compose.yml up --build
```

Сервис будет доступен на `http://localhost:5000`.

## Переменные окружения (.env)

Обязательные:
- `AUTH_JWT_SECRET` — секрет для подписи JWT.
- `MONGODB_URI` — строка подключения к MongoDB.
- `MONGODB_DB` — имя базы данных.
- `TELEGRAM_BOT_USERNAME` — username бота без `@`.
- `TELEGRAM_BOT_SECRET` — секрет для подтверждения webhook-запросов от бота.
- `TG_WHITELIST` — список Telegram user id через запятую.

Пример `.env`:

```env
APP_NAME=website_backend
MONGODB_URI=mongodb://mongo:27017
MONGODB_DB=website_backend
AUTH_JWT_SECRET=change_me
AUTH_JWT_ALG=HS256
ACCESS_TOKEN_EXPIRES_SECONDS=3600
LOGIN_TOKEN_TTL_SECONDS=300
TELEGRAM_BOT_USERNAME=example_bot
TELEGRAM_BOT_SECRET=change_me
TG_WHITELIST=123,456
```

## Проверка

- `GET /health` — публичный статус сервиса.
- `POST /auth/telegram/qr` — получить login_token и URL для QR.
- `GET /auth/telegram/status?login_token=...` — проверить статус логина.
