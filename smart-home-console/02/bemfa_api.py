# -*- coding: utf-8 -*-
"""巴法云HTTP接口封装，适配env004。"""
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
_mock_store: dict[str, str] = {config.ENV_TOPIC: "25.6,60,320"}


def _is_mock() -> bool:
    return bool(getattr(config, "MOCK_MODE", False))


def get_topic_msg(topic: str) -> dict[str, Any]:
    if not topic:
        return {"ok": False, "topic": topic, "msg": "", "time": "", "raw": None, "error": "topic为空"}

    if _is_mock():
        with _mock_lock:
            temp = round(24 + random.uniform(0, 3), 1)
            hum = round(55 + random.uniform(0, 10), 1)
            gas = int(280 + random.uniform(0, 80))
            msg = f"{temp},{hum},{gas}"
            _mock_store[topic] = msg
        return {"ok": True, "topic": topic, "msg": msg, "time": "mock", "raw": {"mock": True}, "error": ""}

    if not config.BEMFA_UID:
        return {"ok": False, "topic": topic, "msg": "", "time": "", "raw": None, "error": "BEMFA_UID未配置"}

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
        return {"ok": False, "topic": topic, "msg": "", "time": "", "raw": None, "error": f"网络请求失败：{exc}"}
    except ValueError as exc:
        return {"ok": False, "topic": topic, "msg": "", "time": "", "raw": resp.text[:500], "error": f"响应不是JSON：{exc}"}

    if data.get("code") != 0:
        return {
            "ok": False, "topic": topic, "msg": "", "time": "", "raw": data,
            "error": data.get("message") or data.get("msg") or "巴法云返回错误",
        }

    items = data.get("data") or []
    if not items:
        return {"ok": True, "topic": topic, "msg": "", "time": "", "raw": data, "error": ""}

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
    """向主题推送消息。设备订阅env004时，HTTP API直接填env004即可。"""
    if not topic:
        return {"ok": False, "error": "topic为空", "raw": None}
    if msg is None or str(msg) == "":
        return {"ok": False, "error": "msg为空", "raw": None}

    if _is_mock():
        with _mock_lock:
            _mock_store[topic] = str(msg)
        return {"ok": True, "error": "", "raw": {"mock": True, "topic": topic, "msg": msg}}

    payload = {
        "uid": config.BEMFA_UID,
        "topic": topic,
        "type": config.BEMFA_TYPE,
        "msg": str(msg),
    }
    try:
        resp = requests.post(POST_MSG_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        # 兼容部分旧账号/旧接口环境
        try:
            resp = requests.get(LEGACY_SEND_MSG_URL, params=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as fallback_exc:  # noqa: BLE001
            return {"ok": False, "error": f"下发失败：{exc}；兼容接口也失败：{fallback_exc}", "raw": None}

    if data.get("code") != 0:
        return {"ok": False, "error": data.get("message") or data.get("msg") or "下发失败", "raw": data}
    return {"ok": True, "error": "", "raw": data}


def parse_env_message(msg: str) -> dict[str, Any]:
    """兼容JSON和逗号分隔两类环境数据格式。"""
    text = (msg or "").strip()
    result: dict[str, Any] = {
        "raw": text,
        "temperature": None,
        "humidity": None,
        "gas": None,
    }
    if not text:
        return result

    # JSON示例：{"temperature":26.5,"humidity":58.2,"gas":423}
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            result["temperature"] = obj.get("temperature", obj.get("temp"))
            result["humidity"] = obj.get("humidity", obj.get("hum"))
            result["gas"] = obj.get("gas", obj.get("mq2", obj.get("gas_value")))
            return result
    except (json.JSONDecodeError, TypeError):
        pass

    # CSV示例：26.5,58.2,423；也兼容中文逗号和空格
    normalized = text.replace("，", ",").replace(";", ",")
    parts = [item.strip() for item in normalized.split(",") if item.strip()]
    keys = ("temperature", "humidity", "gas")
    for key, value in zip(keys, parts):
        try:
            result[key] = float(value)
        except ValueError:
            result[key] = value
    return result


def is_pir_triggered(msg: str) -> bool:
    text = (msg or "").strip().lower()
    return text in {"1", "on", "true", "yes", "触发", "有人", "detected", "alarm"}


def set_mock_pir(triggered: bool) -> None:
    with _mock_lock:
        _mock_store[config.PIR_TOPIC] = "1" if triggered else "0"
