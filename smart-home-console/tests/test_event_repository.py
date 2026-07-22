"""Persistence behavior for danger-zone events."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime

from event_repository import EventClosedError, EventNotFoundError, EventRepository
from zone_detector import NormalizedZone


class EventRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "vision_events.db")
        self.repo = EventRepository(self.db_path)
        self.repo.initialize()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_zone_round_trip_survives_new_repository_instance(self):
        first = EventRepository(self.db_path)
        first.initialize()
        first.save_zone(NormalizedZone(0.1, 0.2, 0.3, 0.4))

        second = EventRepository(self.db_path)
        second.initialize()

        self.assertEqual(second.get_zone(), NormalizedZone(0.1, 0.2, 0.3, 0.4))

    def test_initialize_creates_missing_database_parent_directory(self):
        nested_path = os.path.join(self.temp_dir.name, "data", "vision_events.db")

        EventRepository(nested_path).initialize()

        self.assertTrue(os.path.exists(nested_path))

    def test_deleting_zone_removes_saved_zone(self):
        self.repo.save_zone(NormalizedZone(0.1, 0.2, 0.3, 0.4))

        self.repo.delete_zone()

        self.assertIsNone(self.repo.get_zone())

    def test_event_lifecycle_and_delivery_fields(self):
        event_id = self.repo.create_event("event.jpg", 1)
        self.repo.update_max_people(event_id, 3)
        acknowledged = self.repo.acknowledge_event(event_id)
        self.repo.mark_delivery(event_id, "vision_alarm_on", True, "")
        closed = self.repo.close_event(event_id, "person_left")

        self.assertIsNotNone(acknowledged["acknowledged_at"])
        self.assertEqual(closed["max_people"], 3)
        self.assertEqual(closed["close_reason"], "person_left")
        self.assertTrue(closed["alarm_on_delivered"])

    def test_recovery_closes_only_open_events(self):
        open_id = self.repo.create_event("open.jpg", 1)
        closed_id = self.repo.create_event("closed.jpg", 1)
        self.repo.close_event(closed_id, "person_left")

        recovered = self.repo.recover_open_events("server_restart")

        self.assertEqual(recovered, [open_id])
        self.assertEqual(self.repo.get_event(open_id)["close_reason"], "server_restart")

    def test_list_events_orders_newest_first_and_enforces_bounds(self):
        first_id = self.repo.create_event("first.jpg", 1)
        second_id = self.repo.create_event("second.jpg", 2)

        self.assertEqual(
            [event["id"] for event in self.repo.list_events()],
            [second_id, first_id],
        )
        with self.assertRaises(ValueError):
            self.repo.list_events(0)
        with self.assertRaises(ValueError):
            self.repo.list_events(201)

    def test_list_events_default_and_maximum_limits(self):
        for index in range(205):
            self.repo.create_event(f"{index}.jpg", 1)

        self.assertEqual(len(self.repo.list_events()), 50)
        self.assertEqual(len(self.repo.list_events(200)), 200)

    def test_missing_event_operations_raise_not_found_error(self):
        for operation in (
            lambda: self.repo.get_event(999),
            lambda: self.repo.update_max_people(999, 2),
            lambda: self.repo.acknowledge_event(999),
            lambda: self.repo.close_event(999, "person_left"),
            lambda: self.repo.mark_delivery(999, "vision_alarm_on", True, ""),
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(EventNotFoundError):
                    operation()

    def test_acknowledging_closed_event_raises_conflict(self):
        event_id = self.repo.create_event("event.jpg", 1)
        self.repo.close_event(event_id, "person_left")

        with self.assertRaises(EventClosedError):
            self.repo.acknowledge_event(event_id)

    def test_acknowledgment_is_idempotent(self):
        event_id = self.repo.create_event("event.jpg", 1)

        first = self.repo.acknowledge_event(event_id)
        second = self.repo.acknowledge_event(event_id)

        self.assertEqual(second["acknowledged_at"], first["acknowledged_at"])

    def test_delivery_failure_stores_final_error_text(self):
        event_id = self.repo.create_event("", 1)

        delivered = self.repo.mark_delivery(
            event_id, "vision_alarm_off", False, "broker unavailable"
        )

        self.assertFalse(delivered["alarm_off_delivered"])
        self.assertEqual(delivered["last_error"], "broker unavailable")
        self.assertEqual(delivered["snapshot_filename"], "")

    def test_create_event_accepts_empty_and_basename_snapshot_filenames(self):
        empty_id = self.repo.create_event("", 1)
        filename_id = self.repo.create_event("event.jpg", 1)

        self.assertEqual(self.repo.get_event(empty_id)["snapshot_filename"], "")
        self.assertEqual(
            self.repo.get_event(filename_id)["snapshot_filename"], "event.jpg"
        )

    def test_create_event_rejects_non_basename_snapshot_filenames(self):
        for filename in (
            "/tmp/event.jpg",
            "nested/event.jpg",
            "nested\\event.jpg",
            ".",
            "..",
        ):
            with self.subTest(filename=filename):
                with self.assertRaises(ValueError):
                    self.repo.create_event(filename, 1)
                self.assertEqual(self.repo.list_events(), [])

    def test_event_timestamps_are_timezone_aware_utc_iso_strings(self):
        event_id = self.repo.create_event("event.jpg", 1)
        event = self.repo.close_event(event_id, "person_left")

        for field in ("started_at", "ended_at"):
            timestamp = datetime.fromisoformat(event[field])
            self.assertIsNotNone(timestamp.tzinfo)
            self.assertEqual(timestamp.utcoffset().total_seconds(), 0)


if __name__ == "__main__":
    unittest.main()
