<p align="center">
  <h1 align="center">🏠 智能家居实训控制台</h1>
  <p align="center">
    <strong>Smart Home Training Console</strong><br>
    <sub>FastAPI · 巴法云 IoT · OpenCV · YOLO · Hi3861</sub>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
</p>

---

## 📖 简介

面向 **润和 HiSpark Hi3861** 与 Ubuntu 主机的无人实验室控制台。它将传感器查询、设备控制和 YOLO 视觉安全监控整合到一个统一界面中：

- 📊 **传感器面板** — 实时显示温度、湿度、气体浓度
- 🎮 **设备控制** — 一键控制交通灯、蜂鸣器、RGB 灯
- 🎥 **YOLO 安全监控** — 罗技 USB 摄像头实时画面、person 检测框和人数统计
- 🔄 **双模式** — 模拟模式（无硬件可跑）与真实巴法云模式一键切换

### 视觉子系统第二阶段

后台只打开一次摄像头和 YOLO 模型，所有网页客户端共享同一路 MJPEG。系统支持一个归一化矩形危险区域，以 person 检测框的底边中点判断是否进入。连续占用 2 秒创建一条事件和一张证据图；事件期间不重复创建，连续空置 3 秒后关闭并重新布防。

```text
罗技 USB 摄像头 → OpenCV 采集 → YOLO(person 底边中点)
                                  ├→ FastAPI MJPEG → 浏览器 Canvas 区域/状态/事件
                                  └→ ZoneDetector
                                      ├→ SQLite 事件 + JPEG 证据
                                      └→ 队列异步下发 Bemfa
                                          → vision_alarm_on/off
                                          → Hi3861 多源蜂鸣器
```

默认情况下，区域保存在 `data/vision_events.db` 的 `vision_zone` 表，事件保存在同库的 `vision_events` 表，证据图保存在 `static/vision_events/`。可分别用 `VISION_DB_PATH` 和 `VISION_EVENT_DIR` 覆盖；证据图始终通过专用的同源 `/vision-events/` URL 读取，API 不返回服务器绝对路径。当摄像头无帧或断线时状态计时器不会用空检测结果推进，避免误生成 `person_left`。

```
┌──────────┐     HTTP      ┌──────────────┐     HTTP API     ┌──────────┐
│  浏览器   │ ◄──────────► │  FastAPI 后端  │ ◄─────────────► │  巴法云   │
│  (HTML)  │   /api/...    │  (uvicorn)    │   getmsg/send   │  (IoT)   │
└──────────┘               │               │                 └────┬─────┘
                           │  ┌──────────┐ │                      │
                           │  │ YOLO监控 │ │                 MQTT│
                           │  │(person识别)│ │                      │
                           │  └──────────┘ │              ┌───────┴───────┐
                           └──────────────┘              │ Hi3861 硬件板  │
                                                          │ 传感器/执行器  │
                                                          └───────────────┘
```

---

## 🚀 快速开始

### Ubuntu 硬件检查

插入罗技摄像头后先确认 Linux 已识别设备：

```bash
lsusb
ls -l /dev/video*
v4l2-ctl --list-devices
```

如果系统没有 `v4l2-ctl`，安装 `v4l-utils`：

```bash
sudo apt update
sudo apt install -y v4l-utils
```

如果当前用户无权访问 `/dev/video0`，可加入 `video` 组，然后注销并重新登录：

```bash
sudo usermod -aG video "$USER"
```

### 环境要求

| 工具 | 版本 |
|------|------|
| Python | 3.10–3.12（推荐3.11） |
| pip | 最新版 |

### 安装与启动

```bash
# 1. 克隆仓库
git clone https://github.com/limark-00/200-1.git
cd 200-1/smart-home-console

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置巴法云（可选，不影响模拟模式）
#    通过 BEMFA_UID 环境变量注入私钥，不要写入或提交源码

# 5. 启动
python app.py
```

首次启动视觉服务时，Ultralytics 会自动下载默认的 `yolo11n.pt`。Ubuntu 没有显示器也可运行，在同一局域网的其他电脑访问 `http://Ubuntu主机IP:5001`即可。

若摄像头不是 `/dev/video0`，用环境变量切换索引：

```bash
VISION_CAMERA_INDEX=1 python app.py
```

打开浏览器访问：
| 地址 | 用途 |
|------|------|
| [http://127.0.0.1:5001](http://127.0.0.1:5001) | 🏠 控制台首页 |
| [http://127.0.0.1:5001/docs](http://127.0.0.1:5001/docs) | 📚 Swagger API 文档 |
| [http://127.0.0.1:5001/redoc](http://127.0.0.1:5001/redoc) | 📖 ReDoc 文档 |

---

## 🧱 项目结构

```
smart-home-console/
├── app.py                 # FastAPI路由、生命周期和后台服务
├── config.py              # 全局配置：UID、Topic、端口、模式开关
├── bemfa_api.py           # 巴法云 HTTP 封装：getmsg / send / Mock
├── camera.py              # 摄像头抓拍：OpenCV 拍照 + 占位图降级 + 图像识别预留
├── vision_service.py       # 单例摄像头、YOLO、MJPEG 和区域事件协调
├── zone_detector.py        # 纯危险区域状态机
├── event_repository.py     # SQLite 区域和事件存储
├── vision_alarm.py         # 队列式巴法云视觉报警下发
├── requirements.txt       # Python 依赖清单
├── README.md              # 本文件
├── 实训技术文档.md          # 完整教学文档（原理 / 修改指南 / API 测试）
├── test_bemfa.py          # 巴法云 API 独立测试脚本
├── templates/
│   └── index.html         # 前端页面（Jinja2 模板）
└── static/
    ├── style.css          # 样式
    ├── script.js          # 前端交互逻辑
    ├── captures/          # PIR/手动抓拍（.gitignore 排除）
    └── vision_events/     # 危险区事件证据（.gitignore 排除）
```

---

## 🔌 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 控制台首页 |
| `GET` | `/api/mode` | 查询当前模式（模拟 / 真实） |
| `POST` | `/api/mode` | 切换模式 `{"mock": true/false}` |
| `GET` | `/api/sensor/{topic}` | 查询指定主题最新数据 |
| `GET` | `/api/env` | 读取 env004 环境数据（温湿度/气体） |
| `POST` | `/api/env/send` | 向 env004 下发消息 |
| `GET` | `/api/vision/status` | 查询摄像头、模型、人数和帧率 |
| `GET` | `/api/vision/frame` | 获取最新 YOLO 标注 JPEG |
| `GET` | `/api/vision/stream` | 获取共享 MJPEG 实时画面 |
| `GET` | `/api/vision/zone` | 读取已保存的单个危险区域 |
| `PUT` | `/api/vision/zone` | 保存 `x/y/width/height` 归一化矩形 |
| `DELETE` | `/api/vision/zone` | 删除区域；若有活动事件则以 `zone_deleted` 关闭 |
| `GET` | `/api/vision/events?limit=50` | 按 ID 倒序列出事件，`limit` 为 1–200 |
| `POST` | `/api/vision/events/{event_id}/ack` | 确认未关闭事件并仅关闭视觉报警 |
| `POST` | `/api/vision/alarm/silence` | 静音当前视觉报警；SQLite 降级且无事件行时仍可使用 |
| `GET` | `/vision-events/{filename}` | 读取配置证据目录中的文件名，不接受任意路径 |
| `POST` | `/api/control` | 下发控制指令 `{"topic":"...","msg":"..."}` |
| `GET` | `/api/captures` | 获取抓拍照片列表（倒序，最多 20 张） |
| `POST` | `/api/capture/now` | 手动立即抓拍一张 |
| `POST` | `/api/mock/pir` | 模拟 PIR 触发（仅模拟模式） |

> `/api/...` 接口可在 `/docs` 页面交互测试；`/vision-events/` 是静态证据挂载，请使用事件响应返回的 `snapshot_url`。

第二阶段视觉路由包含区域 CRUD、事件历史/确认、当前报警静音和证据读取。`zone` 为 `null` 或 `{x, y, width, height}`；坐标相对原始图像归一化，宽高至少为 `0.02` 且矩形不得越界。每条事件响应包含：

| 字段 | 含义 |
|------|------|
| `id` | 事件 ID |
| `started_at`, `ended_at` | UTC ISO-8601 开始/结束时间，未结束时 `ended_at=null` |
| `snapshot_filename`, `snapshot_url` | 证据文件名和可访问 URL；写图失败时分别为空字符串和 `null` |
| `max_people` | 该占用周期内区域中最多人数 |
| `acknowledged_at` | 确认时间，未确认时为 `null` |
| `close_reason` | `person_left`/`zone_deleted`/`server_restart`/`server_shutdown` 或 `null` |
| `alarm_on_delivered`, `alarm_off_delivered` | 开/关视觉报警命令是否成功送达 |
| `last_error` | 证据或命令送达的最终错误文本，无错误时为空字符串 |

`GET /api/vision/status` 还返回 `storage_error`：空字符串表示本地事件存储健康；非空时应将其视为粘性降级状态，直到待补写的关闭或投递审计信息成功对账。存储故障不会暴露数据库或证据目录的绝对路径。

### 命令行示例

```bash
# 查询环境数据
curl http://127.0.0.1:5001/api/env

# 控制交通灯
curl -X POST http://127.0.0.1:5001/api/control \
  -H "Content-Type: application/json" \
  -d '{"topic":"trafficLight","msg":"red"}'

# 手动抓拍
curl -X POST http://127.0.0.1:5001/api/capture/now
```

---

## ⚙️ 配置说明

编辑 `config.py` 或通过环境变量覆盖（建议）：

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| `BEMFA_UID` | `BEMFA_UID` | — | 巴法云私钥（必填） |
| `BEMFA_TYPE` | `BEMFA_TYPE` | `1` | 1=MQTT，3=TCP |
| `ENV_TOPIC` | `BEMFA_ENV_TOPIC` | `env004` | 下行控制主题 |
| `ENV_PUB_TOPIC` | `BEMFA_ENV_PUB_TOPIC` | `<ENV_TOPIC>/up` | 开发板上行环境数据和 `vision_alarm` 状态的读取主题 |
| `MOCK_MODE` | — | `False` | 启动默认模式 |
| `APP_PORT` | — | `5001` | 服务端口 |
| `CAPTURE_COOLDOWN` | — | `10` | 抓拍冷却时间（秒） |
| `PIR_POLL_INTERVAL` | — | `3` | PIR 轮询间隔（秒） |
| `VISION_ENABLED` | `VISION_ENABLED` | `1` | 是否启用 YOLO 视觉线程 |
| `VISION_CAMERA_INDEX` | `VISION_CAMERA_INDEX` | `0` | OpenCV 摄像头索引 |
| `VISION_MODEL` | `VISION_MODEL` | `yolo11n.pt` | YOLO 模型名或本地路径 |
| `VISION_CONFIDENCE` | `VISION_CONFIDENCE` | `0.40` | person 检测置信度 |
| `VISION_FRAME_SKIP` | `VISION_FRAME_SKIP` | `2` | 每隔多少帧执行一次推理 |
| `VISION_DB_PATH` | `VISION_DB_PATH` | `data/vision_events.db` | SQLite 数据库，相对路径以 `smart-home-console` 为基准 |
| `VISION_EVENT_DIR` | `VISION_EVENT_DIR` | `static/vision_events` | 事件 JPEG 写入及 `/vision-events/` 提供目录，相对路径以 `smart-home-console` 为基准 |
| `VISION_ENTER_SECONDS` | `VISION_ENTER_SECONDS` | `2.0` | 连续入侵多久后触发 |
| `VISION_EXIT_SECONDS` | `VISION_EXIT_SECONDS` | `3.0` | 连续空置多久后关闭事件并重新布防 |

---

## 🔄 模拟模式 vs 真实模式

| | 🧪 模拟模式 | ☁️ 巴法云真实模式 |
|--|-----------|----------------|
| 传感器数据 | 内存随机生成 | 真实 `getmsg` 读取 |
| 设备控制 | 仅修改内存状态 | 实际 `sendMessage` 下发 |
| PIR 抓拍 | 点「模拟 PIR 触发」按钮 | 硬件上报后自动抓拍 |
| 切换方式 | 页面右上角开关 或 `POST /api/mode` | 同上 |

> 页面切换立即生效，重启后以 `config.MOCK_MODE` 为准。

---

## 🗺️ 危险区域操作和数据管理

1. 在视觉面板点「编辑区域」，从一角拖到对角；拖拽必须在真实图像内开始，黑边不计入归一化坐标。
2. 点「保存区域」写入 SQLite；刷新页面或重启服务后仍会恢复。点「取消」只丢弃未保存草图。
3. 点「删除区域」会停用检测；若当时有活动事件，它会被关闭并下发 `vision_alarm_off`。
4. 报警后点「确认并静音」只清除该事件的视觉蜂鸣源，事件仍活动、不会立即重新布防。人员连续离开 `VISION_EXIT_SECONDS` 后，事件以 `person_left` 关闭并重新布防。

备份前先优雅停止 `app.py`，避免 SQLite WAL 和 JPEG 在复制期间变化。下列最简命令**仅适用于默认路径**：

```bash
cd smart-home-console
mkdir -p ../../vision-backup-YYYYMMDD
cp -p data/vision_events.db ../../vision-backup-YYYYMMDD/
cp -R static/vision_events ../../vision-backup-YYYYMMDD/
```

使用环境变量覆盖后，必须从与服务相同的配置取值备份，不能继续假设默认目录：

```bash
cd smart-home-console
vision_db_path="${VISION_DB_PATH:-data/vision_events.db}"
vision_event_dir="${VISION_EVENT_DIR:-static/vision_events}"
vision_backup_dir="../../vision-backup-YYYYMMDD"
mkdir -p "$vision_backup_dir"
cp -p "$vision_db_path" "$vision_backup_dir/"
cp -R "$vision_event_dir" "$vision_backup_dir/vision_events"
```

备份目录应位于 `smart-home-console` 之外。现有 `.gitignore` 中数据库和证据的规则只覆盖默认路径；自定义路径应优先放在仓库外，否则必须将它的**精确路径**加入 `.git/info/exclude` 或团队共享的 `.gitignore`。每次备份、更改覆盖配置或提交前运行 `git status --short --ignored`，确认数据库、`-wal`/`-shm`、证据图和模型权重都未被跟踪。

如需清空本地运行数据，同样先停服务并完成备份，核对 `VISION_DB_PATH` 和 `VISION_EVENT_DIR` 的实际值后只删除这两个精确目标；默认证据目录需保留 `.gitkeep`。不要用未检查的递归命令、宽泛通配符或空环境变量删除数据。

## ✅ 第二阶段真机验收（必须按顺序）

1. 保存一个矩形，刷新页面并重启 `app.py`，确认区域仍存在。
2. 在区域外走动至少 5 秒，确认没有新事件。
3. 进入区域但少于 2 秒就离开，确认没有新事件。
4. 连续进入至少 2 秒，确认恰好一条事件、一张快照、红色状态和蜂鸣器同时出现。
5. 继续留在区域内 10 秒，确认没有重复事件。
6. 点击确认，确认视觉报警静音，但事件仍活动且未重新布防。
7. 离开至少 3 秒，确认事件关闭且系统重新布防。
8. 使湿度高于 45%，触发后再清除视觉报警，确认湿度源仍使蜂鸣器保持开启。
9. 断开再重连摄像头，确认缺帧期间不会误生成 `person_left`。
10. 在活动事件期间对验收实例执行优雅重启（例如 `systemctl restart`），确认当前事件以 `server_shutdown` 关闭，且硬件收到强制的 `vision_alarm_off`。
11. 仅在可恢复的独立验收实例上，先记录该实例的确切 PID，再用 `kill -9 <受控验收进程PID>` 模拟受控非正常终止。重启后确认遗留事件才以 `server_restart` 恢复关闭，并且强制发送 `vision_alarm_off`；不要对共享或生产实例执行此步骤。

---

## 🛠️ 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | API 服务 + 自动文档 |
| ASGI 服务器 | uvicorn | 进程启动与管理 |
| 模板引擎 | Jinja2 | 渲染控制台页面 |
| IoT 平台 | 巴法云 (bemfa.com) | MQTT 消息中转 |
| 计算机视觉 | OpenCV + Ultralytics YOLO | 摄像头采集、person检测和标注 |
| 图像处理 | Pillow / NumPy | 占位图生成 |
| 数据校验 | Pydantic | 请求体验证 |

---

## 📦 部署（Linux + Nginx + systemd）

安全边界：**本应用不包含内置身份认证**。`PUT`/`POST`/`DELETE` 控制与变更路由、`/api/vision/events` 历史、`/vision-events/` 证据以及 `/docs` 都包含敏感能力或信息，禁止直接暴露到公网。部署时必须选择并验证下列边界之一：

- 仅允许可信局域网网段，并同时用主机/云防火墙拒绝公网入站；
- 只允许经 VPN 进入的已授权用户访问；
- 若业务必须通过公网到达，在 TLS 终端上配置可审计的反向代理身份认证，默认拒绝未认证请求。

下方 Nginx 是一个**局域网限制示例**，`192.168.1.20` 必须替换为服务主机的局域网 IP，并与实际可信网段和防火墙规则一起复核。它不是公网部署配置。

```bash
# 1. 安装依赖
cd /path/to/smart-home-console
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. 配置仅限局域网的 Nginx 反向代理
sudo tee /etc/nginx/sites-available/smart-home << 'EOF'
server {
    listen 192.168.1.20:80;
    server_name _;

    allow 192.168.0.0/16;
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    deny all;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 3. 启用站点
sudo ln -s /etc/nginx/sites-available/smart-home /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 4. 创建 systemd 服务
sudo tee /etc/systemd/system/smart-home.service << 'EOF'
[Unit]
Description=Smart Home Console
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/path/to/smart-home-console
Environment="PATH=/path/to/smart-home-console/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/path/to/smart-home-console/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 5001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 5. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable --now smart-home
```

常用管理命令：
```bash
sudo systemctl status smart-home     # 查看状态
sudo systemctl restart smart-home   # 重启
sudo journalctl -u smart-home -f    # 实时日志
```

---

## 🧪 测试

### 1. 本地离线回归验证

在 `smart-home-console` 目录执行：

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q app.py config.py bemfa_api.py camera.py vision_service.py zone_detector.py event_repository.py vision_alarm.py tests
```

预期：单元测试零失败、零错误，`compileall` 零编译错误。这两条命令不需要连接真实摄像头、Hi3861 或巴法云。

### 2. 无摄像头：先验证其他界面

1. 使用 `VISION_ENABLED=0 python app.py` 关闭视觉线程
2. 打开首页，确认环境数据和报警控制仍正常
3. 访问 `/api/vision/status`，应看到 `"enabled": false`

### 3. Ubuntu 真实摄像头联调

1. 启动后访问 `http://127.0.0.1:5001/api/vision/status`
2. 确认 `model_loaded` 和 `camera_online` 都为 `true`
3. 打开首页，人走入画面后确认检测框、人数和 FPS 变化
4. 若改变了摄像头索引，重启后端再测试

### 4. 用 `/docs` 交互测试 API

打开 http://127.0.0.1:5001/docs → 展开接口 → Try it out → Execute

### 5. 巴法云连接测试（与本地回归分开）

`test_bemfa.py` 不在上述离线回归命令中；它可能根据当前配置访问真实巴法云，只在已确认 UID、Topic 和网络环境时单独执行：

```bash
python test_bemfa.py
```

---

## ❓ 常见问题

<details>
<summary><strong>端口被占用？</strong></summary>

修改 `config.py` 中的 `APP_PORT`，或杀掉占用进程：
```bash
lsof -i :5001
kill -9 <PID>
```
</details>

<details>
<summary><strong>巴法云报错 / 无数据？</strong></summary>

1. 检查 `BEMFA_UID` 是否正确（登录巴法云控制台查看）
2. 确认 `BEMFA_TYPE`：MQTT 填 `1`，TCP 填 `3`
3. 确认硬件板已向该主题发送过数据
4. 先用模拟模式验证界面功能，排除后端问题
</details>

<details>
<summary><strong>摄像头打不开？</strong></summary>

- 用 `v4l2-ctl --list-devices` 确认罗技设备对应的 `/dev/videoN`
- 将 `N` 传给 `VISION_CAMERA_INDEX`，例如 `VISION_CAMERA_INDEX=2 python app.py`
- 用 `ls -l /dev/videoN` 检查权限，并确认没有其他程序占用摄像头
- 查看 `/api/vision/status` 的 `last_error`，后台会每 2 秒自动尝试重连
</details>

<details>
<summary><strong>YOLO模型加载失败或速度慢？</strong></summary>

- 首次运行需要网络下载 `yolo11n.pt`，也可提前下载并用 `VISION_MODEL=/绝对路径/yolo11n.pt`
- CPU 主机可增大 `VISION_FRAME_SKIP`，例如设为 `3` 或 `4`
- 可降低 `VISION_IMAGE_SIZE`，例如 `VISION_IMAGE_SIZE=480`，以换取更高帧率
</details>

<details>
<summary><strong>真实模式 PIR 不抓拍？</strong></summary>

- 检查 `config.ENABLE_PIR_POLLER` 是否为 `True`（当前默认关闭）
- 确认硬件板 PIR 上报的消息内容被 `is_pir_triggered()` 正确匹配（`"1"`, `"on"`, `"true"` 等）
- 确认 `PIR_TOPIC` 和硬件发布主题一致
</details>

---

## 📚 延伸阅读

- [实训技术文档.md](./实训技术文档.md) — 面向小白的完整原理与修改指南
- [巴法云文档](https://cloud.bemfa.com/docs/) — IoT 平台官方文档
- [FastAPI 文档](https://fastapi.tiangolo.com/zh/) — 框架官方中文文档

---

## 📄 License

MIT © 2025
