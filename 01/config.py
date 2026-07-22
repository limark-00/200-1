# -*- coding: utf-8 -*-
"""
config.py —— 项目全局配置

【学生注意】
1. 巴法云 uid（私钥）只写在本文件，其他模块通过 `from config import BEMFA_UID` 引用，不要复制粘贴到别处。
2. 下面的 TOPIC 先用占位符。请登录 https://cloud.bemfa.com 控制台，把真实主题名填进来。
3. MOCK_MODE：True = 用模拟数据练界面；False = 走真实巴法云。
   页面上也可以切换模式，切换后会覆盖这里的初始值（重启后仍以本文件为准）。
"""

# ========== 巴法云账号 ==========
# 私钥在控制台「个人中心 / 密钥」可查看，等同于 uid
BEMFA_UID = "c91130ab47dc43cb8e16aeeb76ca8d4a"

# 主题类型：1 = MQTT，3 = TCP（Hi3861 实训套件多数用 MQTT，不对就改成 3）
BEMFA_TYPE = 1

# ========== 主题名占位符（请改成你控制台里的真实主题）==========
TEMP_HUM_TOPIC = "tempHum"          # 温湿度（若设备有；没有可先放着）
LIGHT_TOPIC = "lightSensor"         # 光照（彩灯板光敏电阻）
PIR_TOPIC = "pirSensor"             # 人体红外 PIR
TRAFFIC_LIGHT_TOPIC = "trafficLight"  # 交通灯板 LED
BUZZER_TOPIC = "buzzer"             # 有源蜂鸣器
RGB_TOPIC = "rgbLed"                # WS2812 RGB 灯带

# ========== 运行模式 ==========
# True：模拟数据 + 页面「模拟 PIR 触发」按钮可用
# False：查询/下发都走巴法云真实接口
MOCK_MODE = True

# ========== 轮询与抓拍 ==========
# 后台每隔多少秒查询一次 PIR（秒）
PIR_POLL_INTERVAL = 3

# 两次抓拍之间的最短间隔（秒），避免 PIR 一直为“有人”时疯狂连拍
CAPTURE_COOLDOWN = 10

# 抓拍图片保存目录（相对项目根目录）
CAPTURE_DIR = "static/captures"

# 照片墙最多返回多少张
CAPTURE_LIST_LIMIT = 20

# 监听地址：0.0.0.0 表示局域网其他电脑也能访问；本机测可用 127.0.0.1
APP_HOST = "0.0.0.0"
APP_PORT = 5001

# 兼容旧变量名（若别处仍写 FLASK_* 也不会立刻报错）
FLASK_HOST = APP_HOST
FLASK_PORT = APP_PORT
FLASK_DEBUG = True
