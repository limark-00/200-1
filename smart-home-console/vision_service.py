# -*- coding: utf-8 -*-
"""单例摄像头与YOLO人员检测服务。"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterator


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


class VisionService:
    """后台持续读取一个摄像头，并共享最新YOLO标注帧。"""

    def __init__(
        self,
        settings: VisionSettings,
        *,
        capture_factory: Callable[[], Any] | None = None,
        model_factory: Callable[[str], Any] | None = None,
        frame_encoder: Callable[[Any, int], bytes] | None = None,
    ) -> None:
        self.settings = settings
        self._capture_factory = capture_factory or (
            lambda: _default_capture_factory(self.settings)
        )
        self._model_factory = model_factory or _default_model_factory
        self._frame_encoder = frame_encoder or _default_frame_encoder

        self._lock = threading.Lock()
        self._frame_ready = threading.Condition(self._lock)
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
            people_count = 0
            annotated = frame

        jpeg = self._frame_encoder(annotated, self.settings.jpeg_quality)
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
            self._last_error = ""
            self._frame_ready.notify_all()

        return jpeg

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            return {
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
