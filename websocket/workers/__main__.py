import asyncio
import os

import django

from websocket.workers.db_listener import DBListenerWorker
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "munaz_back.settings")
django.setup()
POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    f"postgresql://crm:pswd123@localhost:5432/crm",
)


async def main():
    worker = DBListenerWorker(POSTGRES_DSN)
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())
