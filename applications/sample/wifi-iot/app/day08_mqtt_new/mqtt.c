#include "day08_mqtt.h"
#include "day08_alarm.h"
#include "day08_config.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "MQTTClient.h"

/* 2.0change */
 
#include "iot_gpio.h"
#include "iot_pwm.h"
#include "hi_io.h"

/* 2.0change */

// #define DAY08_JSON_MAX          256U
#define DAY08_JSON_MAX 384U
#define DAY08_MQTT_BUF          (4096U + 1024U)
#define DAY08_SUB_PAYLOAD_MAX   256U

/* 2.0change */

#define DAY08_HUMIDITY_THRESHOLD 45.0f

#define DAY08_BUZZER_GPIO       9
#define DAY08_BUZZER_PWM_PORT   0
#define DAY08_BUZZER_DUTY       50
#define DAY08_BUZZER_FREQ       2700

/* 2.0change */

#ifndef DAY08_MQTT_SUB_TOPIC
#define DAY08_MQTT_SUB_TOPIC DAY08_MQTT_TOPIC
#endif

#ifndef DAY08_MQTT_PUB_TOPIC
#define DAY08_MQTT_PUB_TOPIC DAY08_MQTT_TOPIC "/up"
#endif

/* 2.0change */

static Day08AlarmState g_alarm_state = {0};
static volatile int g_buzzer_is_on = 0;
static int g_buzzer_initialized = 0;

static int Day08_BuzzerInit(void)
{
    if (g_buzzer_initialized) {
        return 0;
    }

    if (IoTGpioInit(DAY08_BUZZER_GPIO) != 0) {
        printf("[day08][buzzer] IoTGpioInit failed\n");
        return -1;
    }

    if (hi_io_set_func(HI_IO_NAME_GPIO_9,
                       HI_IO_FUNC_GPIO_9_PWM0_OUT) != 0) {
        printf("[day08][buzzer] PWM0 pin multiplexing failed\n");
        return -1;
    }

    if (IoTPwmInit(DAY08_BUZZER_PWM_PORT) != 0) {
        printf("[day08][buzzer] IoTPwmInit failed\n");
        return -1;
    }

    /*
    * 初始化完成后明确保持关闭，
    * 避免引脚复用或设备重启时蜂鸣器短暂发声。
    */
    (void)IoTPwmStop(DAY08_BUZZER_PWM_PORT);

    g_buzzer_is_on = 0;
    g_buzzer_initialized = 1;

    printf("[day08][buzzer] initialized, duty=%u%%, freq=%uHz\n",
           DAY08_BUZZER_DUTY,
           DAY08_BUZZER_FREQ);

    return 0;
}

static void Day08_SetBuzzer(int on)
{
    on = on ? 1 : 0;

    if (g_buzzer_is_on == on) {
        return;
    }

    if (!g_buzzer_initialized) {
        if (Day08_BuzzerInit() != 0) {
            return;
        }
    }

    if (on) {
        if (IoTPwmStart(DAY08_BUZZER_PWM_PORT,
                        DAY08_BUZZER_DUTY,
                        DAY08_BUZZER_FREQ) != 0) {
            printf("[day08][buzzer] IoTPwmStart failed\n");
            return;
        }
    } else {
        if (IoTPwmStop(DAY08_BUZZER_PWM_PORT) != 0) {
            printf("[day08][buzzer] IoTPwmStop failed\n");
            return;
        }
    }

    g_buzzer_is_on = on;

    printf("[day08][alarm] buzzer=%s\n",
           on ? "ON" : "OFF");
}

static void Day08_UpdateHumidityAlarm(float humidity)
{
    int was_silenced = g_alarm_state.humidity_silenced;

    Day08Alarm_UpdateHumidity(&g_alarm_state, humidity,
                              DAY08_HUMIDITY_THRESHOLD);
    if (was_silenced && !g_alarm_state.humidity_silenced) {
        printf("[day08][alarm] humidity recovered, "
               "manual silence cleared\n");
    }

    Day08_SetBuzzer(Day08Alarm_ShouldBuzz(&g_alarm_state));
}

/* 2.0change */

static int Day08_ToHundredths(float value)
{
    if (value >= 0.0f) {
        return (int)(value * 100.0f + 0.5f);
    }
    return (int)(value * 100.0f - 0.5f);
}

/* MQTT payload不保证以'\0'结尾，必须按payloadlen复制。 */
static void Day08_MessageArrived(MessageData *data)
{
    MQTTMessage *message;
    char payload[DAY08_SUB_PAYLOAD_MAX];
    size_t copy_len;

    if (data == NULL || data->message == NULL) {
        return;
    }

    message = data->message;
    if (message->payload == NULL || message->payloadlen == 0U) {
        printf("[day08][sub] topic=%s, empty payload\n",
               DAY08_MQTT_SUB_TOPIC);
        return;
    }

    copy_len = message->payloadlen;
    if (copy_len >= sizeof(payload)) {
        copy_len = sizeof(payload) - 1U;
    }

    (void)memcpy(payload, message->payload, copy_len);

/* 2.0change */

    /*
 * 去除消息末尾可能存在的空格、回车和换行，
 * 避免"alarm_on\r\n"无法被strcmp识别。
 */
    while (copy_len > 0U &&
        (payload[copy_len - 1U] == '\r' ||
            payload[copy_len - 1U] == '\n' ||
            payload[copy_len - 1U] == ' '  ||
            payload[copy_len - 1U] == '\t')) {
        copy_len--;
    }

/* 2.0change */    

    payload[copy_len] = '\0';

    printf("[day08][sub] topic=%s qos=%d payload=%s\n",
           DAY08_MQTT_SUB_TOPIC,
           (int)message->qos,
           payload);

    /* 后续可在这里根据on/off等指令控制LED、蜂鸣器。 */

    /* 2.0change */

    if (Day08Alarm_ApplyCommand(&g_alarm_state, payload)) {
        printf("[day08][alarm] command applied: %s\n", payload);
        Day08_SetBuzzer(Day08Alarm_ShouldBuzz(&g_alarm_state));
    } else {
        printf("[day08][sub] unknown command: %s\n",
             payload);
    }   

/* 2.0change */
}

int Day08_BuildTelemetryJson(char *buf, unsigned int len,
                             const Day08Aht20Data *sample)
{
    int n;
    int temp100;
    int humi100;
    int temp_abs;
/* 2.0change */
    int threshold100;
/* 2.0change */
    if (buf == NULL || len == 0U || sample == NULL) {
        return -1;
    }

    temp100 = Day08_ToHundredths(sample->temperature_c);
    humi100 = Day08_ToHundredths(sample->humidity_rh);
/* 2.0change */
    threshold100 =
    Day08_ToHundredths(DAY08_HUMIDITY_THRESHOLD);
/* 2.0change */
    if (humi100 < 0) {
        humi100 = 0;
    }
    if (humi100 > 10000) {
        humi100 = 10000;
    }

    temp_abs = (temp100 < 0) ? -temp100 : temp100;

    /* 2.0change */

    // n = snprintf(buf, len,
    //              "{"
    //              "\"group_id\":\"%s\","
    //              "\"device_id\":\"%s\","
    //              "\"temperature\":%s%d.%02d,"
    //              "\"humidity\":%d.%02d,"
    //              "\"state\":\"online\","
    //              "\"source\":\"aht20\""
    //              "}",
    //              DAY08_GROUP_ID,
    //              DAY08_DEVICE_ID,
    //              (temp100 < 0) ? "-" : "",
    //              temp_abs / 100,
    //              temp_abs % 100,
    //              humi100 / 100,
    //              humi100 % 100);

    n = snprintf(buf, len,
             "{"
             "\"group_id\":\"%s\","
             "\"device_id\":\"%s\","
             "\"temperature\":%s%d.%02d,"
             "\"humidity\":%d.%02d,"
             "\"buzzer\":%d,"

/* 2.0change */
             //"\"humidity_threshold\":40,"
             "\"humidity_threshold\":%d.%02d,"
/* 2.0change */

             "\"manual_alarm\":%d,"
             "\"humidity_silenced\":%d,"
             "\"vision_alarm\":%d,"
             "\"state\":\"online\","
             "\"source\":\"aht20\""
             "}",
             DAY08_GROUP_ID,
             DAY08_DEVICE_ID,
             (temp100 < 0) ? "-" : "",
             temp_abs / 100,
             temp_abs % 100,
             humi100 / 100,
             humi100 % 100,
             g_buzzer_is_on,
/* 2.0change */
            threshold100 / 100,
            threshold100 % 100,
/* 2.0change */
             g_alarm_state.manual_alarm_on,
             g_alarm_state.humidity_silenced,
             g_alarm_state.vision_alarm_on);

    /* 2.0change */         

    if (n < 0 || (unsigned int)n >= len) {
        return -1;
    }

    return n;
}

static void Day08_SleepReportPeriod(void)
{
    usleep((unsigned int)DAY08_REPORT_PERIOD_MS * 1000U);
}

/* 2.0change */

// static int Day08_ReadJson(char *json, unsigned int len,
//                           Day08Aht20Data *sample)
// {
//     if (json == NULL || sample == NULL) {
//         return -1;
//     }

//     if (Day08Aht20_Read(sample) != 0) {
//         printf("[day08][aht20] read failed\n");
//         return -1;
//     }

//     return Day08_BuildTelemetryJson(json, len, sample);
// }

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

    /*
     * 必须先根据最新湿度更新蜂鸣器状态，
     * 再生成JSON，保证上报状态与实际硬件一致。
     */
    Day08_UpdateHumidityAlarm(sample->humidity_rh);

    return Day08_BuildTelemetryJson(
        json,
        len,
        sample
    );
}

/* 2.0change */

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

    printf("[day08] broker=%s:%d\n",
           DAY08_BROKER_HOST,
           DAY08_BROKER_PORT);
    printf("[day08] publish topic=%s\n", DAY08_MQTT_PUB_TOPIC);
    printf("[day08] subscribe topic=%s\n", DAY08_MQTT_SUB_TOPIC);

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

    /* 2.0change */

    if (Day08_BuzzerInit() != 0) {
        printf("[day08] buzzer init failed\n");
    }

    /* 2.0change */

    rc = MQTTSubscribe(&client,
                       (char *)DAY08_MQTT_SUB_TOPIC,
                       QOS0,
                       Day08_MessageArrived);
    if (rc != 0) {
        printf("[day08] MQTTSubscribe failed (%d), topic=%s\n",
               rc,
               DAY08_MQTT_SUB_TOPIC);
        free(sendbuf);
        free(readbuf);
        return -1;
    }

    printf("[day08] MQTT subscribed, topic=%s\n",
           DAY08_MQTT_SUB_TOPIC);

    for (;;) {
        /* 2.0change */

        // json_len = Day08_ReadJson(json, sizeof(json), &sample);
        // if (json_len > 0) {
        //     MQTTMessage message = {0};
        
        json_len = Day08_ReadJson(json, sizeof(json), &sample);
        if (json_len > 0) {
            MQTTMessage message = {0};

        //   Day08_UpdateHumidityAlarm(sample.humidity_rh);

        /* 2.0change */

            message.qos = QOS0;
            message.retained = 0;
            message.dup = 0;
            message.payload = (void *)json;
            message.payloadlen = (size_t)json_len;

            rc = MQTTPublish(&client,
                             (char *)DAY08_MQTT_PUB_TOPIC,
                             &message);
            if (rc != 0) {
                printf("[day08] MQTTPublish failed (%d)\n", rc);
                free(sendbuf);
                free(readbuf);
                return -1;
            }

            printf("[day08][mqtt] topic=%s %s\n",
                   DAY08_MQTT_PUB_TOPIC,
                   json);
        }

        Day08_SleepReportPeriod();
    }

    return 0;
}
