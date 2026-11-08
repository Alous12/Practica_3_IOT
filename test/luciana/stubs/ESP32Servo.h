#pragma once
#include "Arduino.h"
extern bool servoAttached;
extern int servoAngle;
class Servo {
 public:
  void setPeriodHertz(int) {}
  bool attached() { return servoAttached; }
  void attach(uint8_t,int,int) { servoAttached=true; }
  void detach() { servoAttached=false; }
  void write(int angle) { servoAngle=angle; }
};
