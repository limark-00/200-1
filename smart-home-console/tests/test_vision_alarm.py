"""Queued delivery behavior for vision alarm commands."""

from __future__ import annotations

import threading
import time
import unittest

from vision_alarm import AlarmTask, VisionAlarmController


def make_controller(sender, sleeper=lambda _seconds: None, delivery_callback=None):
    return VisionAlarmController(
        sender,
        delivery_callback=delivery_callback or (lambda *_args: None),
        sleeper=sleeper,
    )


class VisionAlarmControllerTests(unittest.TestCase):
    def test_same_target_is_not_enqueued_twice(self):
        sent = []
        controller = make_controller(
            lambda command: sent.append(command) or {"ok": True}
        )

        controller.start()
        self.assertTrue(controller.set_alarm(True, event_id=3))
        self.assertFalse(controller.set_alarm(True, event_id=3))
        self.assertTrue(controller.wait_idle(1.0))
        controller.stop()

        self.assertEqual(sent, ["vision_alarm_on"])

    def test_commands_are_delivered_in_enqueue_order(self):
        sent = []
        controller = make_controller(
            lambda command: sent.append(command) or {"ok": True}
        )

        controller.start()
        controller.set_alarm(True, event_id=7)
        controller.set_alarm(False, event_id=7)
        self.assertTrue(controller.wait_idle(1.0))
        controller.stop()

        self.assertEqual(sent, ["vision_alarm_on", "vision_alarm_off"])

    def test_failure_retries_at_fixed_delays(self):
        attempts = []
        sleeps = []

        def sender(command):
            attempts.append(command)
            return {"ok": False, "error": "network down"}

        task = AlarmTask(True, 9, False)
        controller = make_controller(sender, sleeper=sleeps.append)

        controller._deliver(task)

        self.assertEqual(attempts, ["vision_alarm_on"] * 3)
        self.assertEqual(sleeps, [2.0, 5.0])

    def test_forced_off_bypasses_initial_dedupe(self):
        sent = []
        controller = make_controller(
            lambda command: sent.append(command) or {"ok": True}
        )

        controller.start()
        self.assertTrue(controller.set_alarm(False, event_id=None, force=True))
        self.assertTrue(controller.wait_idle(1.0))
        controller.stop()

        self.assertEqual(sent, ["vision_alarm_off"])

    def test_delivery_callback_receives_final_success_result(self):
        deliveries = []
        controller = make_controller(
            lambda _command: {"ok": True},
            delivery_callback=lambda *args: deliveries.append(args),
        )

        controller._deliver(AlarmTask(True, 14))

        self.assertEqual(deliveries, [(14, "vision_alarm_on", True, "")])

    def test_delivery_callback_receives_final_failure_after_retries(self):
        deliveries = []
        controller = make_controller(
            lambda _command: {"ok": False, "error": "broker unavailable"},
            delivery_callback=lambda *args: deliveries.append(args),
        )

        controller._deliver(AlarmTask(False, 14))

        self.assertEqual(
            deliveries,
            [(14, "vision_alarm_off", False, "视觉告警指令发送失败")],
        )

    def test_delivery_callback_failure_is_surfaced_without_replacing_sender_error(self):
        def failing_callback(*_args):
            raise OSError("database unavailable")

        controller = make_controller(
            lambda _command: {"ok": True},
            delivery_callback=failing_callback,
        )

        controller._deliver(AlarmTask(True, 14))

        self.assertEqual(controller.get_last_error(), "")
        self.assertEqual(
            controller.get_callback_error(),
            "视觉告警投递记录暂未保存",
        )

    def test_later_success_clears_last_error(self):
        responses = iter(
            [
                {"ok": False, "error": "offline"},
                {"ok": False, "error": "offline"},
                {"ok": False, "error": "offline"},
                {"ok": True},
            ]
        )
        controller = make_controller(lambda _command: next(responses))

        controller._deliver(AlarmTask(True, 1))
        self.assertEqual(controller.get_last_error(), "视觉告警指令发送失败")
        controller._deliver(AlarmTask(False, 1))

        self.assertEqual(controller.get_last_error(), "")

    def test_sender_exception_is_sanitized_before_state_and_callback(self):
        secret = "secret-bemfa-uid"
        deliveries = []

        def sender(_command):
            raise RuntimeError(
                f"https://example.test/send?uid={secret}&topic=env"
            )

        controller = make_controller(
            sender,
            delivery_callback=lambda *args: deliveries.append(args),
        )

        controller._deliver(AlarmTask(True, 3))

        self.assertEqual(controller.get_last_error(), "视觉告警指令发送失败")
        self.assertEqual(deliveries[-1][-1], "视觉告警指令发送失败")
        self.assertNotIn(secret, str(deliveries))
        self.assertNotIn("?uid=", str(deliveries))

    def test_wait_idle_times_out_while_sender_is_blocked(self):
        started = threading.Event()
        release = threading.Event()

        def sender(_command):
            started.set()
            release.wait(1.0)
            return {"ok": True}

        controller = make_controller(sender)
        controller.start()
        controller.set_alarm(True)
        self.assertTrue(started.wait(1.0))
        self.assertFalse(controller.wait_idle(0.01))
        release.set()
        self.assertTrue(controller.wait_idle(1.0))
        controller.stop()

    def test_stop_waits_for_worker_and_prevents_future_delivery(self):
        sent = []
        controller = make_controller(
            lambda command: sent.append(command) or {"ok": True}
        )

        controller.start()
        controller.set_alarm(True)
        self.assertTrue(controller.wait_idle(1.0))
        controller.stop()
        controller.set_alarm(False)
        time.sleep(0.02)

        self.assertEqual(sent, ["vision_alarm_on"])

    def test_superseded_on_retry_is_cancelled_so_off_is_prompt(self):
        sent = []
        first_on_attempt = threading.Event()
        off_delivered = threading.Event()

        def sender(command):
            sent.append(command)
            if command == "vision_alarm_on":
                first_on_attempt.set()
                return {"ok": False, "error": "offline"}
            off_delivered.set()
            return {"ok": True}

        controller = VisionAlarmController(
            sender,
            delivery_callback=lambda *_args: None,
        )
        controller.start()
        controller.set_alarm(True, event_id=7)
        self.assertTrue(first_on_attempt.wait(1.0))

        controller.set_alarm(False, event_id=7, force=True)

        self.assertTrue(off_delivered.wait(0.5))
        self.assertTrue(controller.wait_idle(1.0))
        controller.stop()
        self.assertEqual(sent, ["vision_alarm_on", "vision_alarm_off"])

    def test_controller_can_restart_and_accept_same_target_again(self):
        sent = []
        controller = make_controller(
            lambda command: sent.append(command) or {"ok": True}
        )

        self.assertTrue(controller.start())
        self.assertTrue(controller.set_alarm(True, event_id=1))
        self.assertTrue(controller.wait_idle(1.0))
        controller.stop()

        self.assertTrue(controller.start())
        self.assertTrue(controller.set_alarm(True, event_id=2))
        self.assertTrue(controller.wait_idle(1.0))
        controller.stop()

        self.assertEqual(sent, ["vision_alarm_on", "vision_alarm_on"])


if __name__ == "__main__":
    unittest.main()
