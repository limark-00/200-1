import unittest
from pathlib import Path


MQTT_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "applications/sample/wifi-iot/app/day08_mqtt_new/mqtt.c"
).read_text(encoding="utf-8")


def function_body(signature: str) -> str:
    start = MQTT_SOURCE.index(signature)
    brace = MQTT_SOURCE.index("{", start)
    depth = 0
    for index in range(brace, len(MQTT_SOURCE)):
        if MQTT_SOURCE[index] == "{":
            depth += 1
        elif MQTT_SOURCE[index] == "}":
            depth -= 1
            if depth == 0:
                return MQTT_SOURCE[brace : index + 1]
    raise AssertionError(f"unterminated function: {signature}")


class Day08MqttAlarmLockingContractTests(unittest.TestCase):
    def test_mutex_is_ready_before_mqtt_worker_and_in_uart_fallback(self) -> None:
        self.assertIn('#include "cmsis_os2.h"', MQTT_SOURCE)

        mqtt_loop = MQTT_SOURCE[
            MQTT_SOURCE.index("int Day08_MqttLoop(void)") :
        ]
        self.assertLess(
            mqtt_loop.index("Day08_AlarmMutexInit()"),
            mqtt_loop.index("MQTTStartTask"),
        )

        fallback = function_body("void Day08_UartFallbackLoop(void)")
        self.assertIn("Day08_AlarmMutexInit()", fallback)

    def test_state_transitions_hold_lock_through_buzzer_update(self) -> None:
        humidity = function_body(
            "Day08_UpdateHumidityAlarm(float humidity)"
        )
        command = function_body(
            "static void Day08_MessageArrived(MessageData *data)"
        )

        for body, transition in (
            (humidity, "Day08Alarm_UpdateHumidity"),
            (command, "Day08Alarm_ApplyCommand"),
        ):
            self.assertIn("Day08_AlarmLock()", body)
            self.assertIn("Day08_AlarmUnlock()", body)
            lock = body.index("Day08_AlarmLock()")
            update = body.index(transition)
            decision = body.index("Day08Alarm_ShouldBuzz")
            hardware = body.index("Day08_SetBuzzer")
            unlock = body.index("Day08_AlarmUnlock()")
            self.assertLess(lock, update)
            self.assertLess(update, decision)
            self.assertLess(decision, hardware)
            self.assertLess(hardware, unlock)

    def test_telemetry_copies_one_locked_snapshot_before_snprintf(self) -> None:
        telemetry = function_body(
            "int Day08_BuildTelemetryJson(char *buf, unsigned int len,"
        )
        self.assertIn("Day08_AlarmLock()", telemetry)
        self.assertIn("Day08_AlarmUnlock()", telemetry)
        lock = telemetry.index("Day08_AlarmLock()")
        buzzer = telemetry.index("buzzer_is_on = g_buzzer_is_on")
        manual = telemetry.index(
            "manual_alarm_on = g_alarm_state.manual_alarm_on"
        )
        silence = telemetry.index(
            "humidity_silenced = g_alarm_state.humidity_silenced"
        )
        vision = telemetry.index(
            "vision_alarm_on = g_alarm_state.vision_alarm_on"
        )
        unlock = telemetry.index("Day08_AlarmUnlock()")
        render = telemetry.index("snprintf")

        self.assertLess(lock, buzzer)
        self.assertLess(buzzer, manual)
        self.assertLess(manual, silence)
        self.assertLess(silence, vision)
        self.assertLess(vision, unlock)
        self.assertLess(unlock, render)


if __name__ == "__main__":
    unittest.main()
