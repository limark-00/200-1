# -*- coding: utf-8 -*-
"""
camera.py —— 电脑摄像头抓拍 + 图像识别占位函数

依赖：opencv-python（cv2）
可选：Pillow（摄像头打不开时画一张占位图，保证流程能测通）
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import config


def _ensure_capture_dir() -> str:
    """确保抓拍目录存在，返回绝对路径。"""
    # 以本文件所在目录（项目根）为基准，避免从别的 cwd 启动时路径错乱
    root = os.path.dirname(os.path.abspath(__file__))
    capture_dir = os.path.join(root, config.CAPTURE_DIR)
    os.makedirs(capture_dir, exist_ok=True)
    return capture_dir


def _save_placeholder(filepath: str, reason: str) -> None:
    """
    摄像头不可用时，生成一张简单占位图，方便无摄像头环境也能测「抓拍流程」。
    优先用 OpenCV 画图；失败再用 Pillow；再失败就写一个空文件提示。
    """
    try:
        import cv2
        import numpy as np

        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = (40, 40, 40)
        cv2.putText(img, "Camera Placeholder", (120, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)
        cv2.putText(img, reason[:40], (40, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.imwrite(filepath, img)
        return
    except Exception:
        pass

    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (640, 480), color=(40, 40, 40))
        draw = ImageDraw.Draw(img)
        draw.text((120, 200), "Camera Placeholder", fill=(0, 200, 255))
        draw.text((40, 280), reason[:60], fill=(200, 200, 200))
        img.save(filepath)
        return
    except Exception:
        # 最后兜底：写一个很小的说明文本（扩展名仍是 .jpg，浏览器可能打不开，但列表能看到文件）
        with open(filepath, "wb") as f:
            f.write(b"placeholder")


def capture_photo(camera_index: int = 0) -> dict[str, Any]:
    """
    用电脑摄像头拍一张照片，保存到 static/captures/。

    返回：
    {
        "ok": True/False,
        "filename": "20260720_213015.jpg",   # 相对 captures 目录的文件名
        "path": "完整路径",
        "error": "失败原因"
    }
    """
    capture_dir = _ensure_capture_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.jpg"
    filepath = os.path.join(capture_dir, filename)

    try:
        import cv2
    except ImportError:
        _save_placeholder(filepath, "opencv not installed")
        return {
            "ok": True,
            "filename": filename,
            "path": filepath,
            "error": "未安装 opencv-python，已保存占位图",
        }

    cap = None
    try:
        # 0 一般是笔记本内置摄像头；外接摄像头可能是 1、2……
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            _save_placeholder(filepath, f"cannot open camera {camera_index}")
            return {
                "ok": True,
                "filename": filename,
                "path": filepath,
                "error": f"无法打开摄像头 {camera_index}，已保存占位图",
            }

        # 有的摄像头前几帧是黑的，多读几帧再拍
        frame = None
        for _ in range(5):
            ok, frame = cap.read()
            if ok and frame is not None:
                break

        if frame is None:
            _save_placeholder(filepath, "read frame failed")
            return {
                "ok": True,
                "filename": filename,
                "path": filepath,
                "error": "读取画面失败，已保存占位图",
            }

        ok = cv2.imwrite(filepath, frame)
        if not ok:
            return {"ok": False, "filename": "", "path": "", "error": "写入图片失败"}

        return {"ok": True, "filename": filename, "path": filepath, "error": ""}
    except Exception as exc:  # noqa: BLE001
        _save_placeholder(filepath, str(exc)[:40])
        return {
            "ok": True,
            "filename": filename,
            "path": filepath,
            "error": f"抓拍异常，已保存占位图: {exc}",
        }
    finally:
        if cap is not None:
            cap.release()


def list_captures(limit: int | None = None) -> list[str]:
    """
    列出抓拍目录中的图片文件名，按时间倒序（新的在前）。
    """
    if limit is None:
        limit = config.CAPTURE_LIST_LIMIT

    capture_dir = _ensure_capture_dir()
    files = []
    for name in os.listdir(capture_dir):
        lower = name.lower()
        if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
            full = os.path.join(capture_dir, name)
            if os.path.isfile(full):
                files.append((name, os.path.getmtime(full)))

    files.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in files[:limit]]


def recognize_image(image_path: str) -> dict[str, Any]:
    """
    【预留】图像识别 / 多模态大模型接口。

    以后可以在这里调用：
    - 本地 YOLO / OpenCV 分类
    - 云端视觉 API / 多模态大模型

    现在先返回假数据，方便前端预留展示区域。
    """
    # TODO: 在这里接入真实的图像识别或大模型 API
    # 例如：读取 image_path → 调用 API → 解析结果 → 返回结构化数据
    _ = image_path  # 暂时未使用，避免 linter 报未使用变量
    return {
        "ok": True,
        "label": "unknown",
        "confidence": 0.0,
        "description": "识别功能开发中（这是假返回值）",
    }
