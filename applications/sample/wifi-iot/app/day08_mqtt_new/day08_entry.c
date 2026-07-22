#include <stdio.h>
#include <unistd.h>

#include "ohos_init.h"
#include "cmsis_os2.h"

#include "day08_aht20.h"
#include "day08_config.h"
#include "day08_mqtt.h"
#include "wifi_connect.h"

static void Day08_InitSensorUntilReady(void)
{
    while (Day08Aht20_Init() != 0) {
        printf("[day08] AHT20 init failed, retry after %u ms\n",
               (unsigned int)DAY08_SENSOR_RETRY_MS);
        usleep((unsigned int)DAY08_SENSOR_RETRY_MS * 1000U);
    }
}

static void Day08_Task(void *arg)
{
    char ip[16] = {0};

    (void)arg;

    printf("[day08] initializing AHT20...\n");
    Day08_InitSensorUntilReady();

    printf("[day08] starting Wi-Fi via wifi_core...\n");
    if (WifiApp_StartSta() != 0) {
        printf("[day08] WifiApp_StartSta failed, UART fallback\n");
        Day08_UartFallbackLoop();
        return;
    }

    if (WifiApp_WaitReady(DAY08_WIFI_WAIT_MS) != 0) {
        printf("[day08] Wi-Fi IP timeout, UART fallback\n");
        Day08_UartFallbackLoop();
        return;
    }

    if (WifiApp_GetIpString(ip, sizeof(ip)) == 0) {
        printf("[day08] Wi-Fi ready, IP=%s\n", ip);
    }

    if (Day08_MqttLoop() != 0) {
        Day08_UartFallbackLoop();
    }
}

static void Day08_Entry(void)
{
    osThreadAttr_t attr = {0};

    attr.name = "day08_mqtt";
    attr.stack_size = 6144U;
    attr.priority = 26;

    if (osThreadNew((osThreadFunc_t)Day08_Task, NULL, &attr) == NULL) {
        printf("[day08] failed to create thread\n");
    }
}

SYS_RUN(Day08_Entry);
