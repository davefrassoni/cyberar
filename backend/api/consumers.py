import asyncio
from contextlib import suppress
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.sessions.backends.db import SessionStore
from mission.models import MissionState
from mission.service import serialize


@database_sync_to_async
def read_state(session_key):
    session = SessionStore(session_key=session_key)
    if not session.get("cyberar_authenticated"): return None
    live = MissionState.objects.filter(mission__owner_session=session_key).first()
    return serialize(live) if live else {}


class MissionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.stream_task = None
        self.session_key = self.scope["session"].session_key
        if not self.session_key or await read_state(self.session_key) is None:
            await self.close(code=4401)
            return
        await self.accept()
        self.stream_task = asyncio.create_task(self.stream())

    async def stream(self):
        while True:
            # One authoritative persisted state; no clocks in websocket workers.
            # Session is reloaded so expiry/logout revokes an existing socket.
            state = await read_state(self.session_key)
            if state is None:
                await self.close(code=4401)
                return
            await self.send_json(state)
            await asyncio.sleep(1)

    async def receive_json(self, content, **kwargs):
        # All mutations go through CSRF-protected HTTP, never arbitrary WS text.
        await self.close(code=4400)

    async def disconnect(self, close_code):
        if self.stream_task:
            self.stream_task.cancel()
            with suppress(asyncio.CancelledError): await self.stream_task
