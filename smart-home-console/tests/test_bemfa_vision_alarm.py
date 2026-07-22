import unittest

from bemfa_api import parse_env_message


class BemfaVisionAlarmParserTests(unittest.TestCase):
    def test_parse_vision_alarm_on(self) -> None:
        parsed = parse_env_message('{"vision_alarm":1}')

        self.assertEqual(parsed["vision_alarm"], 1)

    def test_parse_vision_alarm_off(self) -> None:
        parsed = parse_env_message('{"vision_alarm":0}')

        self.assertEqual(parsed["vision_alarm"], 0)


if __name__ == "__main__":
    unittest.main()
