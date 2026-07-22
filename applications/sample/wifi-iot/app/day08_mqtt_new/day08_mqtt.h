#ifndef DAY08_MQTT_H
#define DAY08_MQTT_H

#include "day08_aht20.h"

/*
 * Build one telemetry JSON payload.
 * Returns payload length excluding NUL, or -1 on error.
 */
int Day08_BuildTelemetryJson(char *buf, unsigned int len,
                             const Day08Aht20Data *sample);

/*
 * Connect to the configured MQTT broker and periodically publish AHT20 data.
 * Returns only on a fatal MQTT/network failure.
 */
int Day08_MqttLoop(void);

/* Print the same AHT20 JSON through UART when Wi-Fi/MQTT is unavailable. */
void Day08_UartFallbackLoop(void);

#endif /* DAY08_MQTT_H */
