#include <unistd.h>
#include <stdio.h>
#include "ohos_init.h"
#include "cmsis_os2.h"
#include "iot_gpio.h"

#define LED_TEST_GPIO 9 // hispark_pegasus板载LED引脚

void *LedTask(const char *arg)
{
    //初始化GPIO
    IoTGpioInit(LED_TEST_GPIO);

    //设置为输出
    IoTGpioSetDir(LED_TEST_GPIO, IOT_GPIO_DIR_OUT);

    (void)arg;
    while (1) 
    {
        //输出低电平
        IoTGpioSetDir(LED_TEST_GPIO, 0);
        usleep(300000);
        //输出高电平
        IoTGpioSetDir(LED_TEST_GPIO, 1);
        usleep(300000);
        
        
        IoTGpioSetOutputVal(LED_TEST_GPIO, 0);
        usleep(300000);
        IoTGpioSetOutputVal(LED_TEST_GPIO, 1);
        usleep(300000);
        
    }

    return NULL;
}
void led_demo(void)
{
    osThreadAttr_t attr;
    attr.name = "LedTask";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 1024;
    attr.priority = 26;

    if (osThreadNew((osThreadFunc_t)LedTask, NULL, &attr) == NULL)
    {
        printf("[LedExample] Failed to create LedTask!\n");
    }
}

// 关键：开机自动执行led_demo函数
SYS_RUN(led_demo);