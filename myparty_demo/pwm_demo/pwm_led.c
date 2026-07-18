#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

#include "cmsis_os2.h"
#include "ohos_init.h"
#include "iot_gpio.h"
#include "iot_pwm.h"
#include "hi_io.h"

#define RED_GPIO 10
#define GREEN_GPIO 11
#define BLUE_GPIO 12
#define RED_PWM_PORT 1
#define GREEN_PWM_PORT 2
#define BLUE_PWM_PORT 3
#define RGB_PWM_FREQ 20000
#define FADE_STEPS 100
#define FADE_STEP_TIME_US 20000

typedef struct {
    uint8_t red;
    uint8_t green;
    uint8_t blue;
} RgbColor;

static int InitPwmPin(unsigned int gpio, hi_io_name ioName,
    unsigned char ioFunc, unsigned int pwmPort)
{
    if (IoTGpioInit(gpio) != 0) {
        printf("[pwm_led] GPIO%u init failed\n", gpio);
        return -1;
    }
    if (hi_io_set_func(ioName, ioFunc) != 0) {
        printf("[pwm_led] GPIO%u PWM function setup failed\n", gpio);
        return -1;
    }
    if (IoTPwmInit(pwmPort) != 0) {
        printf("[pwm_led] PWM%u init failed\n", pwmPort);
        return -1;
    }
    return 0;
}

static int RgbLedInit(void)
{
    if (InitPwmPin(RED_GPIO, HI_IO_NAME_GPIO_10,
        HI_IO_FUNC_GPIO_10_PWM1_OUT, RED_PWM_PORT) != 0 ||
        InitPwmPin(GREEN_GPIO, HI_IO_NAME_GPIO_11,
        HI_IO_FUNC_GPIO_11_PWM2_OUT, GREEN_PWM_PORT) != 0 ||
        InitPwmPin(BLUE_GPIO, HI_IO_NAME_GPIO_12,
        HI_IO_FUNC_GPIO_12_PWM3_OUT, BLUE_PWM_PORT) != 0) {
        return -1;
    }
    return 0;
}

static unsigned short MapToDuty(uint8_t value)
{
    return (unsigned short)(((uint32_t)value * 98U) / 255U + 1U);
}

static void SetChannel(unsigned int pwmPort, uint8_t value)
{
    if (value == 0) {
        (void)IoTPwmStop(pwmPort);
        return;
    }

    if (IoTPwmStart(pwmPort, MapToDuty(value), RGB_PWM_FREQ) != 0) {
        printf("[pwm_led] PWM%u start failed\n", pwmPort);
    }
}

static void SetColor(uint8_t red, uint8_t green, uint8_t blue)
{
    SetChannel(RED_PWM_PORT, red);
    SetChannel(GREEN_PWM_PORT, green);
    SetChannel(BLUE_PWM_PORT, blue);
}

static uint8_t Interpolate(uint8_t from, uint8_t to, unsigned int step)
{
    int value = (int)from + ((int)to - (int)from) * (int)step / FADE_STEPS;
    return (uint8_t)value;
}

static void Fade(RgbColor from, RgbColor to)
{
    unsigned int step;

    for (step = 0; step <= FADE_STEPS; ++step) {
        SetColor(Interpolate(from.red, to.red, step),
            Interpolate(from.green, to.green, step),
            Interpolate(from.blue, to.blue, step));
        usleep(FADE_STEP_TIME_US);
    }
}

static void RgbLedTask(void *argument)
{
    static const RgbColor red = {255, 0, 0};
    static const RgbColor green = {0, 255, 0};
    static const RgbColor blue = {0, 0, 255};
    (void)argument;

    if (RgbLedInit() != 0) {
        return;
    }

    printf("[pwm_led] RGB fade: red -> green -> blue -> red\n");
    for (;;) {
        Fade(red, green);
        Fade(green, blue);
        Fade(blue, red);
    }
}

static void RgbLedExampleEntry(void)
{
    static const osThreadAttr_t attr = {
        .name = "RgbLedTask",
        .stack_size = 2048,
        .priority = osPriorityNormal,
    };

    if (osThreadNew(RgbLedTask, NULL, &attr) == NULL) {
        printf("[pwm_led] create task failed\n");
    }
}

SYS_RUN(RgbLedExampleEntry);
