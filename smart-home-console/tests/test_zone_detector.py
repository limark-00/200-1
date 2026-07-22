import math
import unittest

from zone_detector import NormalizedZone, ZoneDetector, ZoneState


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def armed_detector(clock):
    detector = ZoneDetector(2.0, 3.0, clock=clock)
    detector.set_zone(NormalizedZone(0.2, 0.2, 0.4, 0.5))
    return detector


def start_alarm(detector, clock):
    detector.update([(0.3, 0.4)])
    clock.advance(2.0)
    update = detector.update([(0.3, 0.4)])
    assert update.alarm_started


class ZoneDetectorTests(unittest.TestCase):
    def test_alarm_starts_after_two_continuous_seconds(self):
        clock = FakeClock()
        detector = ZoneDetector(2.0, 3.0, clock=clock)
        detector.set_zone(NormalizedZone(0.2, 0.2, 0.4, 0.5))

        first = detector.update([(0.3, 0.4)])
        clock.advance(1.9)
        second = detector.update([(0.3, 0.4)])
        clock.advance(0.1)
        third = detector.update([(0.3, 0.4)])

        self.assertEqual(first.state, ZoneState.ENTER_PENDING)
        self.assertFalse(second.alarm_started)
        self.assertTrue(third.alarm_started)
        self.assertEqual(third.state, ZoneState.ALARM_ACTIVE)

    def test_brief_exit_does_not_clear_active_event(self):
        clock = FakeClock()
        detector = armed_detector(clock)
        start_alarm(detector, clock)
        detector.bind_event(17)

        clock.advance(2.9)
        pending = detector.update([])
        detector.update([(0.3, 0.4)])

        self.assertFalse(pending.alarm_cleared)
        self.assertEqual(detector.get_status()["state"], "alarm_active")

    def test_three_second_exit_clears_and_rearms(self):
        clock = FakeClock()
        detector = armed_detector(clock)
        start_alarm(detector, clock)
        detector.bind_event(17)

        detector.update([])
        clock.advance(3.0)
        cleared = detector.update([])

        self.assertTrue(cleared.alarm_cleared)
        self.assertEqual(cleared.event_id, 17)
        self.assertEqual(cleared.state, ZoneState.ARMED)

    def test_acknowledged_event_stays_silent_until_exit(self):
        clock = FakeClock()
        detector = armed_detector(clock)
        start_alarm(detector, clock)
        detector.bind_event(17)

        self.assertTrue(detector.acknowledge(17))
        self.assertEqual(
            detector.update([(0.3, 0.4)]).state, ZoneState.ALARM_SILENCED
        )

    def test_zone_boundaries_are_included(self):
        zone = NormalizedZone(0.2, 0.2, 0.4, 0.5)

        self.assertTrue(zone.contains((0.2, 0.2)))
        self.assertTrue(zone.contains((0.6, 0.7)))
        self.assertFalse(zone.contains((0.60001, 0.7)))

    def test_invalid_normalized_rectangles_are_rejected(self):
        invalid_zones = (
            (math.nan, 0.2, 0.4, 0.5),
            (0.2, math.inf, 0.4, 0.5),
            (-0.01, 0.2, 0.4, 0.5),
            (0.2, 0.2, 0.019, 0.5),
            (0.7, 0.2, 0.4, 0.5),
        )

        for values in invalid_zones:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    NormalizedZone(*values)

    def test_entry_timer_resets_when_zone_becomes_empty(self):
        clock = FakeClock()
        detector = armed_detector(clock)

        detector.update([(0.3, 0.4)])
        clock.advance(1.9)
        detector.update([])
        clock.advance(0.1)
        restarted = detector.update([(0.3, 0.4)])

        self.assertEqual(restarted.state, ZoneState.ENTER_PENDING)
        self.assertFalse(restarted.alarm_started)

    def test_max_people_tracks_peak_for_active_event(self):
        clock = FakeClock()
        detector = armed_detector(clock)

        detector.update([(0.3, 0.4), (0.4, 0.5), (0.9, 0.9)])
        clock.advance(2.0)
        started = detector.update([(0.3, 0.4), (0.4, 0.5)])
        detector.update([(0.3, 0.4)])

        self.assertEqual(started.people_in_zone, 2)
        self.assertEqual(started.max_people, 2)
        self.assertEqual(detector.get_status()["max_people"], 2)

    def test_clearing_active_zone_returns_active_event_id_and_disables(self):
        clock = FakeClock()
        detector = armed_detector(clock)
        start_alarm(detector, clock)
        detector.bind_event(17)

        self.assertEqual(detector.clear_zone(), 17)
        status = detector.get_status()
        self.assertEqual(status["state"], "disabled")
        self.assertIsNone(status["zone"])

    def test_acknowledgment_requires_matching_active_event_id(self):
        clock = FakeClock()
        detector = armed_detector(clock)
        start_alarm(detector, clock)
        detector.bind_event(17)

        self.assertFalse(detector.acknowledge(99))
        self.assertEqual(detector.get_status()["state"], "alarm_active")

    def test_rebinding_a_different_event_id_keeps_original_event(self):
        clock = FakeClock()
        detector = armed_detector(clock)
        start_alarm(detector, clock)
        detector.bind_event(17)

        self.assertFalse(detector.bind_event(99))
        self.assertEqual(detector.get_status()["event_id"], 17)

    def test_replacing_zone_while_active_preserves_active_event(self):
        clock = FakeClock()
        detector = armed_detector(clock)
        start_alarm(detector, clock)
        detector.bind_event(17)
        replacement = NormalizedZone(0.5, 0.1, 0.3, 0.4)

        detector.set_zone(replacement)

        status = detector.get_status()
        self.assertEqual(status["state"], "alarm_active")
        self.assertEqual(status["event_id"], 17)
        self.assertEqual(status["zone"], replacement)


if __name__ == "__main__":
    unittest.main()
