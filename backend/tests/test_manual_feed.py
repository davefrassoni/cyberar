import json
import time
from io import BytesIO
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from api import manual_feed


class _FakeUpstream:
    def __init__(self, body, status=200, headers=None):
        self._buffer = BytesIO(body)
        self.status = status
        self.headers = headers or {}

    def read(self, size=-1):
        return self._buffer.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@override_settings(CYBERAR_USER="demo", CYBERAR_PASSWORD="test-only-password", SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class ManualFeedTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        manual_feed._cache.update(content_url="", expires_at=0.0)

    def login(self):
        csrf = self.client.get("/cyberar/api/session/").json()["csrf"]
        self.client.post("/cyberar/api/login/", json.dumps({"username": "demo", "password": "test-only-password"}),
                          content_type="application/json", HTTP_X_CSRFTOKEN=csrf)

    def test_requires_authentication(self):
        self.assertEqual(self.client.get("/cyberar/api/manual-feed/").status_code, 401)

    @patch("api.manual_feed.urlopen")
    def test_streams_video_with_correct_content_type_and_range(self, urlopen):
        urlopen.return_value = _FakeUpstream(b"fake-mp4-bytes", status=206, headers={"Content-Range": "bytes 0-13/1000", "Content-Length": "14"})
        self.login()
        with patch.object(manual_feed, "_resolve_content_url", return_value="https://davefrassoni.com/drive/s/token/content/job/"):
            response = self.client.get("/cyberar/api/manual-feed/", HTTP_RANGE="bytes=0-13")
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response["Content-Type"], "video/mp4")
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertEqual(response["Content-Range"], "bytes 0-13/1000")
        self.assertEqual(b"".join(response.streaming_content), b"fake-mp4-bytes")
        # The Range header the browser sent must reach the upstream request.
        sent_request = urlopen.call_args[0][0]
        self.assertEqual(sent_request.get_header("Range"), "bytes=0-13")
        self.assertIn("Mozilla", sent_request.get_header("User-agent"))

    def test_upstream_resolution_failure_returns_502(self):
        self.login()
        with patch.object(manual_feed, "_resolve_content_url", side_effect=TimeoutError("no")):
            response = self.client.get("/cyberar/api/manual-feed/")
        self.assertEqual(response.status_code, 502)

    def test_cached_content_url_is_reused_within_ttl(self):
        manual_feed._cache.update(content_url="https://davefrassoni.com/cached/", expires_at=time.monotonic() + 60)
        with patch("api.manual_feed._fetch_json") as fetch_json:
            self.assertEqual(manual_feed._resolve_content_url(), "https://davefrassoni.com/cached/")
            fetch_json.assert_not_called()
