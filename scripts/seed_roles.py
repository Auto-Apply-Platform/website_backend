from __future__ import annotations

import asyncio
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.clients.mongo import mongo_client  # noqa: E402
from app.repositories.role import RoleRepository  # noqa: E402


DEFAULT_ROLES = [
    "Backend Developer",
    "Frontend Developer",
    "Fullstack Developer",
    "Mobile Developer",
    "Data Engineer",
    "Data Analyst",
    "Machine Learning Engineer",
    "UI/UX designer",
    "1С разработчик",
]


async def _run() -> int:
    db = mongo_client.connect()
    repo = RoleRepository(db)
    created = 0
    try:
        await repo.ensure_indexes()
        for name in DEFAULT_ROLES:
            existing = await repo.get_by_name(name)
            if existing:
                continue
            await repo.create({"name": name})
            created += 1
        return created
    finally:
        await mongo_client.close()


def main() -> None:
    created = asyncio.run(_run())
    print(f"Seed completed: created {created} role(s).")


if __name__ == "__main__":
    main()
