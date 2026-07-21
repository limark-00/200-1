# -*- coding: utf-8 -*-
"""
bemfa_api.py —— 巴法云 HTTP 接口封装

官方文档：https://cloud.bemfa.com/docs/src/api_device.html

常用接口：
- 获取主题最新消息：GET  https://apis.bemfa.com/va/getmsg
- 向主题推送消息  ：GET  https://apis.bemfa.com/va/sendMessage

【学生提示】
本文件负责「怎么访问巴法云」。业务逻辑（什么时候抓拍、怎么解析温湿度）写在 app.py。
MOCK 模式下不会发真实网络请求，方便没带板子时也能跑通界面。
"""

from __future__ import annotations

import random
import threading
from typing import Any

import requests

import config

# 巴法云接口地址（一般不用改）
GET_MSG_URL = "https://apis.bemfa.com/va/getmsg"
SEND_MSG_URL = "https://apis.bemfa.com/va/sendMessage"

# ---------- Mock 内存数据（仅 MOCK_MODE 使用）----------
# 用线程锁，避免后台轮询线程和网页请求同时改数据时出乱子
_mock_lock = threading.Lock()
_mock_store: dict[str, str] = {
    config.TEMP_HUM_TOPIC: "25.6,60",   # 温度,湿度
    config.LIGHT_TOPIC: "320",          # 光照模拟值
    config.PIR_TOPIC: "0",              # 0=无人，1=有人
    config.TRAFFIC_LIGHT_TOPIC: "off",
    config.BUZZER_TOPIC: "off",
    config.RGB_TOPIC: "off",
}


def _is_mock() -> bool:
    """是否处于模拟模式。运行时可被 app 里的开关改写 config.MOCK_MODE。"""
    return bool(getattr(config, "MOCK_MODE", True))


def set_mock_pir(triggered: bool) -> None:
    """
    手动设置 Mock 的 PIR 状态。
    页面点「模拟 PIR 触发」时会调用这里。
    """
    with _mock_lock:
        _mock_store[config.PIR_TOPIC] = "1" if triggered else "0"


def get_mock_snapshot() -> dict[str, str]:
    """复制一份当前 Mock 数据，方便调试查看。"""
    with _mock_lock:
        return dict(_mock_store)


def get_topic_msg(topic: str) -> dict[str, Any]:
    """
    查询某个主题的最新一条消息。

    返回统一格式（真实模式和 Mock 模式一样），方便前端处理：
    {
        "ok": True/False,
        "topic": "...",
        "msg": "消息内容字符串",
        "time": "时间字符串（可能为空）",
        "raw": 原始返回或 mock 标记,
        "error": 出错时的说明
    }
    """
    if not topic:
        return {"ok": False, "topic": topic, "msg": "", "time": "", "raw": None, "error": "topic 为空"}

    # ----- 模拟模式：从内存字典读 -----
    if _is_mock():
        with _mock_lock:
            # 温湿度、光照每次略微抖动一下，看起来更像实时数据
            if topic == config.TEMP_HUM_TOPIC:
                temp = round(24 + random.uniform(0, 3), 1)
                hum = round(55 + random.uniform(0, 10), 0)
                msg = f"{temp},{int(hum)}"
                _mock_store[topic] = msg
            elif topic == config.LIGHT_TOPIC:
                msg = str(int(280 + random.uniform(0, 80)))
                _mock_store[topic] = msg
            else:
                msg = _mock_store.get(topic, "")
        return {
            "ok": True,
            "topic": topic,
            "msg": msg,
            "time": "mock",
            "raw": {"mock": True},
            "error": "",
        }

    # ----- 真实模式：调用巴法云 -----
    params = {
        "uid": config.BEMFA_UID,
        "topic": topic,
        "type": config.BEMFA_TYPE,
        "num": 1,
    }
    try:
        resp = requests.get(GET_MSG_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001  —— 给学生看清错误，统一包一层
        return {
            "ok": False,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": None,
            "error": f"请求失败: {exc}",
        }

    # 巴法云成功时 code == 0，data 是列表
    if data.get("code") != 0:
        return {
            "ok": False,
            "topic": topic,
            "msg": "",
            "time": "",
            "raw": data,
            "error": data.get("message", "巴法云返回错误"),
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
    """
    向指定主题下发一条控制指令。

    参数：
        topic: 主题名，例如交通灯 TRAFFIC_LIGHT_TOPIC
        msg  : 指令内容，例如 "red" / "on" / "off"（需与板端固件约定一致）
    """
    if not topic:
        return {"ok": False, "error": "topic 为空", "raw": None}

    # ----- 模拟模式：只改内存，假装下发成功 -----
    if _is_mock():
        with _mock_lock:
            _mock_store[topic] = str(msg)
        return {"ok": True, "error": "", "raw": {"mock": True, "topic": topic, "msg": msg}}

    params = {
        "uid": config.BEMFA_UID,
        "topic": topic,
        "type": config.BEMFA_TYPE,
        "msg": msg,
    }
    try:
        resp = requests.get(SEND_MSG_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"请求失败: {exc}", "raw": None}

    if data.get("code") != 0:
        return {"ok": False, "error": data.get("message", "下发失败"), "raw": data}

    return {"ok": True, "error": "", "raw": data}


def is_pir_triggered(msg: str) -> bool:
    """
    判断 PIR 消息是否表示「有人 / 触发」。

    板端上传的字符串可能是 "1"、"on"、"触发" 等，这里做宽松匹配。
    如果你的固件用别的约定，只改这一个函数即可。
    """
    text = (msg or "").strip().lower()
    if not text:
        return False
    trigger_words = {"1", "on", "true", "yes", "触发", "有人", "detected", "alarm"}
    return text in trigger_words
