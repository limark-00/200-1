# -*- coding: utf-8 -*-
"""
app.py —— FastAPI 主程序

功能概览：
1. 提供网页控制台（templates/index.html）
2. 提供传感器查询 / 设备控制 / 抓拍列表等 API
3. 后台线程轮询 PIR：检测到「有人」就调用摄像头抓拍
4. 支持 Mock / 巴法云 模式切换（页面开关 + /api/mode）

启动方式：
    python app.py
    # 或
    uvicorn app:app --host 0.0.0.0 --port 5000

自动接口文档（FastAPI 自带，浏览器打开即可）：
    http://127.0.0.1:5000/docs
"""

from __future__ import annotations

import json
import os
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from pydantic import BaseModel, Field

import bemfa_api
import camera
import config

# ---------- 路径：以本文件所在目录为项目根，避免启动目录不对导致找不到模板/静态文件 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# ---------- 运行时状态（可被页面开关改写）----------
_runtime_mock = bool(config.MOCK_MODE)
_mode_lock = threading.Lock()

_last_capture_ts = 0.0
_last_capture_lock = threading.Lock()

_poller_started = False
_poller_lock = threading.Lock()
_poller_stop = threading.Event()


def _set_mock_mode(enabled: bool) -> None:
    """切换 Mock / 真实巴法云模式。"""
    global _runtime_mock
    with _mode_lock:
        _runtime_mock = bool(enabled)
        config.MOCK_MODE = _runtime_mock


def _get_mock_mode() -> bool:
    with _mode_lock:
        return _runtime_mock


def _try_capture_on_pir() -> dict:
    """PIR 触发时尝试抓拍。带冷却时间，避免连拍。"""
    global _last_capture_ts
    now = time.time()
    with _last_capture_lock:
        if now - _last_capture_ts < config.CAPTURE_COOLDOWN:
            return {
                "captured": False,
                "reason": f"冷却中，还需 {int(config.CAPTURE_COOLDOWN - (now - _last_capture_ts))} 秒",
            }
        _last_capture_ts = now

    result = camera.capture_photo()
    if result.get("ok") and result.get("path"):
        _ = camera.recognize_image(result["path"])
    return {"captured": bool(result.get("ok")), "detail": result}


def _pir_poll_loop() -> None:
    """
    后台死循环：每隔几秒查一次 PIR。
    - Mock 模式：读内存里的 PIR 状态（页面按钮可改）
    - 真实模式：读巴法云 PIR_TOPIC
    """
    print("[PIR轮询] 后台线程已启动")
    while not _poller_stop.is_set():
        try:
            result = bemfa_api.get_topic_msg(config.PIR_TOPIC)
            msg = result.get("msg", "")
            if result.get("ok") and bemfa_api.is_pir_triggered(msg):
                info = _try_capture_on_pir()
                if info.get("captured"):
                    print(f"[PIR轮询] 检测到触发，已抓拍: {info.get('detail')}")
                else:
                    print(f"[PIR轮询] 触发但未抓拍: {info.get('reason')}")
                if _get_mock_mode():
                    bemfa_api.set_mock_pir(False)
        except Exception as exc:  # noqa: BLE001
            print(f"[PIR轮询] 异常: {exc}")
        # 可被 stop 提前唤醒，方便进程退出
        _poller_stop.wait(config.PIR_POLL_INTERVAL)
    print("[PIR轮询] 后台线程已结束")


def _start_poller_once() -> None:
    """启动后台轮询线程（只启动一次）。"""
    global _poller_started
    with _poller_lock:
        if _poller_started:
            return
        _poller_stop.clear()
        t = threading.Thread(target=_pir_poll_loop, name="pir-poller", daemon=True)
        t.start()
        _poller_started = True


def _stop_poller() -> None:
    """通知轮询线程退出（进程结束时调用）。"""
    _poller_stop.set()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    FastAPI 生命周期钩子：
    - 启动时：拉起 PIR 轮询线程
    - 关闭时：通知线程停止
    比在模块 import 时直接起线程更清晰，也适合 uvicorn 多 worker 场景的理解。
    """
    _start_poller_once()
    print("=" * 50)
    print("智能家居网页控制台 (FastAPI)")
    print(f"模式: {'模拟 Mock' if _get_mock_mode() else '巴法云真实'}")
    print(f"控制台: http://127.0.0.1:{config.APP_PORT}/")
    print(f"API文档: http://127.0.0.1:{config.APP_PORT}/docs")
    print("=" * 50)
    yield
    _stop_poller()


app = FastAPI(
    title="智能家居实训控制台",
    description="HiSpark Hi3861 + 巴法云 + 电脑摄像头。打开 /docs 可交互测试 API。",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------- 模板（Jinja2）----------
templates = Jinja2Templates(directory=TEMPLATE_DIR)


def _tojson(value: Any) -> Markup:
    """
    给模板用的 tojson 过滤器（Flask 自带，Jinja2 默认没有）。

    必须返回 Markup，否则 Jinja2 会把双引号转成 &#34;，
    浏览器里就变成非法 JS，window.TOPICS 为空，请求会变成 /api/sensor/ 。
    """
    return Markup(json.dumps(value, ensure_ascii=False))


templates.env.filters["tojson"] = _tojson

# ---------- 静态文件：CSS / JS / 抓拍图片 ----------
# 注意：mount 要写在具体路由之后也可以，但 /static 不会和 /api 冲突
os.makedirs(os.path.join(STATIC_DIR, "captures"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------- 请求体模型（Pydantic：自动校验 + /docs 里能看到字段说明）----------

class ModeBody(BaseModel):
    mock: bool = Field(..., description="true=模拟模式，false=巴法云真实模式")


class ControlBody(BaseModel):
    topic: str = Field(..., description="巴法云主题名")
    msg: str = Field(..., description="下发的指令内容，如 red / on / off")


class MockPirBody(BaseModel):
    triggered: bool = Field(True, description="是否模拟为有人/触发")


# ==================== 页面 ====================

@app.get("/", response_class=HTMLResponse, summary="控制台首页")
async def index(request: Request):
    """控制台首页。把 topic 名传给模板，方便前端按钮知道控制哪个主题。"""
    context_data = {
        "topics": {
            "temp_hum": config.TEMP_HUM_TOPIC,
             "light": config.LIGHT_TOPIC,
              "pir": config.PIR_TOPIC,
             "traffic": config.TRAFFIC_LIGHT_TOPIC,
              "buzzer": config.BUZZER_TOPIC,
              "rgb": config.RGB_TOPIC,
        },
         "mock_mode": _get_mock_mode(),
    }
# 重点：第一个参数传 request，第二个传模板名，第三个传context
    return templates.TemplateResponse(request, "index.html", context=context_data)

# ==================== API（路径与原先 Flask 版保持一致，前端不用改）====================

@app.get("/api/mode", summary="查询运行模式")
async def get_mode():
    """返回当前是模拟模式还是巴法云模式。"""
    return {"ok": True, "mock": _get_mock_mode()}


@app.post("/api/mode", summary="切换运行模式")
async def set_mode(body: ModeBody):
    """POST JSON：{"mock": true/false}"""
    _set_mock_mode(body.mock)
    mode_name = "模拟(Mock)" if _get_mock_mode() else "巴法云(真实)"
    return {"ok": True, "mock": _get_mock_mode(), "message": f"已切换为 {mode_name}"}


@app.get("/api/sensor/{topic:path}", summary="查询主题最新数据")
async def api_sensor(topic: str):
    """查询巴法云（或 Mock）某主题最新数据。topic 写在 URL 路径里。"""
    result = bemfa_api.get_topic_msg(topic)
    if not result.get("ok"):
        return JSONResponse(content=result, status_code=502)
    return result


@app.post("/api/control", summary="下发控制指令")
async def api_control(body: ControlBody):
    """请求 JSON：{"topic": "trafficLight", "msg": "red"}"""
    topic = body.topic.strip()
    msg = str(body.msg).strip()
    if not topic or msg == "":
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "需要参数 topic 和 msg"},
        )

    result = bemfa_api.send_msg(topic, msg)
    if not result.get("ok"):
        return JSONResponse(content=result, status_code=502)
    return result


@app.get("/api/captures", summary="抓拍照片列表")
async def api_captures():
    """返回最近抓拍照片文件名列表（倒序，最多 20 张）。"""
    files = camera.list_captures()
    return {
        "ok": True,
        "files": files,
        "base_url": "/static/captures/",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.post("/api/mock/pir", summary="模拟 PIR 触发")
async def api_mock_pir(body: MockPirBody = MockPirBody()):
    """
    仅 Mock 模式有效。默认 triggered=true。
    后台轮询检测到后会抓拍，并自动清回无人。
    """
    if not _get_mock_mode():
        # 用与前端约定的 {ok, error} 格式，而不是 FastAPI 默认的 {detail}
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": "当前为巴法云真实模式，请先在页面切换到「模拟模式」",
            },
        )

    triggered = bool(body.triggered)
    bemfa_api.set_mock_pir(triggered)
    return {
        "ok": True,
        "triggered": triggered,
        "message": "已设置 Mock PIR=" + ("有人/触发" if triggered else "无人"),
        "hint": f"后台约 {config.PIR_POLL_INTERVAL} 秒内会轮询到并尝试抓拍",
    }


@app.post("/api/capture/now", summary="立即抓拍")
async def api_capture_now():
    """手动立即抓拍一张（测摄像头用，不依赖 PIR）。"""
    result = camera.capture_photo()
    if not result.get("ok"):
        return JSONResponse(content=result, status_code=500)
    return result


if __name__ == "__main__":
    # reload=False：避免热重载启动两个 PIR 轮询线程，实训课更稳
    uvicorn.run(
        "app:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=False,
        log_level="info",
    )
