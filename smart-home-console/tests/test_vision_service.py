from __future__ import annotations

import os
import sys
import tempfile
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
)


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

    def VideoCapture(self, *args):
        self.open_args = args
        return self.capture

    @staticmethod
    def VideoWriter_fourcc(*chars):
        return "".join(chars)


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
        )

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


if __name__ == "__main__":
    unittest.main()
