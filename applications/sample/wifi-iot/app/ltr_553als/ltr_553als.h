/*LTR559 als/ps sensor register*/
#define LTR559_ALS_CONTR		0x80
#define LTR559_PS_CONTR			0x81
#define LTR559_PS_LED			0x82
#define LTR559_PS_N_PULSES		0x83
#define LTR559_PS_MEAS_RATE		0x84
#define LTR559_ALS_MEAS_RATE	0x85
#define LTR559_PART_ID	        0x86
#define LTR559_MANUFACTURER_ID	0x87
#define LTR559_ALS_DATA_CH1_0	0x88
#define LTR559_ALS_DATA_CH1_1	0x89
#define LTR559_ALS_DATA_CH0_0	0x8A
#define LTR559_ALS_DATA_CH0_1	0x8B
#define LTR559_ALS_PS_STATUS	0x8C
#define LTR559_PS_DATA_0		0x8D
#define LTR559_PS_DATA_1		0x8E
#define LTR559_INTERRUPT		0x8F
#define LTR559_PS_THRES_UP_0	0x90
#define LTR559_PS_THRES_UP_1	0x91
#define LTR559_PS_THRES_LOW_0	0x92
#define LTR559_PS_THRES_LOW_1	0x93
#define LTR559_PS_OFFSET_1		0x94
#define LTR559_PS_OFFSET_0		0x95
#define LTR559_ALS_THRES_UP_0	0x97
#define LTR559_ALS_THRES_UP_1	0x98
#define LTR559_ALS_THRES_LOW_0	0x99
#define LTR559_ALS_THRES_LOW_1	0x9A
#define LTR559_INTERRUPT_PERSIST 0x9E
/* LTR-559 Registers */

#define PS_INTERRUPT_MODE         0
#ifdef PS_INTERRUPT_MODE
#define PS_THRES_UP               0x0400
#define PS_THRES_LOW              0x0200
#endif

#define LTR559_SUCCESS            0
#define LTR559_ERROR              0xFF

#define ALS_DATA                  0
#define PS_DATA                   1

uint8_t ltr559_init(void);
uint8_t ltr559_ps_enable(uint8_t enable);
uint8_t ltr559_als_enable(uint8_t enable);
uint16_t ltr559_ps_read(void);
uint16_t ltr559_als_read(uint8_t chn);
uint8_t ltr559_ps_set_threshold(uint16_t high, uint16_t low);
