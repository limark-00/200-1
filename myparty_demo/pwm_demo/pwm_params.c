#include <stdio.h>
#include <unistd.h>

#include "cmsis_os2.h"
#include "ohos_init.h"
#include "iot_gpio.h"
#include "iot_pwm.h"
#include "hi_io.h"

#define BUZZER_GPIO 9
#define BUZZER_PWM_PORT 0
#define FIXED_FREQUENCY 2700
#define FIXED_DUTY 50
#define ITEM_TIME_US 1500000
#define GAP_TIME_US 500000
#define GROUP_GAP_TIME_US 1500000

static const unsigned short g_dutyList[] = {10, 30, 50, 70, 90};
static const unsigned int g_frequencyList[] = {2442, 2700, 3500, 5000};

static int PwmParamsInit(void)
{
    if (IoTGpioInit(BUZZER_GPIO) != 0) {
        printf("[pwm_params] IoTGpioInit failed\n");
        return -1;
    }
    if (hi_io_set_func(HI_IO_NAME_GPIO_9, HI_IO_FUNC_GPIO_9_PWM0_OUT) != 0) {
        printf("[pwm_params] PWM0 pin multiplexing failed\n");
        return -1;
    }
    if (IoTPwmInit(BUZZER_PWM_PORT) != 0) {
        printf("[pwm_params] IoTPwmInit failed\n");
        return -1;
    }
    return 0;
}

static int PlayAndPrint(unsigned short duty, unsigned int frequency)
{
    printf("[pwm_params] duty=%u%%, frequency=%u Hz\n", duty, frequency);
    if (IoTPwmStart(BUZZER_PWM_PORT, duty, frequency) != 0) {
        printf("[pwm_params] IoTPwmStart failed\n");
        return -1;
    }

    usleep(ITEM_TIME_US);
    if (IoTPwmStop(BUZZER_PWM_PORT) != 0) {
        printf("[pwm_params] IoTPwmStop failed\n");
        return -1;
    }
    usleep(GAP_TIME_US);
    return 0;
}

static void PwmParamsTask(void *argument)
{
    unsigned int i;
    (void)argument;

    if (PwmParamsInit() != 0) {
        return;
    }

    for (;;) {
        printf("\n[pwm_params] group 1: change duty, keep frequency fixed\n");
        for (i = 0; i < sizeof(g_dutyList) / sizeof(g_dutyList[0]); ++i) {
            if (PlayAndPrint(g_dutyList[i], FIXED_FREQUENCY) != 0) {
                return;
            }
        }

        usleep(GROUP_GAP_TIME_US);
        printf("\n[pwm_params] group 2: change frequency, keep duty fixed\n");
        for (i = 0; i < sizeof(g_frequencyList) / sizeof(g_frequencyList[0]); ++i) {
            if (PlayAndPrint(FIXED_DUTY, g_frequencyList[i]) != 0) {
                return;
            }
        }

        usleep(GROUP_GAP_TIME_US);
    }
}

static void PwmParamsExampleEntry(void)
{
    static const osThreadAttr_t attr = {
        .name = "PwmParamsTask",
        .stack_size = 2048,
        .priority = osPriorityNormal,
    };

    if (osThreadNew(PwmParamsTask, NULL, &attr) == NULL) {
        printf("[pwm_params] create task failed\n");
    }
}

SYS_RUN(PwmParamsExampleEntry);
