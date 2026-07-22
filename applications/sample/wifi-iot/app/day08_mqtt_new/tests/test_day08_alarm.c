#include <assert.h>

#include "day08_alarm.h"

int main(void)
{
    Day08AlarmState state;
    Day08Alarm_Init(&state);

    Day08Alarm_UpdateHumidity(&state, 60.0f, 45.0f);
    assert(Day08Alarm_ShouldBuzz(&state) == 1);

    assert(Day08Alarm_ApplyCommand(&state, "vision_alarm_on") == 1);
    assert(Day08Alarm_ApplyCommand(&state, "alarm_off") == 1);
    assert(Day08Alarm_ShouldBuzz(&state) == 1);

    assert(Day08Alarm_ApplyCommand(&state, "vision_alarm_off") == 1);
    assert(Day08Alarm_ShouldBuzz(&state) == 0);

    Day08Alarm_UpdateHumidity(&state, 40.0f, 45.0f);
    assert(state.humidity_silenced == 0);
    assert(Day08Alarm_ApplyCommand(&state, "unknown") == 0);
    return 0;
}
