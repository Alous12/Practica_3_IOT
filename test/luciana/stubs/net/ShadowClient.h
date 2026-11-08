#pragma once
#include <ArduinoJson.h>
#include <functional>
#include "core/ShadowPort.h"
class ShadowClient : public ShadowPort {
 public:
  bool online=false, publishOk=true;
  int attempts=0, reports=0;
  JsonDocument last;
  std::function<void(JsonObjectConst)> delta;
  std::function<void()> connect;
  void onDelta(std::function<void(JsonObjectConst)> h) { delta=h; }
  void onConnected(std::function<void()> h) { connect=h; }
  bool connected() { return online; }
  bool publishReported(JsonObjectConst r) {
    attempts++;
    if (!publishOk) return false;
    last.set(r); reports++; return true;
  }
};
