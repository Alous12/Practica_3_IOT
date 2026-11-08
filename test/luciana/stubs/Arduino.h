#pragma once
#include <cstdint>
#include <cstring>
extern unsigned long fakeMillis;
extern int fakeLevel;
constexpr int INPUT=0, HIGH=1;
inline unsigned long millis() { return fakeMillis; }
inline void pinMode(uint8_t, int) {}
inline int digitalRead(uint8_t) { return fakeLevel; }
struct SerialMock {
  void println(const char*) {}
  template<class... T> void printf(const char*, T...) {}
};
extern SerialMock Serial;
