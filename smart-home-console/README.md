<p align="center">
  <h1 align="center">🏠 智能家居实训控制台</h1>
  <p align="center">
    <strong>Smart Home Training Console</strong><br>
    <sub>FastAPI · 巴法云 IoT · OpenCV · Hi3861</sub>
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

面向 **润和 HiSpark Hi3861** 智能家居套件的网页控制台。它将传感器查询、设备控制、PIR 人体感应抓拍整合到一个统一界面中：

- 📊 **传感器面板** — 实时显示温度、湿度、气体浓度
- 🎮 **设备控制** — 一键控制交通灯、蜂鸣器、RGB 灯
- 📸 **PIR 抓拍** — 人体感应触发时自动拍照，支持照片墙浏览
- 🔄 **双模式** — 模拟模式（无硬件可跑）与真实巴法云模式一键切换

```
┌──────────┐     HTTP      ┌──────────────┐     HTTP API     ┌──────────┐
│  浏览器   │ ◄──────────► │  FastAPI 后端  │ ◄─────────────► │  巴法云   │
│  (HTML)  │   /api/...    │  (uvicorn)    │   getmsg/send   │  (IoT)   │
└──────────┘               │               │                 └────┬─────┘
                           │  ┌──────────┐ │                      │
                           │  │ 摄像头抓拍 │ │                 MQTT│
                           │  │ (OpenCV)  │ │                      │
                           │  └──────────┘ │              ┌───────┴───────┐
                           └──────────────┘              │ Hi3861 硬件板  │
                                                          │ 传感器/执行器  │
                                                          └───────────────┘
```

---

## 🚀 快速开始

### 环境要求

| 工具 | 版本 |
|------|------|
| Python | 3.11+ |
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
#    编辑 config.py，设置 BEMFA_UID 环境变量或修改默认值

# 5. 启动
python app.py
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
├── app.py                 # FastAPI 主程序：路由 / 生命周期 / PIR 轮询线程
├── config.py              # 全局配置：UID、Topic、端口、模式开关
├── bemfa_api.py           # 巴法云 HTTP 封装：getmsg / send / Mock
├── camera.py              # 摄像头抓拍：OpenCV 拍照 + 占位图降级 + 图像识别预留
├── requirements.txt       # Python 依赖清单
├── README.md              # 本文件
├── 实训技术文档.md          # 完整教学文档（原理 / 修改指南 / API 测试）
├── test_bemfa.py          # 巴法云 API 独立测试脚本
├── templates/
│   └── index.html         # 前端页面（Jinja2 模板）
└── static/
    ├── style.css          # 样式
    ├── script.js          # 前端交互逻辑
    └── captures/          # 抓拍图片存放目录（.gitignore 排除）
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
| `POST` | `/api/control` | 下发控制指令 `{"topic":"...","msg":"..."}` |
| `GET` | `/api/captures` | 获取抓拍照片列表（倒序，最多 20 张） |
| `POST` | `/api/capture/now` | 手动立即抓拍一张 |
| `POST` | `/api/mock/pir` | 模拟 PIR 触发（仅模拟模式） |

> 以上接口均可在 `/docs` 页面直接交互测试。

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
| `MOCK_MODE` | — | `False` | 启动默认模式 |
| `APP_PORT` | — | `5001` | 服务端口 |
| `CAPTURE_COOLDOWN` | — | `10` | 抓拍冷却时间（秒） |
| `PIR_POLL_INTERVAL` | — | `3` | PIR 轮询间隔（秒） |

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

## 🛠️ 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | API 服务 + 自动文档 |
| ASGI 服务器 | uvicorn | 进程启动与管理 |
| 模板引擎 | Jinja2 | 渲染控制台页面 |
| IoT 平台 | 巴法云 (bemfa.com) | MQTT 消息中转 |
| 计算机视觉 | OpenCV | 摄像头拍照 |
| 图像处理 | Pillow / NumPy | 占位图生成 |
| 数据校验 | Pydantic | 请求体验证 |

---

## 📦 部署（Linux + Nginx + systemd）

```bash
# 1. 安装依赖
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. 配置 Nginx 反向代理
sudo tee /etc/nginx/sites-available/smart-home << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name your-domain.com;
    ssl_certificate /etc/nginx/cert/xxx.pem;
    ssl_certificate_key /etc/nginx/cert/xxx.key;
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
Environment="PATH=/path/to/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/path/to/.venv/bin/uvicorn app:app --host 0.0.0.0 --port 5001
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

### 1. 无硬件：模拟模式跑通界面

1. 确保右上角为「模拟模式」
2. 设备数据约 5 秒自动刷新
3. 点击灯 / 蜂鸣器 / RGB 按钮 → 状态行显示「已下发」
4. 点击「模拟 PIR 触发」→ 几秒后照片墙出现抓拍图
5. 点击「立即抓拍」→ 直接测试摄像头

### 2. 用 `/docs` 交互测试 API

打开 http://127.0.0.1:5001/docs → 展开接口 → Try it out → Execute

### 3. 独立测试巴法云连接

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

- 服务器环境无摄像头会自动生成占位图，不影响其他功能
- 检查摄像头索引：大部分笔记本内置摄像头为 `0`，外接可能为 `1`、`2`
- 修改 `camera.py` 的 `capture_photo(camera_index=0)` 参数
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
