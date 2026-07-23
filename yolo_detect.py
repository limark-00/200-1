# -*- coding:utf-8 -*-

"""
yolo_detect.py

YOLO工具模块

注意：
模型由 camera_stream.py 统一管理

本文件只负责：
1. 获取人数
2. 提供接口给 app.py

"""


# 当前人数

people_count = 0



# 当前状态

running = False





# ==========================================
# 设置人数
# camera_stream.py 调用
# ==========================================

def set_people(count):

    global people_count

    people_count = count





# ==========================================
# 获取人数
# app.py调用
# ==========================================

def get_people():

    return people_count





# ==========================================
# 状态
# ==========================================

def is_running():

    return running





def set_running(status):

    global running

    running=status