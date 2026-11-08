#include "net/TimeSync.h"

#include <Arduino.h>
#include <sys/time.h>
#include <time.h>

#include "config.h"

namespace {
// Cualquier hora anterior a 2024 indica que el reloj aún no se sincronizó.
constexpr time_t kMinValidEpoch = 1704067200;  // 2024-01-01T00:00:00Z
}  // namespace

void TimeSync::begin() {
  configTime(0, 0, NTP_SERVER_1, NTP_SERVER_2);
}

uint32_t TimeSync::nowEpoch() {
  time_t now = time(nullptr);
  return now >= kMinValidEpoch ? static_cast<uint32_t>(now) : 0;
}

uint64_t TimeSync::nowEpochMs() {
  struct timeval tv;
  gettimeofday(&tv, nullptr);
  if (tv.tv_sec < kMinValidEpoch) {
    return 0;
  }
  return static_cast<uint64_t>(tv.tv_sec) * 1000ULL + tv.tv_usec / 1000;
}
