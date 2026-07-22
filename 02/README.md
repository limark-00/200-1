# env004 Python接入巴法云

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 测试读取

```bash
python test_bemfa.py
```

成功时应看到：`"ok": true`，以及env004最新的`msg`和`time`。

## 3. 测试下发

```bash
python test_bemfa.py --send pc_online
```

开发板必须订阅env004，才能实时收到这条消息。

## 4. 启动API平台

```bash
python app.py
```

浏览器打开：

- `http://127.0.0.1:5001/docs`
- GET `/api/env`：读取env004
- POST `/api/env/send`：向env004发送消息，请求体：`{"msg":"alarm_on"}`

## env004消息格式

推荐开发板上传JSON：

```json
{"temperature":26.5,"humidity":58.2,"gas":423}
```

也兼容：

```text
26.5,58.2,423
```

## 常见错误

- `40004`：UID、主题名或主题类型错误。
- 能查询但设备收不到下发：确认开发板已订阅env004；MQTT客户端原生发布时应向`env004/set`发布。
- `type`错误：MQTT主题用1，TCP主题用3。
