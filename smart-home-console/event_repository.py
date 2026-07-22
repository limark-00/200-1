"""SQLite persistence for the configured danger zone and alarm events."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from zone_detector import NormalizedZone


class EventNotFoundError(LookupError):
    """Raised when an event identifier does not exist."""


class EventClosedError(RuntimeError):
    """Raised when an operation requires an event that is still open."""


class EventRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path, timeout=3.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=3000")
        return connection

    def initialize(self) -> None:
        connection = self._connect()
        try:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS vision_zone (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    width REAL NOT NULL,
                    height REAL NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vision_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT NULL,
                    snapshot_filename TEXT NOT NULL,
                    max_people INTEGER NOT NULL DEFAULT 1,
                    acknowledged_at TEXT NULL,
                    close_reason TEXT NULL,
                    alarm_on_delivered INTEGER NOT NULL DEFAULT 0,
                    alarm_off_delivered INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT NOT NULL DEFAULT ''
                );
                """
            )
            connection.commit()
        finally:
            connection.close()

    def get_zone(self) -> NormalizedZone | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT x, y, width, height FROM vision_zone WHERE id = 1"
            ).fetchone()
            if row is None:
                return None
            return NormalizedZone(row["x"], row["y"], row["width"], row["height"])
        finally:
            connection.close()

    def save_zone(self, zone: NormalizedZone) -> None:
        if not isinstance(zone, NormalizedZone):
            raise TypeError("zone must be a NormalizedZone")
        connection = self._connect()
        try:
            connection.execute(
                """
                INSERT INTO vision_zone (id, x, y, width, height, enabled, updated_at)
                VALUES (1, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    x = excluded.x,
                    y = excluded.y,
                    width = excluded.width,
                    height = excluded.height,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (zone.x, zone.y, zone.width, zone.height, self._utc_now()),
            )
            connection.commit()
        finally:
            connection.close()

    def delete_zone(self) -> None:
        connection = self._connect()
        try:
            connection.execute("DELETE FROM vision_zone WHERE id = 1")
            connection.commit()
        finally:
            connection.close()

    def create_event(self, snapshot_filename: str, people_count: int) -> int:
        connection = self._connect()
        try:
            cursor = connection.execute(
                """
                INSERT INTO vision_events (started_at, snapshot_filename, max_people)
                VALUES (?, ?, ?)
                """,
                (self._utc_now(), snapshot_filename, people_count),
            )
            connection.commit()
            return cursor.lastrowid
        finally:
            connection.close()

    def get_event(self, event_id: int) -> dict:
        connection = self._connect()
        try:
            return self._fetch_event(connection, event_id)
        finally:
            connection.close()

    def update_max_people(self, event_id: int, people_count: int) -> dict:
        connection = self._connect()
        try:
            self._fetch_event(connection, event_id)
            connection.execute(
                """
                UPDATE vision_events
                SET max_people = MAX(max_people, ?)
                WHERE id = ?
                """,
                (people_count, event_id),
            )
            connection.commit()
            return self._fetch_event(connection, event_id)
        finally:
            connection.close()

    def acknowledge_event(self, event_id: int) -> dict:
        connection = self._connect()
        try:
            event = self._fetch_event(connection, event_id)
            if event["ended_at"] is not None:
                raise EventClosedError(f"event {event_id} is closed")
            if event["acknowledged_at"] is None:
                connection.execute(
                    "UPDATE vision_events SET acknowledged_at = ? WHERE id = ?",
                    (self._utc_now(), event_id),
                )
                connection.commit()
            return self._fetch_event(connection, event_id)
        finally:
            connection.close()

    def close_event(self, event_id: int, close_reason: str) -> dict:
        connection = self._connect()
        try:
            self._fetch_event(connection, event_id)
            connection.execute(
                """
                UPDATE vision_events
                SET ended_at = COALESCE(ended_at, ?),
                    close_reason = COALESCE(close_reason, ?)
                WHERE id = ?
                """,
                (self._utc_now(), close_reason, event_id),
            )
            connection.commit()
            return self._fetch_event(connection, event_id)
        finally:
            connection.close()

    def mark_delivery(
        self, event_id: int, command: str, delivered: bool, error_text: str
    ) -> dict:
        delivery_column = {
            "vision_alarm_on": "alarm_on_delivered",
            "vision_alarm_off": "alarm_off_delivered",
        }.get(command)
        if delivery_column is None:
            raise ValueError(f"unsupported delivery command: {command}")
        connection = self._connect()
        try:
            self._fetch_event(connection, event_id)
            connection.execute(
                f"UPDATE vision_events SET {delivery_column} = ?, last_error = ? WHERE id = ?",
                (int(delivered), error_text, event_id),
            )
            connection.commit()
            return self._fetch_event(connection, event_id)
        finally:
            connection.close()

    def recover_open_events(self, close_reason: str) -> list[int]:
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT id FROM vision_events WHERE ended_at IS NULL ORDER BY id ASC"
            ).fetchall()
            event_ids = [row["id"] for row in rows]
            if event_ids:
                connection.execute(
                    """
                    UPDATE vision_events
                    SET ended_at = ?, close_reason = ?
                    WHERE ended_at IS NULL
                    """,
                    (self._utc_now(), close_reason),
                )
                connection.commit()
            return event_ids
        finally:
            connection.close()

    def list_events(self, limit: int = 50) -> list[dict]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT * FROM vision_events ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [self._row_to_dict(row) for row in rows]
        finally:
            connection.close()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _fetch_event(self, connection: sqlite3.Connection, event_id: int) -> dict:
        row = connection.execute(
            "SELECT * FROM vision_events WHERE id = ?", (event_id,)
        ).fetchone()
        if row is None:
            raise EventNotFoundError(f"event {event_id} was not found")
        return self._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        event = dict(row)
        event["alarm_on_delivered"] = bool(event["alarm_on_delivered"])
        event["alarm_off_delivered"] = bool(event["alarm_off_delivered"])
        return event
