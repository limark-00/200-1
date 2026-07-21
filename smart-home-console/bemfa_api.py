# -*- coding: utf-8 -*-
"""巴法云HTTP接口封装，适配env004上下行主题。"""

from __future__ import annotations

import json
import random
import threading
from typing import Any

import requests

import config

GET_MSG_URL = "https://apis.bemfa.com/va/getmsg"
POST_MSG_URL = "https://apis.bemfa.com/va/postJsonMsg"
LEGACY_SEND_MSG_URL = "https://apis.bemfa.com/va/sendMessage"

_mock_lock = threading.Lock()
_mock_store: dict[str, str] = {
    config.ENV_PUB_TOPIC: json.dumps(
        {
            "group_id": "env004",
            "device_id": "hi3861",
            "temperature": 25.6,
            "humidity": 60.0,
            "gas": None,
            "buzzer": 0,
            "humidity_threshold": 40.0,
            "manual_alarm": 0,
            "humidity_silenced": 0,
            "state": "online",
            "source": "aht20",
        },
        ensure_ascii=False,
    )
}


def _is_mock() -> bool:
    return bool(getattr(config, "MOCK_MODE", False))


def get_topic_msg(topic: str) -> dict[str, Any]:
    topic = str(topic or "").strip()
    if not topic:
        return {
            "ok": False,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": None,
            "error": "topic为空",
        }

    if _is_mock():
        if topic == config.ENV_PUB_TOPIC:
            with _mock_lock:
                obj = {
                    "group_id": "env004",
                    "device_id": "hi3861",
                    "temperature": round(24 + random.uniform(0, 3), 2),
                    "humidity": round(35 + random.uniform(0, 15), 2),
                    "gas": None,
                    "buzzer": 0,
                    "humidity_threshold": 40.0,
                    "manual_alarm": 0,
                    "humidity_silenced": 0,
                    "state": "online",
                    "source": "aht20",
                }
                msg = json.dumps(obj, ensure_ascii=False)
                _mock_store[topic] = msg
        else:
            with _mock_lock:
                msg = _mock_store.get(topic, "")

        return {
            "ok": True,
            "topic": topic,
            "msg": msg,
            "time": "mock",
            "raw": {"mock": True},
            "error": "",
        }

    if not config.BEMFA_UID:
        return {
            "ok": False,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": None,
            "error": "BEMFA_UID未配置",
        }

    params = {
        "uid": config.BEMFA_UID,
        "topic": topic,
        "type": config.BEMFA_TYPE,
        "num": 1,
    }

    try:
        resp = requests.get(GET_MSG_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return {
            "ok": False,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": None,
            "error": f"网络请求失败：{exc}",
        }
    except ValueError as exc:
        return {
            "ok": False,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": resp.text[:500],
            "error": f"响应不是JSON：{exc}",
        }

    if data.get("code") != 0:
        return {
            "ok": False,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": data,
            "error": data.get("message")
            or data.get("msg")
            or "巴法云返回错误",
        }

    items = data.get("data") or []
    if not items:
        return {
            "ok": True,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": data,
            "error": "",
        }

    latest = items[0]
    return {
        "ok": True,
        "topic": topic,
        "msg": str(latest.get("msg", "")),
        "time": str(latest.get("time", "")),
        "raw": data,
        "error": "",
    }


def send_msg(topic: str, msg: str) -> dict[str, Any]:
    """向控制主题推送消息。开发板订阅env004时，topic应为env004。"""
    topic = str(topic or "").strip()
    message = str(msg or "").strip()

    if not topic:
        return {"ok": False, "error": "topic为空", "raw": None}
    if not message:
        return {"ok": False, "error": "msg为空", "raw": None}
    if not config.BEMFA_UID and not _is_mock():
        return {"ok": False, "error": "BEMFA_UID未配置", "raw": None}

    if _is_mock():
        with _mock_lock:
            _mock_store[topic] = message
        return {
            "ok": True,
            "error": "",
            "raw": {
                "mock": True,
                "topic": topic,
                "msg": message,
            },
        }

    payload = {
        "uid": config.BEMFA_UID,
        "topic": topic,
        "type": config.BEMFA_TYPE,
        "msg": message,
    }

    try:
        resp = requests.post(POST_MSG_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        try:
            resp = requests.get(
                LEGACY_SEND_MSG_URL,
                params=payload,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as fallback_exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": (
                    f"下发失败：{exc}；"
                    f"兼容接口也失败：{fallback_exc}"
                ),
                "raw": None,
            }

    if data.get("code") != 0:
        return {
            "ok": False,
            "error": data.get("message")
            or data.get("msg")
            or "下发失败",
            "raw": data,
        }

    return {"ok": True, "error": "", "raw": data}


def parse_env_message(msg: str) -> dict[str, Any]:
    """兼容开发板JSON和旧版逗号分隔环境数据格式。"""
    text = (msg or "").strip()
    result: dict[str, Any] = {
        "raw": text,
        "group_id": None,
        "device_id": None,
        "temperature": None,
        "humidity": None,
        "gas": None,
        "buzzer": None,
        "humidity_threshold": None,
        "manual_alarm": None,
        "humidity_silenced": None,
        "state": None,
        "source": None,
    }

    if not text:
        return result

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            result["group_id"] = obj.get("group_id")
            result["device_id"] = obj.get("device_id")
            result["temperature"] = obj.get(
                "temperature",
                obj.get("temp"),
            )
            result["humidity"] = obj.get(
                "humidity",
                obj.get("hum"),
            )
            result["gas"] = obj.get(
                "gas",
                obj.get("mq2", obj.get("gas_value")),
            )
            result["buzzer"] = obj.get(
                "buzzer",
                obj.get("buzzer_state"),
            )
            result["humidity_threshold"] = obj.get(
                "humidity_threshold",
                obj.get("threshold"),
            )
            result["manual_alarm"] = obj.get(
                "manual_alarm",
                obj.get("manualAlarm"),
            )
            result["humidity_silenced"] = obj.get(
                "humidity_silenced",
                obj.get("humiditySilenced"),
            )
            result["state"] = obj.get("state")
            result["source"] = obj.get("source")
            return result
    except (json.JSONDecodeError, TypeError):
        pass

    normalized = text.replace("，", ",").replace(";", ",")
    parts = [
        item.strip()
        for item in normalized.split(",")
        if item.strip()
    ]

    keys = ("temperature", "humidity", "gas")
    for key, value in zip(keys, parts):
        try:
            result[key] = float(value)
        except ValueError:
            result[key] = value

    return result


def is_pir_triggered(msg: str) -> bool:
    text = (msg or "").strip().lower()
    return text in {
        "1",
        "on",
        "true",
        "yes",
        "触发",
        "有人",
        "detected",
        "alarm",
    }


def set_mock_pir(triggered: bool) -> None:
    with _mock_lock:
        _mock_store[config.PIR_TOPIC] = "1" if triggered else "0"