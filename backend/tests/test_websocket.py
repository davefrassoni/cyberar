import asyncio
from asgiref.testing import ApplicationCommunicator
from django.test import TransactionTestCase, override_settings
from django.contrib.sessions.backends.db import SessionStore
from channels.db import database_sync_to_async
from config.asgi import application
from mission.service import ensure_mission


class WebSocketTests(TransactionTestCase):
    def scope(self, cookie=b"", origin=b"https://davefrassoni.com"):
        return {"type":"websocket", "path":"/cyberar/ws/mission/", "headers":[(b"origin",origin), (b"cookie",cookie)], "query_string":b"", "subprotocols":[]}

    async def test_unauthorized_and_foreign_origin(self):
        for origin in [b"https://davefrassoni.com", b"https://attacker.invalid"]:
            communicator = ApplicationCommunicator(application, self.scope(origin=origin))
            await communicator.send_input({"type":"websocket.connect"})
            self.assertEqual((await communicator.receive_output())["type"], "websocket.close")
            await communicator.send_input({"type":"websocket.disconnect", "code":1000})
            await communicator.wait()

    async def test_stream_and_revocation(self):
        @database_sync_to_async
        def create():
            session = SessionStore()
            session["cyberar_authenticated"] = True
            session.save()
            ensure_mission(session.session_key)
            return session.session_key
        key = await create()
        communicator = ApplicationCommunicator(application, self.scope(cookie=f"cyberar_session={key}".encode()))
        await communicator.send_input({"type":"websocket.connect"})
        self.assertEqual((await communicator.receive_output())["type"], "websocket.accept")
        self.assertEqual((await communicator.receive_output())["type"], "websocket.send")
        await database_sync_to_async(SessionStore(session_key=key).delete)()
        response = await communicator.receive_output(timeout=3)
        self.assertEqual(response["type"], "websocket.close")
        self.assertEqual(response["code"], 4401)
        await communicator.send_input({"type":"websocket.disconnect", "code":1000})
        await communicator.wait()
