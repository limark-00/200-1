from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from vision_service import (
    VisionService,
    VisionSettings,
    _default_capture_factory,
    build_mjpeg_chunk,
    extract_foot_points,
)
from event_repository import EventRepository
from zone_detector import NormalizedZone, ZoneDetector, ZoneState


class FakeBoxes:
    def __len__(self) -> int:
        return 2


class FakeResult:
    boxes = FakeBoxes()

    def plot(self):
        return "annotated-frame"


class FakeModel:
    def __init__(self) -> None:
        self.calls = []

    def predict(self, frame, **kwargs):
        self.calls.append((frame, kwargs))
        return [FakeResult()]


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeFrame:
    def __init__(self, width=640, height=480, label="frame"):
        self.shape = (height, width, 3)
        self.label = label

    def __str__(self):
        return self.label


class FakeXyxy:
    def __init__(self, rows=None):
        self.rows = rows or []

    def cpu(self):
        return self

    def tolist(self):
        return self.rows


class SafetyBoxes:
    def __init__(self, rows=None):
        self.xyxy = FakeXyxy(
            rows
            if rows is not None
            else [[100.0, 100.0, 300.0, 400.0]]
        )

    def __len__(self):
        return len(self.xyxy.rows)


class SafetyResult:
    def __init__(self, frame, rows=None):
        self.frame = frame
        self.boxes = SafetyBoxes(rows)

    def plot(self):
        return self.frame


class SafetyModel:
    def __init__(self, rows=None):
        self.rows = rows

    def predict(self, frame, **_kwargs):
        return [SafetyResult(frame, self.rows)]


class RecordingAlarm:
    def __init__(self, log=None):
        self.targets = []
        self.log = log
        self.wait_timeouts = []
        self.stop_timeouts = []

    def start(self):
        if self.log is not None:
            self.log.append("alarm.start")
        return True

    def set_alarm(self, enabled, event_id=None, force=False):
        self.targets.append((enabled, event_id))
        if self.log is not None:
            self.log.append(("alarm.set", enabled, event_id, force))
        return True

    def wait_idle(self, timeout):
        self.wait_timeouts.append(timeout)
        if self.log is not None:
            self.log.append(("alarm.wait", timeout))
        return True

    def stop(self, timeout=3.0):
        self.stop_timeouts.append(timeout)
        if self.log is not None:
            self.log.append(("alarm.stop", timeout))

    def get_last_error(self):
        return ""


class FakeCapture:
    def __init__(self) -> None:
        self.released = False

    def isOpened(self) -> bool:
        return True

    def read(self):
        return True, "raw-frame"

    def set(self, _prop, _value) -> bool:
        return True

    def release(self) -> None:
        self.released = True


class FailingCapture(FakeCapture):
    def read(self):
        return False, None


class ConfigurableFakeCapture(FakeCapture):
    def __init__(self) -> None:
        super().__init__()
        self.set_calls = []

    def set(self, prop, value) -> bool:
        self.set_calls.append((prop, value))
        return True


class FakeCv2Module:
    CAP_V4L2 = 200
    CAP_PROP_FOURCC = 6
    CAP_PROP_FRAME_WIDTH = 3
    CAP_PROP_FRAME_HEIGHT = 4
    CAP_PROP_BUFFERSIZE = 38

    def __init__(self) -> None:
        self.capture = ConfigurableFakeCapture()
        self.open_args = None
        self.rectangles = []

    def VideoCapture(self, *args):
        self.open_args = args
        return self.capture

    @staticmethod
    def VideoWriter_fourcc(*chars):
        return "".join(chars)

    def rectangle(self, frame, start, end, color, thickness):
        self.rectangles.append((start, end, color, thickness))
        return frame


def fake_encoder(frame, _quality: int) -> bytes:
    return ("jpeg:" + str(frame)).encode("utf-8")


class VisionServiceTests(unittest.TestCase):
    def make_service(self, **overrides) -> VisionService:
        settings = VisionSettings(
            enabled=True,
            camera_index=0,
            model_name="fake.pt",
            confidence=0.4,
            image_size=320,
            frame_skip=1,
            width=640,
            height=480,
            jpeg_quality=75,
            reconnect_delay=0.01,
        )
        return VisionService(
            settings,
            capture_factory=overrides.get("capture_factory", FakeCapture),
            model_factory=overrides.get("model_factory", lambda _name: FakeModel()),
            frame_encoder=overrides.get("frame_encoder", fake_encoder),
            zone_detector=overrides.get("zone_detector"),
            event_repository=overrides.get("event_repository"),
            alarm_controller=overrides.get("alarm_controller"),
            event_snapshot_dir=overrides.get("event_snapshot_dir"),
            overlay_renderer=overrides.get("overlay_renderer"),
        )

    def make_safety_service(self, **overrides):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        clock = overrides.get("clock", FakeClock())
        detector = overrides.get(
            "detector", ZoneDetector(2.0, 3.0, clock=clock)
        )
        zone = overrides.get("zone", NormalizedZone(0.1, 0.1, 0.8, 0.8))
        if zone is not None:
            detector.set_zone(zone)
        repository = overrides.get(
            "repository",
            EventRepository(os.path.join(temporary.name, "events.db")),
        )
        repository.initialize()
        alarm = overrides.get("alarm", RecordingAlarm())
        service = self.make_service(
            capture_factory=overrides.get("capture_factory", FakeCapture),
            model_factory=overrides.get(
                "model_factory", lambda _name: SafetyModel()
            ),
            zone_detector=detector,
            event_repository=repository,
            alarm_controller=alarm,
            event_snapshot_dir=overrides.get("event_snapshot_dir", temporary.name),
            overlay_renderer=overrides.get(
                "overlay_renderer", lambda frame, _zone, _state: frame
            ),
        )
        return service, detector, repository, alarm, clock, temporary.name

    def active_safety_service(self, **overrides):
        values = self.make_safety_service(**overrides)
        service, _detector, _repository, _alarm, clock, _directory = values
        service.process_frame(SafetyModel(), FakeFrame())
        clock.advance(2.0)
        service.process_frame(SafetyModel(), FakeFrame())
        return values

    def test_initial_status_is_offline_and_empty(self):
        service = self.make_service()

        status = service.get_status()

        self.assertFalse(status["running"])
        self.assertFalse(status["camera_online"])
        self.assertFalse(status["model_loaded"])
        self.assertEqual(status["people_count"], 0)
        self.assertEqual(status["frame_sequence"], 0)
        self.assertEqual(status["last_error"], "")

    def test_linux_capture_uses_v4l2_and_mjpg(self):
        service = self.make_service()
        fake_cv2 = FakeCv2Module()

        with (
            patch.dict(sys.modules, {"cv2": fake_cv2}),
            patch.object(sys, "platform", "linux"),
        ):
            capture = _default_capture_factory(service.settings)

        self.assertIs(capture, fake_cv2.capture)
        self.assertEqual(fake_cv2.open_args, (0, fake_cv2.CAP_V4L2))
        self.assertIn(
            (fake_cv2.CAP_PROP_FOURCC, "MJPG"),
            fake_cv2.capture.set_calls,
        )

    def test_process_frame_requests_person_only_and_updates_latest_jpeg(self):
        model = FakeModel()
        service = self.make_service(model_factory=lambda _name: model)

        jpeg = service.process_frame(model, "raw-frame")

        self.assertEqual(jpeg, b"jpeg:annotated-frame")
        self.assertEqual(service.get_latest_jpeg(), jpeg)
        self.assertEqual(service.get_status()["people_count"], 2)
        _, kwargs = model.calls[0]
        self.assertEqual(kwargs["classes"], [0])
        self.assertEqual(kwargs["conf"], 0.4)
        self.assertEqual(kwargs["imgsz"], 320)
        self.assertFalse(kwargs["verbose"])

    def test_mjpeg_chunk_has_boundary_and_jpeg_headers(self):
        chunk = build_mjpeg_chunk(b"jpeg-data")

        self.assertTrue(chunk.startswith(b"--frame\r\n"))
        self.assertIn(b"Content-Type: image/jpeg\r\n", chunk)
        self.assertTrue(chunk.endswith(b"jpeg-data\r\n"))

    def test_save_snapshot_writes_current_annotated_frame(self):
        service = self.make_service()
        service.process_frame(FakeModel(), "raw-frame")

        with tempfile.TemporaryDirectory() as directory:
            result = service.save_snapshot(directory)

            self.assertTrue(result["ok"])
            self.assertTrue(result["filename"].startswith("vision_"))
            with open(result["path"], "rb") as file:
                self.assertEqual(file.read(), b"jpeg:annotated-frame")

    def test_save_snapshot_reports_when_no_frame_is_available(self):
        service = self.make_service()

        with tempfile.TemporaryDirectory() as directory:
            result = service.save_snapshot(directory)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "视觉服务尚无可用画面")

    def test_background_worker_processes_frames_and_releases_camera(self):
        capture = FakeCapture()
        model = FakeModel()
        service = self.make_service(
            capture_factory=lambda: capture,
            model_factory=lambda _name: model,
        )

        service.start()
        deadline = time.time() + 1.0
        while service.get_status()["frame_sequence"] == 0 and time.time() < deadline:
            time.sleep(0.01)
        service.stop()

        status = service.get_status()
        self.assertGreater(status["frame_sequence"], 0)
        self.assertFalse(status["running"])
        self.assertTrue(capture.released)

    def test_extract_foot_points_uses_bottom_center_and_clamps(self):
        boxes = SafetyBoxes(
            [
                [100.0, 100.0, 300.0, 400.0],
                [-500.0, -20.0, -100.0, -10.0],
                [700.0, 100.0, 900.0, 800.0],
            ]
        )

        points = extract_foot_points(boxes, 640, 480)

        self.assertEqual(points[0], (0.3125, 400.0 / 480.0))
        self.assertEqual(points[1], (0.0, 0.0))
        self.assertEqual(points[2], (1.0, 1.0))

    def test_no_zone_stays_disabled_without_event_or_alarm(self):
        service, _detector, repository, alarm, clock, _directory = (
            self.make_safety_service(zone=None)
        )

        service.process_frame(SafetyModel(), FakeFrame())
        clock.advance(2.0)
        service.process_frame(SafetyModel(), FakeFrame())

        self.assertEqual(repository.list_events(), [])
        self.assertEqual(alarm.targets, [])
        status = service.get_status()
        self.assertEqual(status["zone_state"], "disabled")
        self.assertEqual(status["people_in_zone"], 0)

    def test_person_outside_zone_does_not_start_alarm(self):
        service, _detector, repository, alarm, clock, _directory = (
            self.make_safety_service(zone=NormalizedZone(0.0, 0.0, 0.2, 0.2))
        )

        service.process_frame(SafetyModel(), FakeFrame())
        clock.advance(5.0)
        service.process_frame(SafetyModel(), FakeFrame())

        self.assertEqual(repository.list_events(), [])
        self.assertEqual(alarm.targets, [])
        self.assertEqual(service.get_status()["zone_state"], "armed")

    def test_zone_alarm_creates_one_event_and_one_command(self):
        overlay_calls = []

        def render(_frame, zone, state):
            overlay_calls.append((zone, state))
            return FakeFrame(label="overlaid-frame")

        service, _detector, repository, alarm, clock, directory = (
            self.make_safety_service(overlay_renderer=render)
        )
        service.process_frame(SafetyModel(), FakeFrame())
        clock.advance(2.0)
        jpeg = service.process_frame(SafetyModel(), FakeFrame())
        service.process_frame(SafetyModel(), FakeFrame())

        events = repository.list_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(alarm.targets, [(True, events[0]["id"])])
        self.assertEqual(service.get_status()["zone_state"], "alarm_active")
        self.assertIn(ZoneState.ALARM_ACTIVE, [state for _zone, state in overlay_calls])
        self.assertEqual(jpeg, service.get_latest_jpeg())
        with open(os.path.join(directory, events[0]["snapshot_filename"]), "rb") as file:
            self.assertEqual(file.read(), jpeg)

    def test_acknowledge_silences_without_rearming(self):
        service, _detector, repository, alarm, _clock, _directory = (
            self.active_safety_service()
        )
        event_id = repository.list_events()[0]["id"]

        result = service.acknowledge_event(event_id)

        self.assertIsNotNone(result["acknowledged_at"])
        self.assertEqual(alarm.targets[-1], (False, event_id))
        self.assertEqual(service.get_status()["zone_state"], "alarm_silenced")

    def test_three_second_vacancy_closes_event_and_rearms(self):
        service, _detector, repository, alarm, clock, _directory = (
            self.active_safety_service()
        )
        event_id = repository.list_events()[0]["id"]
        empty_model = SafetyModel(rows=[])

        service.process_frame(empty_model, FakeFrame())
        clock.advance(3.0)
        service.process_frame(empty_model, FakeFrame())

        event = repository.get_event(event_id)
        self.assertEqual(event["close_reason"], "person_left")
        self.assertIsNotNone(event["ended_at"])
        self.assertEqual(alarm.targets[-1], (False, event_id))
        self.assertEqual(service.get_status()["zone_state"], "armed")

    def test_active_event_updates_max_people_only_when_peak_increases(self):
        class CountingRepository(EventRepository):
            def __init__(self, db_path):
                super().__init__(db_path)
                self.max_updates = []

            def update_max_people(self, event_id, people_count):
                self.max_updates.append((event_id, people_count))
                return super().update_max_people(event_id, people_count)

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = CountingRepository(os.path.join(temporary.name, "events.db"))
        service, _detector, repository, _alarm, _clock, _directory = (
            self.active_safety_service(repository=repository)
        )
        event_id = repository.list_events()[0]["id"]
        two_people = SafetyModel(
            rows=[
                [100.0, 100.0, 300.0, 400.0],
                [200.0, 100.0, 400.0, 400.0],
            ]
        )

        service.process_frame(two_people, FakeFrame())
        service.process_frame(two_people, FakeFrame())
        service.process_frame(SafetyModel(), FakeFrame())

        self.assertEqual(repository.get_event(event_id)["max_people"], 2)
        self.assertEqual(repository.max_updates, [(event_id, 2)])

    def test_snapshot_failure_records_empty_filename_and_still_alarms(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        blocked_path = os.path.join(temporary.name, "not-a-directory")
        with open(blocked_path, "wb") as file:
            file.write(b"block directory creation")
        service, _detector, repository, alarm, clock, _directory = (
            self.make_safety_service(event_snapshot_dir=blocked_path)
        )

        service.process_frame(SafetyModel(), FakeFrame())
        clock.advance(2.0)
        service.process_frame(SafetyModel(), FakeFrame())

        event = repository.list_events()[0]
        self.assertEqual(event["snapshot_filename"], "")
        self.assertIn("not-a-directory", event["last_error"])
        self.assertEqual(alarm.targets, [(True, event["id"])])

    def test_successful_alarm_delivery_preserves_snapshot_failure_error(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        blocked_path = os.path.join(temporary.name, "not-a-directory")
        with open(blocked_path, "wb") as file:
            file.write(b"block directory creation")
        service, _detector, repository, _alarm, clock, _directory = (
            self.make_safety_service(event_snapshot_dir=blocked_path)
        )
        service.process_frame(SafetyModel(), FakeFrame())
        clock.advance(2.0)
        service.process_frame(SafetyModel(), FakeFrame())
        event_id = repository.list_events()[0]["id"]

        repository.mark_delivery(event_id, "vision_alarm_on", True, "")

        event = repository.get_event(event_id)
        self.assertTrue(event["alarm_on_delivered"])
        self.assertIn("not-a-directory", event["last_error"])

    def test_event_creation_failure_does_not_bind_fake_id_but_still_alarms(self):
        class CreateFailingRepository(EventRepository):
            def create_event(self, snapshot_filename, people_count):
                raise OSError("database is read-only")

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = CreateFailingRepository(os.path.join(temporary.name, "events.db"))
        service, detector, repository, alarm, clock, _directory = (
            self.make_safety_service(repository=repository)
        )

        service.process_frame(SafetyModel(), FakeFrame())
        clock.advance(2.0)
        service.process_frame(SafetyModel(), FakeFrame())

        self.assertEqual(repository.list_events(), [])
        self.assertIsNone(detector.get_status()["event_id"])
        self.assertEqual(alarm.targets, [(True, None)])
        self.assertIn("database is read-only", service.get_status()["last_error"])

    def test_snapshot_error_update_failure_keeps_created_event_id(self):
        class ErrorUpdateFailingRepository(EventRepository):
            def record_error(self, event_id, error_text):
                raise OSError("error update failed")

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        blocked_path = os.path.join(temporary.name, "not-a-directory")
        with open(blocked_path, "wb") as file:
            file.write(b"block directory creation")
        repository = ErrorUpdateFailingRepository(
            os.path.join(temporary.name, "events.db")
        )
        service, detector, repository, alarm, clock, _directory = (
            self.make_safety_service(
                repository=repository,
                event_snapshot_dir=blocked_path,
            )
        )

        service.process_frame(SafetyModel(), FakeFrame())
        clock.advance(2.0)
        service.process_frame(SafetyModel(), FakeFrame())

        event_id = repository.list_events()[0]["id"]
        self.assertEqual(detector.get_status()["event_id"], event_id)
        self.assertEqual(alarm.targets, [(True, event_id)])

    def test_camera_disconnect_does_not_call_zone_update_without_a_frame(self):
        class CountingDetector(ZoneDetector):
            def __init__(self, clock):
                super().__init__(2.0, 3.0, clock=clock)
                self.update_calls = 0

            def update(self, foot_points):
                self.update_calls += 1
                return super().update(foot_points)

        clock = FakeClock()
        detector = CountingDetector(clock)
        detector.set_zone(NormalizedZone(0.1, 0.1, 0.8, 0.8))
        capture = FailingCapture()
        service, _detector, _repository, _alarm, _clock, _directory = (
            self.make_safety_service(
                detector=detector,
                clock=clock,
                capture_factory=lambda: capture,
            )
        )
        service.process_frame(SafetyModel(), FakeFrame())
        clock.advance(10.0)

        service.start()
        time.sleep(0.04)
        service.stop()

        self.assertEqual(detector.update_calls, 1)
        self.assertEqual(detector.get_status()["state"], "enter_pending")
        self.assertEqual(service.get_status()["enter_elapsed"], 0.0)

    def test_process_frame_after_stop_returns_jpeg_without_publishing(self):
        service, detector, repository, alarm, _clock, _directory = (
            self.make_safety_service()
        )
        service.stop(timeout=0.0)

        jpeg = service.process_frame(SafetyModel(), FakeFrame())

        # A delayed caller still receives normal encoded bytes for compatibility,
        # but a stopped service does not publish or advance any safety state.
        self.assertEqual(jpeg, b"jpeg:frame")
        self.assertIsNone(service.get_latest_jpeg())
        self.assertEqual(service.get_status()["frame_sequence"], 0)
        self.assertEqual(detector.get_status()["state"], "armed")
        self.assertEqual(repository.list_events(), [])
        self.assertEqual(alarm.targets, [])

    def test_blocked_prediction_cannot_publish_or_alarm_after_shutdown(self):
        class BlockingModel:
            def __init__(self):
                self.started = threading.Event()
                self.release = threading.Event()

            def predict(self, frame, **_kwargs):
                self.started.set()
                self.release.wait()
                return [SafetyResult(frame)]

        class FrameCapture(FakeCapture):
            def read(self):
                return True, FakeFrame()

        model = BlockingModel()
        capture = FrameCapture()
        service, detector, repository, alarm, clock, _directory = (
            self.make_safety_service(
                capture_factory=lambda: capture,
                model_factory=lambda _name: model,
            )
        )
        service.process_frame(SafetyModel(), FakeFrame())
        clock.advance(2.0)
        baseline_sequence = service.get_status()["frame_sequence"]

        service.start()
        self.assertTrue(model.started.wait(1.0))
        service.stop(timeout=0.01)
        service.shutdown_safety()
        model.release.set()
        service.stop(timeout=1.0)

        self.assertEqual(detector.get_status()["state"], "enter_pending")
        self.assertEqual(repository.list_events(), [])
        self.assertNotIn((True, None), alarm.targets)
        self.assertEqual(alarm.targets, [(False, None)])
        self.assertEqual(
            service.get_status()["frame_sequence"],
            baseline_sequence,
        )
        self.assertTrue(capture.released)

    def test_delete_active_zone_closes_event_and_turns_alarm_off(self):
        service, detector, repository, alarm, _clock, _directory = (
            self.active_safety_service()
        )
        event_id = repository.list_events()[0]["id"]

        service.delete_zone()

        self.assertIsNone(repository.get_zone())
        self.assertEqual(repository.get_event(event_id)["close_reason"], "zone_deleted")
        self.assertEqual(detector.get_status()["state"], "disabled")
        self.assertEqual(alarm.targets[-1], (False, event_id))

    def test_save_zone_persistence_failure_keeps_in_memory_zone(self):
        class SaveFailingRepository(EventRepository):
            def save_zone(self, zone):
                raise OSError("disk full")

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = SaveFailingRepository(os.path.join(temporary.name, "events.db"))
        service, detector, _repository, _alarm, _clock, _directory = (
            self.make_safety_service(repository=repository)
        )
        original = detector.get_status()["zone"]

        with self.assertRaisesRegex(OSError, "disk full"):
            service.save_zone(NormalizedZone(0.2, 0.2, 0.3, 0.3))

        self.assertEqual(detector.get_status()["zone"], original)

    def test_delete_zone_persistence_failure_keeps_active_state(self):
        class DeleteFailingRepository(EventRepository):
            def delete_zone(self):
                raise OSError("database locked")

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = DeleteFailingRepository(os.path.join(temporary.name, "events.db"))
        service, detector, repository, alarm, _clock, _directory = (
            self.active_safety_service(repository=repository)
        )
        event_id = repository.list_events()[0]["id"]
        alarm_count = len(alarm.targets)

        with self.assertRaisesRegex(OSError, "database locked"):
            service.delete_zone()

        self.assertEqual(detector.get_status()["state"], "alarm_active")
        self.assertIsNone(repository.get_event(event_id)["ended_at"])
        self.assertEqual(len(alarm.targets), alarm_count)

    def test_default_overlay_draws_pending_zone_in_amber(self):
        fake_cv2 = FakeCv2Module()
        service, _detector, _repository, _alarm, _clock, _directory = (
            self.make_safety_service(overlay_renderer=None)
        )

        with patch.dict(sys.modules, {"cv2": fake_cv2}):
            service.process_frame(SafetyModel(), FakeFrame())

        self.assertEqual(
            fake_cv2.rectangles,
            [((64, 48), (576, 432), (0, 191, 255), 2)],
        )

    def test_status_adds_only_the_declared_safety_fields(self):
        service, _detector, _repository, _alarm, _clock, _directory = (
            self.make_safety_service()
        )
        phase_one_keys = {
            "enabled",
            "running",
            "camera_online",
            "model_loaded",
            "people_count",
            "frame_sequence",
            "fps",
            "last_error",
            "camera_index",
            "model_name",
        }
        safety_keys = {
            "zone",
            "zone_state",
            "people_in_zone",
            "active_event_id",
            "enter_elapsed",
            "exit_elapsed",
            "alarm_delivery_error",
        }

        status = service.get_status()

        self.assertEqual(set(status), phase_one_keys | safety_keys)
        self.assertEqual(
            status["zone"],
            {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8},
        )

    def test_list_events_delegates_limit_to_repository(self):
        service, _detector, repository, _alarm, _clock, _directory = (
            self.make_safety_service()
        )
        event_id = repository.create_event("manual.jpg", 1)

        self.assertEqual(service.list_events(1)[0]["id"], event_id)
        with self.assertRaises(ValueError):
            service.list_events(201)

    def test_initialize_safety_uses_required_recovery_order(self):
        log = []

        class LoggingRepository(EventRepository):
            def initialize(self):
                log.append("repo.initialize")
                return super().initialize()

            def get_zone(self):
                log.append("repo.get_zone")
                return NormalizedZone(0.2, 0.2, 0.3, 0.3)

            def recover_open_events(self, close_reason):
                log.append(("repo.recover", close_reason))
                return []

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = LoggingRepository(os.path.join(temporary.name, "events.db"))
        detector = ZoneDetector(2.0, 3.0, clock=FakeClock())
        alarm = RecordingAlarm(log)
        service = self.make_service(
            zone_detector=detector,
            event_repository=repository,
            alarm_controller=alarm,
            event_snapshot_dir=temporary.name,
            overlay_renderer=lambda frame, _zone, _state: frame,
        )

        service.initialize_safety()

        self.assertEqual(
            log,
            [
                "repo.initialize",
                "repo.get_zone",
                ("repo.recover", "server_restart"),
                "alarm.start",
                ("alarm.set", False, None, True),
            ],
        )
        self.assertEqual(detector.get_status()["state"], "armed")

    def test_initialize_safety_resets_stale_in_memory_event_before_recovery(self):
        service, detector, repository, _alarm, _clock, _directory = (
            self.active_safety_service()
        )
        zone = detector.get_status()["zone"]
        repository.save_zone(zone)
        event_id = repository.list_events()[0]["id"]

        service.initialize_safety()

        self.assertEqual(repository.get_event(event_id)["close_reason"], "server_restart")
        self.assertEqual(detector.get_status()["state"], "armed")
        self.assertIsNone(detector.get_status()["event_id"])

    def test_shutdown_safety_uses_required_close_and_alarm_order(self):
        log = []

        class LoggingRepository(EventRepository):
            def close_event(self, event_id, close_reason):
                log.append(("repo.close", event_id, close_reason))
                return super().close_event(event_id, close_reason)

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = LoggingRepository(os.path.join(temporary.name, "events.db"))
        alarm = RecordingAlarm(log)
        service, _detector, repository, _alarm, _clock, _directory = (
            self.active_safety_service(repository=repository, alarm=alarm)
        )
        event_id = repository.list_events()[0]["id"]
        log.clear()

        service.shutdown_safety()

        self.assertEqual(
            log,
            [
                ("repo.close", event_id, "server_shutdown"),
                ("alarm.set", False, event_id, True),
                ("alarm.wait", 3.0),
                ("alarm.stop", 0.0),
            ],
        )


if __name__ == "__main__":
    unittest.main()
