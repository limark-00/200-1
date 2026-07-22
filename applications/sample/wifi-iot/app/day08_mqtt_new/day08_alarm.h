#ifndef DAY08_ALARM_H
#define DAY08_ALARM_H

typedef struct {
    int manual_alarm_on;
    int humidity_over;
    int humidity_silenced;
    int vision_alarm_on;
} Day08AlarmState;

void Day08Alarm_Init(Day08AlarmState *state);
void Day08Alarm_UpdateHumidity(Day08AlarmState *state, float humidity,
                               float threshold);
int Day08Alarm_ApplyCommand(Day08AlarmState *state, const char *command);
int Day08Alarm_ShouldBuzz(const Day08AlarmState *state);

#endif
