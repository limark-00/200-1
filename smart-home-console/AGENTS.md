# AGENTS.md

## Project Overview

Smart Home Training Console — FastAPI app for IoT device control (HiSpark Hi3861 + Bemfa cloud) with YOLO person detection and danger zone monitoring. Training lab project, not production.

## Quick Commands

```bash
# Always work from this directory
cd smart-home-console

# Activate venv (always required)
source .venv/bin/activate

# Run locally
python app.py

# Run tests (no hardware required)
python -m unittest discover -s tests -v

# Run a single test file
python -m unittest tests.test_vision_service -v

# Compile check
python -m compileall -q app.py config.py bemfa_api.py camera.py vision_service.py zone_detector.py event_repository.py vision_alarm.py tests
```

## Architecture

Single-package Python app (no monorepo). Key modules:

| File | Role |
|------|------|
| `app.py` | FastAPI routes, lifespan, static mounts. Entry point. |
| `config.py` | All settings via env vars. No secrets in source. |
| `bemfa_api.py` | Bemfa IoT HTTP API wrapper (getmsg/send/Mock) |
| `vision_service.py` | Singleton camera + YOLO + MJPEG stream + zone event coordination |
| `zone_detector.py` | Pure state machine for danger zone occupancy |
| `event_repository.py` | SQLite storage for zones and events |
| `vision_alarm.py` | Queue-based alarm delivery to Bemfa |
| `camera.py` | OpenCV capture + placeholder fallback |

Frontend: `templates/index.html` (Jinja2) + `static/style.css` + `static/script.js`

## Environment Variables

All config in `config.py`. Key ones:

- `BEMFA_UID` — Bemfa cloud private key (required for real mode, never commit)
- `VISION_ENABLED` — `1` to enable YOLO thread, `0` to disable
- `VISION_CAMERA_INDEX` — OpenCV camera device index (default `0`)
- `VISION_MODEL` — YOLO model path (default `yolo11n.pt`, auto-downloaded on first run)
- `VISION_DB_PATH` — SQLite database path (default `data/vision_events.db`)
- `VISION_EVENT_DIR` — Evidence JPEG directory (default `static/vision_events`)

## Testing

- Tests use `unittest` (not pytest). Run from `smart-home-console/` directory.
- `test_bemfa.py` is a standalone script, NOT included in test discovery — run separately only when Bemfa credentials are configured.
- Tests are offline-safe: no real camera, hardware, or Bemfa connection needed.
- Vision event data in `data/*.db` and `static/vision_events/` is gitignored.

## Gotchas

- The `tojson` Jinja2 filter in `app.py` must return `Markup`, not raw string —否则前端 JS 会收到 HTML-escaped quotes and break.
- `ConsoleStaticFiles` blocks the evidence subtree to prevent direct static access — evidence is served via `/vision-events/` with basename-only routing.
- Camera opens once as singleton in `vision_service.py`. All browser clients share one MJPEG stream.
- Zone coordinates are normalized (0.0–1.0). Minimum width/height is 0.02.
- `vision_alarm.py` uses a short send budget (0.5s) so shutdown `alarm_off` isn't blocked by network I/O.
- Evidence directory path validation in `resolve_vision_event_directory()` rejects paths that could expose project root or static root.

## Deployment

Bare FastAPI app — `uvicorn app:app --host 0.0.0.0 --port 5001`. No built-in auth. Must be behind LAN-only Nginx or VPN for real deployment. See README for systemd + Nginx config.

## Language

Project documentation and UI are in Chinese (Simplified). Code comments are mixed Chinese/English.
