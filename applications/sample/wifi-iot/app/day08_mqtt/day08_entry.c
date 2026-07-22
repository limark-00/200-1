#include <stdio.h>
#include <unistd.h>

#include "ohos_init.h"
#include "cmsis_os2.h"

#include "wifi_connect.h"
#include "day08_mqtt.h"
#include "day08_config.h"

static void Day08_Task(void *arg)
{
    char ip[16] = {0};

    (void)arg;

    printf("[day08] starting Wi-Fi via wifi_core...\n");
    if (WifiApp_StartSta() != 0) {
        printf("[day08] WifiApp_StartSta failed — UART fallback\n");
        Day08_UartFallbackLoop();
        return;
    }

    if (WifiApp_WaitReady(DAY08_WIFI_WAIT_MS) != 0) {
        printf("[day08] Wi-Fi IP timeout — UART fallback\n");
        Day08_UartFallbackLoop();
        return;
    }

    if (WifiApp_GetIpString(ip, sizeof(ip)) == 0) {
        printf("[day08] Wi-Fi ready, IP=%s\n", ip);
    }

    /* Prefer MQTT; on failure keep demo alive via UART */
    if (Day08_MqttLoop() != 0) {
        Day08_UartFallbackLoop();
    }
}

static void Day08_Entry(void)
{
    osThreadAttr_t attr;

    attr.name = "day08_mqtt";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 4096;
    attr.priority = 26;

    if (osThreadNew((osThreadFunc_t)Day08_Task, NULL, &attr) == NULL) {
        printf("[day08] Failed to create day08_mqtt thread\n");
    }
}

SYS_RUN(Day08_Entry);
