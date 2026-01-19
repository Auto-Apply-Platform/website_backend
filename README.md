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
- `JWT_SECRET` — секрет для подписи JWT.
- `MONGODB_URI` — строка подключения к MongoDB.
- `MONGODB_DB` — имя базы данных.

Рекомендуемые:
- `ADMIN_USERNAME` — логин администратора, который создаётся при первом запуске.
- `ADMIN_PASSWORD` — пароль администратора.

Пример `.env`:

```env
APP_NAME=website_backend
MONGODB_URI=mongodb://mongo:27017
MONGODB_DB=website_backend
JWT_SECRET=change_me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
ADMIN_USERNAME=admin
ADMIN_PASSWORD=pass123@
```

## Проверка

- `GET /health` — публичный статус сервиса.
- `POST /auth/login` — логин по JSON:

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass123@"}'
```
