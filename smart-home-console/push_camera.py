# -*- coding: utf-8 -*-
"""
本地摄像头推流脚本 —— 在笔记本上运行，将摄像头画面实时推送到云服务器。

用法:
    python push_camera.py                          # 推送到默认服务器
    python push_camera.py --url https://xxx.com    # 指定服务器

依赖: opencv-python, requests
"""

import argparse
import time

import cv2
import requests

DEFAULT_URL = "https://app7804.acapp.acwing.com.cn/api/vision/frame/upload"


def main():
    parser = argparse.ArgumentParser(description="推流本地摄像头到云服务器")
    parser.add_argument("--url", default=DEFAULT_URL, help="上传接口地址")
    parser.add_argument("--camera", type=int, default=0, help="摄像头索引")
    parser.add_argument("--fps", type=int, default=10, help="目标帧率")
    parser.add_argument("--width", type=int, default=640, help="帧宽度")
    parser.add_argument("--height", type=int, default=480, help="帧高度")
    parser.add_argument("--quality", type=int, default=70, help="JPEG 质量 (1-100)")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"❌ 无法打开摄像头 {args.camera}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    interval = 1.0 / args.fps
    print(f"📡 推流中 → {args.url}")
    print(f"📷 摄像头 {args.camera} | {args.width}x{args.height} | {args.fps} FPS")
    print("按 Ctrl+C 停止")

    count = 0
    t0 = time.time()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("⚠️ 读帧失败，重试...")
                time.sleep(1)
                continue

            _, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), args.quality])
            frame_bytes = jpeg.tobytes()

            try:
                resp = requests.post(
                    args.url,
                    data=frame_bytes,
                    headers={"Content-Type": "image/jpeg"},
                    timeout=5,
                )
            except requests.RequestException:
                pass  # 网络不好跳过一帧

            count += 1
            elapsed = time.time() - t0
            sleep_time = interval - (time.time() - t0 - (count - 1) * interval)
            if sleep_time > 0:
                time.sleep(sleep_time)

            if count % 50 == 0:
                fps = count / elapsed
                print(f"  已推 {count} 帧 | {fps:.1f} FPS")

    except KeyboardInterrupt:
        print(f"\n🛑 停止。共推送 {count} 帧, 平均 {count / (time.time() - t0):.1f} FPS")
    finally:
        cap.release()


if __name__ == "__main__":
    main()
