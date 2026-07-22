# wifi_core — 课堂可复用连网基础模块

本目录是按《WiFi 模块技术说明与改造方案》落地的 **新模块**，**不修改** 原有 `demo_wifi_sta` / `mqtt_test`。

**小白学生请先读：[`学生指南.md`](./学生指南.md)**（原理 + 改哪里 + 怎么看串口）。

## 学生只改哪里

| 文件 | 改什么 |
|------|--------|
| `wifi_app_config.h` | 课堂热点 `WIFI_APP_SSID` / `WIFI_APP_PASSWORD` / 加密方式 |

业务 `.c` 里不应再出现 SSID、密码或 `hi_wifi_*`。

## 对外 API（`wifi_connect.h`）

- `WifiApp_StartSta()` — 启动 STA 并按配置连接
- `WifiApp_WaitReady(timeout_ms)` — 等到拿到 IP（或超时）
- `WifiApp_IsReady()` — 是否已有 IP
- `WifiApp_GetIpString(buf, len)` — 读 STA IP 字符串

## 谁在用

| 目录 | 用途 |
|------|------|
| `wifi_core_demo/` | **单独测连网**：只验证拿 IP，无 MQTT |
| `day08_mqtt/` | Day08：连网 + MQTT + UART 保底 |

## 编译

在 `applications/sample/wifi-iot/app/BUILD.gn` 中 **一次只开一个** feature。

只测 Wi-Fi：

```gn
features = [
  "wifi_core_demo:wifi_core_demo",
]
```

测 Day08 MQTT：

```gn
features = [
  "day08_mqtt:day08_mqtt",
]
```

改 `wifi_app_config.h` 后编译烧录；串口应看到 `STA IP: 192.168.x.x`（demo 还会周期性打印 `still online`）。
