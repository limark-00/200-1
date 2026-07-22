# -*- coding: utf-8 -*-
"""单例摄像头与YOLO人员检测服务。"""

from __future__ import annotations

import os
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Callable, Iterator

from event_repository import EventRepository
from vision_alarm import VisionAlarmController
from zone_detector import NormalizedZone, ZoneDetector, ZoneState, ZoneUpdate


@dataclass(frozen=True)
class VisionSettings:
    enabled: bool
    camera_index: int
    model_name: str
    confidence: float
    image_size: int
    frame_skip: int
    width: int
    height: int
    jpeg_quality: int
    reconnect_delay: float


def build_mjpeg_chunk(jpeg: bytes) -> bytes:
    """把一帧JPEG包装成浏览器可播放的multipart片段。"""
    return (
        b"--frame\r\n"
        b"Content-Type: image/jpeg\r\n"
        b"Content-Length: "
        + str(len(jpeg)).encode("ascii")
        + b"\r\n\r\n"
        + jpeg
        + b"\r\n"
    )


def _default_model_factory(model_name: str):
    from ultralytics import YOLO

    return YOLO(model_name)


def _default_capture_factory(settings: VisionSettings):
    import cv2

    if sys.platform.startswith("linux"):
        # VMware/UVC 摄像头常会在 OpenCV 默认格式下读帧超时；
        # 明确使用 V4L2 + MJPG，与 v4l2-ctl 可用视频流保持一致。
        capture = cv2.VideoCapture(settings.camera_index, cv2.CAP_V4L2)
        capture.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(*"MJPG"),
        )
    else:
        capture = cv2.VideoCapture(settings.camera_index)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, settings.width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.height)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return capture


def _default_frame_encoder(frame: Any, quality: int) -> bytes:
    import cv2

    ok, encoded = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, quality],
    )
    if not ok:
        raise RuntimeError("JPEG编码失败")
    return encoded.tobytes()


def extract_foot_points(
    boxes: Any,
    frame_width: int,
    frame_height: int,
) -> list[tuple[float, float]]:
    """Convert YOLO xyxy person boxes to clamped normalized foot points."""
    if boxes is None:
        return []
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("frame dimensions must be positive")

    xyxy = getattr(boxes, "xyxy", None)
    if xyxy is None:
        return []
    rows = xyxy.cpu().tolist()
    points = []
    for x1, _y1, x2, y2, *_rest in rows:
        x = ((float(x1) + float(x2)) / 2.0) / frame_width
        y = float(y2) / frame_height
        points.append((min(1.0, max(0.0, x)), min(1.0, max(0.0, y))))
    return points


def _default_overlay_renderer(
    frame: Any,
    zone: NormalizedZone | None,
    state: ZoneState,
) -> Any:
    """Draw the persisted zone on the annotated frame using state colors."""
    if zone is None:
        return frame

    import cv2

    height, width = frame.shape[:2]
    start = (round(zone.x * width), round(zone.y * height))
    end = (
        round((zone.x + zone.width) * width),
        round((zone.y + zone.height) * height),
    )
    colors = {
        ZoneState.ARMED: (0, 255, 0),
        ZoneState.ENTER_PENDING: (0, 191, 255),
        ZoneState.ALARM_ACTIVE: (0, 0, 255),
        ZoneState.ALARM_SILENCED: (128, 128, 128),
    }
    cv2.rectangle(frame, start, end, colors.get(state, (0, 255, 0)), 2)
    return frame


class VisionService:
    """后台持续读取一个摄像头，并共享最新YOLO标注帧。"""

    def __init__(
        self,
        settings: VisionSettings,
        *,
        capture_factory: Callable[[], Any] | None = None,
        model_factory: Callable[[str], Any] | None = None,
        frame_encoder: Callable[[Any, int], bytes] | None = None,
        zone_detector: ZoneDetector | None = None,
        event_repository: EventRepository | None = None,
        alarm_controller: VisionAlarmController | None = None,
        event_snapshot_dir: str | None = None,
        overlay_renderer: (
            Callable[[Any, NormalizedZone | None, ZoneState], Any] | None
        ) = None,
    ) -> None:
        self.settings = settings
        self._capture_factory = capture_factory or (
            lambda: _default_capture_factory(self.settings)
        )
        self._model_factory = model_factory or _default_model_factory
        self._frame_encoder = frame_encoder or _default_frame_encoder
        self._zone_detector = zone_detector
        self._event_repository = event_repository
        self._alarm_controller = alarm_controller
        self._event_snapshot_dir = event_snapshot_dir
        self._overlay_renderer = overlay_renderer or _default_overlay_renderer

        self._lock = threading.Lock()
        self._frame_ready = threading.Condition(self._lock)
        self._safety_lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self._latest_jpeg: bytes | None = None
        self._running = False
        self._camera_online = False
        self._model_loaded = False
        self._people_count = 0
        self._frame_sequence = 0
        self._fps = 0.0
        self._last_frame_time: float | None = None
        self._last_error = ""
        self._people_in_zone = 0
        self._persisted_max_people = 0
        self._enter_started_at: float | None = None
        self._exit_started_at: float | None = None
        self._enter_elapsed = 0.0
        self._exit_elapsed = 0.0
        self._safety_clock = getattr(zone_detector, "_clock", time.monotonic)

    def start(self) -> bool:
        """启动后台视觉线程；重复调用不会创建第二个线程。"""
        if not self.settings.enabled:
            return False

        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return False
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="yolo-vision",
                daemon=True,
            )
            self._thread.start()
        return True

    def stop(self, timeout: float = 3.0) -> None:
        """停止线程并等待摄像头释放。"""
        self._stop_event.set()
        with self._frame_ready:
            self._frame_ready.notify_all()

        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=timeout)

        with self._lock:
            self._running = False
            self._camera_online = False

    def process_frame(self, model: Any, frame: Any) -> bytes:
        """对单帧执行person检测、标注和JPEG编码。"""
        results = model.predict(
            frame,
            classes=[0],
            conf=self.settings.confidence,
            imgsz=self.settings.image_size,
            verbose=False,
        )

        if results:
            result = results[0]
            boxes = getattr(result, "boxes", None)
            people_count = len(boxes) if boxes is not None else 0
            annotated = result.plot()
        else:
            boxes = None
            people_count = 0
            annotated = frame

        processing_error = ""
        if self._zone_detector is None:
            jpeg = self._frame_encoder(annotated, self.settings.jpeg_quality)
        else:
            height, width = frame.shape[:2]
            foot_points = extract_foot_points(boxes, width, height)
            with self._safety_lock:
                previous_state = self._zone_detector.get_status()["state"]
                update = self._zone_detector.update(foot_points)
                self._update_safety_timers(previous_state, update)
                detector_status = self._zone_detector.get_status()
                annotated = self._overlay_renderer(
                    annotated,
                    detector_status["zone"],
                    update.state,
                )
                jpeg = self._frame_encoder(annotated, self.settings.jpeg_quality)
                processing_error = self._coordinate_zone_update(update, jpeg)

        now = time.monotonic()

        with self._frame_ready:
            if self._last_frame_time is not None and now > self._last_frame_time:
                instant_fps = 1.0 / (now - self._last_frame_time)
                self._fps = (
                    instant_fps
                    if self._fps == 0.0
                    else self._fps * 0.8 + instant_fps * 0.2
                )
            self._last_frame_time = now
            self._latest_jpeg = jpeg
            self._people_count = people_count
            self._frame_sequence += 1
            self._last_error = processing_error
            self._frame_ready.notify_all()

        return jpeg

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            status = {
                "enabled": self.settings.enabled,
                "running": self._running,
                "camera_online": self._camera_online,
                "model_loaded": self._model_loaded,
                "people_count": self._people_count,
                "frame_sequence": self._frame_sequence,
                "fps": round(self._fps, 1),
                "last_error": self._last_error,
                "camera_index": self.settings.camera_index,
                "model_name": self.settings.model_name,
            }

        with self._safety_lock:
            if self._zone_detector is None:
                detector_status = {
                    "state": ZoneState.DISABLED.value,
                    "zone": None,
                    "event_id": None,
                }
            else:
                detector_status = self._zone_detector.get_status()
            zone = detector_status["zone"]
            safety_status = {
                "zone": asdict(zone) if zone is not None else None,
                "zone_state": detector_status["state"],
                "people_in_zone": self._people_in_zone,
                "active_event_id": detector_status["event_id"],
                "enter_elapsed": round(self._enter_elapsed, 3),
                "exit_elapsed": round(self._exit_elapsed, 3),
                "alarm_delivery_error": (
                    self._alarm_controller.get_last_error()
                    if self._alarm_controller is not None
                    else ""
                ),
            }
        status.update(safety_status)
        return status

    def save_zone(self, zone: NormalizedZone) -> dict[str, float]:
        """Persist a zone before applying it to the in-memory detector."""
        repository, detector = self._require_safety_storage()
        with self._safety_lock:
            repository.save_zone(zone)
            detector.set_zone(zone)
            return asdict(zone)

    def delete_zone(self) -> None:
        """Persist zone deletion and safely close an active event."""
        repository, detector = self._require_safety_storage()
        with self._safety_lock:
            repository.delete_zone()
            event_id = detector.clear_zone()
            self._reset_safety_observation()
            if event_id is None:
                return
            try:
                repository.close_event(event_id, "zone_deleted")
            finally:
                if self._alarm_controller is not None:
                    self._alarm_controller.set_alarm(False, event_id=event_id)

    def list_events(self, limit: int = 50) -> list[dict]:
        if self._event_repository is None:
            raise RuntimeError("视觉事件存储未配置")
        return self._event_repository.list_events(limit)

    def acknowledge_event(self, event_id: int) -> dict:
        """Persist acknowledgment, silence detector state, then enqueue off."""
        repository, detector = self._require_safety_storage()
        with self._safety_lock:
            event = repository.acknowledge_event(event_id)
            transitioned = detector.acknowledge(event_id)
            if transitioned and self._alarm_controller is not None:
                self._alarm_controller.set_alarm(False, event_id=event_id)
            return event

    def initialize_safety(self) -> None:
        """Recover persisted safety state before vision processing starts."""
        if self._event_repository is not None:
            self._event_repository.initialize()
            zone = self._event_repository.get_zone()
            if self._zone_detector is not None:
                with self._safety_lock:
                    self._zone_detector.clear_zone()
                    self._reset_safety_observation()
                    if zone is not None:
                        self._zone_detector.set_zone(zone)
            self._event_repository.recover_open_events("server_restart")
        if self._alarm_controller is not None:
            self._alarm_controller.start()
            self._alarm_controller.set_alarm(False, event_id=None, force=True)

    def shutdown_safety(self) -> None:
        """Stop frames, close the current event, force off, then stop delivery."""
        self.stop(timeout=3.0)
        event_id = None
        close_error = ""
        with self._safety_lock:
            if self._zone_detector is not None:
                event_id = self._zone_detector.get_status()["event_id"]
            if event_id is not None and self._event_repository is not None:
                try:
                    self._event_repository.close_event(event_id, "server_shutdown")
                except Exception as exc:  # Shutdown must still force alarm-off.
                    close_error = str(exc) or exc.__class__.__name__
            if self._alarm_controller is not None:
                self._alarm_controller.set_alarm(
                    False,
                    event_id=event_id,
                    force=True,
                )

        if close_error:
            with self._lock:
                self._last_error = close_error
        if self._alarm_controller is not None:
            self._alarm_controller.wait_idle(timeout=3.0)
            self._alarm_controller.stop(timeout=0.0)

    def get_latest_jpeg(self) -> bytes | None:
        with self._lock:
            return self._latest_jpeg

    def iter_mjpeg(self) -> Iterator[bytes]:
        """等待新画面并按MJPEG格式持续输出，供StreamingResponse使用。"""
        last_sequence = -1
        while not self._stop_event.is_set():
            with self._frame_ready:
                self._frame_ready.wait_for(
                    lambda: (
                        self._frame_sequence != last_sequence
                        or self._stop_event.is_set()
                    ),
                    timeout=1.0,
                )
                if self._stop_event.is_set():
                    break
                jpeg = self._latest_jpeg
                last_sequence = self._frame_sequence

            if jpeg is not None:
                yield build_mjpeg_chunk(jpeg)

    def save_snapshot(self, directory: str) -> dict[str, Any]:
        jpeg = self.get_latest_jpeg()
        if jpeg is None:
            return {
                "ok": False,
                "filename": "",
                "path": "",
                "error": "视觉服务尚无可用画面",
            }

        os.makedirs(directory, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"vision_{timestamp}.jpg"
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "wb") as file:
                file.write(jpeg)
        except OSError as exc:
            return {
                "ok": False,
                "filename": "",
                "path": "",
                "error": f"保存视觉截图失败：{exc}",
            }

        return {
            "ok": True,
            "filename": filename,
            "path": filepath,
            "error": "",
        }

    def _coordinate_zone_update(self, update: ZoneUpdate, jpeg: bytes) -> str:
        """Apply local event side effects; alarm calls only enqueue delivery."""
        self._people_in_zone = update.people_in_zone
        error = ""

        if update.alarm_started:
            filename, snapshot_error = self._write_event_snapshot(jpeg)
            event_id = None
            if self._event_repository is None:
                error = "视觉事件存储未配置"
            else:
                try:
                    event_id = self._event_repository.create_event(
                        filename,
                        update.max_people,
                    )
                    if self._zone_detector is not None:
                        self._zone_detector.bind_event(event_id)
                    self._persisted_max_people = update.max_people
                except Exception as exc:  # Keep detection and hardware alarm alive.
                    error = str(exc) or exc.__class__.__name__
                    event_id = None
                if event_id is not None and snapshot_error:
                    try:
                        self._event_repository.record_error(
                            event_id,
                            snapshot_error,
                        )
                    except Exception as exc:
                        error = str(exc) or exc.__class__.__name__
            if snapshot_error:
                error = error or snapshot_error
            if self._alarm_controller is not None:
                self._alarm_controller.set_alarm(True, event_id=event_id)
            return error

        active_event_id = update.event_id
        if self._zone_detector is not None:
            active_event_id = self._zone_detector.get_status()["event_id"]

        if (
            update.state in (ZoneState.ALARM_ACTIVE, ZoneState.ALARM_SILENCED)
            and active_event_id is not None
            and update.max_people > self._persisted_max_people
            and self._event_repository is not None
        ):
            try:
                self._event_repository.update_max_people(
                    active_event_id,
                    update.max_people,
                )
                self._persisted_max_people = update.max_people
            except Exception as exc:
                error = str(exc) or exc.__class__.__name__

        if update.alarm_cleared:
            cleared_event_id = update.event_id
            try:
                if cleared_event_id is not None and self._event_repository is not None:
                    self._event_repository.close_event(
                        cleared_event_id,
                        "person_left",
                    )
            except Exception as exc:
                error = str(exc) or exc.__class__.__name__
            finally:
                self._persisted_max_people = 0
                if self._alarm_controller is not None:
                    self._alarm_controller.set_alarm(
                        False,
                        event_id=cleared_event_id,
                    )
        return error

    def _write_event_snapshot(self, jpeg: bytes) -> tuple[str, str]:
        if not self._event_snapshot_dir:
            return "", "保存视觉告警截图失败：未配置截图目录"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"vision_event_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(self._event_snapshot_dir, filename)
        try:
            os.makedirs(self._event_snapshot_dir, exist_ok=True)
            with open(filepath, "wb") as file:
                file.write(jpeg)
        except OSError as exc:
            return "", f"保存视觉告警截图失败：{exc}"
        return filename, ""

    def _update_safety_timers(
        self,
        previous_state: str,
        update: ZoneUpdate,
    ) -> None:
        now = self._safety_clock()
        if update.state == ZoneState.ENTER_PENDING:
            if (
                previous_state != ZoneState.ENTER_PENDING.value
                or self._enter_started_at is None
            ):
                self._enter_started_at = now
            self._enter_elapsed = max(0.0, now - self._enter_started_at)
        else:
            self._enter_started_at = None
            self._enter_elapsed = 0.0

        if (
            update.state in (ZoneState.ALARM_ACTIVE, ZoneState.ALARM_SILENCED)
            and update.people_in_zone == 0
        ):
            if self._exit_started_at is None:
                self._exit_started_at = now
            self._exit_elapsed = max(0.0, now - self._exit_started_at)
        else:
            self._exit_started_at = None
            self._exit_elapsed = 0.0

    def _reset_safety_observation(self) -> None:
        self._people_in_zone = 0
        self._persisted_max_people = 0
        self._enter_started_at = None
        self._exit_started_at = None
        self._enter_elapsed = 0.0
        self._exit_elapsed = 0.0

    def _require_safety_storage(self) -> tuple[EventRepository, ZoneDetector]:
        if self._event_repository is None:
            raise RuntimeError("视觉事件存储未配置")
        if self._zone_detector is None:
            raise RuntimeError("危险区域检测器未配置")
        return self._event_repository, self._zone_detector

    def _run(self) -> None:
        capture = None
        with self._lock:
            self._running = True

        try:
            model = self._model_factory(self.settings.model_name)
            with self._lock:
                self._model_loaded = True

            while not self._stop_event.is_set():
                try:
                    capture = self._capture_factory()
                    if capture is None or not capture.isOpened():
                        raise RuntimeError(
                            f"无法打开摄像头索引 {self.settings.camera_index}"
                        )

                    with self._lock:
                        self._camera_online = True
                        self._last_error = ""

                    frame_number = 0
                    while not self._stop_event.is_set():
                        ok, frame = capture.read()
                        if not ok or frame is None:
                            raise RuntimeError("摄像头读取画面失败")

                        frame_number += 1
                        if (frame_number - 1) % self.settings.frame_skip != 0:
                            continue
                        self.process_frame(model, frame)
                except Exception as exc:  # noqa: BLE001
                    with self._lock:
                        self._camera_online = False
                        self._last_error = str(exc)
                    if self._stop_event.wait(self.settings.reconnect_delay):
                        break
                finally:
                    if capture is not None:
                        capture.release()
                        capture = None
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._model_loaded = False
                self._last_error = f"YOLO模型加载失败：{exc}"
        finally:
            if capture is not None:
                capture.release()
            with self._frame_ready:
                self._running = False
                self._camera_online = False
                self._frame_ready.notify_all()
