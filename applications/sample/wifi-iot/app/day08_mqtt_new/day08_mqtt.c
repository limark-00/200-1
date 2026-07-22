#include "day08_mqtt.h"
#include "day08_config.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "MQTTClient.h"

#define DAY08_JSON_MAX  256U
#define DAY08_MQTT_BUF  (4096U + 1024U)

static int Day08_ToHundredths(float value)
{
    if (value >= 0.0f) {
        return (int)(value * 100.0f + 0.5f);
    }
    return (int)(value * 100.0f - 0.5f);
}

int Day08_BuildTelemetryJson(char *buf, unsigned int len,
                             const Day08Aht20Data *sample)
{
    int n;
    int temp100;
    int humi100;
    int temp_abs;

    if (buf == NULL || len == 0U || sample == NULL) {
        return -1;
    }

    temp100 = Day08_ToHundredths(sample->temperature_c);
    humi100 = Day08_ToHundredths(sample->humidity_rh);
    if (humi100 < 0) {
        humi100 = 0;
    }
    if (humi100 > 10000) {
        humi100 = 10000;
    }

    temp_abs = (temp100 < 0) ? -temp100 : temp100;

    n = snprintf(buf, len,
                 "{"
                 "\"group_id\":\"%s\","
                 "\"device_id\":\"%s\","
                 "\"temperature\":%s%d.%02d,"
                 "\"humidity\":%d.%02d,"
                 "\"state\":\"online\","
                 "\"source\":\"aht20\""
                 "}",
                 DAY08_GROUP_ID,
                 DAY08_DEVICE_ID,
                 (temp100 < 0) ? "-" : "",
                 temp_abs / 100,
                 temp_abs % 100,
                 humi100 / 100,
                 humi100 % 100);

    if (n < 0 || (unsigned int)n >= len) {
        return -1;
    }
    return n;
}

static void Day08_SleepReportPeriod(void)
{
    usleep((unsigned int)DAY08_REPORT_PERIOD_MS * 1000U);
}

static int Day08_ReadJson(char *json, unsigned int len,
                          Day08Aht20Data *sample)
{
    if (json == NULL || sample == NULL) {
        return -1;
    }

    if (Day08Aht20_Read(sample) != 0) {
        printf("[day08][aht20] read failed\n");
        return -1;
    }

    return Day08_BuildTelemetryJson(json, len, sample);
}

void Day08_UartFallbackLoop(void)
{
    char json[DAY08_JSON_MAX];
    Day08Aht20Data sample;

    printf("[day08] no network / MQTT unavailable, UART fallback\n");

    for (;;) {
        if (Day08_ReadJson(json, sizeof(json), &sample) > 0) {
            printf("[day08][uart] %s\n", json);
        }
        Day08_SleepReportPeriod();
    }
}

int Day08_MqttLoop(void)
{
    Network network;
    MQTTClient client;
    MQTTPacket_connectData connect_data =
        MQTTPacket_connectData_initializer;
    unsigned char *sendbuf = NULL;
    unsigned char *readbuf = NULL;
    char json[DAY08_JSON_MAX];
    Day08Aht20Data sample;
    int rc;
    int json_len;

    printf("[day08] broker=%s:%d topic=%s\n",
           DAY08_BROKER_HOST,
           DAY08_BROKER_PORT,
           DAY08_MQTT_TOPIC);

    NetworkInit(&network);
    rc = NetworkConnect(&network,
                        (char *)DAY08_BROKER_HOST,
                        DAY08_BROKER_PORT);
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

    MQTTClientInit(&client,
                   &network,
                   1000,
                   sendbuf,
                   DAY08_MQTT_BUF,
                   readbuf,
                   DAY08_MQTT_BUF);
    MQTTStartTask(&client);

    connect_data.MQTTVersion = DAY08_MQTT_VERSION;
    connect_data.keepAliveInterval = DAY08_MQTT_KEEPALIVE;
    connect_data.cleansession = DAY08_MQTT_CLEAN_SESSION;
    connect_data.clientID.cstring = (char *)DAY08_MQTT_CLIENT_ID;
    connect_data.username.cstring = NULL;
    connect_data.password.cstring = NULL;

    rc = MQTTConnect(&client, &connect_data);
    if (rc != 0) {
        printf("[day08] MQTTConnect failed (%d)\n", rc);
        free(sendbuf);
        free(readbuf);
        return -1;
    }

    printf("[day08] MQTT connected to Bemfa\n");

    for (;;) {
        json_len = Day08_ReadJson(json, sizeof(json), &sample);
        if (json_len > 0) {
            MQTTMessage message = {0};

            message.qos = QOS0;
            message.retained = 0;
            message.dup = 0;
            message.payload = (void *)json;
            message.payloadlen = (size_t)json_len;

            
            char publish_topic[64];

            snprintf(publish_topic,
            sizeof(publish_topic),"%s/up",DAY08_MQTT_TOPIC);

            rc = MQTTPublish(&client,publish_topic,&message);
            if (rc != 0) {
                printf("[day08] MQTTPublish failed (%d)\n", rc);
                return -1;
            }

            printf("[day08][mqtt] topic=%s %s\n",
                   publish_topic,
                   json);
        }

        Day08_SleepReportPeriod();
    }

    return 0;
}
