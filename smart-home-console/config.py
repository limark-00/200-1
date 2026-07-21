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

APP_HOST = "0.0.0.0"
APP_PORT = 5001

# 保留旧项目兼容字段
FLASK_HOST = APP_HOST
FLASK_PORT = APP_PORT
FLASK_DEBUG = True