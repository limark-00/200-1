from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import app as app_module
from vision_service import build_mjpeg_chunk


class FakeVisionService:
    def __init__(self, jpeg: bytes | None = b"jpeg-frame") -> None:
        self.jpeg = jpeg
        self.started = False
        self.stopped = False

    def start(self) -> bool:
        self.started = True
        return True

    def stop(self) -> None:
        self.stopped = True

    def get_status(self):
        return {
            "enabled": True,
            "running": True,
            "camera_online": True,
            "model_loaded": True,
            "people_count": 1,
            "frame_sequence": 7,
            "fps": 8.5,
            "last_error": "",
            "camera_index": 0,
            "model_name": "fake.pt",
        }

    def get_latest_jpeg(self):
        return self.jpeg

    def iter_mjpeg(self):
        if self.jpeg is not None:
            yield build_mjpeg_chunk(self.jpeg)


class VisionApiTests(unittest.TestCase):
    def open_client(self, fake: FakeVisionService):
        return patch.object(app_module, "vision_service", fake, create=True)

    def test_status_endpoint_returns_vision_state(self):
        fake = FakeVisionService()
        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.get("/api/vision/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["people_count"], 1)
        self.assertTrue(fake.started)
        self.assertTrue(fake.stopped)

    def test_frame_endpoint_returns_latest_jpeg(self):
        fake = FakeVisionService(b"latest-jpeg")
        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.get("/api/vision/frame")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/jpeg")
        self.assertEqual(response.content, b"latest-jpeg")

    def test_frame_endpoint_reports_when_no_frame_exists(self):
        fake = FakeVisionService(None)
        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.get("/api/vision/frame")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "视觉服务尚无可用画面")

    def test_stream_endpoint_uses_mjpeg_media_type(self):
        fake = FakeVisionService(b"stream-jpeg")
        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.get("/api/vision/stream")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.headers["content-type"].startswith(
                "multipart/x-mixed-replace; boundary=frame"
            )
        )
        self.assertIn(b"stream-jpeg", response.content)


if __name__ == "__main__":
    unittest.main()
