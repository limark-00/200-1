#include "day08_alarm.h"

#include <string.h>

void Day08Alarm_Init(Day08AlarmState *state)
{
    if (state == NULL) {
        return;
    }

    state->manual_alarm_on = 0;
    state->humidity_over = 0;
    state->humidity_silenced = 0;
    state->vision_alarm_on = 0;
}

void Day08Alarm_UpdateHumidity(Day08AlarmState *state, float humidity,
                               float threshold)
{
    if (state == NULL) {
        return;
    }

    state->humidity_over = humidity > threshold;
    if (!state->humidity_over) {
        state->humidity_silenced = 0;
    }
}

int Day08Alarm_ApplyCommand(Day08AlarmState *state, const char *command)
{
    if (state == NULL || command == NULL) {
        return 0;
    }

    if (strcmp(command, "alarm_on") == 0) {
        state->manual_alarm_on = 1;
        state->humidity_silenced = 0;
        return 1;
    }

    if (strcmp(command, "alarm_off") == 0) {
        state->manual_alarm_on = 0;
        state->humidity_silenced = 1;
        return 1;
    }

    if (strcmp(command, "vision_alarm_on") == 0) {
        state->vision_alarm_on = 1;
        return 1;
    }

    if (strcmp(command, "vision_alarm_off") == 0) {
        state->vision_alarm_on = 0;
        return 1;
    }

    return 0;
}

int Day08Alarm_ShouldBuzz(const Day08AlarmState *state)
{
    if (state == NULL) {
        return 0;
    }

    return state->manual_alarm_on ||
           state->vision_alarm_on ||
           (state->humidity_over && !state->humidity_silenced);
}
