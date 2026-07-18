#include <stdio.h>
#include <unistd.h>

#include "cmsis_os2.h"
#include "ohos_init.h"
#include "iot_gpio.h"
#include "iot_pwm.h"
#include "hi_io.h"

#define BUZZER_GPIO 9
#define BUZZER_PWM_PORT 0
#define BUZZER_DUTY 50
#define BUZZER_FREQ 2700
#define BUZZER_ON_TIME_US 1000000
#define BUZZER_OFF_TIME_US 1000000

static int BuzzerInit(void)
{
    if (IoTGpioInit(BUZZER_GPIO) != 0) {
        printf("[pwm_buz] IoTGpioInit failed\n");
        return -1;
    }
    if (hi_io_set_func(HI_IO_NAME_GPIO_9, HI_IO_FUNC_GPIO_9_PWM0_OUT) != 0) {
        printf("[pwm_buz] PWM0 pin multiplexing failed\n");
        return -1;
    }
    if (IoTPwmInit(BUZZER_PWM_PORT) != 0) {
        printf("[pwm_buz] IoTPwmInit failed\n");
        return -1;
    }
    return 0;
}

static void BuzzerTask(void *argument)
{
    (void)argument;

    if (BuzzerInit() != 0) {
        return;
    }

    printf("[pwm_buz] buzzer: duty=%u%%, frequency=%u Hz\n",
        BUZZER_DUTY, BUZZER_FREQ);

    for (;;) {
        if (IoTPwmStart(BUZZER_PWM_PORT, BUZZER_DUTY, BUZZER_FREQ) != 0) {
            printf("[pwm_buz] IoTPwmStart failed\n");
            return;
        }
        usleep(BUZZER_ON_TIME_US);

        if (IoTPwmStop(BUZZER_PWM_PORT) != 0) {
            printf("[pwm_buz] IoTPwmStop failed\n");
            return;
        }
        usleep(BUZZER_OFF_TIME_US);
    }
}

static void BuzzerExampleEntry(void)
{
    static const osThreadAttr_t attr = {
        .name = "BuzzerTask",
        .stack_size = 2048,
        .priority = osPriorityNormal,
    };

    if (osThreadNew(BuzzerTask, NULL, &attr) == NULL) {
        printf("[pwm_buz] create task failed\n");
    }
}

SYS_RUN(BuzzerExampleEntry);
