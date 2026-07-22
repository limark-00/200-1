"""Thread-safe, time-driven danger-zone alarm state machine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from threading import RLock
from time import monotonic
from typing import Callable, Sequence


class ZoneState(str, Enum):
    DISABLED = "disabled"
    ARMED = "armed"
    ENTER_PENDING = "enter_pending"
    ALARM_ACTIVE = "alarm_active"
    ALARM_SILENCED = "alarm_silenced"


@dataclass(frozen=True)
class NormalizedZone:
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self):
        values = (self.x, self.y, self.width, self.height)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("区域坐标必须是有限数值")
        if self.x < 0 or self.y < 0 or self.width < 0.02 or self.height < 0.02:
            raise ValueError("区域坐标越界或尺寸过小")
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("区域超出画面范围")

    def contains(self, point):
        px, py = point
        return (
            self.x <= px <= self.x + self.width
            and self.y <= py <= self.y + self.height
        )


@dataclass(frozen=True)
class ZoneUpdate:
    state: ZoneState
    people_in_zone: int
    max_people: int
    alarm_started: bool = False
    alarm_cleared: bool = False
    event_id: int | None = None


@dataclass(frozen=True)
class _DetectorCheckpoint:
    zone: NormalizedZone | None
    state: ZoneState
    enter_started_at: float | None
    exit_started_at: float | None
    max_people: int
    active_event_id: int | None


class ZoneDetector:
    def __init__(
        self,
        enter_delay_seconds: float,
        exit_delay_seconds: float,
        *,
        clock: Callable[[], float] = monotonic,
    ):
        if enter_delay_seconds < 0 or exit_delay_seconds < 0:
            raise ValueError("延迟时间不能为负数")
        self._enter_delay_seconds = enter_delay_seconds
        self._exit_delay_seconds = exit_delay_seconds
        self._clock = clock
        self._lock = RLock()
        self._zone: NormalizedZone | None = None
        self._state = ZoneState.DISABLED
        self._enter_started_at: float | None = None
        self._exit_started_at: float | None = None
        self._max_people = 0
        self._active_event_id: int | None = None

    def set_zone(self, zone: NormalizedZone) -> None:
        if not isinstance(zone, NormalizedZone):
            raise TypeError("zone 必须是 NormalizedZone")
        with self._lock:
            self._zone = zone
            if self._state not in (ZoneState.ALARM_ACTIVE, ZoneState.ALARM_SILENCED):
                self._state = ZoneState.ARMED
                self._reset_event_tracking()

    def clear_zone(self) -> int | None:
        with self._lock:
            event_id = self._active_event_id
            self._zone = None
            self._state = ZoneState.DISABLED
            self._reset_event_tracking()
            return event_id

    def update(self, foot_points: Sequence[tuple[float, float]]) -> ZoneUpdate:
        with self._lock:
            people_in_zone = self._count_people(foot_points)
            now = self._clock()

            if self._state == ZoneState.DISABLED:
                return self._update(people_in_zone)

            if self._state == ZoneState.ARMED:
                if people_in_zone:
                    self._state = ZoneState.ENTER_PENDING
                    self._enter_started_at = now
                    self._max_people = people_in_zone
                return self._update(people_in_zone)

            if self._state == ZoneState.ENTER_PENDING:
                if not people_in_zone:
                    self._state = ZoneState.ARMED
                    self._enter_started_at = None
                    self._max_people = 0
                    return self._update(people_in_zone)
                self._max_people = max(self._max_people, people_in_zone)
                if now - self._enter_started_at >= self._enter_delay_seconds:
                    self._state = ZoneState.ALARM_ACTIVE
                    self._enter_started_at = None
                    return self._update(people_in_zone, alarm_started=True)
                return self._update(people_in_zone)

            self._max_people = max(self._max_people, people_in_zone)
            if people_in_zone:
                self._exit_started_at = None
                return self._update(people_in_zone)
            if self._exit_started_at is None:
                self._exit_started_at = now
            if now - self._exit_started_at >= self._exit_delay_seconds:
                event_id = self._active_event_id
                self._state = ZoneState.ARMED
                self._reset_event_tracking()
                return self._update(people_in_zone, alarm_cleared=True, event_id=event_id)
            return self._update(people_in_zone)

    def observation_gap(self) -> ZoneUpdate:
        """Break continuity without treating an unknown frame as vacancy.

        A missing/failed observation invalidates pending entry time.  During an
        active or silenced alarm it only clears a vacancy timer, preserving the
        event identity until real empty frames are observed again.
        """
        with self._lock:
            if self._state == ZoneState.ENTER_PENDING:
                self._state = ZoneState.ARMED
                self._enter_started_at = None
                self._max_people = 0
            elif self._state in (
                ZoneState.ALARM_ACTIVE,
                ZoneState.ALARM_SILENCED,
            ):
                self._exit_started_at = None
            return self._update(0)

    def bind_event(self, event_id: int) -> bool:
        with self._lock:
            if (
                self._state in (ZoneState.ALARM_ACTIVE, ZoneState.ALARM_SILENCED)
                and self._active_event_id is None
            ):
                self._active_event_id = event_id
                return True
            return self._active_event_id == event_id

    def acknowledge(self, event_id: int) -> bool:
        with self._lock:
            if (
                self._state == ZoneState.ALARM_ACTIVE
                and self._active_event_id == event_id
            ):
                self._state = ZoneState.ALARM_SILENCED
                return True
            return False

    def get_status(self) -> dict:
        with self._lock:
            return {
                "state": self._state.value,
                "zone": self._zone,
                "max_people": self._max_people,
                "event_id": self._active_event_id,
            }

    def _checkpoint(self) -> _DetectorCheckpoint:
        """Capture state for VisionService's lifecycle commit barrier."""
        with self._lock:
            return _DetectorCheckpoint(
                zone=self._zone,
                state=self._state,
                enter_started_at=self._enter_started_at,
                exit_started_at=self._exit_started_at,
                max_people=self._max_people,
                active_event_id=self._active_event_id,
            )

    def _restore(self, checkpoint: _DetectorCheckpoint) -> None:
        """Restore an update that lost the lifecycle commit race."""
        if not isinstance(checkpoint, _DetectorCheckpoint):
            raise TypeError("checkpoint 类型无效")
        with self._lock:
            self._zone = checkpoint.zone
            self._state = checkpoint.state
            self._enter_started_at = checkpoint.enter_started_at
            self._exit_started_at = checkpoint.exit_started_at
            self._max_people = checkpoint.max_people
            self._active_event_id = checkpoint.active_event_id

    def _count_people(self, foot_points: Sequence[tuple[float, float]]) -> int:
        if self._zone is None:
            return 0
        return sum(1 for point in foot_points if self._zone.contains(point))

    def _update(
        self,
        people_in_zone: int,
        *,
        alarm_started: bool = False,
        alarm_cleared: bool = False,
        event_id: int | None = None,
    ) -> ZoneUpdate:
        return ZoneUpdate(
            state=self._state,
            people_in_zone=people_in_zone,
            max_people=self._max_people,
            alarm_started=alarm_started,
            alarm_cleared=alarm_cleared,
            event_id=event_id,
        )

    def _reset_event_tracking(self) -> None:
        self._enter_started_at = None
        self._exit_started_at = None
        self._max_people = 0
        self._active_event_id = None
