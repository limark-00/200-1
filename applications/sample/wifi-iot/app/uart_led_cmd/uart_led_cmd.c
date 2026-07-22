/*
 * USB 调试串口 (UART0) 收指令，控制板载 LED (GPIO9)。
 *
 * 启用方式：在上级 app/BUILD.gn 的 features 中只保留一行：
 *   "uart_led_cmd:uart_led_cmd"
 *
 * 串口助手：115200 8N1，发送（建议带换行）：
 *   on / off
 *   LED:1 / LED:0
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "cmsis_os2.h"
#include "iot_errno.h"
#include "iot_gpio.h"
#include "iot_uart.h"
#include "ohos_init.h"

#define LED_GPIO          9
#define UART_ID           0
#define UART_BAUDRATE     115200
#define LINE_BUF_SIZE     64
#define TASK_STACK_SIZE   2048
#define TASK_PRIO         25

static void LedInit(void)
{
    IoTGpioInit(LED_GPIO);
    IoTGpioSetDir(LED_GPIO, IOT_GPIO_DIR_OUT);
    IoTGpioSetOutputVal(LED_GPIO, 0);
}

static void LedSet(int on)
{
    IoTGpioSetOutputVal(LED_GPIO, on ? 1 : 0);
}

static int UartInit(void)
{
    IotUartAttribute attr = {0};
    attr.baudRate = UART_BAUDRATE;
    attr.dataBits = IOT_UART_DATA_BIT_8;
    attr.stopBits = IOT_UART_STOP_BIT_1;
    attr.parity = IOT_UART_PARITY_NONE;
    attr.rxBlock = IOT_UART_BLOCK_STATE_BLOCK;
    attr.txBlock = IOT_UART_BLOCK_STATE_NONE_BLOCK;
    attr.pad = 0;

    unsigned int ret = IoTUartInit(UART_ID, &attr);
    if (ret != IOT_SUCCESS) {
        /* 控制台可能已初始化过 UART0，仍继续尝试读 */
        printf("[uart_led_cmd] IoTUartInit ret=%u, continue read\n", ret);
    }
    return 0;
}

static void TrimLine(char *s)
{
    size_t n = strlen(s);
    while (n > 0 && (s[n - 1] == '\r' || s[n - 1] == '\n' || s[n - 1] == ' ' || s[n - 1] == '\t')) {
        s[--n] = '\0';
    }
}

static void Reply(const char *msg)
{
    printf("%s\n", msg);
    IoTUartWrite(UART_ID, (const unsigned char *)msg, (unsigned int)strlen(msg));
    IoTUartWrite(UART_ID, (const unsigned char *)"\r\n", 2);
}

static void HandleCmd(char *line)
{
    TrimLine(line);
    if (line[0] == '\0') {
        return;
    }

    if (strcmp(line, "on") == 0 || strcmp(line, "ON") == 0 || strcmp(line, "LED:1") == 0) {
        LedSet(1);
        Reply("OK on");
        return;
    }
    if (strcmp(line, "off") == 0 || strcmp(line, "OFF") == 0 || strcmp(line, "LED:0") == 0) {
        LedSet(0);
        Reply("OK off");
        return;
    }

    Reply("ERR use: on|off|LED:1|LED:0");
}

static void *UartLedTask(const char *arg)
{
    unsigned char ch = 0;
    char line[LINE_BUF_SIZE];
    size_t pos = 0;

    (void)arg;
    LedInit();
    UartInit();

    printf("[uart_led_cmd] ready, baud=%d, send on/off\n", UART_BAUDRATE);
    Reply("uart_led_cmd ready");

    while (1) {
        int n = IoTUartRead(UART_ID, &ch, 1);
        if (n <= 0) {
            usleep(10000);
            continue;
        }

        if (ch == '\r' || ch == '\n') {
            if (pos > 0) {
                line[pos] = '\0';
                HandleCmd(line);
                pos = 0;
            }
            continue;
        }

        if (pos + 1 < LINE_BUF_SIZE) {
            line[pos++] = (char)ch;
        } else {
            pos = 0;
            Reply("ERR line too long");
        }
    }

    return NULL;
}

static void UartLedCmdEntry(void)
{
    osThreadAttr_t attr;
    attr.name = "UartLedTask";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = TASK_STACK_SIZE;
    attr.priority = TASK_PRIO;

    if (osThreadNew((osThreadFunc_t)UartLedTask, NULL, &attr) == NULL) {
        printf("[uart_led_cmd] Failed to create UartLedTask\n");
    }
}

SYS_RUN(UartLedCmdEntry);
