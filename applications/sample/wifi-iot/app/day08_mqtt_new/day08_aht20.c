#include "day08_aht20.h"

#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

/*
 * OpenHarmony 1.x commonly uses wifiiot_i2c.h; some newer trees expose
 * iot_i2c.h. Keep both paths so this module can be copied between the
 * common Hi3861 source layouts.
 */
#include "iot_i2c.h"
#include "hi_io.h"

#define DAY08_AHT20_ADDR_WRITE     0x70U
#define DAY08_AHT20_ADDR_READ      0x71U
#define DAY08_AHT20_I2C_BAUDRATE   400000U

#define DAY08_AHT20_STATUS_BUSY       0x80U
#define DAY08_AHT20_STATUS_CALIBRATED 0x08U

#define DAY08_AHT20_POWER_ON_US      40000U
#define DAY08_AHT20_CALIBRATE_US     40000U
#define DAY08_AHT20_MEASURE_US       85000U
#define DAY08_AHT20_BUSY_RETRY_US    10000U
#define DAY08_AHT20_BUSY_RETRY_COUNT 5U

static unsigned int Day08Aht20_I2cWrite(const unsigned char *buf,unsigned int len)
{
    return IoTI2cWrite(0U,DAY08_AHT20_ADDR_WRITE,buf,len);
}

static unsigned int Day08Aht20_I2cRead(unsigned char *buf,unsigned int len)
{
    return IoTI2cRead(0U,DAY08_AHT20_ADDR_READ,buf,len);
}

static int Day08Aht20_ReadStatus(unsigned char *status)
{
    if (status == NULL) {
        return -1;
    }

    *status = 0;
    if (Day08Aht20_I2cRead(status, 1U) != 0U) {
        return -1;
    }
    return 0;
}

static int Day08Aht20_Calibrate(void)
{
    static const unsigned char cmd[] = {0xBEU, 0x08U, 0x00U};

    if (Day08Aht20_I2cWrite(cmd, sizeof(cmd)) != 0U) {
        return -1;
    }
    usleep(DAY08_AHT20_CALIBRATE_US);
    return 0;
}

int Day08Aht20_Init(void)
{
    unsigned int ret;
    unsigned char status = 0;ret = hi_io_set_func(HI_IO_NAME_GPIO_13, HI_IO_FUNC_GPIO_13_I2C0_SDA);
    if (ret != 0U) {
        printf("[day08][aht20] set GPIO13/I2C0_SDA failed (%u)\n",ret);
        return -1;
    }

    ret = hi_io_set_func(HI_IO_NAME_GPIO_14,HI_IO_FUNC_GPIO_14_I2C0_SCL);
    if (ret != 0U) {
        printf("[day08][aht20] set GPIO14/I2C0_SCL failed (%u)\n",ret);
        return -1;
    }

    ret = IoTI2cInit(0U,DAY08_AHT20_I2C_BAUDRATE);


    if (ret != 0U) {
        printf("[day08][aht20] I2C0 init failed (%u)\n", ret);
        return -1;
    }

    usleep(DAY08_AHT20_POWER_ON_US);

    if (Day08Aht20_ReadStatus(&status) != 0) {
        printf("[day08][aht20] read status failed\n");
        return -1;
    }

    if ((status & DAY08_AHT20_STATUS_CALIBRATED) == 0U) {
        printf("[day08][aht20] calibrating...\n");
        if (Day08Aht20_Calibrate() != 0) {
            printf("[day08][aht20] calibrate command failed\n");
            return -1;
        }

        if (Day08Aht20_ReadStatus(&status) != 0 ||
            (status & DAY08_AHT20_STATUS_CALIBRATED) == 0U) {
            printf("[day08][aht20] calibration not ready, status=0x%02X\n",
                   status);
            return -1;
        }
    }

    printf("[day08][aht20] ready, status=0x%02X\n", status);
    return 0;
}

int Day08Aht20_Read(Day08Aht20Data *data)
{
    static const unsigned char measure_cmd[] = {0xACU, 0x33U, 0x00U};
    unsigned char raw[6] = {0};
    unsigned int humidity_raw;
    unsigned int temperature_raw;
    unsigned int retry;

    if (data == NULL) {
        return -1;
    }

    if (Day08Aht20_I2cWrite(measure_cmd, sizeof(measure_cmd)) != 0U) {
        return -1;
    }

    usleep(DAY08_AHT20_MEASURE_US);

    for (retry = 0; retry < DAY08_AHT20_BUSY_RETRY_COUNT; retry++) {
        if (Day08Aht20_I2cRead(raw, sizeof(raw)) != 0U) {
            return -1;
        }
        if ((raw[0] & DAY08_AHT20_STATUS_BUSY) == 0U) {
            break;
        }
        usleep(DAY08_AHT20_BUSY_RETRY_US);
    }

    if ((raw[0] & DAY08_AHT20_STATUS_BUSY) != 0U) {
        return -1;
    }

    humidity_raw =
        (((unsigned int)raw[1] << 16U) |
         ((unsigned int)raw[2] << 8U) |
         (unsigned int)raw[3]) >> 4U;

    temperature_raw =
        (((unsigned int)raw[3] & 0x0FU) << 16U) |
        ((unsigned int)raw[4] << 8U) |
        (unsigned int)raw[5];

    data->humidity_rh =
        ((float)humidity_raw * 100.0f) / 1048576.0f;
    data->temperature_c =
        ((float)temperature_raw * 200.0f) / 1048576.0f - 50.0f;

    if (data->humidity_rh < 0.0f || data->humidity_rh > 100.0f ||
        data->temperature_c < -50.0f || data->temperature_c > 100.0f) {
        return -1;
    }

    return 0;
}
