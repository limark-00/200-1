# -*- coding: utf-8 -*-
"""项目全局配置：巴法云 env004 真实设备。"""

import os

# 建议通过环境变量设置：Windows PowerShell：
# $env:BEMFA_UID="你的巴法云私钥"
# 若未设置环境变量，则使用下方默认值。
BEMFA_UID = os.getenv("BEMFA_UID", "554419557d4567eb2f683d752c6aad23").strip()

# 1=MQTT主题，3=TCP主题。env004若在MQTT设备云创建，保持1。
BEMFA_TYPE = int(os.getenv("BEMFA_TYPE", "1"))

# 巴法云主题/设备名
ENV_TOPIC = os.getenv("BEMFA_ENV_TOPIC", "env004").strip()

# 当前项目只有环境监测板，因此温湿度、气体等由同一主题env004上传。
TEMP_HUM_TOPIC = ENV_TOPIC
GAS_TOPIC = ENV_TOPIC

# 为兼容原网页代码，暂时都指向env004；未使用的功能不会影响环境数据读取。
LIGHT_TOPIC = ENV_TOPIC
PIR_TOPIC = ENV_TOPIC
TRAFFIC_LIGHT_TOPIC = ENV_TOPIC
BUZZER_TOPIC = ENV_TOPIC
RGB_TOPIC = ENV_TOPIC

# False=真实巴法云，True=模拟模式
MOCK_MODE = False

# 是否启动原项目中的PIR自动抓拍轮询。
# 环境监测项目不需要PIR，默认关闭，避免把env004环境数据误判为人体触发。
ENABLE_PIR_POLLER = False
PIR_POLL_INTERVAL = 3
CAPTURE_COOLDOWN = 10
CAPTURE_DIR = "static/captures"
CAPTURE_LIST_LIMIT = 20

APP_HOST = "0.0.0.0"
APP_PORT = 5001
FLASK_HOST = APP_HOST
FLASK_PORT = APP_PORT
FLASK_DEBUG = True
