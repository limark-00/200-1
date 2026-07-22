# AHT20温湿度通过Wi-Fi上传巴法云

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
巴法云主题
```

## 一、目录放置

将本目录内全部文件复制到：

```text
applications/sample/wifi-iot/app/day08_mqtt/
```

目录应为：

```text
day08_mqtt/
├── BUILD.gn
├── day08_aht20.c
├── day08_aht20.h
├── day08_config.h
├── day08_entry.c
├── day08_mqtt.c
├── day08_mqtt.h
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
        "day08_mqtt:day08_mqtt",
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

`wifi_core`不需要单独加入`features`，因为`day08_mqtt/BUILD.gn`已通过`deps`依赖它。

## 五、上传的数据

每5秒读取一次AHT20并向配置的主题发送：

```json
{
  "group_id": "group01",
  "device_id": "dev01",
  "temperature": 25.36,
  "humidity": 58.42,
  "state": "online",
  "source": "aht20"
}
```

巴法云或MQTTX订阅相同主题即可看到原始JSON。

## 六、正常串口输出

```text
[day08] initializing AHT20...
[day08][aht20] ready, status=0x18
[day08] starting Wi-Fi via wifi_core...
WiFi: Connected, starting DHCP
[day08] Wi-Fi ready, IP=192.168.43.19
[day08] broker=bemfa.com:9501 topic=你的主题
[day08] MQTT connected to Bemfa
[day08][mqtt] topic=你的主题 {"temperature":25.36,"humidity":58.42,...}
```

如果Wi-Fi或MQTT连接失败，程序仍会从AHT20采集数据并输出：

```text
[day08][uart] {"temperature":25.36,"humidity":58.42,...}
```

## 七、编译检查

重新编译后搜索日志：

```bash
grep -niE "day08_mqtt|day08_aht20|wifi_core|pahomqtt" build.log
```

应看到`day08_aht20.c`、`day08_mqtt.c`、`day08_entry.c`参与编译。

## 八、常见问题

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
