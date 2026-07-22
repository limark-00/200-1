# AHT20 + 多源蜂鸣器通过 Wi-Fi 接入巴法云

该目录基于原有`day08_mqtt`修改，完整链路如下：

```text
AHT20(GPIO13/14，I2C0)
        ↓
温度、湿度采集
        ↓
JSON数据
        ↓
Wi-Fi STA
        ↓
MQTT
        ↓
巴法云主题 ↔ 控制台 vision_alarm_on/off
        ↓
手动 / 湿度 / 视觉独立状态合并 → 蜂鸣器
```

## 一、目录放置

将本目录内全部文件复制到：

```text
applications/sample/wifi-iot/app/day08_mqtt_new/
```

目录应为：

```text
day08_mqtt_new/
├── BUILD.gn
├── day08_aht20.c
├── day08_aht20.h
├── day08_alarm.c
├── day08_alarm.h
├── day08_config.h
├── day08_entry.c
├── day08_mqtt.h
├── mqtt.c
├── tests/test_day08_alarm.c
└── README.md
```

## 二、配置Wi-Fi

修改：

```text
applications/sample/wifi-iot/app/wifi_core/wifi_app_config.h
```

填写热点名称、密码。Hi3861连接手机热点时建议使用2.4GHz和WPA2。

## 三、配置巴法云

修改`day08_config.h`：

```c
#define DAY08_MQTT_CLIENT_ID "巴法云私钥"
#define DAY08_MQTT_TOPIC     "巴法云中已创建的主题"
```

默认连接：

```text
Host: bemfa.com
Port: 9501
MQTT: 3.1
QoS: 0
```

不要把私钥上传到公开仓库。

## 四、父级BUILD.gn

修改：

```text
applications/sample/wifi-iot/app/BUILD.gn
```

只启用：

```gn
import("//build/lite/config/component/lite_component.gni")

lite_component("app") {
    features = [
        "day08_mqtt_new:day08_mqtt_new",
    ]
}
```

测试本程序时，请注释掉：

```gn
#"wifi_core_demo:wifi_core_demo",
#"gpio_input_demo:gpio_input_demo",
#"aht20:aht20",
#"sensor_lab:sensor_lab",
```

`wifi_core`不需要单独加入 `features`，因为 `day08_mqtt_new/BUILD.gn` 已通过 `deps` 依赖它。

## 五、上传的数据

每5秒读取一次AHT20并向配置的主题发送：

```json
{
  "group_id": "group01",
  "device_id": "dev01",
  "temperature": 25.36,
  "humidity": 58.42,
  "buzzer": 1,
  "humidity_threshold": 45.00,
  "manual_alarm": 0,
  "humidity_silenced": 0,
  "vision_alarm": 1,
  "state": "online",
  "source": "aht20"
}
```

上行发布到 `<DAY08_MQTT_TOPIC>/up`；`buzzer` 是最终输出，`manual_alarm`、`humidity_silenced` 和 `vision_alarm` 用于核对三个报警源。

## 六、控制命令与蜂鸣器真值表

下行订阅主题为 `DAY08_MQTT_TOPIC`。`vision_alarm_on` 只将视觉源置 1，`vision_alarm_off` 只将视觉源置 0。`alarm_on` 开启手动源并解除湿度静音；`alarm_off` 关闭手动源并将当前湿度源静音，但绝不会清除视觉源。湿度回落到阈值后会自动解除该静音锁存。

`H` 表示「湿度超阈值且未静音」；最终逻辑为 `buzzer = manual_alarm OR H OR vision_alarm`。

| `manual_alarm` | `H` | `vision_alarm` | `buzzer` |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 0 | 0 | 1 | 1 |
| 0 | 1 | 0 | 1 |
| 0 | 1 | 1 | 1 |
| 1 | 0 | 0 | 1 |
| 1 | 0 | 1 | 1 |
| 1 | 1 | 0 | 1 |
| 1 | 1 | 1 | 1 |

## 七、正常串口输出和视觉命令检查

```text
[day08] initializing AHT20...
[day08][aht20] ready, status=0x18
[day08] starting Wi-Fi via wifi_core...
WiFi: Connected, starting DHCP
[day08] Wi-Fi ready, IP=192.168.43.19
[day08] broker=bemfa.com:9501 topic=你的主题
[day08] MQTT connected to Bemfa
[day08] MQTT subscribed, topic=你的主题
[day08][mqtt] topic=你的主题/up {"temperature":25.36,"humidity":58.42,...,"vision_alarm":0,...}
```

如果Wi-Fi或MQTT连接失败，程序仍会从AHT20采集数据并输出：

```text
[day08][uart] {"temperature":25.36,"humidity":58.42,...}
```

在巴法云依次下发 `vision_alarm_on` 和 `vision_alarm_off`，串口必须分别出现：

```text
[day08][sub] topic=你的主题 qos=0 payload=vision_alarm_on
[day08][alarm] buzzer=ON
[day08][alarm] command applied: vision_alarm_on
[day08][mqtt] ... "vision_alarm":1 ...

[day08][sub] topic=你的主题 qos=0 payload=vision_alarm_off
[day08][alarm] buzzer=OFF
[day08][alarm] command applied: vision_alarm_off
[day08][mqtt] ... "vision_alarm":0 ...
```

若手动或湿度源仍为真，收到 `vision_alarm_off` 后不应出现 `buzzer=OFF`；此时上行数据中应同时看到 `"vision_alarm":0` 和 `"buzzer":1`。

## 八、Ubuntu/OpenHarmony 编译和主机可移植测试

在已配置 OpenHarmony/Hi3861 工具链的 Ubuntu 项目仓库根目录执行：

```bash
python build.py wifiiot 2>&1 | tee build.log
```

应成功链接 `Hi3861_wifiiot_app.out`，并可在日志中核对：

重新编译后搜索日志：

```bash
grep -niE "day08_alarm\.c|day08_mqtt_new|wifi_core|pahomqtt" build.log
```

无 OpenHarmony 工具链时只验证纯 C 状态组件（仓库根目录）：

```bash
cc -std=c99 -Wall -Wextra -Werror \
  -I applications/sample/wifi-iot/app/day08_mqtt_new \
  applications/sample/wifi-iot/app/day08_mqtt_new/day08_alarm.c \
  applications/sample/wifi-iot/app/day08_mqtt_new/tests/test_day08_alarm.c \
  -o /tmp/day08_alarm_test
/tmp/day08_alarm_test
```

## 九、常见问题

### 找不到`wifiiot_i2c.h`或`iot_i2c.h`

本代码会自动适配两套常见API。如果仍找不到，请在源码中执行：

```bash
find . -name "wifiiot_i2c.h" -o -name "iot_i2c.h"
```

再将对应头文件所在目录补充到本目录的`BUILD.gn/include_dirs`。

### AHT20一直初始化失败

确认环境监测板插接牢固，并确认GPIO13、GPIO14没有被OLED或其他模块同时占用。

### MQTT连接成功但云端没有数据

核对：

1. `DAY08_MQTT_CLIENT_ID`是否为巴法云私钥；
2. `DAY08_MQTT_TOPIC`是否已在巴法云创建；
3. MQTTX是否订阅了完全相同的主题；
4. 串口是否持续出现`[day08][mqtt]`。
