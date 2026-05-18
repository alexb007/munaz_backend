import asyncio
import json
import logging
import asyncpg

from websocket.router import route_db_event

log = logging.getLogger("db_listener")

PG_CHANNEL = "db_changes"
RECONNECT_DELAY = 3


class DBListenerWorker:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.conn: asyncpg.Connection | None = None

    async def start(self):
        while True:
            try:
                await self._connect()
                await self._listen_forever()
            except Exception as e:
                log.exception("DB listener crashed, reconnecting...")
                await asyncio.sleep(RECONNECT_DELAY)

    async def _connect(self):
        log.info("Connecting to PostgreSQL...")
        self.conn = await asyncpg.connect(self.dsn)

        await self.conn.add_listener(
            PG_CHANNEL,
            self._on_notify,
        )

        log.info("Listening on channel: %s", PG_CHANNEL)

    async def _listen_forever(self):
        while True:
            await asyncio.sleep(3600)

    def _on_notify(self, *args):
        payload = args[3]

        asyncio.create_task(self._handle_payload(payload))

    async def _handle_payload(self, payload: str):
        try:
            data = json.loads(payload)
            await route_db_event(data)
        except Exception:
            log.exception("Failed to handle payload")
