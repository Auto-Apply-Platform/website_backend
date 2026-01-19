import asyncio
import os
from datetime import datetime

from app.clients.mongo import mongo_client
from app.core.config import settings
from app.repositories.user import UserRepository
from app.services.users import hash_password


async def main() -> None:
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    if not username or not password:
        raise SystemExit(
            "ADMIN_USERNAME and ADMIN_PASSWORD are required for seeding"
        )

    db = mongo_client.connect()
    repo = UserRepository(db)
    existing = await repo.get_by_username(username)
    if existing:
        print("Admin user already exists")
        return

    password_hash = hash_password(password)
    await repo.create(
        {
            "username": username,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
        }
    )
    print("Admin user created")


if __name__ == "__main__":
    asyncio.run(main())
