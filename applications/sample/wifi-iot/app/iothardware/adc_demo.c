/*
 * Copyright (c) 2020, HiHope Community.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived from
 *    this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <stdio.h>
#include <unistd.h>

#include "ohos_init.h"
#include "cmsis_os2.h"

#include <unistd.h>
#include <hi_types_base.h>

#include <hi_adc.h>
#include <hi_stdlib.h>
#include <hi_early_debug.h>
#include "iot_gpio.h"

//LDE灯
#define LED_TEST_GPIO 9 // for hispark_pegasus

//光感传感器IO
#define LIGHT_SENSOR_CHAN_NAME HI_ADC_CHANNEL_4


static void ADCLightTask(void *arg)
{
    (void)arg;
    
    //初始化GPIO
    IoTGpioInit(LED_TEST_GPIO);

    //设置为输出
    IoTGpioSetDir(LED_TEST_GPIO, IOT_GPIO_DIR_OUT);

    while (1) {
        unsigned short data = 0;
        
        //读取光敏传感器得数值
        if (hi_adc_read(LIGHT_SENSOR_CHAN_NAME, &data, HI_ADC_EQU_MODEL_4, HI_ADC_CUR_BAIS_DEFAULT, 0)
            == HI_ERR_SUCCESS) {
            printf("ADC_VALUE = %d\n", (unsigned int)data);
                 printf("select high and lower level!!!!!!!---------------------------------\n");
            if(data > 150)
            {
                //输出高电平

                printf("high level!!!!!!!---------------------------------\n");

                IoTGpioSetOutputVal(LED_TEST_GPIO, 1);
            }else{
                //输出低电平
                printf("h---------------------------------lower level!!!!!!!\n");

                IoTGpioSetOutputVal(LED_TEST_GPIO, 0);
            }
            osDelay(1000);
        }
        
    }
}

static void ADCLightDemo(void)
{
    osThreadAttr_t attr;

    attr.name = "ADCLightTask";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 4096;
    attr.priority = osPriorityNormal;

    if (osThreadNew(ADCLightTask, NULL, &attr) == NULL) {
        printf("[ADCLightDemo] Falied to create ADCLightTask!\n");
    }
}

APP_FEATURE_INIT(ADCLightDemo);
