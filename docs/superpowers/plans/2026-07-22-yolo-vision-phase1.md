# YOLO Vision Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a CPU-friendly Ubuntu camera service that detects people with YOLO, publishes one shared annotated MJPEG stream through FastAPI, and displays live status in the existing web console.

**Architecture:** A single `VisionService` owns the Logitech camera and YOLO model in one background thread. FastAPI clients read the latest encoded frame without reopening the camera or reloading the model. The first phase detects only the pretrained `person` class; restricted-zone, dwell, evidence-event, and NFC authorization logic remain out of scope.

**Tech Stack:** Python 3, FastAPI, OpenCV, Ultralytics YOLO, Jinja2, browser MJPEG.

## Global Constraints

- Work only under `smart-home-console/` on branch `codex/yolo-vision-phase1`.
- Preserve the existing Bemfa environment monitoring and control APIs.
- Do not modify Hi3861 firmware in this phase.
- Use one camera/model worker for all web clients.
- Load Ultralytics lazily so configuration and unit tests work before model weights are installed.
- Default to a nano model and person-only inference for CPU compatibility.
- Do not add restricted-zone, dwell, face recognition, fire/smoke detection, or NFC logic in phase 1.

---

### Task 1: Vision configuration and service contract

**Files:**
- Modify: `smart-home-console/config.py`
- Create: `smart-home-console/vision_service.py`
- Create: `smart-home-console/tests/test_vision_service.py`

**Interfaces:**
- Consumes: OpenCV frames, configuration values, and a lazy Ultralytics model factory.
- Produces: `VisionService.start()`, `VisionService.stop()`, `VisionService.get_status()`, `VisionService.get_latest_jpeg()`, `VisionService.iter_mjpeg()`, and `VisionService.save_snapshot()`.

- [x] Write unit tests for initial status, person count extraction, MJPEG chunk formatting, snapshot behavior, and fake-model frame processing.
- [x] Run `python3 -m unittest discover -s smart-home-console/tests -v` and verify failure because `vision_service` does not exist.
- [x] Add environment-driven camera/model configuration to `config.py`.
- [x] Implement the minimal thread-safe `VisionService` with injected camera/model factories and lazy Ultralytics import.
- [x] Re-run the unit tests and verify they pass.

### Task 2: FastAPI lifecycle and vision endpoints

**Files:**
- Modify: `smart-home-console/app.py`
- Create: `smart-home-console/tests/test_vision_api.py`

**Interfaces:**
- Consumes: the singleton `VisionService` created from `config.py`.
- Produces: `GET /api/vision/status`, `GET /api/vision/frame`, and `GET /api/vision/stream`.

- [x] Write API tests using a fake vision service for JSON status, JPEG response, missing-frame response, and MJPEG media type.
- [x] Run the API test and verify it fails because the routes are absent.
- [x] Start/stop the singleton service in FastAPI lifespan without affecting the existing Bemfa flow.
- [x] Add the three vision endpoints and make manual capture reuse the current vision frame when available.
- [x] Re-run all unit tests and verify they pass.

### Task 3: Web monitoring panel

**Files:**
- Modify: `smart-home-console/templates/index.html`

**Interfaces:**
- Consumes: `/api/vision/status` and `/api/vision/stream`.
- Produces: a live video card with camera/model state, detected person count, FPS, last error, and reconnect action.

- [x] Add a static HTML contract test that fails until the vision panel IDs and endpoints exist.
- [x] Add the responsive monitoring panel and inline JavaScript status polling to the current self-contained template.
- [x] Re-run all unit tests and verify the HTML contract passes.

### Task 4: Dependencies, deployment notes, and final verification

**Files:**
- Modify: `smart-home-console/requirements.txt`
- Modify: `smart-home-console/.gitignore`
- Modify: `smart-home-console/README.md`

**Interfaces:**
- Consumes: Ubuntu USB camera exposed as `/dev/video*`.
- Produces: reproducible install/start/check instructions for phase 1.

- [x] Add `ultralytics` to runtime dependencies and ignore downloaded model weights/runtime snapshots.
- [x] Document `lsusb`, `/dev/video*`, model download, CPU operation, endpoints, and troubleshooting.
- [x] Run `python3 -m unittest discover -s smart-home-console/tests -v`.
- [x] Run `python3 -m compileall -q smart-home-console`.
- [x] Run a FastAPI import smoke test with vision disabled and verify existing routes remain importable.
- [x] Inspect the final diff for scope and accidental credential/model/image additions.
