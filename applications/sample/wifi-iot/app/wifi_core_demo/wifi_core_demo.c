#include <stdio.h>
#include <unistd.h>

#include "ohos_init.h"
#include "cmsis_os2.h"

#include "wifi_connect.h"

/* Standalone smoke test for wifi_core — no MQTT / sensors. */
#define WIFI_CORE_DEMO_WAIT_MS 60000U

static void WifiCoreDemo_Task(void *arg)
{
    char ip[16] = {0};

    (void)arg;

    printf("[wifi_core_demo] WifiApp_StartSta...\n");
    if (WifiApp_StartSta() != 0) {
        printf("[wifi_core_demo] StartSta failed\n");
        return;
    }

    if (WifiApp_WaitReady(WIFI_CORE_DEMO_WAIT_MS) != 0) {
        printf("[wifi_core_demo] wait IP timeout\n");
        return;
    }

    if (WifiApp_GetIpString(ip, sizeof(ip)) == 0) {
        printf("[wifi_core_demo] OK, STA IP=%s\n", ip);
    }

    for (;;) {
        usleep(1000000);
        if (WifiApp_IsReady()) {
            printf("[wifi_core_demo] still online\n");
        } else {
            printf("[wifi_core_demo] offline\n");
        }
    }
}

static void WifiCoreDemo_Entry(void)
{
    osThreadAttr_t attr;

    attr.name = "wifi_core_demo";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 2048;
    attr.priority = 26;

    if (osThreadNew((osThreadFunc_t)WifiCoreDemo_Task, NULL, &attr) == NULL) {
        printf("[wifi_core_demo] Failed to create thread\n");
    }
}

SYS_RUN(WifiCoreDemo_Entry);
