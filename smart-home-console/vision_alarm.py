"""Asynchronous, ordered delivery of vision alarm commands."""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class AlarmTask:
    enabled: bool
    event_id: int | None
    force: bool = False


class VisionAlarmController:
    """Serializes alarm delivery so inference never waits on network I/O."""

    RETRY_DELAYS = (0.0, 2.0, 5.0)
    _STOP = object()

    def __init__(
        self,
        sender: Callable[[str], dict],
        *,
        delivery_callback: Callable[[int | None, str, bool, str], None],
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._sender = sender
        self._delivery_callback = delivery_callback
        self._sleeper = sleeper
        self._queue: queue.Queue[AlarmTask | object] = queue.Queue()
        self._lock = threading.Lock()
        self._idle = threading.Condition(self._lock)
        self._thread: threading.Thread | None = None
        self._target_enabled = False
        self._pending = 0
        self._last_error = ""

    def start(self) -> bool:
        """Start one delivery worker; repeated calls leave it unchanged."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return False
            self._thread = threading.Thread(
                target=self._run,
                name="vision-alarm-delivery",
                daemon=True,
            )
            self._thread.start()
        return True

    def set_alarm(self, enabled, event_id=None, force=False):
        """Queue a target-state change without invoking the sender inline."""
        enabled = bool(enabled)
        with self._idle:
            if not force and enabled == self._target_enabled:
                return False
            self._target_enabled = enabled
            self._pending += 1
            self._queue.put(AlarmTask(enabled, event_id, force))
            return True

    def wait_idle(self, timeout: float | None) -> bool:
        """Wait at most *timeout* seconds until every queued task has completed."""
        with self._idle:
            return self._idle.wait_for(lambda: self._pending == 0, timeout=timeout)

    def stop(self, timeout: float = 3.0) -> None:
        """Finish queued work, then stop the worker without blocking indefinitely."""
        with self._lock:
            thread = self._thread
            if thread is None:
                return
            self._queue.put(self._STOP)

        if thread is not threading.current_thread():
            thread.join(timeout=timeout)

        with self._lock:
            if self._thread is thread and not thread.is_alive():
                self._thread = None

    def get_last_error(self) -> str:
        with self._lock:
            return self._last_error

    def _run(self) -> None:
        while True:
            task = self._queue.get()
            try:
                if task is self._STOP:
                    return
                self._deliver(task)
            finally:
                if task is not self._STOP:
                    with self._idle:
                        self._pending -= 1
                        self._idle.notify_all()
                self._queue.task_done()

    def _deliver(self, task: AlarmTask) -> None:
        command = "vision_alarm_on" if task.enabled else "vision_alarm_off"
        delivered = False
        error = ""

        for delay in self.RETRY_DELAYS:
            if delay:
                self._sleeper(delay)
            try:
                result = self._sender(command)
            except Exception as exc:  # Sender is an injected network boundary.
                error = str(exc) or exc.__class__.__name__
                continue

            if result.get("ok", False):
                delivered = True
                error = ""
                break
            error = str(result.get("error") or "alarm command failed")

        with self._lock:
            self._last_error = error

        try:
            self._delivery_callback(task.event_id, command, delivered, error)
        except Exception:
            # Persistence callbacks must not terminate the delivery worker.
            pass
