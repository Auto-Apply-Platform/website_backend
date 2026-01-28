from __future__ import annotations

import asyncio
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.clients.mongo import mongo_client  # noqa: E402
from app.services.requests import backfill_request_status_fields  # noqa: E402


async def _run() -> int:
    db = mongo_client.connect()
    try:
        return await backfill_request_status_fields(db)
    finally:
        await mongo_client.close()


def main() -> None:
    updated = asyncio.run(_run())
    print(f"Backfill completed: updated {updated} request(s).")


if __name__ == "__main__":
    main()
