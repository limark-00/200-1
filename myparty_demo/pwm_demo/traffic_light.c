#include <stdio.h>
#include <unistd.h>

#include "cmsis_os2.h"
#include "ohos_init.h"
#include "iot_gpio.h"
#include "iot_pwm.h"
#include "hi_io.h"

#define BUTTON_GPIO 8
#define BUZZER_GPIO 9
#define RED_LED_GPIO 10
#define GREEN_LED_GPIO 11
#define YELLOW_LED_GPIO 12
#define BUZZER_PWM_PORT 0

#define BUZZER_DUTY 50
#define BUZZER_FREQ 2700
#define RED_TIME_MS 5000
#define GREEN_TIME_MS 5000
#define BUTTON_POLL_MS 50
#define YELLOW_BLINK_COUNT 6
#define YELLOW_HALF_PERIOD_US 500000
#define BEEP_TIME_US 200000

static int InitOutputPin(unsigned int gpio, hi_io_name ioName, unsigned char ioFunc)
{
    if (IoTGpioInit(gpio) != 0) {
        printf("[traffic_light] GPIO%u init failed\n", gpio);
        return -1;
    }
    if (hi_io_set_func(ioName, ioFunc) != 0) {
        printf("[traffic_light] GPIO%u function setup failed\n", gpio);
        return -1;
    }
    if (IoTGpioSetDir(gpio, IOT_GPIO_DIR_OUT) != 0) {
        printf("[traffic_light] GPIO%u direction setup failed\n", gpio);
        return -1;
    }
    if (IoTGpioSetOutputVal(gpio, IOT_GPIO_VALUE0) != 0) {
        printf("[traffic_light] GPIO%u initial output failed\n", gpio);
        return -1;
    }
    return 0;
}

static int TrafficLightInit(void)
{
    if (InitOutputPin(RED_LED_GPIO, HI_IO_NAME_GPIO_10,
        HI_IO_FUNC_GPIO_10_GPIO) != 0 ||
        InitOutputPin(YELLOW_LED_GPIO, HI_IO_NAME_GPIO_12,
        HI_IO_FUNC_GPIO_12_GPIO) != 0 ||
        InitOutputPin(GREEN_LED_GPIO, HI_IO_NAME_GPIO_11,
        HI_IO_FUNC_GPIO_11_GPIO) != 0) {
        return -1;
    }

    if (IoTGpioInit(BUTTON_GPIO) != 0 ||
        hi_io_set_func(HI_IO_NAME_GPIO_8, HI_IO_FUNC_GPIO_8_GPIO) != 0 ||
        hi_io_set_pull(HI_IO_NAME_GPIO_8, HI_IO_PULL_UP) != 0 ||
        IoTGpioSetDir(BUTTON_GPIO, IOT_GPIO_DIR_IN) != 0) {
        printf("[traffic_light] button setup failed\n");
        return -1;
    }

    if (IoTGpioInit(BUZZER_GPIO) != 0 ||
        hi_io_set_func(HI_IO_NAME_GPIO_9, HI_IO_FUNC_GPIO_9_PWM0_OUT) != 0 ||
        IoTPwmInit(BUZZER_PWM_PORT) != 0) {
        printf("[traffic_light] buzzer setup failed\n");
        return -1;
    }
    return 0;
}

static void SetLights(IotGpioValue red, IotGpioValue yellow, IotGpioValue green)
{
    if (IoTGpioSetOutputVal(RED_LED_GPIO, red) != 0 ||
        IoTGpioSetOutputVal(YELLOW_LED_GPIO, yellow) != 0 ||
        IoTGpioSetOutputVal(GREEN_LED_GPIO, green) != 0) {
        printf("[traffic_light] set light output failed\n");
    }
}

static void Beep(void)
{
    if (IoTPwmStart(BUZZER_PWM_PORT, BUZZER_DUTY, BUZZER_FREQ) != 0) {
        printf("[traffic_light] buzzer start failed\n");
        return;
    }
    usleep(BEEP_TIME_US);
    if (IoTPwmStop(BUZZER_PWM_PORT) != 0) {
        printf("[traffic_light] buzzer stop failed\n");
    }
}

static int IsButtonPressed(void)
{
    IotGpioValue value = IOT_GPIO_VALUE1;

    if (IoTGpioGetInputVal(BUTTON_GPIO, &value) != 0) {
        printf("[traffic_light] read button failed\n");
        return 0;
    }
    return value == IOT_GPIO_VALUE0;
}

static void WaitButtonRelease(void)
{
    while (IsButtonPressed()) {
        usleep(BUTTON_POLL_MS * 1000);
    }
}

static int WaitOrButton(unsigned int durationMs)
{
    unsigned int elapsedMs;

    for (elapsedMs = 0; elapsedMs < durationMs; elapsedMs += BUTTON_POLL_MS) {
        if (IsButtonPressed()) {
            printf("[traffic_light] button pressed, change state early\n");
            WaitButtonRelease();
            return 1;
        }
        usleep(BUTTON_POLL_MS * 1000);
    }
    return 0;
}

static void YellowBlink(void)
{
    unsigned int i;

    for (i = 0; i < YELLOW_BLINK_COUNT; ++i) {
        SetLights(IOT_GPIO_VALUE0, IOT_GPIO_VALUE1, IOT_GPIO_VALUE0);
        usleep(YELLOW_HALF_PERIOD_US);
        SetLights(IOT_GPIO_VALUE0, IOT_GPIO_VALUE0, IOT_GPIO_VALUE0);
        usleep(YELLOW_HALF_PERIOD_US);
    }
}

static void TrafficLightTask(void *argument)
{
    (void)argument;

    if (TrafficLightInit() != 0) {
        return;
    }

    for (;;) {
        printf("[traffic_light] RED\n");
        SetLights(IOT_GPIO_VALUE1, IOT_GPIO_VALUE0, IOT_GPIO_VALUE0);
        (void)WaitOrButton(RED_TIME_MS);
        Beep();

        printf("[traffic_light] GREEN\n");
        SetLights(IOT_GPIO_VALUE0, IOT_GPIO_VALUE0, IOT_GPIO_VALUE1);
        (void)WaitOrButton(GREEN_TIME_MS);
        Beep();

        printf("[traffic_light] YELLOW flashing\n");
        YellowBlink();
    }
}

static void TrafficLightExampleEntry(void)
{
    static const osThreadAttr_t attr = {
        .name = "TrafficLightTask",
        .stack_size = 3072,
        .priority = osPriorityNormal,
    };

    if (osThreadNew(TrafficLightTask, NULL, &attr) == NULL) {
        printf("[traffic_light] create task failed\n");
    }
}

SYS_RUN(TrafficLightExampleEntry);
