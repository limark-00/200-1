# -*- coding: utf-8 -*-
"""项目全局配置：巴法云 env004 真实设备。"""

import os

# 建议通过环境变量设置：
# Windows PowerShell：
# $env:BEMFA_UID="你的巴法云私钥"
BEMFA_UID = os.getenv("BEMFA_UID", "").strip()

# 1=MQTT主题，3=TCP主题。env004若在MQTT设备云创建，保持1。
BEMFA_TYPE = int(os.getenv("BEMFA_TYPE", "1"))

# 下行控制主题：主机向该主题发送alarm_on/alarm_off，开发板订阅该主题。
ENV_TOPIC = os.getenv("BEMFA_ENV_TOPIC", "env004").strip()

# 上行数据主题：开发板向该主题发布温湿度和蜂鸣器状态，主机读取该主题。
ENV_PUB_TOPIC = os.getenv(
    "BEMFA_ENV_PUB_TOPIC",
    f"{ENV_TOPIC}/up",
).strip()

# 温湿度、气体等环境数据都从上行主题读取。
TEMP_HUM_TOPIC = ENV_PUB_TOPIC
GAS_TOPIC = ENV_PUB_TOPIC

# 兼容原网页代码。
LIGHT_TOPIC = ENV_PUB_TOPIC
PIR_TOPIC = ENV_TOPIC
TRAFFIC_LIGHT_TOPIC = ENV_TOPIC
BUZZER_TOPIC = ENV_TOPIC
RGB_TOPIC = ENV_TOPIC

# False=真实巴法云，True=模拟模式
MOCK_MODE = False

# 当前环境监测项目不启动PIR自动抓拍。
ENABLE_PIR_POLLER = False
PIR_POLL_INTERVAL = 3
CAPTURE_COOLDOWN = 10
CAPTURE_DIR = "static/captures"
CAPTURE_LIST_LIMIT = 20

# YOLO视觉监控（Ubuntu主机 + 罗技USB摄像头）
# 首阶段仅做人员检测与实时标注画面，不包含危险区域和NFC联动。
VISION_ENABLED = os.getenv("VISION_ENABLED", "1").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}
VISION_CAMERA_INDEX = int(os.getenv("VISION_CAMERA_INDEX", "0"))
VISION_MODEL = os.getenv("VISION_MODEL", "yolo11n.pt").strip()
VISION_CONFIDENCE = float(os.getenv("VISION_CONFIDENCE", "0.40"))
VISION_IMAGE_SIZE = int(os.getenv("VISION_IMAGE_SIZE", "640"))
VISION_FRAME_SKIP = max(1, int(os.getenv("VISION_FRAME_SKIP", "2")))
VISION_FRAME_WIDTH = int(os.getenv("VISION_FRAME_WIDTH", "640"))
VISION_FRAME_HEIGHT = int(os.getenv("VISION_FRAME_HEIGHT", "480"))
VISION_JPEG_QUALITY = int(os.getenv("VISION_JPEG_QUALITY", "80"))
VISION_RECONNECT_DELAY = float(os.getenv("VISION_RECONNECT_DELAY", "2.0"))
VISION_DB_PATH = os.getenv(
    "VISION_DB_PATH",
    "data/vision_events.db",
).strip()
VISION_EVENT_DIR = os.getenv(
    "VISION_EVENT_DIR",
    "static/vision_events",
).strip()
VISION_ENTER_SECONDS = float(os.getenv("VISION_ENTER_SECONDS", "2.0"))
VISION_EXIT_SECONDS = float(os.getenv("VISION_EXIT_SECONDS", "3.0"))

APP_HOST = "0.0.0.0"
APP_PORT = 5001

# 保留旧项目兼容字段
FLASK_HOST = APP_HOST
FLASK_PORT = APP_PORT
FLASK_DEBUG = True
