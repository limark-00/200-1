# YOLO 危险区域入侵与独立告警系统设计

## 1. 目标

在第一阶段「实时监控 + YOLO 人员识别」基础上，增加一个可由用户在网页视频上拖拽设置的矩形危险区域。人员连续进入区域 2 秒后，系统应当：

1. 在网页显示入侵告警；
2. 保存一张带检测框和危险区域的证据截图；
3. 向 SQLite 写入告警事件；
4. 通过巴法云发送 `vision_alarm_on`；
5. 通过 Hi3861 独立的视觉告警状态驱动蜂鸣器。

人员连续离开危险区域 3 秒后，系统发送 `vision_alarm_off`、结束当前事件并自动重新布防。

## 2. 范围

### 2.1 本阶段包含

- 单个矩形危险区域；
- 网页拖拽绘制、保存、重绘和删除区域；
- 按人物检测框底边中心点进行区域命中判断；
- 2 秒连续进入、3 秒连续离开的防抖状态机；
- SQLite 事件持久化和证据截图；
- 告警事件查询、人工确认与本次静音；
- 巴法云视觉告警指令的去重、异步发送和有限重试；
- Hi3861 `day08_mqtt_new` 中的独立视觉告警状态；
- 视觉、湿度和网页人工告警的安全合并。

### 2.2 本阶段不包含

- 多个危险区域；
- 不规则多边形区域；
- NFC 授权后进入不报警；
- 人脸识别或人员身份判断；
- 多摄像头、跨摄像头跟踪；
- 云端视频存储；
- 事件自动清理或存储配额管理。

## 3. 总体架构

系统仍只运行一个 FastAPI 进程。现有 `VisionService` 继续独占摄像头和 YOLO 模型，新增三个职责独立的模块：

### 3.1 `ZoneDetector`

- 读取当前矩形区域；
- 将 YOLO 人物检测框转换为底边中心点；
- 统计当前区域内人数；
- 活动事件期间人数增大时，发出最大人数更新；
- 使用可注入的单调时钟管理进入和离开计时；
- 输出明确的状态转换事件，不直接访问数据库或巴法云。

### 3.2 `EventRepository`

- 初始化和升级 SQLite 表；
- 持久化唯一的危险区域配置；
- 新建、结束、查询和确认告警事件；
- 记录巴法云指令发送结果与最后错误；
- 服务启动时将上次未结束事件标记为 `server_restart`。

### 3.3 `VisionAlarmController`

- 从内存队列消费告警开启、关闭任务；
- 调用现有 `bemfa_api.send_msg()` 发送 `vision_alarm_on/off`；
- 相同的目标状态不重复发送；
- 发送失败时最多尝试 3 次，间隔固定为 0、2、5 秒；
- 将最终投递状态写回对应事件；
- 网络操作不阻塞 YOLO 推理线程。

### 3.4 组件数据流

```text
摄像头帧
  → VisionService / YOLO person检测
  → ZoneDetector / 脚点与区域判断
  → 状态转换
      → 截图 + EventRepository
      → VisionAlarmController
      → 巴法云
      → Hi3861视觉告警状态
  → 绘制检测框、危险区域和告警颜色
  → MJPEG网页画面
```

### 3.5 并发边界

- `ZoneDetector` 使用一把可重入锁保护区域、计时器、当前事件 ID 和状态转换；
- YOLO 线程调用检测入口，FastAPI 请求线程调用区域更新、删除和事件确认入口；
- `EventRepository` 每次操作使用独立 SQLite 连接，开启 WAL、外键和 3000 毫秒 `busy_timeout`，不在线程之间共享连接对象；
- `VisionAlarmController` 只有一个队列消费线程，保证指令按顺序投递；
- YOLO 线程只将状态转换放入队列，不在帧处理路径中执行网络请求。

## 4. 危险区域坐标

矩形区域使用归一化坐标，不依赖视频分辨率：

```json
{
  "x": 0.10,
  "y": 0.20,
  "width": 0.40,
  "height": 0.50
}
```

约束：

- `0 <= x < 1`；
- `0 <= y < 1`；
- `0.02 <= width <= 1`；
- `0.02 <= height <= 1`；
- `x + width <= 1`；
- `y + height <= 1`。

服务端将检测框底边中心点 `(center_x, bottom_y)` 转换为归一化坐标后判断是否在区域内。网页绘制时，必须按 `object-fit: contain` 后图像的真实显示矩形换算指针坐标，排除黑边对坐标的影响。

## 5. 状态机

### 5.1 状态

- `DISABLED`：没有已启用的危险区域；
- `ARMED`：已布防，区域内无人；
- `ENTER_PENDING`：区域内检测到人，但尚未连续达到 2 秒；
- `ALARM_ACTIVE`：已生成事件且视觉蜂鸣器处于开启目标状态；
- `ALARM_SILENCED`：用户已确认并关闭本次视觉告警，但人员尚未连续离开 3 秒。

### 5.2 状态转换

1. `DISABLED -> ARMED`：保存有效区域。
2. `ARMED -> ENTER_PENDING`：区域内人数从 0 变为大于 0。
3. `ENTER_PENDING -> ARMED`：2 秒内区域人数恢复为 0。
4. `ENTER_PENDING -> ALARM_ACTIVE`：区域内连续有人达到 2 秒。此转换仅生成一个事件。
5. `ALARM_ACTIVE -> ALARM_SILENCED`：用户确认当前事件并发送 `vision_alarm_off`。
6. `ALARM_ACTIVE/ALARM_SILENCED -> ARMED`：区域内连续无人达到 3 秒，结束事件；如尚未静音，发送 `vision_alarm_off`。
7. 任意启用状态 `-> DISABLED`：删除区域。如存在活动事件，以 `zone_deleted` 原因结束并发送 `vision_alarm_off`。

在 `ALARM_ACTIVE` 或 `ALARM_SILENCED` 中，人员短暂离开不会立即结束事件；如 3 秒内重新进入，离开计时清零。

## 6. SQLite 数据设计

数据库路径：`smart-home-console/data/vision_events.db`。

### 6.1 `vision_zone`

单例表，固定使用 `id = 1`：

- `id INTEGER PRIMARY KEY CHECK (id = 1)`；
- `x REAL NOT NULL`；
- `y REAL NOT NULL`；
- `width REAL NOT NULL`；
- `height REAL NOT NULL`；
- `enabled INTEGER NOT NULL DEFAULT 1`；
- `updated_at TEXT NOT NULL`。

### 6.2 `vision_events`

- `id INTEGER PRIMARY KEY AUTOINCREMENT`；
- `started_at TEXT NOT NULL`；
- `ended_at TEXT NULL`；
- `snapshot_filename TEXT NOT NULL`；
- `max_people INTEGER NOT NULL DEFAULT 1`；
- `acknowledged_at TEXT NULL`；
- `close_reason TEXT NULL`；
- `alarm_on_delivered INTEGER NOT NULL DEFAULT 0`；
- `alarm_off_delivered INTEGER NOT NULL DEFAULT 0`；
- `last_error TEXT NOT NULL DEFAULT ''`。

`ended_at IS NULL` 表示活动事件。第二阶段不自动删除事件或截图。事件查询默认返回最新 50 条，单次上限 200 条。

## 7. 证据截图

- 保存目录：`smart-home-console/static/vision_events/`；
- 触发 `ALARM_ACTIVE` 时保存当前最新的 YOLO 标注帧；
- 截图必须包含人物检测框、危险区域和告警颜色；
- 文件名使用事件时间和随机后缀，避免同秒冲突；
- 数据库只保存文件名，不保存任意绝对路径。

## 8. FastAPI 接口

### 8.1 危险区域

```text
GET    /api/vision/zone
PUT    /api/vision/zone
DELETE /api/vision/zone
```

`PUT` 请求体：

```json
{
  "x": 0.10,
  "y": 0.20,
  "width": 0.40,
  "height": 0.50
}
```

服务端对第 4 节中的所有坐标约束进行校验，非法参数返回 HTTP 422。

### 8.2 告警事件

```text
GET  /api/vision/events?limit=50
POST /api/vision/events/{event_id}/ack
```

- 事件列表按 `id DESC` 返回；
- `ack` 仅允许确认当前活动事件；
- 不存在的事件返回 404；
- 已结束事件的确认请求返回 409；
- 重复确认是幂等操作，返回当前事件状态。

### 8.3 视觉状态扩展

`GET /api/vision/status` 保留现有字段并增加：

- `zone`：当前区域或 `null`；
- `zone_state`：状态机当前状态；
- `people_in_zone`：当前区域内人数；
- `active_event_id`：当前事件 ID 或 `null`；
- `enter_elapsed`：当前进入计时；
- `exit_elapsed`：当前离开计时；
- `alarm_delivery_error`：最后一次视觉告警指令错误。

## 9. 网页交互

在现有 YOLO 视觉面板内增加：

1. 与视频图像重合的透明 `canvas`；
2. 「编辑危险区域」、「保存」、「取消」、「删除」按钮；
3. 拖拽起点和终点构成一个矩形；
4. 对保存区域进行比例坐标转换；
5. 未编辑时画布不拦截视频面板的普通操作；
6. 状态徽标：未设置、已布防、进入判定中、正在告警、已确认静音；
7. 告警时危险区域及面板使用红色告警样式；
8. 事件列表显示事件编号、起止时间、持续时间、最大人数、截图、确认和投递状态；
9. 活动事件提供「确认并静音」操作。

视频流中的危险区域和告警颜色由服务端绘制，即使不进入编辑模式，所有浏览器也能看到同一区域。

## 10. Hi3861 蜂鸣器状态合并

### 10.1 新增状态

`day08_mqtt_new/mqtt.c` 新增：

```c
static volatile int g_vision_alarm_on = 0;
static volatile int g_humidity_over = 0;
```

### 10.2 统一输出决策

新增 `Day08_RefreshBuzzer()`，且只有该函数根据业务状态决定最终开关：

```text
buzzer_on =
    g_manual_alarm_on
    OR g_vision_alarm_on
    OR (g_humidity_over AND NOT g_humidity_alarm_silenced)
```

`Day08_UpdateHumidityAlarm()` 改为更新湿度状态和自动解除静音，然后调用 `Day08_RefreshBuzzer()`。

### 10.3 MQTT 指令

- `alarm_on`：保留现有人工开启逻辑，不改变视觉状态；
- `alarm_off`：保留现有人工关闭及湿度本次静音逻辑，不改变视觉状态；
- `vision_alarm_on`：设置 `g_vision_alarm_on = 1`；
- `vision_alarm_off`：设置 `g_vision_alarm_on = 0`；
- 每次状态改变后调用 `Day08_RefreshBuzzer()`。

上行 JSON 增加 `"vision_alarm": 0/1`，同时扩展 `bemfa_api.parse_env_message()` 解析该字段，供网页查看开发板实际状态。

## 11. 异常处理

### 11.1 巴法云不可用

- 事件和截图仍然保存；
- 最多发送 3 次；
- 失败结果写入 `last_error`；
- 网页明确显示蜂鸣器指令未投递；
- 系统不因网络失败重复创建告警事件。

### 11.2 SQLite 不可用

- 实时视频和区域判断不停止；
- 状态接口返回数据库错误；
- 区域保存或删除失败时返回 HTTP 503，内存中的区域保持不变；
- 不伪造已保存的事件 ID；
- 即使本地事件无法持久化，已确认的区域入侵仍尝试发送 `vision_alarm_on`；
- 如告警已在硬件端开启，离开或人工静音仍发送关闭指令。

### 11.3 摄像头不可用

- 复用第一阶段自动重连；
- 保留 SQLite 中的区域；
- 无新帧时不推进进入或离开计时；
- 不将「摄像头断开」当作「人已离开」。

### 11.4 证据截图写入失败

- 告警事件和蜂鸣器投递仍继续；
- `snapshot_filename` 保存空字符串；
- 文件系统错误写入事件 `last_error`；
- 网页事件列表显示「截图保存失败」，不生成无效图片链接。

### 11.5 进程异常退出

- 启动顺序固定为：初始化数据库、恢复区域、关闭遗留事件、启动告警工作线程、强制发送一次 `vision_alarm_off`、启动视觉线程；
- 启动清理指令使用 `force` 标志绕过目标状态去重，保证开发板确实收到 `vision_alarm_off`；
- 上次未结束事件以 `server_restart` 原因关闭；
- 若区域仍有人，新进程连续检测 2 秒后创建新事件并重新开启视觉告警。

### 11.6 正常关闭

- 先停止摄像头与 YOLO 线程，避免再生成新事件；
- 如存在活动事件，以 `server_shutdown` 原因关闭；
- 强制队列化 `vision_alarm_off`，最多等待 3 秒完成第一次投递；
- 最后停止告警工作线程。

## 12. 测试策略

### 12.1 Python 单元测试

- 检测框底边中心点转换；
- 区域内部、边界、外部判断；
- 区域外检测框不引发状态转换；
- 2 秒进入防抖和 3 秒离开防抖；
- 中途进入、离开导致计时清零；
- 单次入侵只产生一次开启事件；
- 确认静音后不重复开启；
- 临时 SQLite 中的区域 CRUD、事件创建、结束、确认和启动恢复；
- 告警指令去重、失败重试和最终投递状态；
- 事件截图文件名和数据库字段一致。

### 12.2 FastAPI 测试

- 区域读取、保存和删除；
- 归一化坐标的范围校验；
- 事件列表排序和条数上限；
- 事件确认的 200、404、409 语义；
- 现有视频状态、单帧和 MJPEG 接口保持兼容；
- 现有巴法云环境数据和控制接口保持兼容。

### 12.3 网页合同和人工测试

- 危险区域绘制控件、状态字段和事件接口存在；
- 不同网页尺寸下区域位置保持一致；
- 编辑和非编辑模式的指针事件不冲突；
- 告警事件截图可正常打开；
- 活动事件确认后网页立即显示静音状态。

### 12.4 Hi3861 验证

- OpenHarmony 全量或对应目标编译通过；
- 串口能看到 `vision_alarm_on/off` 指令及状态更新；
- 只有视觉告警时，`vision_alarm_off` 能关闭蜂鸣器；
- 湿度告警仍活动时，`vision_alarm_off` 不能关闭蜂鸣器；
- 视觉告警仍活动时，现有 `alarm_off` 不能关闭蜂鸣器；
- 上行 JSON 的 `vision_alarm` 与开发板内部状态一致。

## 13. 验收标准

1. 用户能在网页画面中拖拽保存一个矩形危险区域。
2. 区域在刷新网页和重启 `app.py` 后仍存在。
3. 人员在区域外不产生告警。
4. 人员脚点在区域内连续 2 秒后，仅创建一条告警事件和一张截图。
5. 告警发生后，网页红色提示、SQLite 记录、证据截图和蜂鸣器均生效。
6. 人员离开区域连续 3 秒后，事件结束、视觉告警解除并自动重新布防。
7. 人工确认只对当前视觉事件静音，在人员离开前不重复告警。
8. 视觉告警解除不影响仍在进行的湿度告警。
9. 巴法云指令失败时，本地事件和截图仍可查看，页面显示投递错误。
10. 第一阶段实时画面、人数、FPS、单帧、MJPEG 和环境数据功能保持正常。

## 14. 运行数据与仓库

以下路径是运行时数据，不进入 Git：

```text
smart-home-console/data/vision_events.db
smart-home-console/static/vision_events/*
```

仓库保留所需的空目录占位文件，并在 `.gitignore` 中排除数据库、截图和 SQLite 临时文件。
