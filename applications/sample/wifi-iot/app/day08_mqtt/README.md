# Day08 MQTT（可烧录实现）

对应金样例契约：`internship-course/03-asset-pack/gold-samples/day08-mqtt/`。

本目录为 **新建实现**，**不修改** 原有 `mqtt_test/`、`demo_wifi_sta/`。

## 架构

```
day08_entry.c     → WifiApp_StartSta / WaitReady（wifi_core）
                  → 有 IP：Day08_MqttLoop
                  → 无网/MQTT 失败：Day08_UartFallbackLoop（UART 保底）
day08_mqtt.c      → topic internship/{group_id}/state
day08_config.h    → group_id / device_id / broker / 周期
../wifi_core/wifi_app_config.h → SSID / 密码（唯一入口）
```

## 学生可改

| 项 | 文件 |
|----|------|
| Wi-Fi SSID / 密码 | `../wifi_core/wifi_app_config.h` |
| `group_id` / `device_id` / broker / 上报周期 | `day08_config.h` |

## 验收对照

- Topic：`internship/{group_id}/state`
- 有网：串口可见 `[day08][mqtt] {...}`，broker 可收到同 JSON
- 无网：串口每秒 `[day08][uart] {...}`（同一 JSON）

## 编译

在 `applications/sample/wifi-iot/app/BUILD.gn` **只打开**：

```gn
"day08_mqtt:day08_mqtt",
```

并注释掉其它 feature（含当前的 `sensor_lab:...`）。
