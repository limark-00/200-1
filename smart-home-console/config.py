# -*- coding: utf-8 -*-
"""项目全局配置：巴法云 env004 真实设备。"""

import os

# 建议通过环境变量设置：
# Windows PowerShell：
# $env:BEMFA_UID="你的巴法云私钥"
BEMFA_UID = os.getenv("BEMFA_UID", "554419557d4567eb2f683d752c6aad23").strip()

# 1=MQTT主题，3=TCP主题。env004若在MQTT设备云创建，保持1。
BEMFA_TYPE = int(os.getenv("BEMFA_TYPE", "1"))

# 下行控制主题：主机向该主题发送alarm_on/alarm_off，开发板订阅该主题。
ENV_TOPIC = os.getenv("BEMFA_ENV_TOPIC", "env004").strip()

# 上行数据主题：开发板向该主题发布温湿度和蜂鸣器状态，主机读取该主题。
ENV_PUB_TOPIC = os.getenv(
    "BEMFA_ENV_PUB_TOPIC",
    ENV_TOPIC,
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
).strip() or "static/vision_events"
VISION_ENTER_SECONDS = float(os.getenv("VISION_ENTER_SECONDS", "2.0"))
VISION_EXIT_SECONDS = float(os.getenv("VISION_EXIT_SECONDS", "3.0"))

APP_HOST = "0.0.0.0"
APP_PORT = 5001

# 巴法云 MQTT 配置
MQTT_BROKER = os.getenv("MQTT_BROKER", "bemfa.com").strip()
MQTT_PORT = int(os.getenv("MQTT_PORT", "9501"))

# 混元大模型配置（OpenAI 兼容格式）
# Hy3-preview: 输入 1.2元/百万tokens, 输出 4元/百万tokens, 免费100万tokens
HUNYUAN_API_KEY = os.getenv("HUNYUAN_API_KEY", "").strip()
HUNYUAN_BASE_URL = os.getenv("HUNYUAN_BASE_URL", "https://tokenhub-intl.tencentmaas.com/v1").strip()
HUNYUAN_MODEL = os.getenv("HUNYUAN_MODEL", "hy3-preview").strip()
HUNYUAN_VISION_MODEL = os.getenv("HUNYUAN_VISION_MODEL", "hunyuan-vision").strip()
HUNYUAN_TEMPERATURE = float(os.getenv("HUNYUAN_TEMPERATURE", "0.7"))
HUNYUAN_MAX_TOKENS = int(os.getenv("HUNYUAN_MAX_TOKENS", "2048"))

# 混元文生图配置
# HY-Image-3.0: 0.2元/张, 免费50张
HUNYUAN_IMAGE_API_KEY = os.getenv("HUNYUAN_IMAGE_API_KEY", "").strip()
HUNYUAN_IMAGE_BASE_URL = os.getenv("HUNYUAN_IMAGE_BASE_URL", "https://tokenhub.tencentmaas.com/v1").strip()
HUNYUAN_IMAGE_MODEL = os.getenv("HUNYUAN_IMAGE_MODEL", "hy-image-v3.0").strip()

# 保留旧项目兼容字段
FLASK_HOST = APP_HOST
FLASK_PORT = APP_PORT
FLASK_DEBUG = True
