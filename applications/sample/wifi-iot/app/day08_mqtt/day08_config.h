/*
 * Day08 / 巴法云 MQTT 配置（学生可改）
 * Wi-Fi SSID/密码：只改 ../wifi_core/wifi_app_config.h
 */
#ifndef DAY08_CONFIG_H
#define DAY08_CONFIG_H

/* —— 身份（JSON 载荷用）—— */
#ifndef DAY08_GROUP_ID
#define DAY08_GROUP_ID   "group01"
#endif

#ifndef DAY08_DEVICE_ID
#define DAY08_DEVICE_ID  "dev02"
#endif

/*
 * 巴法云 MQTT（与 MQTTX 一致）
 * Host: bemfa.com  Port: 9501
 * Client ID = 巴法云控制台「密钥」
 */
#ifndef DAY08_BROKER_HOST
#define DAY08_BROKER_HOST  "bemfa.com"
#endif

/* 兼容旧宏名 */
#ifndef DAY08_BROKER_IP
#define DAY08_BROKER_IP    DAY08_BROKER_HOST
#endif

#ifndef DAY08_BROKER_PORT
#define DAY08_BROKER_PORT  9501
#endif

/* 必须与 MQTTX / 巴法控制台密钥一致 */
#ifndef DAY08_MQTT_CLIENT_ID
#define DAY08_MQTT_CLIENT_ID  "554419557d4567eb2f683d752c6aad23"
#endif

/* 巴法控制台已创建的主题名（MQTTX 订阅同一主题可看到上报） */
#ifndef DAY08_MQTT_TOPIC
#define DAY08_MQTT_TOPIC  "env004"
#endif

#ifndef DAY08_MQTT_KEEPALIVE
#define DAY08_MQTT_KEEPALIVE  60
#endif

/* 与 MQTTX：Clean Session = 关 → 0 */
#ifndef DAY08_MQTT_CLEAN_SESSION
#define DAY08_MQTT_CLEAN_SESSION  0
#endif

/* MQTT 3.1（与 MQTTX 一致）；Paho: 3=3.1, 4=3.1.1 */
#ifndef DAY08_MQTT_VERSION
#define DAY08_MQTT_VERSION  3
#endif

/* 上报周期（毫秒） */
#ifndef DAY08_REPORT_PERIOD_MS
#define DAY08_REPORT_PERIOD_MS 1000
#endif

/* 等 Wi-Fi IP：0=一直等 */
#ifndef DAY08_WIFI_WAIT_MS
#define DAY08_WIFI_WAIT_MS 60000U
#endif

#endif /* DAY08_CONFIG_H */
