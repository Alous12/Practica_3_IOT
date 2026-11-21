#pragma once
#include <cstdint>
#include <cstring>
#include <string>
/** String mínimo de Arduino (solo lo que usa SmartObject). */
class String {
 public:
  String(const char *text = "") : text_(text) {}
  const char *c_str() const { return text_.c_str(); }
 private:
  std::string text_;
};
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
