from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
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

    def probe_static_routes(self, configured_directory, urls):
        environment = os.environ.copy()
        environment["VISION_EVENT_DIR"] = configured_directory
        environment["VISION_STATIC_PROBE_URLS"] = json.dumps(urls)
        script = """
import asyncio
import json
import os

import httpx
import app


async def main():
    transport = httpx.ASGITransport(app=app.app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        statuses = [
            (await client.get(url)).status_code
            for url in json.loads(os.environ["VISION_STATIC_PROBE_URLS"])
        ]
    print(json.dumps({"statuses": statuses}))


asyncio.run(main())
"""
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=PROJECT_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        return json.loads(completed.stdout.strip().splitlines()[-1])

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
            ["initialize_safety", "start", "shutdown_safety"],
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

    def test_zone_rejects_booleans_and_coercive_strings(self):
        fake = FakeVisionService()
        invalid_zones = [
            {"x": True, "y": 0.2, "width": 0.4, "height": 0.5},
            {"x": "0.1", "y": 0.2, "width": 0.4, "height": 0.5},
            {"x": {}, "y": 0.2, "width": 0.4, "height": 0.5},
        ]
        with self.open_client(fake), TestClient(app_module.app) as client:
            responses = [
                client.put("/api/vision/zone", json=zone)
                for zone in invalid_zones
            ]

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
            "/vision-events/closed%20event.jpg",
        )
        self.assertIsNone(events[1]["snapshot_url"])
        self.assertNotIn(os.path.abspath("static/vision_events"), response.text)

    def test_unsafe_snapshot_filename_is_not_returned_or_linked(self):
        fake = FakeVisionService()
        secret_directory = "/private/runtime/evidence"
        fake.events[0]["snapshot_filename"] = (
            f"{secret_directory}/event.jpg"
        )

        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.get("/api/vision/events")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["events"][0]["snapshot_filename"], "")
        self.assertIsNone(response.json()["events"][0]["snapshot_url"])
        self.assertNotIn(secret_directory, response.text)

    def test_legacy_event_error_is_redacted_before_history_response(self):
        fake = FakeVisionService()
        secret = "legacy-bemfa-uid"
        secret_directory = "/private/runtime/evidence"
        fake.events[0]["last_error"] = (
            f"GET https://example.test/send?uid={secret}; "
            f"snapshot={secret_directory}/event.jpg"
        )

        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.get("/api/vision/events")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["events"][0]["last_error"],
            "视觉事件历史错误已隐藏",
        )
        self.assertNotIn(secret, response.text)
        self.assertNotIn(secret_directory, response.text)
        self.assertNotIn("?uid=", response.text)

    def test_non_default_event_directory_is_served_on_dedicated_mount(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = "configured-event.jpg"
            with open(os.path.join(directory, filename), "wb") as evidence:
                evidence.write(b"configured-jpeg")
            test_app = FastAPI()
            resolved = app_module.mount_vision_event_files(test_app, directory)

            response = TestClient(test_app).get(f"/vision-events/{filename}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"configured-jpeg")
        self.assertEqual(resolved, os.path.realpath(directory))
        self.assertEqual(app_module.event_static_subtree(resolved), "")
        self.assertNotIn(directory, response.text)

    def test_empty_and_console_root_event_directories_do_not_serve_source(self):
        unsafe_directories = ("", app_module.BASE_DIR)
        guessed_files = (
            "config.py",
            "app.py",
            ".env",
            "data/vision_events.db",
        )

        for directory in unsafe_directories:
            with self.subTest(directory="empty" if not directory else "console"):
                test_app = FastAPI()
                resolved = app_module.mount_vision_event_files(
                    test_app,
                    directory,
                )

                self.assertEqual(
                    resolved,
                    os.path.realpath(
                        os.path.join(
                            app_module.BASE_DIR,
                            "static/vision_events",
                        )
                    ),
                )
                with TestClient(test_app) as client:
                    for filename in guessed_files:
                        with self.subTest(filename=filename):
                            response = client.get(f"/vision-events/{filename}")
                            self.assertEqual(response.status_code, 404)

    def test_missing_event_directory_is_not_created_during_mount(self):
        with tempfile.TemporaryDirectory() as parent:
            missing = os.path.join(parent, "missing-evidence")
            test_app = FastAPI()

            resolved = app_module.mount_vision_event_files(test_app, missing)

            self.assertEqual(resolved, os.path.realpath(missing))
            self.assertFalse(os.path.exists(missing))
            with TestClient(test_app) as client:
                response = client.get("/vision-events/not-created.jpg")
            self.assertEqual(response.status_code, 404)
            self.assertFalse(os.path.exists(missing))

    def test_generic_static_mount_cannot_bypass_evidence_policy(self):
        fake = FakeVisionService()

        with self.open_client(fake), TestClient(app_module.app) as client:
            response = client.get("/static/vision_events/.gitkeep")

        self.assertEqual(response.status_code, 404)

    def test_default_event_subtree_is_dedicated_only(self):
        default_directory = os.path.join(
            app_module.STATIC_DIR,
            "vision_events",
        )
        with tempfile.NamedTemporaryFile(
            dir=default_directory,
            suffix=".jpg",
        ) as evidence:
            evidence.write(b"default evidence")
            evidence.flush()
            filename = os.path.basename(evidence.name)

            result = self.probe_static_routes(
                "static/vision_events",
                [
                    f"/vision-events/{filename}",
                    f"/static/vision_events/{filename}",
                    "/vision-events/config.py",
                    "/static/style.css",
                ],
            )

        self.assertEqual(result["statuses"], [200, 404, 404, 200])
        self.assertEqual(
            app_module.event_static_subtree(default_directory),
            "vision_events",
        )

    def test_static_captures_override_blocks_its_complete_subtree(self):
        captures_directory = os.path.join(app_module.STATIC_DIR, "captures")
        with tempfile.NamedTemporaryFile(
            dir=captures_directory,
            suffix=".jpg",
        ) as evidence:
            evidence.write(b"capture evidence")
            evidence.flush()
            filename = os.path.basename(evidence.name)

            result = self.probe_static_routes(
                "static/captures",
                [
                    f"/vision-events/{filename}",
                    f"/static/captures/{filename}",
                    "/vision-events/config.py",
                    "/static/style.css",
                ],
            )

        self.assertEqual(result["statuses"], [200, 404, 404, 200])

    def test_nested_static_override_and_symlink_block_only_resolved_subtree(self):
        with tempfile.TemporaryDirectory(dir=app_module.STATIC_DIR) as temporary:
            event_directory = os.path.join(temporary, "custom", "evidence")
            sibling_directory = os.path.join(
                temporary,
                "custom",
                "evidence-sibling",
            )
            os.makedirs(event_directory)
            os.makedirs(sibling_directory)
            os.makedirs(os.path.join(temporary, "custom", "decoy"))
            event_filename = "nested-event.jpg"
            sibling_filename = "sibling.txt"
            with open(os.path.join(event_directory, event_filename), "wb") as file:
                file.write(b"nested evidence")
            with open(os.path.join(sibling_directory, sibling_filename), "wb") as file:
                file.write(b"normal static sibling")
            event_relative = os.path.relpath(
                event_directory,
                app_module.BASE_DIR,
            )
            event_static_url = os.path.relpath(
                event_directory,
                app_module.STATIC_DIR,
            ).replace(os.sep, "/")
            sibling_static_url = os.path.relpath(
                sibling_directory,
                app_module.STATIC_DIR,
            ).replace(os.sep, "/")
            symlink = os.path.join(temporary, "event-directory-link")
            os.symlink(event_directory, symlink)
            static_alias = os.path.join(
                temporary,
                "custom",
                "evidence-alias",
            )
            os.symlink(event_directory, static_alias)
            static_alias_url = os.path.relpath(
                static_alias,
                app_module.STATIC_DIR,
            ).replace(os.sep, "/")
            traversal_url = (
                os.path.relpath(
                    os.path.join(temporary, "custom", "decoy"),
                    app_module.STATIC_DIR,
                ).replace(os.sep, "/")
                + "/%2e%2e/evidence/"
                + event_filename
            )

            urls = [
                f"/vision-events/{event_filename}",
                f"/static/{event_static_url}/{event_filename}",
                f"/static/{event_static_url}",
                f"/static/{static_alias_url}/{event_filename}",
                f"/static/{traversal_url}",
                f"/static/{sibling_static_url}/{sibling_filename}",
                "/vision-events/config.py",
                "/static/style.css",
            ]
            direct = self.probe_static_routes(event_relative, urls)
            via_symlink = self.probe_static_routes(symlink, urls)

        expected = [200, 404, 404, 404, 404, 200, 404, 200]
        self.assertEqual(direct["statuses"], expected)
        self.assertEqual(via_symlink["statuses"], expected)

    def test_static_prefix_does_not_block_case_distinct_sibling(self):
        with tempfile.TemporaryDirectory(dir=app_module.STATIC_DIR) as temporary:
            event_directory = os.path.join(temporary, "evidence")
            case_sibling = os.path.join(temporary, "EVIDENCE")
            os.makedirs(event_directory)
            configured = os.path.relpath(event_directory, app_module.BASE_DIR)
            sibling_url = os.path.relpath(
                case_sibling,
                app_module.STATIC_DIR,
            ).replace(os.sep, "/")
            if os.path.exists(case_sibling):
                self.assertTrue(os.path.samefile(event_directory, case_sibling))
                filename = "case-variant.jpg"
                with open(os.path.join(event_directory, filename), "wb") as file:
                    file.write(b"same evidence directory")
                result = self.probe_static_routes(
                    configured,
                    [f"/static/{sibling_url}/{filename}"],
                )
                self.assertEqual(result["statuses"], [404])
                return

            os.makedirs(case_sibling)
            sibling_filename = "case-sibling.txt"
            with open(os.path.join(case_sibling, sibling_filename), "wb") as file:
                file.write(b"case-distinct sibling")
            result = self.probe_static_routes(
                configured,
                [f"/static/{sibling_url}/{sibling_filename}"],
            )

        self.assertEqual(result["statuses"], [200])

    def test_static_root_and_symlink_to_static_root_fall_back_safely(self):
        safe_default = os.path.realpath(
            os.path.join(app_module.STATIC_DIR, "vision_events")
        )
        with tempfile.TemporaryDirectory() as temporary:
            static_symlink = os.path.join(temporary, "static-link")
            os.symlink(app_module.STATIC_DIR, static_symlink)

            for configured in (app_module.STATIC_DIR, static_symlink):
                with self.subTest(configured=configured):
                    resolved, warning = (
                        app_module.resolve_vision_event_directory(configured)
                    )
                    self.assertEqual(resolved, safe_default)
                    self.assertEqual(
                        warning,
                        app_module.VISION_EVENT_DIRECTORY_WARNING_TEXT,
                    )

    def test_external_event_directory_needs_no_static_exclusion(self):
        with tempfile.TemporaryDirectory() as event_directory:
            event_filename = "external-event.jpg"
            with open(os.path.join(event_directory, event_filename), "wb") as file:
                file.write(b"external evidence")

            result = self.probe_static_routes(
                event_directory,
                [
                    f"/vision-events/{event_filename}",
                    "/static/style.css",
                    "/static/vision_events/.gitkeep",
                ],
            )

        self.assertEqual(result["statuses"], [200, 200, 200])
        self.assertEqual(app_module.event_static_subtree(event_directory), "")

    def test_inaccessible_event_directory_is_fail_soft_not_unauthorized(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_files = app_module.VisionEvidenceFiles(
                directory=directory,
                check_dir=False,
            )
            test_app = FastAPI()
            test_app.mount("/vision-events", evidence_files)

            with (
                patch.object(
                    evidence_files,
                    "lookup_path",
                    side_effect=PermissionError("inaccessible evidence"),
                ),
                TestClient(test_app) as client,
            ):
                response = client.get("/vision-events/evidence.jpg")

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("inaccessible evidence", response.text)

    def test_file_collision_does_not_abort_app_import(self):
        with tempfile.TemporaryDirectory() as parent:
            collision = os.path.join(parent, "evidence")
            with open(collision, "wb") as blocker:
                blocker.write(b"not a directory")
            environment = os.environ.copy()
            environment["VISION_EVENT_DIR"] = collision

            completed = subprocess.run(
                [sys.executable, "-c", "import app"],
                cwd=PROJECT_DIR,
                env=environment,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

        self.assertEqual(completed.returncode, 0)

    def test_missing_event_directory_does_not_abort_or_mutate_app_import(self):
        with tempfile.TemporaryDirectory() as parent:
            missing = os.path.join(parent, "missing-evidence")
            environment = os.environ.copy()
            environment["VISION_EVENT_DIR"] = missing

            completed = subprocess.run(
                [sys.executable, "-c", "import app"],
                cwd=PROJECT_DIR,
                env=environment,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertFalse(os.path.exists(missing))

    def test_unsafe_event_directory_warning_is_sanitized_in_status(self):
        fake = FakeVisionService()
        warning = "视觉证据目录配置不安全，已使用安全默认目录"

        with (
            patch.object(
                app_module,
                "VISION_EVENT_DIRECTORY_WARNING",
                warning,
                create=True,
            ),
            self.open_client(fake),
            TestClient(app_module.app) as client,
        ):
            response = client.get("/api/vision/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("storage_error"), warning)
        self.assertNotIn(app_module.BASE_DIR, response.text)

    def test_event_limit_outside_fastapi_bounds_returns_422(self):
        fake = FakeVisionService()
        with self.open_client(fake), TestClient(app_module.app) as client:
            too_large = client.get("/api/vision/events?limit=201")
            too_small = client.get("/api/vision/events?limit=0")

        self.assertEqual(too_large.status_code, 422)
        self.assertEqual(too_small.status_code, 422)

    def test_event_id_outside_sqlite_integer_range_returns_422(self):
        fake = FakeVisionService()
        with self.open_client(fake), TestClient(app_module.app) as client:
            zero = client.post("/api/vision/events/0/ack")
            oversized = client.post(
                "/api/vision/events/9223372036854775808/ack"
            )

        self.assertEqual(zero.status_code, 422)
        self.assertEqual(oversized.status_code, 422)

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
                    response.json(),
                    {"ok": False, "error": "视觉事件存储不可用"},
                )

    def test_env_reads_publish_topic_and_returns_board_vision_alarm(self):
        fake = FakeVisionService()
        topics = []

        def get_topic(topic):
            topics.append(topic)
            return {
                "ok": True,
                "topic": topic,
                "msg": '{"temperature":25.0,"vision_alarm":1}',
                "time": "now",
                "raw": None,
                "error": "",
            }

        with (
            patch.object(app_module.config, "ENV_TOPIC", "env-control"),
            patch.object(app_module.config, "ENV_PUB_TOPIC", "env-control/up"),
            patch.object(app_module.bemfa_api, "get_topic_msg", side_effect=get_topic),
            self.open_client(fake),
            TestClient(app_module.app) as client,
        ):
            response = client.get("/api/env")

        self.assertEqual(topics, ["env-control/up"])
        self.assertEqual(response.json()["data"]["vision_alarm"], 1)

    def test_capture_success_warning_does_not_expose_runtime_details(self):
        fake = FakeVisionService(None)
        secret_directory = "/private/runtime/captures"
        capture_result = {
            "ok": True,
            "filename": "capture.jpg",
            "path": f"{secret_directory}/capture.jpg",
            "error": f"camera fallback failed at {secret_directory}",
        }

        with (
            patch.object(
                app_module.camera,
                "capture_photo",
                return_value=capture_result,
            ),
            self.open_client(fake),
            TestClient(app_module.app) as client,
        ):
            response = client.post("/api/capture/now")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["path"], "capture.jpg")
        self.assertEqual(
            response.json()["error"],
            "抓拍已完成但使用占位图",
        )
        self.assertNotIn(secret_directory, response.text)

    def test_vision_alarm_sender_uses_bounded_total_timeout(self):
        with patch.object(
            app_module.bemfa_api,
            "send_msg",
            return_value={"ok": True},
        ) as sender:
            result = app_module._send_vision_alarm("vision_alarm_off")

        self.assertTrue(result["ok"])
        timeout = sender.call_args.kwargs["timeout"]
        self.assertGreater(timeout, 0.0)
        self.assertLessEqual(timeout, 1.0)


if __name__ == "__main__":
    unittest.main()
