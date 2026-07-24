# -*- coding: utf-8 -*-
"""
app.py —— FastAPI 主程序

功能概览：
1. 提供网页控制台（templates/index.html）
2. 提供传感器查询 / 设备控制 / 抓拍列表等 API
3. 后台运行 YOLO 人员检测，提供状态、单帧和 MJPEG 视频流
4. 支持 Mock / 巴法云 模式切换（页面开关 + /api/mode）

启动方式：
    python app.py
    # 或
    uvicorn app:app --host 0.0.0.0 --port 5001

自动接口文档（FastAPI 自带，浏览器打开即可）：
    http://127.0.0.1:5001/docs
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any
from urllib.parse import quote

import uvicorn
from fastapi import FastAPI, Path as ApiPath, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from pydantic import BaseModel, Field, model_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

import bemfa_api
import camera
import config
import llm_service
from bemfa_api import mqtt_start, mqtt_stop
from event_repository import EventClosedError, EventNotFoundError, EventRepository
from vision_alarm import VisionAlarmController
from vision_service import VisionService, VisionSettings
from zone_detector import NormalizedZone, ZoneDetector

# ---------- 路径：以本文件所在目录为项目根，避免启动目录不对导致找不到模板/静态文件 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
VISION_ALARM_SEND_BUDGET_SECONDS = 0.5
DEFAULT_VISION_EVENT_DIR = "static/vision_events"
VISION_EVENT_DIRECTORY_WARNING_TEXT = (
    "视觉证据目录配置不安全，已使用安全默认目录"
)

# ---------- 运行时状态（可被页面开关改写）----------
_runtime_mock = bool(config.MOCK_MODE)
_mode_lock = threading.Lock()

_last_capture_ts = 0.0
_last_capture_lock = threading.Lock()

_poller_started = False
_poller_lock = threading.Lock()
_poller_stop = threading.Event()

# 整个进程共用同一套视觉、区域和事件依赖。
def _project_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(BASE_DIR, path)


def resolve_vision_event_directory(directory: str) -> tuple[str, str]:
    """Resolve evidence storage, falling back when a root could expose source."""
    safe_default = os.path.realpath(
        os.path.join(BASE_DIR, DEFAULT_VISION_EVENT_DIR)
    )
    configured = str(directory or "").strip() or DEFAULT_VISION_EVENT_DIR
    try:
        resolved = os.path.realpath(_project_path(configured))
        resolved_base = os.path.realpath(BASE_DIR)
        resolved_static = os.path.realpath(STATIC_DIR)
        common = os.path.commonpath([resolved, resolved_base])
        contains_console = common == resolved
        filesystem_root = os.path.dirname(resolved) == resolved
        is_static_root = resolved == resolved_static
        file_collision = os.path.exists(resolved) and not os.path.isdir(resolved)
    except (OSError, TypeError, ValueError):
        return safe_default, VISION_EVENT_DIRECTORY_WARNING_TEXT

    if contains_console or filesystem_root or is_static_root or file_collision:
        return safe_default, VISION_EVENT_DIRECTORY_WARNING_TEXT
    return resolved, ""


def event_static_subtree(directory: str) -> str:
    """Return the normalized static-relative event prefix, if there is one."""
    try:
        resolved_static = os.path.realpath(STATIC_DIR)
        resolved_event = os.path.realpath(directory)
        if (
            resolved_event == resolved_static
            or os.path.commonpath([resolved_event, resolved_static])
            != resolved_static
        ):
            return ""
        relative = os.path.relpath(resolved_event, resolved_static)
    except (OSError, TypeError, ValueError):
        return ""
    return relative.replace("\\", "/").strip("/")


class VisionEvidenceFiles(StaticFiles):
    """Serve only basename JPEG evidence and treat storage failures as absent."""

    async def check_config(self) -> None:
        """A missing/unavailable evidence directory is an empty directory."""
        return None

    async def get_response(self, path: str, scope: dict[str, Any]) -> Response:
        if (
            os.path.basename(path) != path
            or not path.lower().endswith((".jpg", ".jpeg"))
        ):
            raise StarletteHTTPException(status_code=404)
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code in {401, 404}:
                raise StarletteHTTPException(status_code=404) from None
            raise
        except (OSError, RuntimeError):
            raise StarletteHTTPException(status_code=404) from None


class ConsoleStaticFiles(StaticFiles):
    """Serve console assets without exposing the evidence storage subtree."""

    def __init__(self, *, blocked_subtree: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        normalized = os.path.normcase(os.path.normpath(blocked_subtree or ""))
        self._blocked_subtree = (
            ""
            if normalized in {"", "."}
            else normalized.replace("\\", "/").strip("/")
        )
        self._blocked_path = (
            os.path.normcase(
                os.path.realpath(
                    os.path.join(
                        os.fspath(self.directory),
                        self._blocked_subtree,
                    )
                )
            )
            if self._blocked_subtree and self.directory is not None
            else ""
        )
        self._static_root_path = (
            os.path.normcase(os.path.realpath(os.fspath(self.directory)))
            if self.directory is not None
            else ""
        )

    def lookup_path(self, path: str) -> tuple[str, os.stat_result | None]:
        full_path, stat_result = super().lookup_path(path)
        if full_path and self._is_blocked_path(full_path):
            return "", None
        return full_path, stat_result

    def _is_blocked_path(self, path: str) -> bool:
        if not self._blocked_path:
            return False
        try:
            resolved = os.path.normcase(os.path.realpath(path))
            if (
                os.path.commonpath([resolved, self._blocked_path])
                == self._blocked_path
            ):
                return True
        except (OSError, TypeError, ValueError):
            return False

        # ``normcase`` follows operating-system path rules, but macOS may use
        # a case-insensitive filesystem while retaining POSIX string casing.
        # Compare existing ancestors by identity so aliases/case variants
        # cannot reach the blocked directory without overblocking distinct
        # siblings on case-sensitive filesystems.
        candidate = resolved
        while True:
            try:
                if os.path.samefile(candidate, self._blocked_path):
                    return True
            except (OSError, ValueError):
                pass
            try:
                if self._static_root_path and os.path.samefile(
                    candidate,
                    self._static_root_path,
                ):
                    return False
            except (OSError, ValueError):
                pass
            parent = os.path.dirname(candidate)
            if parent == candidate:
                return False
            candidate = parent

    async def get_response(self, path: str, scope: dict[str, Any]) -> Response:
        normalized = os.path.normcase(os.path.normpath(path))
        normalized = normalized.replace("\\", "/").strip("/")
        if self._blocked_subtree and (
            normalized == self._blocked_subtree
            or normalized.startswith(f"{self._blocked_subtree}/")
        ):
            raise StarletteHTTPException(status_code=404)
        return await super().get_response(path, scope)


def _mount_resolved_vision_event_files(
    application: FastAPI,
    resolved: str,
) -> None:
    application.mount(
        "/vision-events",
        VisionEvidenceFiles(directory=resolved, check_dir=False),
        name="vision-events",
    )


def mount_vision_event_files(application: FastAPI, directory: str) -> str:
    """Validate and fail-soft mount an evidence directory for isolated apps."""
    resolved, _warning = resolve_vision_event_directory(directory)
    _mount_resolved_vision_event_files(application, resolved)
    return resolved


VISION_EVENT_DIRECTORY, VISION_EVENT_DIRECTORY_WARNING = (
    resolve_vision_event_directory(config.VISION_EVENT_DIR)
)
VISION_EVENT_STATIC_SUBTREE = event_static_subtree(VISION_EVENT_DIRECTORY)
event_repository = EventRepository(_project_path(config.VISION_DB_PATH))
zone_detector = ZoneDetector(
    config.VISION_ENTER_SECONDS,
    config.VISION_EXIT_SECONDS,
)


def _send_vision_alarm(command: str) -> dict[str, Any]:
    """Use a short total budget so shutdown off is not stuck behind network I/O."""
    return bemfa_api.send_msg(
        config.ENV_TOPIC,
        command,
        timeout=VISION_ALARM_SEND_BUDGET_SECONDS,
    )


alarm_controller = VisionAlarmController(
    _send_vision_alarm,
    delivery_callback=lambda event_id, command, delivered, error: (
        vision_service.enqueue_alarm_delivery(
            event_id,
            command,
            delivered,
            error,
        )
    ),
)
vision_service = VisionService(
    VisionSettings(
        enabled=config.VISION_ENABLED,
        camera_index=config.VISION_CAMERA_INDEX,
        model_name=config.VISION_MODEL,
        confidence=config.VISION_CONFIDENCE,
        image_size=config.VISION_IMAGE_SIZE,
        frame_skip=config.VISION_FRAME_SKIP,
        width=config.VISION_FRAME_WIDTH,
        height=config.VISION_FRAME_HEIGHT,
        jpeg_quality=config.VISION_JPEG_QUALITY,
        reconnect_delay=config.VISION_RECONNECT_DELAY,
    ),
    zone_detector=zone_detector,
    event_repository=event_repository,
    alarm_controller=alarm_controller,
    event_snapshot_dir=VISION_EVENT_DIRECTORY,
)


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
    - 启动时：拉起视觉服务、MQTT 订阅与可选的 PIR 轮询线程
    - 关闭时：释放摄像头、断开 MQTT 并通知线程停止
    比在模块 import 时直接起线程更清晰，也适合 uvicorn 多 worker 场景的理解。
    """
    vision_service.initialize_safety()
    vision_service.start()
    if not _get_mock_mode():
        mqtt_start()
    if getattr(config, "ENABLE_PIR_POLLER", False):
        _start_poller_once()
    print("=" * 50)
    print("智能家居网页控制台 (FastAPI)")
    print(f"模式: {'模拟 Mock' if _get_mock_mode() else '巴法云真实'}")
    print(f"控制台: http://127.0.0.1:{config.APP_PORT}/")
    print(f"API文档: http://127.0.0.1:{config.APP_PORT}/docs")
    print("=" * 50)
    try:
        yield
    finally:
        vision_service.shutdown_safety()
        mqtt_stop()
        if getattr(config, "ENABLE_PIR_POLLER", False):
            _stop_poller()


app = FastAPI(
    title="智能家居实训控制台",
    description="HiSpark Hi3861 + 巴法云 + YOLO视觉监控。打开 /docs 可交互测试 API。",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def request_validation_error(_request: Request, exc: RequestValidationError):
    """Keep FastAPI's 422 shape serializable for rejected NaN/Infinity inputs."""
    errors = exc.errors()
    for error in errors:
        value = error.get("input")
        if isinstance(value, float) and not math.isfinite(value):
            error["input"] = str(value)
    return JSONResponse(status_code=422, content=jsonable_encoder({"detail": errors}))

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
_mount_resolved_vision_event_files(app, VISION_EVENT_DIRECTORY)
app.mount(
    "/static",
    ConsoleStaticFiles(
        directory=STATIC_DIR,
        blocked_subtree=VISION_EVENT_STATIC_SUBTREE,
    ),
    name="static",
)


# ---------- 请求体模型（Pydantic：自动校验 + /docs 里能看到字段说明）----------

class ModeBody(BaseModel):
    mock: bool = Field(..., description="true=模拟模式，false=巴法云真实模式")


class ControlBody(BaseModel):
    topic: str = Field(..., description="巴法云主题名")
    msg: str = Field(..., description="下发的指令内容，如 red / on / off")


class MockPirBody(BaseModel):
    triggered: bool = Field(True, description="是否模拟为有人/触发")


class VisionZoneBody(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0, strict=True)
    y: float = Field(..., ge=0.0, le=1.0, strict=True)
    width: float = Field(..., ge=0.02, le=1.0, strict=True)
    height: float = Field(..., ge=0.02, le=1.0, strict=True)

    @model_validator(mode="after")
    def validate_frame_bounds(self):
        if self.x + self.width > 1.0 or self.y + self.height > 1.0:
            raise ValueError("区域超出画面范围")
        return self

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
    was_mock = _get_mock_mode()
    _set_mock_mode(body.mock)
    now_mock = _get_mock_mode()

    # 模式切换时管理 MQTT 连接
    if was_mock and not now_mock:
        mqtt_start()
    elif not was_mock and now_mock:
        mqtt_stop()

    mode_name = "模拟(Mock)" if now_mock else "巴法云(真实)"
    return {"ok": True, "mock": now_mock, "message": f"已切换为 {mode_name}"}


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


@app.get("/api/env", summary="读取env004最新环境数据")
async def api_env():
    result = bemfa_api.get_topic_msg(config.ENV_PUB_TOPIC)
    if not result.get("ok"):
        return JSONResponse(content=result, status_code=502)
    result["data"] = bemfa_api.parse_env_message(result.get("msg", ""))
    return result


class EnvCommandBody(BaseModel):
    msg: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="发送给env004的控制命令，只支持alarm_on或alarm_off",
    )


@app.post("/api/env/send", summary="向env004发送报警控制指令")
async def api_env_send(body: EnvCommandBody):
    message = body.msg.strip()
    allowed_commands = {"alarm_on", "alarm_off"}

    if message not in allowed_commands:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": f"不支持的控制命令：{message}",
                "allowed_commands": sorted(allowed_commands),
            },
        )

    result = bemfa_api.send_msg(config.ENV_TOPIC, message)
    if not result.get("ok"):
        return JSONResponse(content=result, status_code=502)

    return {
        "ok": True,
        "topic": config.ENV_TOPIC,
        "msg": message,
        "message": "控制命令已发送至巴法云",
        "raw": result.get("raw"),
    }


@app.get("/api/vision/status", summary="查询YOLO视觉服务状态")
async def api_vision_status():
    """返回摄像头、模型、当前人数和处理帧率。"""
    status = dict(vision_service.get_status())
    if VISION_EVENT_DIRECTORY_WARNING:
        status["storage_error"] = (
            status.get("storage_error")
            or VISION_EVENT_DIRECTORY_WARNING
        )
    return status


def _vision_error(exc: Exception, status_code: int) -> JSONResponse:
    if status_code == 503:
        message = "视觉事件存储不可用"
    elif status_code >= 500:
        message = "视觉服务请求失败"
    else:
        message = str(exc) or exc.__class__.__name__
    return JSONResponse(
        status_code=status_code,
        content={"ok": False, "error": message},
    )


def _event_response(event: dict[str, Any]) -> dict[str, Any]:
    result = dict(event)
    filename = result.get("snapshot_filename")
    if not isinstance(filename, str) or (
        not filename
        or filename in {".", ".."}
        or os.path.basename(filename) != filename
        or "/" in filename
        or "\\" in filename
    ):
        filename = ""
    result["snapshot_filename"] = filename
    result["snapshot_url"] = (
        f"/vision-events/{quote(filename, safe='')}"
        if filename
        else None
    )
    safe_errors = {
        "",
        "保存视觉告警截图失败",
        "保存视觉告警截图失败：未配置截图目录",
        "视觉告警指令发送失败",
    }
    last_error = result.get("last_error")
    result["last_error"] = (
        last_error
        if isinstance(last_error, str) and last_error in safe_errors
        else "视觉事件历史错误已隐藏"
    )
    return result


@app.get("/api/vision/zone", summary="查询危险区域")
async def api_vision_zone_get():
    try:
        return {"ok": True, "zone": vision_service.get_status().get("zone")}
    except (sqlite3.Error, OSError) as exc:
        return _vision_error(exc, 503)
    except Exception as exc:  # noqa: BLE001
        return _vision_error(exc, 500)


@app.put("/api/vision/zone", summary="保存危险区域")
async def api_vision_zone_put(body: VisionZoneBody):
    try:
        zone = NormalizedZone(body.x, body.y, body.width, body.height)
        return {"ok": True, "zone": vision_service.save_zone(zone)}
    except ValueError as exc:
        return _vision_error(exc, 422)
    except (sqlite3.Error, OSError) as exc:
        return _vision_error(exc, 503)
    except Exception as exc:  # noqa: BLE001
        return _vision_error(exc, 500)


@app.delete("/api/vision/zone", summary="删除危险区域")
async def api_vision_zone_delete():
    try:
        vision_service.delete_zone()
        return {"ok": True, "zone": None}
    except (sqlite3.Error, OSError) as exc:
        return _vision_error(exc, 503)
    except Exception as exc:  # noqa: BLE001
        return _vision_error(exc, 500)


@app.get("/api/vision/events", summary="查询危险区域事件")
async def api_vision_events(limit: int = Query(50, ge=1, le=200)):
    try:
        events = vision_service.list_events(limit)
        return {"ok": True, "events": [_event_response(event) for event in events]}
    except (sqlite3.Error, OSError) as exc:
        return _vision_error(exc, 503)
    except Exception as exc:  # noqa: BLE001
        return _vision_error(exc, 500)


@app.post("/api/vision/events/{event_id}/ack", summary="确认危险区域事件")
async def api_vision_event_ack(
    event_id: int = ApiPath(ge=1, le=2**63 - 1),
):
    try:
        event = vision_service.acknowledge_event(event_id)
        return {"ok": True, "event": _event_response(event)}
    except EventNotFoundError as exc:
        return _vision_error(exc, 404)
    except EventClosedError as exc:
        return _vision_error(exc, 409)
    except (sqlite3.Error, OSError) as exc:
        return _vision_error(exc, 503)
    except Exception as exc:  # noqa: BLE001
        return _vision_error(exc, 500)


@app.post("/api/vision/alarm/silence", summary="静音当前视觉告警")
async def api_vision_alarm_silence():
    try:
        return {"ok": True, "alarm": vision_service.silence_current_alarm()}
    except EventClosedError as exc:
        return _vision_error(exc, 409)
    except Exception as exc:  # Silence itself does not require SQLite.
        return _vision_error(exc, 500)


@app.get("/api/vision/frame", summary="获取最新YOLO标注帧")
async def api_vision_frame():
    """返回最新一帧JPEG，尚未获得摄像头画面时返回503。"""
    jpeg = vision_service.get_latest_jpeg()
    if jpeg is None:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": "视觉服务尚无可用画面"},
        )
    return Response(
        content=jpeg,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/vision/stream", summary="YOLO标注画面MJPEG视频流")
async def api_vision_stream():
    """共享后台最新标注帧，不会因新建页面连接而重复打开摄像头。"""
    return StreamingResponse(
        vision_service.iter_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store"},
    )


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
    if vision_service.get_latest_jpeg() is not None:
        result = vision_service.save_snapshot(
            os.path.join(BASE_DIR, config.CAPTURE_DIR)
        )
    else:
        # 视觉服务被关闭或尚未就绪时，保留原有单次抓拍能力。
        result = camera.capture_photo()
    public_result = dict(result)
    if public_result.get("path"):
        public_result["path"] = os.path.basename(str(public_result["path"]))
    if not public_result.get("ok"):
        public_result["error"] = "保存视觉截图失败"
        return JSONResponse(content=public_result, status_code=500)
    if public_result.get("error"):
        public_result["error"] = "抓拍已完成但使用占位图"
    return public_result


# ==================== AI 对话 ====================

class ChatBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="用户输入的消息")
    history: list[dict[str, str]] = Field(default_factory=list, description="历史对话")
    stream: bool = Field(default=False, description="是否流式输出")


@app.post("/api/chat", summary="AI 智能助手对话")
async def api_chat(body: ChatBody):
    """与混元大模型对话，自动注入当前传感器数据作为上下文。支持流式 SSE 输出。"""
    api_key = getattr(config, "HUNYUAN_API_KEY", "")
    if not api_key:
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "error": "未配置混元 API Key，请设置环境变量 HUNYUAN_API_KEY",
            },
        )

    sensor_data = llm_service.get_current_sensor_data()

    if body.stream:
        # 流式 SSE 输出
        async def generate():
            result = llm_service.chat(
                user_message=body.message,
                history=body.history,
                sensor_data=sensor_data,
                stream=True,
            )
            if not result.get("ok"):
                yield f"data: {json.dumps({'error': result.get('error')})}\n\n"
                return
            for token in result["reply"]:
                yield f"data: {json.dumps({'content': token})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    result = llm_service.chat(
        user_message=body.message,
        history=body.history,
        sensor_data=sensor_data,
    )

    if not result.get("ok"):
        return JSONResponse(status_code=502, content=result)

    return result


@app.post("/api/chat/image", summary="AI 图片分析")
async def api_chat_image(prompt: str = "请描述这张图片的内容"):
    """用摄像头抓拍一张照片，发送给混元 vision 模型分析。"""
    api_key = getattr(config, "HUNYUAN_API_KEY", "")
    if not api_key:
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "error": "未配置混元 API Key，请设置环境变量 HUNYUAN_API_KEY",
            },
        )

    # 抓拍当前画面
    capture = camera.capture_photo()
    if not capture.get("ok"):
        return JSONResponse(status_code=500, content={"ok": False, "error": capture.get("error", "抓拍失败")})

    image_path = capture.get("path", "")
    if not image_path or not os.path.exists(image_path):
        return JSONResponse(status_code=500, content={"ok": False, "error": "抓拍图片不存在"})

    result = llm_service.chat_about_image(image_path, prompt)

    if not result.get("ok"):
        return JSONResponse(status_code=502, content=result)

    return {
        "ok": True,
        "reply": result["reply"],
        "image": capture.get("filename", ""),
        "usage": result.get("usage", {}),
    }


@app.get("/api/llm/status", summary="查询 LLM 服务状态")
async def api_llm_status():
    """返回混元大模型配置和可用性。"""
    api_key = getattr(config, "HUNYUAN_API_KEY", "")
    img_key = getattr(config, "HUNYUAN_IMAGE_API_KEY", "")
    return {
        "ok": True,
        "configured": bool(api_key),
        "image_configured": bool(img_key),
        "provider": "混元 (腾讯云)",
        "model": getattr(config, "HUNYUAN_MODEL", "hy3-preview"),
        "vision_model": getattr(config, "HUNYUAN_VISION_MODEL", "hunyuan-vision"),
        "image_model": getattr(config, "HUNYUAN_IMAGE_MODEL", "hy-image-v3.0"),
        "base_url": getattr(config, "HUNYUAN_BASE_URL", "https://tokenhub-intl.tencentmaas.com/v1"),
    }


# ==================== 文生图 ====================

class ImageGenBody(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="图片描述文本")
    model: str = Field(default="hy-image-lite", description="模型: hy-image-lite / hy-image-v3.0")


@app.post("/api/chat/image/generate", summary="AI 文生图")
async def api_image_generate(body: ImageGenBody):
    """文生图。默认 hy-image-lite（同步快速，0.099元/张），可选 hy-image-v3.0（高质量，0.2元/张）。"""
    api_key = getattr(config, "HUNYUAN_IMAGE_API_KEY", "")
    if not api_key:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": "未配置文生图 API Key"},
        )

    model = body.model.strip()
    from hunyuan_image import HunyuanImageClient

    client = HunyuanImageClient(
        api_key=api_key,
        base_url=getattr(config, "HUNYUAN_IMAGE_BASE_URL", "https://tokenhub.tencentmaas.com/v1"),
        model=model,
    )
    result = client.generate(body.prompt)

    if not result.get("ok"):
        return JSONResponse(status_code=502, content=result)

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
