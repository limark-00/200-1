#include "day08_mqtt.h"
#include "day08_config.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "MQTTClient.h"

#define DAY08_JSON_MAX  256
#define DAY08_MQTT_BUF  (4096 + 1024)

int Day08_BuildStateJson(char *buf, unsigned int len)
{
    int n;

    if (buf == NULL || len == 0) {
        return -1;
    }

    n = snprintf(buf, len,
                 "{"
                 "\"group_id\":\"%s\","
                 "\"device_id\":\"%s\","
                 "\"state\":\"online\","
                 "\"source\":\"day08_mqtt\""
                 "}",
                 DAY08_GROUP_ID, DAY08_DEVICE_ID);
    if (n < 0 || (unsigned int)n >= len) {
        return -1;
    }
    return n;
}

static void Day08_SleepReportPeriod(void)
{
    usleep((unsigned int)DAY08_REPORT_PERIOD_MS * 1000U);
}

void Day08_UartFallbackLoop(void)
{
    char json[DAY08_JSON_MAX];

    printf("[day08] no network / MQTT unavailable — UART fallback\n");
    for (;;) {
        if (Day08_BuildStateJson(json, sizeof(json)) > 0) {
            printf("[day08][uart] %s\n", json);
        }
        Day08_SleepReportPeriod();
    }
}

int Day08_MqttLoop(void)
{
    Network n;
    MQTTClient client;
    MQTTPacket_connectData data = MQTTPacket_connectData_initializer;
    unsigned char *sendbuf = NULL;
    unsigned char *readbuf = NULL;
    char json[DAY08_JSON_MAX];
    int rc;
    int json_len;

    printf("[day08] broker %s:%d topic %s\n",
           DAY08_BROKER_HOST, DAY08_BROKER_PORT, DAY08_MQTT_TOPIC);
    printf("[day08] clientId=%s\n", DAY08_MQTT_CLIENT_ID);

    NetworkInit(&n);
    rc = NetworkConnect(&n, (char *)DAY08_BROKER_HOST, DAY08_BROKER_PORT);
    if (rc != 0) {
        printf("[day08] NetworkConnect failed (%d)\n", rc);
        return -1;
    }

    sendbuf = (unsigned char *)malloc(DAY08_MQTT_BUF);
    readbuf = (unsigned char *)malloc(DAY08_MQTT_BUF);
    if (sendbuf == NULL || readbuf == NULL) {
        printf("[day08] no memory for MQTT buffers\n");
        free(sendbuf);
        free(readbuf);
        return -1;
    }

    MQTTClientInit(&client, &n, 1000, sendbuf, DAY08_MQTT_BUF, readbuf, DAY08_MQTT_BUF);
    MQTTStartTask(&client);

    /* 与 MQTTX / 巴法云：MQTT 3.1、Keep Alive 60、Clean Session 关 */
    data.MQTTVersion = DAY08_MQTT_VERSION;
    data.keepAliveInterval = DAY08_MQTT_KEEPALIVE;
    data.cleansession = DAY08_MQTT_CLEAN_SESSION;
    data.clientID.cstring = (char *)DAY08_MQTT_CLIENT_ID;
    data.username.cstring = NULL;
    data.password.cstring = NULL;

    rc = MQTTConnect(&client, &data);
    if (rc != 0) {
        printf("[day08] MQTTConnect failed (%d)\n", rc);
        free(sendbuf);
        free(readbuf);
        return -1;
    }
    printf("[day08] MQTT connected (bemfa)\n");

    for (;;) {
        json_len = Day08_BuildStateJson(json, sizeof(json));
        if (json_len > 0) {
            MQTTMessage message;
            message.qos = QOS0;
            message.retained = 0;
            message.payload = (void *)json;
            message.payloadlen = (size_t)json_len;

            if (MQTTPublish(&client, (char *)DAY08_MQTT_TOPIC, &message) < 0) {
                printf("[day08] MQTTPublish failed\n");
                free(sendbuf);
                free(readbuf);
                return -1;
            }
            printf("[day08][mqtt] topic=%s %s\n", DAY08_MQTT_TOPIC, json);
        }
        Day08_SleepReportPeriod();
    }

    return 0;
}
