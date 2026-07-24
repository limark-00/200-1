# -*- coding: utf-8 -*-
"""巴法云HTTP接口 + MQTT订阅封装，适配env004上下行主题。"""

from __future__ import annotations

import json
import math
import random
import threading
import time
from typing import Any

import paho.mqtt.client as mqtt
import requests

import config

GET_MSG_URL = "https://apis.bemfa.com/va/getmsg"
POST_MSG_URL = "https://apis.bemfa.com/va/postJsonMsg"
LEGACY_SEND_MSG_URL = "https://apis.bemfa.com/va/sendMessage"

# ---------- Mock 模式存储 ----------
_mock_lock = threading.Lock()
_mock_store: dict[str, str] = {
    config.ENV_PUB_TOPIC: json.dumps(
        {
            "group_id": "env004",
            "device_id": "hi3861",
            "temperature": 25.6,
            "humidity": 60.0,
            "smoke": 146,
            "smoke_alarm": 0,
            "buzzer": 0,
            "humidity_threshold": 40.0,
            "manual_alarm": 0,
            "humidity_silenced": 0,
            "vision_alarm": 0,
            "state": "online",
            "source": "mq2",
        },
        ensure_ascii=False,
    )
}

# ---------- MQTT 订阅缓存 ----------
_mqtt_lock = threading.Lock()
_mqtt_store: dict[str, str] = {}  # topic -> latest message string
_mqtt_client: mqtt.Client | None = None
_mqtt_connected = False


def _on_connect(client: mqtt.Client, userdata: Any, flags: dict, reason_code: Any, properties: Any = None) -> None:
    global _mqtt_connected
    rc = int(reason_code) if reason_code is not None else -1
    if rc == 0:
        _mqtt_connected = True
        # 同时订阅上行和下行主题，确保收到设备上报的传感器数据
        topics = set()
        topics.add(config.ENV_PUB_TOPIC)      # env004/up（设备发布传感器数据）
        topics.add(config.ENV_TOPIC)           # env004（兼容设备直接发布到主主题）
        for topic in topics:
            client.subscribe(topic, qos=1)
            print(f"[MQTT] 已订阅主题: {topic}")
        print("[MQTT] 已连接巴法云")
    else:
        _mqtt_connected = False
        print(f"[MQTT] 连接失败，返回码: {rc}")


def _on_disconnect(client: mqtt.Client, userdata: Any, flags: Any = None, reason_code: Any = None, properties: Any = None) -> None:
    global _mqtt_connected
    _mqtt_connected = False
    rc = int(reason_code) if reason_code is not None else -1
    if rc != 0:
        print(f"[MQTT] 连接断开 (rc={rc})，将自动重连")


def _on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    topic = msg.topic
    payload = msg.payload.decode("utf-8", errors="replace")
    with _mqtt_lock:
        _mqtt_store[topic] = payload
    print(f"[MQTT] 收到 {topic}: {payload[:120]}")


def mqtt_start() -> None:
    """启动 MQTT 客户端，连接巴法云并订阅上行主题。"""
    global _mqtt_client
    if _mqtt_client is not None:
        return

    client = mqtt.Client(
        client_id=config.BEMFA_UID,
        protocol=mqtt.MQTTv311,
    )
    # 巴法云 MQTT 认证方式：只用 Client ID（=UID），不填 username/password
    client.username_pw_set(None, None)
    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_message = _on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        client.connect(config.MQTT_BROKER, config.MQTT_PORT, keepalive=60)
        client.loop_start()
        _mqtt_client = client
        print(f"[MQTT] 正在连接 {config.MQTT_BROKER}:{config.MQTT_PORT} ...")
    except Exception as exc:
        print(f"[MQTT] 连接异常: {exc}")


def mqtt_stop() -> None:
    """停止 MQTT 客户端。"""
    global _mqtt_client, _mqtt_connected
    if _mqtt_client is not None:
        try:
            _mqtt_client.loop_stop()
            _mqtt_client.disconnect()
        except Exception:
            pass
        _mqtt_client = None
        _mqtt_connected = False
        print("[MQTT] 已断开连接")


def mqtt_is_connected() -> bool:
    return _mqtt_connected


def _mqtt_get(topic: str) -> str | None:
    """从 MQTT 缓存中读取主题最新消息，无缓存返回 None。"""
    with _mqtt_lock:
        return _mqtt_store.get(topic)


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

    # ---- Mock 模式 ----
    if _is_mock():
        if topic == config.ENV_PUB_TOPIC:
            with _mock_lock:
                obj = {
                    "group_id": "env004",
                    "device_id": "hi3861",
                    "temperature": round(24 + random.uniform(0, 3), 2),
                    "humidity": round(35 + random.uniform(0, 15), 2),
                    "smoke": round(100 + random.uniform(0, 200), 0),
                    "smoke_alarm": 0,
                    "buzzer": 0,
                    "humidity_threshold": 40.0,
                    "manual_alarm": 0,
                    "humidity_silenced": 0,
                    "vision_alarm": 0,
                    "state": "online",
                    "source": "mq2",
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

    # ---- 真实模式：优先从 MQTT 缓存读取 ----
    mqtt_msg = _mqtt_get(topic)
    if mqtt_msg is not None:
        return {
            "ok": True,
            "topic": topic,
            "msg": mqtt_msg,
            "time": "mqtt",
            "raw": {"source": "mqtt"},
            "error": "",
        }

    # ---- MQTT 无缓存，回退 HTTP API ----
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
    except requests.RequestException:
        return {
            "ok": False,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": None,
            "error": "巴法云网络请求失败",
        }
    except ValueError:
        return {
            "ok": False,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": None,
            "error": "巴法云响应格式错误",
        }

    if data.get("code") != 0:
        return {
            "ok": False,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": None,
            "error": "巴法云返回错误",
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


def send_msg(
    topic: str,
    msg: str,
    *,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """向控制主题推送消息，主接口和兼容回退共享一个时间预算。"""
    topic = str(topic or "").strip()
    message = str(msg or "").strip()
    timeout = float(timeout)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")

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
    deadline = time.monotonic() + timeout

    try:
        resp = requests.post(
            POST_MSG_URL,
            json=payload,
            timeout=max(0.001, deadline - time.monotonic()),
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {
                "ok": False,
                "error": "巴法云指令下发失败",
                "raw": None,
            }
        try:
            resp = requests.get(
                LEGACY_SEND_MSG_URL,
                params=payload,
                timeout=remaining,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:  # noqa: BLE001
            return {
                "ok": False,
                "error": "巴法云指令下发失败",
                "raw": None,
            }

    if data.get("code") != 0:
        return {
            "ok": False,
            "error": "巴法云指令下发失败",
            "raw": None,
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
        "vision_alarm": None,
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
                obj.get("smoke",
                obj.get("mq2",
                obj.get("gas_value",
                obj.get("smoke_value")))),
            )
            result["smoke_alarm"] = obj.get("smoke_alarm")
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
            result["vision_alarm"] = obj.get(
                "vision_alarm",
                obj.get("visionAlarm"),
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
