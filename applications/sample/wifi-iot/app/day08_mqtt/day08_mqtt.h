#ifndef DAY08_MQTT_H
#define DAY08_MQTT_H

/**
 * Build the Day08 state JSON into buf.
 * Returns length written (excluding NUL), or -1 on error.
 */
int Day08_BuildStateJson(char *buf, unsigned int len);

/**
 * Online path: connect to broker and publish state periodically.
 * Returns only on fatal MQTT failure (caller may fall back to UART).
 */
int Day08_MqttLoop(void);

/**
 * Offline fallback: print the same JSON to UART every report period.
 * Never returns.
 */
void Day08_UartFallbackLoop(void);

#endif /* DAY08_MQTT_H */
