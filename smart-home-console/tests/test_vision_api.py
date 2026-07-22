from __future__ import annotations

import os
import sqlite3
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
        self.zone = None
        self.lifecycle_calls = []
        self.events = [
            {
                "id": 22,
                "started_at": "2026-07-22T02:00:00+00:00",
                "ended_at": "2026-07-22T02:01:00+00:00",
                "snapshot_filename": "closed event.jpg",
                "max_people": 1,
                "acknowledged_at": None,
                "close_reason": "person_left",
                "alarm_on_delivered": True,
                "alarm_off_delivered": True,
                "last_error": "",
            },
            {
                "id": 21,
                "started_at": "2026-07-22T01:00:00+00:00",
                "ended_at": None,
                "snapshot_filename": "",
                "max_people": 2,
                "acknowledged_at": None,
                "close_reason": None,
                "alarm_on_delivered": True,
                "alarm_off_delivered": False,
                "last_error": "",
            },
        ]

    def initialize_safety(self) -> None:
        self.lifecycle_calls.append("initialize_safety")

    def start(self) -> bool:
        self.lifecycle_calls.append("start")
        self.started = True
        return True

    def stop(self) -> None:
        self.lifecycle_calls.append("stop")
        self.stopped = True

    def shutdown_safety(self) -> None:
        self.lifecycle_calls.append("shutdown_safety")

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
            "zone": self.zone,
        }

    def get_latest_jpeg(self):
        return self.jpeg

    def iter_mjpeg(self):
        if self.jpeg is not None:
            yield build_mjpeg_chunk(self.jpeg)

    def save_zone(self, zone):
        self.zone = {
            "x": zone.x,
            "y": zone.y,
            "width": zone.width,
            "height": zone.height,
        }
        return self.zone

    def delete_zone(self) -> None:
        self.zone = None

    def list_events(self, limit: int = 50):
        return self.events[:limit]

    def acknowledge_event(self, event_id: int):
        from event_repository import EventClosedError, EventNotFoundError

        for event in self.events:
            if event["id"] != event_id:
                continue
            if event["ended_at"] is not None:
                raise EventClosedError(f"event {event_id} is closed")
            if event["acknowledged_at"] is None:
                event["acknowledged_at"] = "2026-07-22T03:00:00+00:00"
            return dict(event)
        raise EventNotFoundError(f"event {event_id} was not found")

    def silence_current_alarm(self):
        return {"silenced": True, "persisted": False, "event_id": None}


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
        self.assertEqual(
            fake.lifecycle_calls,
            ["initialize_safety", "start", "stop", "shutdown_safety"],
        )

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

    def test_put_zone_validates_and_persists(self):
        fake = FakeVisionService()
        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.put(
                "/api/vision/zone",
                json={"x": 0.1, "y": 0.2, "width": 0.4, "height": 0.5},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["zone"]["width"], 0.4)
        self.assertEqual(fake.zone["height"], 0.5)

    def test_get_and_delete_zone(self):
        fake = FakeVisionService()
        fake.zone = {"x": 0.1, "y": 0.2, "width": 0.4, "height": 0.5}
        with self.open_client(fake), TestClient(app_module.app) as client:
            get_response = client.get("/api/vision/zone")
            delete_response = client.delete("/api/vision/zone")
            empty_response = client.get("/api/vision/zone")

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["zone"]["x"], 0.1)
        self.assertEqual(delete_response.status_code, 200)
        self.assertIsNone(delete_response.json()["zone"])
        self.assertIsNone(empty_response.json()["zone"])

    def test_zone_outside_frame_returns_422(self):
        fake = FakeVisionService()
        invalid_zones = [
            {"x": 0.8, "y": 0.2, "width": 0.4, "height": 0.5},
            {"x": 0.1, "y": 0.8, "width": 0.4, "height": 0.3},
            {"x": 0.1, "y": 0.2, "width": 0.019, "height": 0.5},
        ]
        with self.open_client(fake), TestClient(app_module.app) as client:
            responses = [
                client.put("/api/vision/zone", json=zone) for zone in invalid_zones
            ]
            responses.append(
                client.put(
                    "/api/vision/zone",
                    content='{"x": NaN, "y": 0.2, "width": 0.4, "height": 0.5}',
                    headers={"content-type": "application/json"},
                )
            )

        self.assertTrue(all(response.status_code == 422 for response in responses))
        self.assertIsNone(fake.zone)

    def test_events_use_default_order_and_safe_snapshot_urls(self):
        fake = FakeVisionService()
        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.get("/api/vision/events")

        self.assertEqual(response.status_code, 200)
        events = response.json()["events"]
        self.assertEqual([event["id"] for event in events], [22, 21])
        self.assertEqual(
            events[0]["snapshot_url"],
            "/static/vision_events/closed%20event.jpg",
        )
        self.assertIsNone(events[1]["snapshot_url"])
        self.assertNotIn(os.path.abspath("static/vision_events"), response.text)

    def test_event_limit_outside_fastapi_bounds_returns_422(self):
        fake = FakeVisionService()
        with self.open_client(fake), TestClient(app_module.app) as client:
            too_large = client.get("/api/vision/events?limit=201")
            too_small = client.get("/api/vision/events?limit=0")

        self.assertEqual(too_large.status_code, 422)
        self.assertEqual(too_small.status_code, 422)

    def test_acknowledging_closed_event_returns_409(self):
        fake = FakeVisionService()
        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.post("/api/vision/events/22/ack")

        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json()["ok"])

    def test_acknowledging_missing_event_returns_404(self):
        fake = FakeVisionService()
        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.post("/api/vision/events/999/ack")

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["ok"])

    def test_acknowledging_active_event_is_idempotent(self):
        fake = FakeVisionService()
        with self.open_client(fake), TestClient(app_module.app) as client:
            first = client.post("/api/vision/events/21/ack")
            second = client.post("/api/vision/events/21/ack")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            first.json()["event"]["acknowledged_at"],
            second.json()["event"]["acknowledged_at"],
        )

    def test_current_alarm_silence_does_not_require_event_id(self):
        fake = FakeVisionService()
        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.post("/api/vision/alarm/silence")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["alarm"],
            {"silenced": True, "persisted": False, "event_id": None},
        )

    def test_zone_persistence_error_returns_503(self):
        errors = [
            sqlite3.OperationalError("database is locked"),
            OSError("cannot create database directory"),
        ]
        for error in errors:
            with self.subTest(error=error):
                fake = FakeVisionService()
                with patch.object(
                    fake,
                    "save_zone",
                    side_effect=error,
                ), self.open_client(fake), TestClient(app_module.app) as client:
                    response = client.put(
                        "/api/vision/zone",
                        json={
                            "x": 0.1,
                            "y": 0.2,
                            "width": 0.4,
                            "height": 0.5,
                        },
                    )

                self.assertEqual(response.status_code, 503)
                self.assertEqual(
                    response.json(), {"ok": False, "error": str(error)}
                )


if __name__ == "__main__":
    unittest.main()
