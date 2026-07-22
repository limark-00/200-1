# -*- coding: utf-8 -*-

"""
LabSafetyMonitor
全局配置文件

Hi3861
    |
巴法云 MQTT
    |
FastAPI
    |
Web Dashboard


"""

import os



# ==================================================
# 巴法云配置
# ==================================================


# 巴法云私钥
# 推荐使用环境变量

BEMFA_UID = os.getenv(

    "BEMFA_UID",

    "你的巴法云私钥"

).strip()





# 设备类型

# 1 MQTT
# 3 TCP

BEMFA_TYPE = int(

    os.getenv(
        "BEMFA_TYPE",
        "1"
    )

)





# ==================================================
# 巴法云主题
# ==================================================


# Hi3861上传主题

ENV_TOPIC = os.getenv(

    "BEMFA_ENV_TOPIC",

    "env004"

).strip()



# 上行数据主题

ENV_PUB_TOPIC = os.getenv(

    "BEMFA_ENV_PUB_TOPIC",

    f"{ENV_TOPIC}/up"

).strip()





# 数据读取主题

TEMP_HUM_TOPIC = ENV_PUB_TOPIC


GAS_TOPIC = ENV_PUB_TOPIC


LIGHT_TOPIC = ENV_PUB_TOPIC





# 控制主题

BUZZER_TOPIC = ENV_TOPIC


RGB_TOPIC = ENV_TOPIC


TRAFFIC_LIGHT_TOPIC = ENV_TOPIC


PIR_TOPIC = ENV_TOPIC






# ==================================================
# 工作模式
# ==================================================


# False:
# 读取真实Hi3861数据


# True:
# 使用随机模拟数据


MOCK_MODE = True







# ==================================================
# 环境安全阈值
# ==================================================


# 温度最大安全值

TEMP_MAX = float(

    os.getenv(

        "TEMP_MAX",

        "30"

    )

)




# 湿度最大安全值

HUM_MAX = float(

    os.getenv(

        "HUM_MAX",

        "70"

    )

)




# MQ-2气体值

GAS_MAX = float(

    os.getenv(

        "GAS_MAX",

        "200"

    )

)





# 光照最大值

LIGHT_MAX = float(

    os.getenv(

        "LIGHT_MAX",

        "1000"

    )

)









# ==================================================
# 历史数据配置
# ==================================================


# ECharts保存多少个点


HISTORY_SIZE = int(

    os.getenv(

        "HISTORY_SIZE",

        "60"

    )

)





# 数据刷新周期

DATA_INTERVAL = int(

    os.getenv(

        "DATA_INTERVAL",

        "2"

    )

)









# =================================
# 摄像头配置
# =================================


ENABLE_CAMERA=True



# 默认外接USB摄像头

CAMERA_INDEX=int(

    os.getenv(

        "CAMERA_INDEX",

        "1"

    )

)



CAMERA_WIDTH=1280


CAMERA_HEIGHT=720




# 自动抓拍功能

ENABLE_PIR_POLLER = False



PIR_POLL_INTERVAL = 3



CAPTURE_COOLDOWN = 10



CAPTURE_DIR = (

    "static/captures"

)



CAPTURE_LIST_LIMIT = 20








# ==================================================
# FastAPI服务器
# ==================================================


APP_HOST = "0.0.0.0"


APP_PORT = 5001



# 兼容旧版本

FLASK_HOST = APP_HOST


FLASK_PORT = APP_PORT



FLASK_DEBUG = True









# ==================================================
# 日志
# ==================================================


DEBUG = True