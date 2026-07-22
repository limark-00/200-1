# YOLO Zone Intrusion Alarm Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one persistent, browser-drawn rectangular danger zone that creates SQLite-backed evidence events and independently controls the Hi3861 buzzer after stable YOLO person intrusion.

**Architecture:** Keep one FastAPI process and the existing singleton `VisionService`. Add a pure `ZoneDetector`, a thread-safe SQLite `EventRepository`, and a queue-backed `VisionAlarmController`; coordinate them from `VisionService` while keeping Bemfa network work off the inference thread. Refactor the embedded buzzer state into a small portable C module so humidity, manual, and vision alarm sources are combined without silencing one another.

**Tech Stack:** Python 3.10-3.12, FastAPI, OpenCV, Ultralytics YOLO, SQLite (`sqlite3`), Jinja2, browser Canvas/Pointer Events, OpenHarmony C, Hi3861, Bemfa MQTT/HTTP.

## Global Constraints

- Work on branch `codex/yolo-zone-alarm-phase2`, which already contains phase 1 and the Linux V4L2/MJPG fix.
- Preserve `GET /api/env`, `POST /api/env/send`, `GET /api/vision/status`, `GET /api/vision/frame`, and `GET /api/vision/stream`.
- Support exactly one enabled rectangular zone using normalized `x`, `y`, `width`, and `height` values.
- Require `width >= 0.02`, `height >= 0.02`, `x + width <= 1`, and `y + height <= 1`.
- Use the bottom-center point of each YOLO person box for zone membership.
- Trigger after 2.0 seconds of continuous occupancy and re-arm after 3.0 seconds of continuous vacancy.
- Create only one event and one evidence image per occupancy cycle.
- Store runtime data at `smart-home-console/data/vision_events.db` and `smart-home-console/static/vision_events/`; never commit runtime DBs or images.
- Send `vision_alarm_on` and `vision_alarm_off` through the existing Bemfa control topic; never use `alarm_off` to clear a vision event.
- Retain all events in phase 2; list 50 by default and accept a maximum query limit of 200.
- Do not implement multiple zones, polygons, NFC, face recognition, cloud video storage, or automatic retention cleanup.
- Do not expose Bemfa credentials in tests, logs, screenshots, or new documentation.

---

### Task 1: Pure Danger-Zone State Machine

**Files:**
- Create: `smart-home-console/zone_detector.py`
- Create: `smart-home-console/tests/test_zone_detector.py`

**Interfaces:**
- Consumes: normalized person foot points as `Sequence[tuple[float, float]]`, an optional `NormalizedZone`, and an injected monotonic clock.
- Produces: `NormalizedZone`, `ZoneState`, `ZoneUpdate`, and `ZoneDetector` with `set_zone()`, `clear_zone()`, `update()`, `bind_event()`, `acknowledge()`, and `get_status()`.

- [x] **Step 1: Write failing state-machine tests**

Create tests with an explicitly controlled clock:

```python
class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def armed_detector(clock):
    detector = ZoneDetector(2.0, 3.0, clock=clock)
    detector.set_zone(NormalizedZone(0.2, 0.2, 0.4, 0.5))
    return detector


def start_alarm(detector, clock):
    detector.update([(0.3, 0.4)])
    clock.advance(2.0)
    update = detector.update([(0.3, 0.4)])
    assert update.alarm_started


def test_alarm_starts_after_two_continuous_seconds():
    clock = FakeClock()
    detector = ZoneDetector(2.0, 3.0, clock=clock)
    detector.set_zone(NormalizedZone(0.2, 0.2, 0.4, 0.5))

    first = detector.update([(0.3, 0.4)])
    clock.advance(1.9)
    second = detector.update([(0.3, 0.4)])
    clock.advance(0.1)
    third = detector.update([(0.3, 0.4)])

    assert first.state == ZoneState.ENTER_PENDING
    assert not second.alarm_started
    assert third.alarm_started
    assert third.state == ZoneState.ALARM_ACTIVE


def test_brief_exit_does_not_clear_active_event():
    clock = FakeClock()
    detector = armed_detector(clock)
    start_alarm(detector, clock)
    detector.bind_event(17)

    clock.advance(2.9)
    pending = detector.update([])
    detector.update([(0.3, 0.4)])

    assert not pending.alarm_cleared
    assert detector.get_status()["state"] == "alarm_active"


def test_three_second_exit_clears_and_rearms():
    clock = FakeClock()
    detector = armed_detector(clock)
    start_alarm(detector, clock)
    detector.bind_event(17)

    detector.update([])
    clock.advance(3.0)
    cleared = detector.update([])

    assert cleared.alarm_cleared
    assert cleared.event_id == 17
    assert cleared.state == ZoneState.ARMED


def test_acknowledged_event_stays_silent_until_exit():
    clock = FakeClock()
    detector = armed_detector(clock)
    start_alarm(detector, clock)
    detector.bind_event(17)

    assert detector.acknowledge(17)
    assert detector.update([(0.3, 0.4)]).state == ZoneState.ALARM_SILENCED
```

Also cover zone boundary inclusion, invalid normalized rectangles, entry-timer reset, maximum people, deleting an active zone, and acknowledgment with the wrong event ID.

- [x] **Step 2: Run tests and verify the intended failure**

Run:

```bash
.venv/bin/python -m unittest tests.test_zone_detector -v
```

Expected: import failure because `zone_detector.py` does not exist.

- [x] **Step 3: Implement the state machine**

Use these exact public types and state names:

```python
class ZoneState(str, Enum):
    DISABLED = "disabled"
    ARMED = "armed"
    ENTER_PENDING = "enter_pending"
    ALARM_ACTIVE = "alarm_active"
    ALARM_SILENCED = "alarm_silenced"


@dataclass(frozen=True)
class NormalizedZone:
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self):
        values = (self.x, self.y, self.width, self.height)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("区域坐标必须是有限数值")
        if self.x < 0 or self.y < 0 or self.width < 0.02 or self.height < 0.02:
            raise ValueError("区域坐标越界或尺寸过小")
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("区域超出画面范围")

    def contains(self, point):
        px, py = point
        return (
            self.x <= px <= self.x + self.width
            and self.y <= py <= self.y + self.height
        )


@dataclass(frozen=True)
class ZoneUpdate:
    state: ZoneState
    people_in_zone: int
    max_people: int
    alarm_started: bool = False
    alarm_cleared: bool = False
    event_id: int | None = None
```

Implement `ZoneDetector` with an `RLock`. Store `_enter_started_at`, `_exit_started_at`, `_max_people`, and `_active_event_id`. Reset the entry timer whenever occupancy becomes zero before 2 seconds. In active or silenced state, reset the exit timer whenever occupancy becomes nonzero before 3 seconds. `clear_zone()` returns the former active event ID so callers can close it safely.

- [x] **Step 4: Run focused and full tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_zone_detector -v
.venv/bin/python -m unittest discover -s tests -v
```

Expected: all zone tests and all existing phase-1 tests pass.

- [x] **Step 5: Commit the state machine**

```bash
git add smart-home-console/zone_detector.py smart-home-console/tests/test_zone_detector.py
git commit -m "feat: add danger-zone state machine"
```

---

### Task 2: SQLite Zone and Event Repository

**Files:**
- Create: `smart-home-console/event_repository.py`
- Create: `smart-home-console/tests/test_event_repository.py`
- Modify: `smart-home-console/config.py:44-68`
- Modify: `smart-home-console/.gitignore`

**Interfaces:**
- Consumes: `NormalizedZone`, event timestamps, snapshot filenames, people counts, close reasons, and delivery results.
- Produces: `EventRepository.initialize()`, `get_zone()`, `save_zone()`, `delete_zone()`, `create_event()`, `get_event()`, `update_max_people()`, `acknowledge_event()`, `close_event()`, `mark_delivery()`, `recover_open_events()`, and `list_events()`.

- [x] **Step 1: Write failing repository tests against a temporary database**

Test exact persistence semantics:

```python
def test_zone_round_trip_survives_new_repository_instance(self):
    first = EventRepository(self.db_path)
    first.initialize()
    first.save_zone(NormalizedZone(0.1, 0.2, 0.3, 0.4))

    second = EventRepository(self.db_path)
    second.initialize()

    self.assertEqual(second.get_zone(), NormalizedZone(0.1, 0.2, 0.3, 0.4))


def test_event_lifecycle_and_delivery_fields(self):
    event_id = self.repo.create_event("event.jpg", 1)
    self.repo.update_max_people(event_id, 3)
    acknowledged = self.repo.acknowledge_event(event_id)
    self.repo.mark_delivery(event_id, "vision_alarm_on", True, "")
    closed = self.repo.close_event(event_id, "person_left")

    self.assertIsNotNone(acknowledged["acknowledged_at"])
    self.assertEqual(closed["max_people"], 3)
    self.assertEqual(closed["close_reason"], "person_left")
    self.assertTrue(closed["alarm_on_delivered"])


def test_recovery_closes_only_open_events(self):
    open_id = self.repo.create_event("open.jpg", 1)
    closed_id = self.repo.create_event("closed.jpg", 1)
    self.repo.close_event(closed_id, "person_left")

    recovered = self.repo.recover_open_events("server_restart")

    self.assertEqual(recovered, [open_id])
    self.assertEqual(self.repo.get_event(open_id)["close_reason"], "server_restart")
```

Also test list ordering, default/maximum limits, missing-event errors, closed-event acknowledgment conflict, idempotent acknowledgment, and delivery failure text.

- [x] **Step 2: Run tests and verify failure**

Run:

```bash
.venv/bin/python -m unittest tests.test_event_repository -v
```

Expected: import failure because `event_repository.py` does not exist.

- [x] **Step 3: Implement schema and connection policy**

Add configuration:

```python
VISION_DB_PATH = os.getenv(
    "VISION_DB_PATH",
    "data/vision_events.db",
).strip()
VISION_EVENT_DIR = os.getenv(
    "VISION_EVENT_DIR",
    "static/vision_events",
).strip()
VISION_ENTER_SECONDS = float(os.getenv("VISION_ENTER_SECONDS", "2.0"))
VISION_EXIT_SECONDS = float(os.getenv("VISION_EXIT_SECONDS", "3.0"))
```

Use a new SQLite connection per repository operation:

```python
def _connect(self):
    connection = sqlite3.connect(self.db_path, timeout=3.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=3000")
    return connection
```

Create the tables with this schema:

```sql
CREATE TABLE IF NOT EXISTS vision_zone (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    x REAL NOT NULL,
    y REAL NOT NULL,
    width REAL NOT NULL,
    height REAL NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vision_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    ended_at TEXT NULL,
    snapshot_filename TEXT NOT NULL,
    max_people INTEGER NOT NULL DEFAULT 1,
    acknowledged_at TEXT NULL,
    close_reason TEXT NULL,
    alarm_on_delivered INTEGER NOT NULL DEFAULT 0,
    alarm_off_delivered INTEGER NOT NULL DEFAULT 0,
    last_error TEXT NOT NULL DEFAULT ''
);
```

Use timezone-aware UTC ISO-8601 strings for all timestamps. Implement `save_zone()` as an `INSERT ... ON CONFLICT(id) DO UPDATE`, always with `id = 1`, and make `list_events(limit=50)` enforce `1 <= limit <= 200` and order by `id DESC`. Define `EventNotFoundError` and `EventClosedError`. Convert rows to plain dictionaries before closing connections. `snapshot_filename` remains an empty string when evidence writing fails. `mark_delivery()` updates only the on/off delivery column selected by the command and stores the final error text.

- [x] **Step 4: Ignore runtime files and verify repository tests**

Add:

```gitignore
data/*.db
data/*.db-shm
data/*.db-wal
static/vision_events/*
!static/vision_events/.gitkeep
```

Create `smart-home-console/static/vision_events/.gitkeep`, then run:

```bash
.venv/bin/python -m unittest tests.test_event_repository -v
.venv/bin/python -m unittest discover -s tests -v
```

Expected: repository and existing tests pass; no DB appears in `git status --short`.

- [x] **Step 5: Commit persistence support**

```bash
git add smart-home-console/event_repository.py smart-home-console/tests/test_event_repository.py smart-home-console/config.py smart-home-console/.gitignore smart-home-console/static/vision_events/.gitkeep
git commit -m "feat: persist vision zones and events"
```

---

### Task 3: Asynchronous Bemfa Vision Alarm Controller

**Files:**
- Create: `smart-home-console/vision_alarm.py`
- Create: `smart-home-console/tests/test_vision_alarm.py`

**Interfaces:**
- Consumes: a sender `Callable[[str], dict]`, a delivery callback `Callable[[int | None, str, bool, str], None]`, and alarm targets.
- Produces: `AlarmTask`, `VisionAlarmController.start()`, `set_alarm()`, `wait_idle()`, `stop()`, and `get_last_error()`.

- [x] **Step 1: Write failing tests for ordering, dedupe, and retries**

Use injected sender and sleeper functions:

```python
def make_controller(sender, sleeper=lambda _seconds: None):
    return VisionAlarmController(
        sender,
        delivery_callback=lambda *_args: None,
        sleeper=sleeper,
    )


def test_same_target_is_not_enqueued_twice():
    sent = []
    controller = make_controller(lambda command: sent.append(command) or {"ok": True})
    controller.start()
    controller.set_alarm(True, event_id=3)
    controller.set_alarm(True, event_id=3)
    self.assertTrue(controller.wait_idle(1.0))
    controller.stop()
    self.assertEqual(sent, ["vision_alarm_on"])


def test_failure_retries_at_fixed_delays():
    attempts = []
    sleeps = []

    def sender(command):
        attempts.append(command)
        return {"ok": False, "error": "network down"}

    task = AlarmTask(True, 9, False)
    controller = make_controller(sender, sleeper=sleeps.append)
    controller._deliver(task)

    self.assertEqual(attempts, ["vision_alarm_on"] * 3)
    self.assertEqual(sleeps, [2.0, 5.0])


def test_forced_off_bypasses_initial_dedupe():
    sent = []
    controller = make_controller(lambda command: sent.append(command) or {"ok": True})
    controller.start()
    controller.set_alarm(False, event_id=None, force=True)
    self.assertTrue(controller.wait_idle(1.0))
    controller.stop()
    self.assertEqual(sent, ["vision_alarm_off"])
```

Also verify on/off ordering, callback arguments, stop behavior, and last-error clearing after a later success.

- [x] **Step 2: Run tests and verify failure**

```bash
.venv/bin/python -m unittest tests.test_vision_alarm -v
```

Expected: import failure because `vision_alarm.py` does not exist.

- [x] **Step 3: Implement the queue worker**

Use this task contract:

```python
@dataclass(frozen=True)
class AlarmTask:
    enabled: bool
    event_id: int | None
    force: bool = False


class VisionAlarmController:
    RETRY_DELAYS = (0.0, 2.0, 5.0)

    def set_alarm(self, enabled, event_id=None, force=False):
        with self._lock:
            if not force and enabled == self._target_enabled:
                return False
            self._target_enabled = enabled
            self._queue.put(AlarmTask(enabled, event_id, force))
            return True
```

The worker converts `enabled` into `vision_alarm_on` or `vision_alarm_off`. Call the sender as `sender(command)`, never directly from `set_alarm()`. Call `queue.task_done()` in `finally`. Implement `wait_idle(timeout)` with a condition/event rather than an unbounded sleep.

- [x] **Step 4: Run focused and full tests**

```bash
.venv/bin/python -m unittest tests.test_vision_alarm -v
.venv/bin/python -m unittest discover -s tests -v
```

Expected: all tests pass without real Bemfa requests.

- [x] **Step 5: Commit the alarm controller**

```bash
git add smart-home-console/vision_alarm.py smart-home-console/tests/test_vision_alarm.py
git commit -m "feat: queue vision alarm commands"
```

---

### Task 4: Independent Hi3861 Alarm-State Combiner

**Files:**
- Create: `applications/sample/wifi-iot/app/day08_mqtt_new/day08_alarm.h`
- Create: `applications/sample/wifi-iot/app/day08_mqtt_new/day08_alarm.c`
- Create: `applications/sample/wifi-iot/app/day08_mqtt_new/tests/test_day08_alarm.c`
- Modify: `applications/sample/wifi-iot/app/day08_mqtt_new/BUILD.gn:3-8`
- Modify: `applications/sample/wifi-iot/app/day08_mqtt_new/mqtt.c:43-166,178-255,257-340`
- Modify: `smart-home-console/bemfa_api.py:227-289`
- Create: `smart-home-console/tests/test_bemfa_vision_alarm.py`

**Interfaces:**
- Consumes: humidity samples and MQTT payloads `alarm_on`, `alarm_off`, `vision_alarm_on`, and `vision_alarm_off`.
- Produces: portable `Day08AlarmState`, `Day08Alarm_UpdateHumidity()`, `Day08Alarm_ApplyCommand()`, `Day08Alarm_ShouldBuzz()`, and upstream JSON field `vision_alarm`.

- [x] **Step 1: Write a host-runnable C regression test**

Use these assertions:

```c
int main(void)
{
    Day08AlarmState state;
    Day08Alarm_Init(&state);

    Day08Alarm_UpdateHumidity(&state, 60.0f, 45.0f);
    assert(Day08Alarm_ShouldBuzz(&state) == 1);

    assert(Day08Alarm_ApplyCommand(&state, "vision_alarm_on") == 1);
    assert(Day08Alarm_ApplyCommand(&state, "alarm_off") == 1);
    assert(Day08Alarm_ShouldBuzz(&state) == 1);

    assert(Day08Alarm_ApplyCommand(&state, "vision_alarm_off") == 1);
    assert(Day08Alarm_ShouldBuzz(&state) == 0);

    Day08Alarm_UpdateHumidity(&state, 40.0f, 45.0f);
    assert(state.humidity_silenced == 0);
    assert(Day08Alarm_ApplyCommand(&state, "unknown") == 0);
    return 0;
}
```

- [x] **Step 2: Compile the test and verify failure**

Run:

```bash
cc -std=c99 -Wall -Wextra -Werror -I applications/sample/wifi-iot/app/day08_mqtt_new applications/sample/wifi-iot/app/day08_mqtt_new/day08_alarm.c applications/sample/wifi-iot/app/day08_mqtt_new/tests/test_day08_alarm.c -o /tmp/day08_alarm_test
```

Expected: compiler failure because `day08_alarm.c` and `day08_alarm.h` do not exist.

- [x] **Step 3: Implement the portable alarm state**

Define:

```c
typedef struct {
    int manual_alarm_on;
    int humidity_over;
    int humidity_silenced;
    int vision_alarm_on;
} Day08AlarmState;
```

`Day08Alarm_ShouldBuzz()` must return:

```c
return state->manual_alarm_on ||
       state->vision_alarm_on ||
       (state->humidity_over && !state->humidity_silenced);
```

`alarm_on` sets `manual_alarm_on` and clears `humidity_silenced`, without changing `vision_alarm_on`. `alarm_off` clears only `manual_alarm_on` and sets `humidity_silenced`; it never changes `vision_alarm_on`. `vision_alarm_off` clears only `vision_alarm_on`. A humidity value at or below 45 clears `humidity_silenced` and re-arms the next humidity excursion.

- [x] **Step 4: Integrate the state module into MQTT and telemetry**

Add `day08_alarm.c` to `sources`. Replace the three separate alarm globals with one `Day08AlarmState`. After humidity samples or recognized commands, call:

```c
Day08_SetBuzzer(Day08Alarm_ShouldBuzz(&g_alarm_state));
```

Add telemetry field:

```c
"\"vision_alarm\":%d,"
```

and pass `g_alarm_state.vision_alarm_on` to `snprintf`. Extend `parse_env_message()` with `vision_alarm`, preserving all existing fields.

- [x] **Step 5: Run portable C and Python parser tests**

```bash
/tmp/day08_alarm_test
.venv/bin/python -m unittest tests.test_bemfa_vision_alarm -v
.venv/bin/python -m unittest discover -s tests -v
```

Expected: C test exits 0; parser returns `vision_alarm` as `0` or `1`; all Python tests pass.

- [x] **Step 6: Commit embedded alarm separation**

```bash
git add applications/sample/wifi-iot/app/day08_mqtt_new/day08_alarm.h applications/sample/wifi-iot/app/day08_mqtt_new/day08_alarm.c applications/sample/wifi-iot/app/day08_mqtt_new/tests/test_day08_alarm.c applications/sample/wifi-iot/app/day08_mqtt_new/BUILD.gn applications/sample/wifi-iot/app/day08_mqtt_new/mqtt.c smart-home-console/bemfa_api.py smart-home-console/tests/test_bemfa_vision_alarm.py
git commit -m "feat: separate Hi3861 vision alarm state"
```

---

### Task 5: Integrate Zone Events into `VisionService`

**Files:**
- Modify: `smart-home-console/vision_service.py:15-306`
- Modify: `smart-home-console/tests/test_vision_service.py`

**Interfaces:**
- Consumes: `ZoneDetector`, `EventRepository`, `VisionAlarmController`, YOLO `boxes.xyxy`, and a snapshot directory.
- Produces: foot-point extraction, server-side zone overlay, evidence-event lifecycle, extended status, `save_zone()`, `delete_zone()`, `list_events()`, `acknowledge_event()`, `initialize_safety()`, and `shutdown_safety()`.

- [x] **Step 1: Write failing integration tests with injected fakes**

Extend the existing test fakes with a frame shape, pixel coordinates, a real temporary repository, and a recording alarm controller:

```python
class FakeFrame:
    def __init__(self, width=640, height=480):
        self.shape = (height, width, 3)


class FakeXyxy:
    def cpu(self):
        return self

    def tolist(self):
        return [[100.0, 100.0, 300.0, 400.0]]


class SafetyBoxes:
    xyxy = FakeXyxy()

    def __len__(self):
        return 1


class SafetyResult:
    boxes = SafetyBoxes()

    def __init__(self, frame):
        self.frame = frame

    def plot(self):
        return self.frame


class SafetyModel:
    def predict(self, frame, **_kwargs):
        return [SafetyResult(frame)]


class RecordingAlarm:
    def __init__(self):
        self.targets = []

    def set_alarm(self, enabled, event_id=None, force=False):
        self.targets.append((enabled, event_id))
        return True


def make_safety_service(self):
    temporary = tempfile.TemporaryDirectory()
    self.addCleanup(temporary.cleanup)
    clock = FakeClock()
    detector = ZoneDetector(2.0, 3.0, clock=clock)
    detector.set_zone(NormalizedZone(0.1, 0.1, 0.8, 0.8))
    repository = EventRepository(os.path.join(temporary.name, "events.db"))
    repository.initialize()
    alarm = RecordingAlarm()
    service = self.make_service(
        zone_detector=detector,
        event_repository=repository,
        alarm_controller=alarm,
        event_snapshot_dir=temporary.name,
        overlay_renderer=lambda frame, _zone, _state: frame,
    )
    return service, detector, repository, alarm, clock


def active_safety_service(self):
    service, detector, repository, alarm, clock = make_safety_service(self)
    service.process_frame(SafetyModel(), FakeFrame())
    clock.advance(2.0)
    service.process_frame(SafetyModel(), FakeFrame())
    return service, detector, repository, alarm, clock


def test_zone_alarm_creates_one_event_and_one_command(self):
    service, detector, repository, alarm, clock = make_safety_service(self)
    service.process_frame(SafetyModel(), FakeFrame())
    clock.advance(2.0)
    service.process_frame(SafetyModel(), FakeFrame())
    service.process_frame(SafetyModel(), FakeFrame())

    events = repository.list_events()
    self.assertEqual(len(events), 1)
    self.assertEqual(alarm.targets, [(True, events[0]["id"])])
    self.assertEqual(service.get_status()["zone_state"], "alarm_active")


def test_acknowledge_silences_without_rearming():
    service, detector, repository, alarm, clock = active_safety_service(self)
    event_id = repository.list_events()[0]["id"]

    result = service.acknowledge_event(event_id)

    self.assertIsNotNone(result["acknowledged_at"])
    self.assertEqual(alarm.targets[-1], (False, event_id))
    self.assertEqual(service.get_status()["zone_state"], "alarm_silenced")
```

Update `make_service()` to pass through each of the five new optional constructor arguments. Reuse Task 1's `FakeClock` definition in this test module rather than importing test code from another module.

Also test bottom-center normalization, no zone, outside-zone persons, three-second clearing, maximum people updates, screenshot failure, camera disconnect not advancing timers, and active-zone deletion.

- [x] **Step 2: Run focused tests and verify failure**

```bash
.venv/bin/python -m unittest tests.test_vision_service -v
```

Expected: failures because phase-1 `VisionService` has no safety dependencies or extended status.

- [x] **Step 3: Extend constructor and helpers**

Add optional constructor arguments so existing phase-1 tests remain valid:

```python
zone_detector: ZoneDetector | None = None
event_repository: EventRepository | None = None
alarm_controller: VisionAlarmController | None = None
event_snapshot_dir: str | None = None
overlay_renderer: Callable[[Any, NormalizedZone | None, ZoneState], Any] | None = None
```

Implement `extract_foot_points(boxes, frame_width, frame_height)` by converting `boxes.xyxy.cpu().tolist()`. Each point is `((x1 + x2) / 2 / width, y2 / height)`, clamped to `[0, 1]`.

- [x] **Step 4: Coordinate state transitions without network I/O**

During `process_frame()`:

1. Run YOLO and produce the normal annotated frame.
2. Extract foot points and call `ZoneDetector.update()`.
3. Draw the saved zone green, pending amber, active red, or silenced gray.
4. Encode the final frame once.
5. On `alarm_started`, write the encoded bytes to the evidence directory, create the event, bind its ID, and enqueue alarm-on.
6. While active, update `max_people` only when it increases.
7. On `alarm_cleared`, close the event with `person_left` and enqueue alarm-off.

`get_status()` must merge phase-1 fields with exactly `zone`, `zone_state`, `people_in_zone`, `active_event_id`, `enter_elapsed`, `exit_elapsed`, and `alarm_delivery_error`. `acknowledge_event()` must update SQLite, transition the detector, and enqueue alarm-off in that order.

If snapshot writing fails, create the event with an empty filename and store the filesystem message in `last_error`; still enqueue alarm-on. If event creation fails, do not bind a fake ID, but still enqueue alarm-on with `event_id=None`. `delete_zone()` must persist deletion before mutating the detector; if an event was active, close it as `zone_deleted` and enqueue alarm-off. `save_zone()` follows the same persist-first rule so an SQLite failure leaves the in-memory zone unchanged.

- [x] **Step 5: Implement lifecycle recovery and shutdown**

`initialize_safety()` initializes SQLite, loads the zone, closes stale events as `server_restart`, starts the alarm worker, and calls `set_alarm(False, force=True)`. `shutdown_safety()` stops frame processing, closes any active event as `server_shutdown`, forces alarm-off, waits at most 3 seconds, and stops the alarm worker.

- [x] **Step 6: Run focused and full tests**

```bash
.venv/bin/python -m unittest tests.test_vision_service -v
.venv/bin/python -m unittest discover -s tests -v
```

Expected: integration tests and all phase-1 tests pass.

- [x] **Step 7: Commit vision integration**

```bash
git add smart-home-console/vision_service.py smart-home-console/tests/test_vision_service.py
git commit -m "feat: detect and record zone intrusions"
```

---

### Task 6: FastAPI Zone and Event Endpoints

**Files:**
- Modify: `smart-home-console/app.py:40-72,150-180,198-217,325-355`
- Modify: `smart-home-console/tests/test_vision_api.py`

**Interfaces:**
- Consumes: the extended singleton `VisionService` API.
- Produces: zone CRUD, event listing/acknowledgment, and corrected startup/shutdown ordering.

- [x] **Step 1: Write failing API tests**

Add a fake service that stores a zone and events, then test:

```python
def test_put_zone_validates_and_persists(self):
    response = self.client.put(
        "/api/vision/zone",
        json={"x": 0.1, "y": 0.2, "width": 0.4, "height": 0.5},
    )
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()["zone"]["width"], 0.4)


def test_zone_outside_frame_returns_422(self):
    response = self.client.put(
        "/api/vision/zone",
        json={"x": 0.8, "y": 0.2, "width": 0.4, "height": 0.5},
    )
    self.assertEqual(response.status_code, 422)


def test_acknowledging_closed_event_returns_409(self):
    response = self.client.post("/api/vision/events/22/ack")
    self.assertEqual(response.status_code, 409)
```

Also test GET/DELETE zone, default event ordering, limit 201 rejection, missing-event 404, and idempotent active acknowledgment.

- [x] **Step 2: Run API tests and verify route failures**

```bash
.venv/bin/python -m unittest tests.test_vision_api -v
```

Expected: new requests return 404 before route implementation.

- [x] **Step 3: Add validated request models and routes**

Define `VisionZoneBody` with bounded floats and a model-level `x + width` / `y + height` check. Add:

```python
@app.get("/api/vision/zone")
@app.put("/api/vision/zone")
@app.delete("/api/vision/zone")
@app.get("/api/vision/events")
@app.post("/api/vision/events/{event_id}/ack")
```

Map `EventNotFoundError` to 404, `EventClosedError` to 409, persistence errors to 503, and unexpected errors to the existing `{ok: false, error: string}` JSON format.

For event responses, add a derived `snapshot_url`: use `/static/vision_events/{URL-encoded filename}` when `snapshot_filename` is nonempty and `null` otherwise. The route must never expose the absolute evidence-directory path. Validate `limit` with FastAPI bounds `ge=1, le=200` so invalid values return 422.

- [x] **Step 4: Update singleton construction and lifespan**

Create repository, detector, and alarm controller from `config.py`. The controller sender is:

```python
lambda command: bemfa_api.send_msg(config.ENV_TOPIC, command)
```

Pass `repository.mark_delivery` as the controller's delivery callback so the final result for `vision_alarm_on` or `vision_alarm_off` reaches the matching event. When `event_id` is `None`, the callback only updates the controller-level error exposed by status and performs no event-row update.

Lifespan startup calls `vision_service.initialize_safety()` before `vision_service.start()`. Shutdown calls `vision_service.stop()` before `vision_service.shutdown_safety()`.

- [x] **Step 5: Run API and full tests**

```bash
.venv/bin/python -m unittest tests.test_vision_api -v
.venv/bin/python -m unittest discover -s tests -v
```

Expected: all API status codes and existing interfaces pass.

- [x] **Step 6: Commit the API**

```bash
git add smart-home-console/app.py smart-home-console/tests/test_vision_api.py
git commit -m "feat: expose zone intrusion APIs"
```

---

### Task 7: Browser Zone Editor and Event History

**Files:**
- Modify: `smart-home-console/templates/index.html:191-520,592-665,803-1375`
- Modify: `smart-home-console/tests/test_vision_template.py`

**Interfaces:**
- Consumes: `/api/vision/zone`, `/api/vision/events`, `/api/vision/events/{id}/ack`, extended status, and static evidence image URLs.
- Produces: rectangle editor, zone-state display, active-event silence control, and event history.

- [x] **Step 1: Extend the failing HTML contract test**

Assert the template includes:

```python
for element_id in (
    "visionZoneCanvas",
    "visionZoneEditButton",
    "visionZoneSaveButton",
    "visionZoneCancelButton",
    "visionZoneDeleteButton",
    "visionZoneState",
    "visionPeopleInZone",
    "visionActiveAlert",
    "visionAckButton",
    "visionEventList",
):
    self.assertIn(f'id="{element_id}"', self.html)

self.assertIn('fetch("/api/vision/zone"', self.html)
self.assertIn('fetch("/api/vision/events"', self.html)
self.assertIn("function imageContentRect()", self.html)
self.assertIn("function normalizedZoneFromDrag", self.html)
```

- [x] **Step 2: Run template tests and verify failure**

```bash
.venv/bin/python -m unittest tests.test_vision_template -v
```

Expected: missing element IDs and JavaScript functions.

- [x] **Step 3: Add the overlay and editor controls**

Place `<canvas id="visionZoneCanvas">` absolutely over `#visionStream`. In normal mode set `pointer-events: none`; in editing mode enable pointer events and crosshair cursor. Add edit/save/cancel/delete buttons and disable save until the drag rectangle satisfies the 0.02 minimum dimensions.

Implement `imageContentRect()` from the `<img>` element's client size and `naturalWidth/naturalHeight`, accounting for `object-fit: contain`. Convert pointer positions through that rectangle before normalizing. Do not include letterbox pixels.

- [x] **Step 4: Add status and event rendering**

Map server states to Chinese labels and colors:

```javascript
const ZONE_STATE_LABELS = {
  disabled: "未设置区域",
  armed: "已布防",
  enter_pending: "进入判定中",
  alarm_active: "正在告警",
  alarm_silenced: "已确认静音"
};
```

Refresh events every 5 seconds and immediately after zone saves, deletes, alarms, and acknowledgments. Render snapshot links only when `snapshot_filename` is nonempty. Escape all server-provided text before inserting HTML.

Use one escaping function for every interpolated event/error field:

```javascript
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  })[character]);
}
```

- [x] **Step 5: Run template and full tests**

```bash
.venv/bin/python -m unittest tests.test_vision_template -v
.venv/bin/python -m unittest discover -s tests -v
```

Expected: contract tests and all backend tests pass.

- [x] **Step 6: Commit the browser interface**

```bash
git add smart-home-console/templates/index.html smart-home-console/tests/test_vision_template.py
git commit -m "feat: add browser danger-zone editor"
```

---

### Task 8: Documentation and End-to-End Verification

**Files:**
- Modify: `smart-home-console/README.md`
- Modify: `applications/sample/wifi-iot/app/day08_mqtt_new/README.md`
- Modify: `docs/superpowers/plans/2026-07-22-yolo-zone-alarm-phase2.md`

**Interfaces:**
- Consumes: the completed Python, browser, and Hi3861 behavior.
- Produces: reproducible deployment, firmware, test, and acceptance instructions.

- [x] **Step 1: Document exact run and firmware steps**

Add:

- phase-2 architecture and data paths;
- environment variables `VISION_DB_PATH`, `VISION_EVENT_DIR`, `VISION_ENTER_SECONDS`, and `VISION_EXIT_SECONDS`;
- all five new API routes and event response fields;
- drawing, saving, deleting, acknowledging, and re-arming behavior;
- commands `vision_alarm_on/off` and the combined buzzer truth table;
- OpenHarmony build command `python build.py wifiiot` from the repository root;
- serial-output checks for both vision commands and `vision_alarm` telemetry;
- backup/removal instructions for the runtime DB and evidence directory without committing either.

- [x] **Step 2: Run fresh full Python verification**

```bash
cd smart-home-console
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q app.py config.py bemfa_api.py camera.py vision_service.py zone_detector.py event_repository.py vision_alarm.py tests
```

Expected: zero failures and zero compilation errors.

- [x] **Step 3: Run portable C verification**

```bash
cd ..
cc -std=c99 -Wall -Wextra -Werror -I applications/sample/wifi-iot/app/day08_mqtt_new applications/sample/wifi-iot/app/day08_mqtt_new/day08_alarm.c applications/sample/wifi-iot/app/day08_mqtt_new/tests/test_day08_alarm.c -o /tmp/day08_alarm_test
/tmp/day08_alarm_test
```

Expected: compile exit 0 and test exit 0.

- [ ] **Step 4: Run OpenHarmony build on the configured Ubuntu machine**

```bash
python build.py wifiiot
```

Expected: `Hi3861_wifiiot_app.out` links successfully and build logs include `day08_alarm.c` and `day08_mqtt_new`.

> Deferred: requires the project configured Ubuntu OpenHarmony/Hi3861 toolchain; it is not available in this Mac worktree.

- [ ] **Step 5: Perform real hardware acceptance**

Verify in order:

1. Save one rectangle and refresh/restart to confirm persistence.
2. Walk outside the rectangle for at least 5 seconds; no event appears.
3. Enter for less than 2 seconds; no event appears.
4. Enter for at least 2 seconds; one event, one snapshot, red status, and buzzer appear.
5. Stay inside for another 10 seconds; no duplicate event appears.
6. Acknowledge; vision alarm silences without re-arming.
7. Leave for at least 3 seconds; event closes and system re-arms.
8. Force humidity above 45%, trigger then clear vision alarm, and confirm humidity still holds the buzzer on.
9. Disconnect/reconnect the camera and confirm no false `person_left` event is generated during missing frames.
10. Restart `app.py` during an active event and confirm stale state closes with `server_restart` and hardware receives forced vision-off.

> Deferred: requires the project Ubuntu machine, connected Hi3861/Bemfa hardware path, and a live camera browser acceptance setup.

- [x] **Step 6: Inspect scope and runtime artifacts**

```bash
git diff --check
git status --short
git diff --stat codex/yolo-vision-phase1...HEAD
```

Expected: no model weights, database files, evidence images, credentials, or unrelated edits appear.

- [x] **Step 7: Mark this plan complete and commit documentation**

Change all completed checkboxes in this plan to `[x]`, then run:

```bash
git add smart-home-console/README.md applications/sample/wifi-iot/app/day08_mqtt_new/README.md docs/superpowers/plans/2026-07-22-yolo-zone-alarm-phase2.md
git commit -m "docs: document phase-two zone alarms"
```
