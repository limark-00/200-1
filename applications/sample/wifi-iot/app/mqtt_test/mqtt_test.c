#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include "ohos_init.h"
#include "cmsis_os2.h"

#include "hi_wifi_api.h"
#include "lwip/ip_addr.h"
#include "lwip/netifapi.h"
#include "lwip/sockets.h"

#include "MQTTClient.h"

#include "aht20.h"

#include "hi_gpio.h"
#include "hi_io.h"
#include "hi_i2c.h"



//#include "iot_gpio.h"
#include "iot_pwm.h"
#include "iot_i2c.h"
#include "iot_errno.h"

#include "ssd1306.h"
// #include "cJSON.h"       // JSON 解析库头文件



#define OLED_I2C_BAUDRATE 400*1000










static MQTTClient mq_client;

unsigned char *onenet_mqtt_buf;
unsigned char *onenet_mqtt_readbuf;
int buf_size;

Network n;
MQTTPacket_connectData data = MQTTPacket_connectData_initializer;

// 消息回调函数
void mqtt_callback(MessageData *msg_data)
{
	size_t res_len = 0;
	uint8_t *response_buf = NULL;
	char topicname[45] = {"$crsp/"};

	LOS_ASSERT(msg_data);

	printf("topic %.*s receive a message\r\n", msg_data->topicName->lenstring.len, msg_data->topicName->lenstring.data);

	printf("message is %.*s\r\n", msg_data->message->payloadlen, msg_data->message->payload);

    ssd1306_Fill(Black);
	ssd1306_SetCursor(0, 0);
	ssd1306_DrawString(msg_data->message->payload, Font_7x10, White);

	ssd1306_UpdateScreen();
	usleep(1000000); // 建议延长延时（1秒），避免刷新太快看不清

}

int mqtt_connect(void)
{

	uint32_t retval = 0;

	hi_io_set_func(HI_IO_NAME_GPIO_13, HI_IO_FUNC_GPIO_13_I2C0_SDA);
	hi_io_set_func(HI_IO_NAME_GPIO_14, HI_IO_FUNC_GPIO_14_I2C0_SCL);

	hi_i2c_init(HI_I2C_IDX_0, 400 * 1000);
	


    usleep(20*1000);
    ssd1306_Init();
    ssd1306_Fill(Black);
    ssd1306_SetCursor(0, 0);
    ssd1306_DrawString("system start!", Font_7x10, White);

	ssd1306_UpdateScreen();
	    usleep(1000000); // 建议延长延时（1秒），避免刷新太快看不清




	retval = AHT20_Calibrate();
	printf("AHT20_Calibrate: %d\r\n", retval);

	int rc = 0;

	NetworkInit(&n);
	// NetworkConnect(&n, "192.168.38.195", 1883);
	NetworkConnect(&n, "192.168.38.195", 1883);

	buf_size = 4096 + 1024;
	onenet_mqtt_buf = (unsigned char *)malloc(buf_size);
	onenet_mqtt_readbuf = (unsigned char *)malloc(buf_size);
	if (!(onenet_mqtt_buf && onenet_mqtt_readbuf))
	{
		printf("No memory for MQTT client buffer!");
		return -2;
	}

	MQTTClientInit(&mq_client, &n, 1000, onenet_mqtt_buf, buf_size, onenet_mqtt_readbuf, buf_size);

	MQTTStartTask(&mq_client);

	data.keepAliveInterval = 30;
	data.cleansession = 1;
	// data.clientID.cstring = "hm_dev_002";
	// data.username.cstring = "user4";
	// data.password.cstring = "1234";
	data.clientID.cstring = "c91130ab47dc43cb8e16aeeb76ca8d4a";
	data.username.cstring = "";
	data.password.cstring = "";
	data.cleansession = 1;

	mq_client.defaultMessageHandler = mqtt_callback;

	// 连接服务器
	rc = MQTTConnect(&mq_client, &data);

	// 订阅消息，并设置回调函数
	// MQTTSubscribe(&mq_client, "ohossub", 0, mqtt_callback);

	// 订阅消息，并设置回调函数
	int sub_rc = MQTTSubscribe(&mq_client, "harmony/car_room/control", 0, mqtt_callback);
	if (sub_rc != 0)
	{
		printf("Subscription failed! Error code: %d\r\n", sub_rc);
	}
	else
	{
		printf("Subscription topic 'harmony/car_room/control' success\r\n");
	}

	while (1)
	{

		// read temp

		float temp = 0.0, humi = 0.0;

		retval = AHT20_StartMeasure();
		printf("AHT20_StartMeasure: %d\r\n", retval);

		retval = AHT20_GetMeasureResult(&temp, &humi);
		printf("AHT20_GetMeasureResult: %d, temp = %.2f, humi = %.2f\r\n", retval, temp, humi);

		// 专门为智能家居传感器设计的 JSON 格式
		// float temperature = 25.5;
		// float humidity = 60.0;
		int light_level = 350;
		// 获取当前时间戳
		//time_t current_time = time(NULL);

		char json_payload[200];
		snprintf(json_payload, sizeof(json_payload),
				 "{"
				 "\"device_id\": \"hm_dev_002\","
				 "\"messageId\": \"messageId\","
				 "\"properties\": {"
				 "\"temperature\": %.1f,"
				 "\"humidity\": %.1f,"
				 "\"light\": %d"
				 "},"
				 "\"success\": true"
				 "}",
				 temp, humi, light_level, (long)time(NULL));

		MQTTMessage message;
		message.qos = QOS1;
		message.retained = 0;
		message.payload = (void *)json_payload;
		message.payloadlen = strlen(json_payload);

		// 使用更有意义的主题名称
		if (MQTTPublish(&mq_client, "/hm002p/hm_dev_002/properties/report", &message) < 0)
		{
			printf("MQTTPublish failed !\r\n");
		}

		// MQTTMessage message;

		// message.qos = QOS1;
		// message.retained = 0;
		// message.payload = (void *)"openharmony";
		// message.payloadlen = strlen("openharmony");

		// 发送消息
		// if (MQTTPublish(&mq_client, "ohospub", &message) < 0)
		// {
		// 	printf("MQTTPublish faild !\r\n");
		// }
		usleep(1000000);
	}

	return 0;
}

void mqtt_test(void)
{
	mqtt_connect();
}
