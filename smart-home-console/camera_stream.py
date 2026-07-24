# -*- coding: utf-8 -*-
"""
camera_stream.py - 摄像头核心模块
自动寻找摄像头 / MJPEG视频流 / YOLOv8人体检测 / 危险区域检测
"""
import cv2
import time
import threading
import os
from datetime import datetime
from ultralytics import YOLO

# YOLO模型
try:
    yolo_model = YOLO("yolov8n.pt")
    print("YOLO模型加载成功")
except Exception as e:
    print("YOLO模型加载失败:", e)
    yolo_model = None

# 摄像头编号
CAMERA_LIST = [1, 0, 2, 3]

# 全局变量
camera = None
camera_index = -1
camera_lock = threading.Lock()
people_count = 0
danger_people_count = 0
fps = 0
danger_alarm = False

# 报警callback
alarm_callback = None

# 危险区域
danger_area = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}

# 抓拍目录
CAPTURE_DIR = "static/capture"
if not os.path.exists(CAPTURE_DIR):
    os.makedirs(CAPTURE_DIR)


def set_alarm_callback(callback):
    global alarm_callback
    alarm_callback = callback
    print("报警callback注册成功")


def set_danger_area(area):
    global danger_area
    danger_area = {
        "x1": int(area.get("x1", 0)),
        "y1": int(area.get("y1", 0)),
        "x2": int(area.get("x2", 0)),
        "y2": int(area.get("y2", 0))
    }
    print("危险区域更新:", danger_area)


def find_camera():
    global camera_index
    print("正在检测摄像头...")
    for index in CAMERA_LIST:
        try:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            time.sleep(0.5)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    camera_index = index
                    print("摄像头连接成功:", index)
                    return cap
            cap.release()
        except Exception as e:
            print("摄像头检测失败:", e)
    print("未找到摄像头")
    return None


def get_camera():
    global camera
    with camera_lock:
        if camera is None:
            camera = find_camera()
        return camera


def release_camera():
    global camera
    with camera_lock:
        if camera:
            camera.release()
        camera = None


def check_danger_area(cx, cy):
    x1 = danger_area["x1"]
    y1 = danger_area["y1"]
    x2 = danger_area["x2"]
    y2 = danger_area["y2"]
    if x1 <= cx <= x2 and y1 <= cy <= y2:
        return True
    return False


def save_alarm_image(frame):
    try:
        filename = "alarm_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
        filepath = os.path.join(CAPTURE_DIR, filename)
        cv2.imwrite(filepath, frame)
        print("报警图片保存:", filepath)
        return "/static/capture/" + filename
    except Exception as e:
        print("图片保存失败:", e)
        return "/static/no-image.png"


def send_alarm(image):
    global alarm_callback
    alarm = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "危险区域入侵",
        "people": people_count,
        "image": image
    }
    if alarm_callback:
        alarm_callback(alarm)
    else:
        print("没有注册报警回调")


def detect(frame):
    global people_count
    global danger_people_count
    global danger_alarm

    if yolo_model is None:
        return frame

    try:
        results = yolo_model(frame, verbose=False)
        count = 0
        danger_count = 0
        current_alarm = False

        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                if cls == 0 and conf > 0.5:
                    count += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    inside = check_danger_area(cx, cy)
                    if inside:
                        danger_count += 1
                        current_alarm = True
                        color = (0, 0, 255)
                        text = "DANGER"
                    else:
                        color = (0, 255, 0)
                        text = "person"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.circle(frame, (cx, cy), 5, color, -1)
                    cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        people_count = count
        danger_people_count = danger_count

        if current_alarm and not danger_alarm:
            image = save_alarm_image(frame)
            send_alarm(image)

        danger_alarm = current_alarm

    except Exception as e:
        print("YOLO检测异常:", e)

    return frame


def generate_frames():
    global fps
    last_time = time.time()

    while True:
        cap = get_camera()
        if cap is None:
            time.sleep(3)
            continue

        success, frame = cap.read()
        if not success:
            print("摄像头读取失败")
            release_camera()
            continue

        frame = cv2.flip(frame, 1)
        frame = detect(frame)

        now = time.time()
        if now - last_time != 0:
            fps = int(1 / (now - last_time))
        last_time = now

        cv2.putText(frame, f"People:{people_count}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.putText(frame, f"FPS:{fps}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        frame = cv2.resize(frame, (1280, 720))

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        jpg = buffer.tobytes()
        yield(b"--frame\r\n" b"Content-Type:image/jpeg\r\n\r\n" + jpg + b"\r\n")
        time.sleep(0.03)


def get_camera_info():
    has_area = not (danger_area["x1"] == 0 and danger_area["y1"] == 0 and danger_area["x2"] == 0 and danger_area["y2"] == 0)
    return {
        "connected": camera is not None,
        "index": camera_index,
        "people": people_count,
        "area_people": danger_people_count if has_area else 0,
        "has_danger_area": has_area,
        "fps": fps
    }


if __name__ == "__main__":
    print("camera_stream测试启动")
    for frame in generate_frames():
        pass
