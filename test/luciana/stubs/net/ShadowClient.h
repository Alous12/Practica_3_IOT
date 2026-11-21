#pragma once
#include <ArduinoJson.h>
#include <functional>
#include "core/ShadowPort.h"
class ShadowClient : public ShadowPort {
 public:
  bool online=false, publishOk=true;
  int attempts=0, reports=0;
  JsonDocument last;
  JsonDocument lastDesired;
  std::function<void(JsonObjectConst)> delta;
  std::function<void()> connect;
  void onDelta(std::function<void(JsonObjectConst)> h) { delta=h; }
  void onConnected(std::function<void()> h) { connect=h; }
  bool connected() { return online; }
  bool publishReported(JsonObjectConst r) {
    return publishUpdate(r, JsonObjectConst());
  }
  bool publishUpdate(JsonObjectConst r, JsonObjectConst desired) {
    attempts++;
    if (!publishOk) return false;
    last.set(r); lastDesired.set(desired); reports++; return true;
  }
};
