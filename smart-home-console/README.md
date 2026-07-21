# 智能家居实训控制台（FastAPI + 巴法云 + 摄像头）

面向润和 HiSpark Hi3861 智能家居套件的网页控制台：查询传感器、下发灯/蜂鸣器指令，并在人体感应（PIR）触发时用电脑摄像头抓拍。

**给小白学生的完整原理与测试说明 → [`实训技术文档.md`](./实训技术文档.md)**  
（FastAPI 用法、如何测 API、如何挂服务、前后端/巴法云/摄像头交互）

本项目后端为 **FastAPI**（由 uvicorn 启动）。浏览器打开 `/docs` 可交互测试全部接口。

## 为什么推荐独立 venv，而不是共用 conda 的 `py01`？

| 方式 | 适合谁 | 给学生时的问题 |
|------|--------|----------------|
| 你本机的 conda `py01`（包很多） | 老师自己临时调试 | 学生环境对不上；依赖不清晰 |
| **项目内独立 venv + `requirements.txt`** | 课堂分发 | 每人一套干净环境，按文档即可复现 |

**结论：分发给学生请用 venv（或新建专用 conda 环境，只装本项目依赖）。**

### 推荐给学生的环境命令（Windows）

```bat
cd D:\chinasoft\XTU\smart-home-console
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
python app.py
```

或 conda：

```bat
conda create -n smart-home python=3.11 -y
conda activate smart-home
pip install -r requirements.txt
python app.py
```

---

## 项目结构

```
smart-home-console/
├── app.py                 # FastAPI 主程序 + PIR 后台轮询
├── config.py              # uid、topic、MOCK 开关、端口等
├── bemfa_api.py           # 巴法云 HTTP 封装（含 Mock）
├── camera.py              # 摄像头抓拍 + recognize_image 占位
├── requirements.txt
├── README.md
├── 实训技术文档.md
├── templates/index.html
└── static/
    ├── style.css
    ├── script.js
    └── captures/          # 抓拍图片存放目录
```

---

## 配置真实巴法云 topic

1. 打开 [巴法云控制台](https://cloud.bemfa.com/)
2. 创建/查看主题名（与板端固件一致）
3. 编辑 `config.py` 中的 `BEMFA_UID`、`BEMFA_TYPE` 与各 `*_TOPIC`
4. 控制指令（`red` / `on` / `off` 等）需与板端固件约定一致
5. PIR「有人」判定见 `bemfa_api.is_pir_triggered()`

---

## 模拟模式 vs 巴法云模式

| | 模拟模式（Mock） | 巴法云模式 |
|--|------------------|------------|
| 传感器数据 | 内存假数据 | 真实 `getmsg` |
| 控制下发 | 只改内存 | 真实 `sendMessage` |
| PIR 抓拍 | 「模拟 PIR 触发」按钮 | 设备上报后自动抓拍 |
| 切换 | 页面右上角开关，或 `POST /api/mode` | 同上 |

`config.MOCK_MODE` 是启动默认值；页面切换立即生效，重启后仍以 config 为准。

---

## 启动（挂载服务）

```bat
cd D:\chinasoft\XTU\smart-home-console
.venv\Scripts\activate
python app.py
```

等价命令：

```bat
uvicorn app:app --host 0.0.0.0 --port 5000
```

- 控制台：http://127.0.0.1:5000/  
- **Swagger 交互文档**：http://127.0.0.1:5000/docs  
- ReDoc：http://127.0.0.1:5000/redoc  

端口/地址在 `config.py` 的 `APP_HOST` / `APP_PORT`。

---

## 测试方法（建议按顺序）

### 1. 无板子：模拟模式跑通界面

1. 右上角为 **模拟模式**  
2. 设备数据约 5 秒刷新  
3. 点灯/蜂鸣器/RGB → 状态行「已下发」  
4. **模拟 PIR 触发** → 几秒后照片墙出图  
5. **立即抓拍** → 直接测摄像头  

### 2. 用 `/docs` 测 API（推荐）

1. 打开 http://127.0.0.1:5000/docs  
2. 展开接口 → Try it out → Execute  
3. 例如：`POST /api/mock/pir`、`POST /api/capture/now`、`GET /api/captures`  

### 3. 命令行（可选）

```bat
curl http://127.0.0.1:5000/api/mode
curl -X POST http://127.0.0.1:5000/api/mock/pir -H "Content-Type: application/json" -d "{\"triggered\":true}"
curl -X POST http://127.0.0.1:5000/api/control -H "Content-Type: application/json" -d "{\"topic\":\"trafficLight\",\"msg\":\"red\"}"
```

### 4. 巴法云真实模式

填好真实 topic → 关闭模拟开关 → 硬件上报/收指令 → PIR 触发自动抓拍（约 3 秒轮询，10 秒冷却）。

---

## 依赖说明

见 `requirements.txt`：

- `fastapi` / `uvicorn`：Web 服务与启动  
- `jinja2`：渲染 `templates/index.html`  
- `pydantic`：请求体校验（随 FastAPI 安装）  
- `requests`：调巴法云  
- `opencv-python` / `numpy` / `Pillow`：摄像头与占位图  

---

## 常见问题

1. **端口占用**：改 `config.APP_PORT`  
2. **巴法云报错**：检查 uid、topic、`BEMFA_TYPE`（1=MQTT / 3=TCP）  
3. **真实模式无数据**：板端是否已往该主题发过消息  
4. **不要开 uvicorn `--reload` 做 PIR 实验**：热重载可能起两个轮询线程；本项目 `python app.py` 已关闭 reload  
