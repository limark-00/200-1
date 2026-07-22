#ifndef DAY08_AHT20_H
#define DAY08_AHT20_H

typedef struct {
    float temperature_c;
    float humidity_rh;
} Day08Aht20Data;

/* Configure GPIO13/GPIO14 as I2C0 and initialize the AHT20. */
int Day08Aht20_Init(void);

/* Read one temperature/humidity sample. */
int Day08Aht20_Read(Day08Aht20Data *data);

#endif /* DAY08_AHT20_H */
