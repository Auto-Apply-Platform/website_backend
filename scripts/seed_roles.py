from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.clients.mongo import mongo_client  # noqa: E402
from app.repositories.role import RoleRepository  # noqa: E402


def _load_roles() -> list[str]:
    roles_env = os.getenv("ROLES_SEED", "")
    if roles_env.strip():
        return [role.strip() for role in roles_env.split(",") if role.strip()]
    roles_file = os.getenv("ROLES_SEED_FILE", "")
    if roles_file.strip():
        content = Path(roles_file).read_text(encoding="utf-8")
        return [line.strip() for line in content.splitlines() if line.strip()]
    raise RuntimeError("Set ROLES_SEED or ROLES_SEED_FILE to seed roles.")


async def _run() -> int:
    db = mongo_client.connect()
    repo = RoleRepository(db)
    created = 0
    try:
        await repo.ensure_indexes()
        roles = _load_roles()
        for name in roles:
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
