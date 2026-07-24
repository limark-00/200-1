# -*- coding: utf-8 -*-
"""LLM 服务 — 百炼 qwen-plus（对话）+ qwen-vl-plus（识图）。"""

from __future__ import annotations

import json
from typing import Any, Iterator

import bemfa_api
import config
from deepseek_client import HunyuanClient

# 智能家居助手系统提示词
SYSTEM_PROMPT = """你是一个智能家居AI助手，运行在实验室环境安全监测平台上。

你的功能：
1. 回答关于智能家居、传感器、物联网的问题
2. 分析当前传感器数据（温度、湿度、气体值），给出环境建议
3. 帮助用户理解设备状态和控制命令

当前系统信息：
- 通信平台：巴法云 IoT
- 开发板：HiSpark Hi3861
- 传感器：AHT20（温湿度）+ MQ-2（气体）
- 后端：FastAPI
- 视觉监控：YOLO 人员检测

回复规则：
- 用中文回答，简洁友好
- 如果用户问传感器数据，告诉用户需要调用 /api/env 接口获取实时数据
- 如果用户想控制设备，提示可用的命令：alarm_on、alarm_off 等
- 不要编造传感器数值，建议用户查看控制台面板
- 对于技术问题，可以解释原理但不要过于冗长
"""

_client: HunyuanClient | None = None


def _get_client() -> HunyuanClient | None:
    """延迟初始化大模型客户端（优先百炼，fallback 混元）。"""
    global _client
    if _client is not None:
        return _client
    api_key = getattr(config, "DASHSCOPE_API_KEY", "") or getattr(config, "HUNYUAN_API_KEY", "")
    if not api_key:
        return None
    _client = HunyuanClient(
        api_key=api_key,
        base_url=getattr(config, "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model=getattr(config, "DASHSCOPE_MODEL", "qwen-plus"),
        vision_model=getattr(config, "DASHSCOPE_VISION_MODEL", "qwen-vl-plus"),
    )
    return _client


def chat(
    user_message: str,
    history: list[dict[str, str]] | None = None,
    sensor_data: dict[str, Any] | None = None,
    stream: bool = False,
) -> dict[str, Any]:
    """与混元对话。

    Args:
        user_message: 用户输入
        history: 历史对话 [{"role": "user/assistant", "content": "..."}]
        sensor_data: 当前传感器数据（可选，自动注入系统提示）
        stream: 是否流式输出，此时 reply 为生成器

    Returns:
        {"ok": True, "reply": "...", "usage": {...}}
        或 {"ok": False, "error": "..."}
    """
    client = _get_client()
    if client is None:
        return {"ok": False, "error": "未配置 DASHSCOPE_API_KEY 或 HUNYUAN_API_KEY，请在环境变量中设置"}

    # 构建消息列表
    system_msg = SYSTEM_PROMPT

    # 如果有传感器数据，注入到系统提示中
    if sensor_data:
        sensor_text = f"\n\n当前实时传感器数据：\n{json.dumps(sensor_data, ensure_ascii=False, indent=2)}"
        system_msg += sensor_text

    # 注入最近告警事件，方便 AI 回答截图相关问题
    events = get_recent_events(10)
    if events:
        events_text = f"\n\n最近告警事件（最新10条）：\n{json.dumps(events, ensure_ascii=False, indent=2)}"
        events_text += "\n截图存储在 static/vision_events/ 目录，可通过 /vision-events/{filename} 查看。"
        system_msg += events_text

    messages = [{"role": "system", "content": system_msg}]

    # 添加历史对话
    if history:
        messages.extend(history[-20:])  # 最多保留最近 20 条

    # 添加当前用户消息
    messages.append({"role": "user", "content": user_message})

    result = client.chat(messages, temperature=0.7, max_tokens=2048, stream=stream)

    if "error" in result:
        return {"ok": False, "error": result["error"]}

    return {
        "ok": True,
        "reply": result["reply"],
        "usage": result.get("usage", {}),
    }


def chat_about_image(
    image_path: str,
    prompt: str = "请描述这张图片的内容",
) -> dict[str, Any]:
    """用混元 vision 模型分析图片。

    Args:
        image_path: 本地图片路径
        prompt: 对图片的提问

    Returns:
        {"ok": True, "reply": "...", "usage": {...}}
        或 {"ok": False, "error": "..."}
    """
    client = _get_client()
    if client is None:
        return {"ok": False, "error": "未配置 DASHSCOPE_API_KEY 或 HUNYUAN_API_KEY，请在环境变量中设置"}

    result = client.chat_with_image(image_path, prompt)
    if "error" in result:
        return {"ok": False, "error": result["error"]}

    return {
        "ok": True,
        "reply": result["reply"],
        "usage": result.get("usage", {}),
    }


def get_current_sensor_data() -> dict[str, Any]:
    """获取当前传感器数据，用于注入对话上下文。"""
    try:
        result = bemfa_api.get_topic_msg(config.ENV_PUB_TOPIC)
        if result.get("ok"):
            data = bemfa_api.parse_env_message(result.get("msg", ""))
            return {
                "temperature": data.get("temperature"),
                "humidity": data.get("humidity"),
                "gas": data.get("gas"),
                "raw_message": result.get("msg", ""),
            }
    except Exception:
        pass
    return {}


def get_recent_events(limit: int = 10) -> list[dict[str, Any]]:
    """从 SQLite 读取最近告警事件摘要。"""
    import sqlite3

    db_path = getattr(config, "VISION_DB_PATH", "data/vision_events.db")
    events = []
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT id, started_at, ended_at, snapshot_filename, max_people, close_reason, acknowledged_at "
            "FROM vision_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        for row in rows:
            events.append({
                "事件ID": row[0],
                "开始时间": row[1],
                "结束时间": row[2] or "进行中",
                "截图文件": row[3],
                "最多人数": row[4],
                "结束原因": row[5] or "未知",
                "已确认": "是" if row[6] else "否",
            })
    except Exception as e:
        return [{"error": str(e)}]
    return events
