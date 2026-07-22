import unittest
from unittest.mock import Mock, patch

import requests

import bemfa_api
from bemfa_api import get_topic_msg, parse_env_message, send_msg


class BemfaVisionAlarmParserTests(unittest.TestCase):
    def test_parse_vision_alarm_on(self) -> None:
        parsed = parse_env_message('{"vision_alarm":1}')

        self.assertEqual(parsed["vision_alarm"], 1)

    def test_parse_vision_alarm_off(self) -> None:
        parsed = parse_env_message('{"vision_alarm":0}')

        self.assertEqual(parsed["vision_alarm"], 0)

    def test_get_error_never_exposes_uid_or_query_string(self) -> None:
        secret = "secret-bemfa-uid"
        error = requests.RequestException(
            f"request failed for https://example.test/get?uid={secret}&topic=x"
        )

        with (
            patch.object(bemfa_api.config, "MOCK_MODE", False),
            patch.object(bemfa_api.config, "BEMFA_UID", secret),
            patch.object(bemfa_api.requests, "get", side_effect=error),
        ):
            result = get_topic_msg("env/up")

        self.assertEqual(result["error"], "巴法云网络请求失败")
        self.assertNotIn(secret, str(result))
        self.assertNotIn("?uid=", str(result))

    def test_send_error_never_exposes_uid_or_fallback_url(self) -> None:
        secret = "secret-bemfa-uid"
        error = requests.RequestException(
            f"request failed for https://example.test/send?uid={secret}"
        )

        with (
            patch.object(bemfa_api.config, "MOCK_MODE", False),
            patch.object(bemfa_api.config, "BEMFA_UID", secret),
            patch.object(bemfa_api.requests, "post", side_effect=error),
            patch.object(bemfa_api.requests, "get", side_effect=error),
        ):
            result = send_msg("env", "vision_alarm_on")

        self.assertEqual(result["error"], "巴法云指令下发失败")
        self.assertNotIn(secret, str(result))
        self.assertNotIn("?uid=", str(result))

    def test_send_uses_one_total_timeout_budget_across_fallback(self) -> None:
        fallback_response = Mock()
        fallback_response.json.return_value = {"code": 0}

        with (
            patch.object(bemfa_api.config, "MOCK_MODE", False),
            patch.object(bemfa_api.config, "BEMFA_UID", "configured-secret"),
            patch.object(
                bemfa_api.requests,
                "post",
                side_effect=requests.RequestException("primary failed"),
            ) as post,
            patch.object(
                bemfa_api.requests,
                "get",
                return_value=fallback_response,
            ) as fallback,
        ):
            result = send_msg(
                "env",
                "vision_alarm_off",
                timeout=0.5,
            )

        self.assertTrue(result["ok"])
        self.assertGreater(post.call_args.kwargs["timeout"], 0.0)
        self.assertLessEqual(post.call_args.kwargs["timeout"], 0.5)
        self.assertGreater(fallback.call_args.kwargs["timeout"], 0.0)
        self.assertLessEqual(fallback.call_args.kwargs["timeout"], 0.5)


if __name__ == "__main__":
    unittest.main()
