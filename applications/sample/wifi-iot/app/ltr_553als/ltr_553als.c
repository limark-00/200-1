#include <stdio.h>
#include <unistd.h>

#include "ohos_init.h"
#include "cmsis_os2.h"
#include "iot_gpio.h"
#include "iot_pwm.h"
#include "iot_i2c.h"
#include "iot_errno.h"

#include "hi_io.h"
#include "hi_i2c.h"
#include "hi_errno.h"

#include "ltr_553als.h"

#define LTR553_I2C_BAUDRATE 400*1000

#ifndef LTR553_I2C_PORT
#define LTR553_I2C_PORT        0
#endif

#ifndef LTR553_I2C_ADDR
#define LTR553_I2C_ADDR        (0x23 << 1)
#endif



static uint32_t i2c_write_reg(uint8_t regAddr, uint8_t val)
{
    uint8_t buffer[] = {regAddr, val};
    hi_i2c_data data = { 0 };
    data.send_buf = buffer;
    data.send_len = 2;
    uint32_t retval = hi_i2c_write(LTR553_I2C_PORT, LTR553_I2C_ADDR, &data);
    if (retval != HI_ERR_SUCCESS) {
        printf("_______>>>>>>>> %s %d \r\n", __FILE__, __LINE__);
        printf("I2cWrite(%02X) failed, %0X!\n", buffer[0], retval);
        return retval;
    }
    return HI_ERR_SUCCESS;
}


static uint32_t i2c_read_reg(uint8_t regAddr)
{
    uint8_t buffer[] = {regAddr};
    uint8_t rbuffer[] = {0};
    hi_i2c_data data = { 0 };
    data.send_buf = buffer;
    data.send_len = 1;
    data.receive_buf = rbuffer;
    data.receive_len = 1;
    uint32_t retval = hi_i2c_writeread(LTR553_I2C_PORT, LTR553_I2C_ADDR | 0x01, &data);
    if (retval != HI_ERR_SUCCESS) {
        printf("_______>>>>>>>> %s %d \r\n", __FILE__, __LINE__);
        printf("I2cRead() failed, %0X!\n", retval);
        return retval;
    }
    printf("_____>>>>>>> rbuffer[0] is %d \r\n", rbuffer[0]);
    return rbuffer[0];
}

uint8_t ltr559_init(void)
{
  printf("_______>>>>>>>> %s %d \r\n", __FILE__, __LINE__);
  i2c_write_reg(LTR559_PS_N_PULSES, 0x04);
  i2c_write_reg(LTR559_PS_LED, 0x7f);
  i2c_write_reg(LTR559_PS_MEAS_RATE, 0x02);
  i2c_write_reg(LTR559_ALS_CONTR, 0x00);
  i2c_write_reg(LTR559_ALS_MEAS_RATE, 0x02);
	
  /*for interrup work mode support */
  if (PS_INTERRUPT_MODE)
  {
    printf("_______>>>>>>>> %s %d \r\n", __FILE__, __LINE__);
    i2c_write_reg(LTR559_INTERRUPT, 0x01);
    i2c_write_reg(LTR559_INTERRUPT_PERSIST, 0x20);
	  ltr559_ps_set_threshold(PS_THRES_UP, PS_THRES_LOW);    
  }   
  printf("_______>>>>>>>> %s %d \r\n", __FILE__, __LINE__);
  ltr559_ps_enable(1);
  ltr559_als_enable(1);

  return LTR559_SUCCESS;
}

uint8_t ltr559_ps_enable(uint8_t enable)
{
  uint8_t regdata = 0;
	
  regdata = i2c_read_reg(LTR559_PS_CONTR);
  if (enable != 0) {
    regdata |= 0x03;
  }
  else {
    regdata &= 0xfc;
  }

  i2c_write_reg(LTR559_PS_CONTR, regdata);
    
  return LTR559_SUCCESS;
}

uint8_t ltr559_als_enable(uint8_t enable)
{
  uint8_t regdata = 0;
	
  regdata = i2c_read_reg(LTR559_ALS_CONTR);
  if (enable != 0) {
    regdata |= 0x01;
  }
  else {
    regdata &= 0xfe;
  }

  i2c_write_reg(LTR559_ALS_CONTR, regdata);
    
  return LTR559_SUCCESS;
}

uint16_t ltr559_ps_read(void)
{
  uint8_t psval_lo, psval_hi;
  uint16_t psdata;
    
  psval_lo = i2c_read_reg(LTR559_PS_DATA_0);
  psval_hi = i2c_read_reg(LTR559_PS_DATA_1);
    
  psdata = ((psval_hi & 0x07) * 256) + psval_lo;
    
  return psdata;
}

uint16_t ltr559_als_read(uint8_t chn)
{
  uint8_t alsval_lo, alsval_hi;
  uint16_t alsdata;
    
  if (chn == 1)
  {
	alsval_lo = i2c_read_reg(LTR559_ALS_DATA_CH1_0);
	alsval_hi = i2c_read_reg(LTR559_ALS_DATA_CH1_1);
  }
  else if (chn == 0)
  {
	alsval_lo = i2c_read_reg(LTR559_ALS_DATA_CH0_0);
	alsval_hi = i2c_read_reg(LTR559_ALS_DATA_CH0_1);
  }
  else
  {
	  return 0;
  }
    
  alsdata = (alsval_hi << 8) + alsval_lo;
    
  return alsdata;  
}

uint8_t ltr559_ps_set_threshold(uint16_t high, uint16_t low)
{
	i2c_write_reg(LTR559_PS_THRES_UP_0, high & 0x00FF);
	i2c_write_reg(LTR559_PS_THRES_UP_1, (high >> 8) & 0x00FF);
	i2c_write_reg(LTR559_PS_THRES_LOW_0, low & 0x00FF);
	i2c_write_reg(LTR559_PS_THRES_LOW_1, (low >> 8) & 0x00FF);

	return LTR559_SUCCESS;
}


void Ltr553TestTask(void* arg)
{
    uint16_t ltr559_ps, ltr559_als_0, ltr559_als_1;

    (void) arg;
    IoTGpioInit(HI_IO_NAME_GPIO_13);
    IoTGpioInit(HI_IO_NAME_GPIO_14);

    hi_io_set_func(HI_IO_NAME_GPIO_13, HI_IO_FUNC_GPIO_13_I2C0_SDA);
    hi_io_set_func(HI_IO_NAME_GPIO_14, HI_IO_FUNC_GPIO_14_I2C0_SCL);
    
    IoTI2cInit(0, LTR553_I2C_BAUDRATE);

    ltr559_init();


    while (1) {
        
        ltr559_ps = ltr559_ps_read();
        ltr559_als_0 = ltr559_als_read(0);
        ltr559_als_1 = ltr559_als_read(1);

        printf("_______>>>>>>>>> ltr559_ps is %d \r\n", ltr559_ps);
        printf("_______>>>>>>>>> ltr559_als_0 is %d \r\n", ltr559_als_0);
        printf("_______>>>>>>>>> ltr559_als_1 is %d \r\n", ltr559_als_1);
        printf("\r\n");

        usleep(2000000);
    }
}

void Ssd1306TestDemo(void)
{
    osThreadAttr_t attr;

    attr.name = "Ltr553TestTask";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 10240;
    attr.priority = osPriorityNormal;

    if (osThreadNew(Ltr553TestTask, NULL, &attr) == NULL) {
        printf("[Ltr553TestTask] Falied to create Ltr553TestTask!\n");
    }
}
APP_FEATURE_INIT(Ssd1306TestDemo);
