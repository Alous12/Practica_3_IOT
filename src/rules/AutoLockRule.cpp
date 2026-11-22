#include "rules/AutoLockRule.h"
#include <cstring>
#include "config.h"

bool AutoLockRule::evaluate(JsonObjectConst reported) {
  // El modo lo aporta el registro de ajustes de Alejandro al estado completo.
  // Sin ese ajuste, se conserva el comportamiento manual de la P3.
  const char *mode = reported["modo"] | "manual";
  const bool automatic = strcmp(mode, "automatico") == 0 || strcmp(mode, "bloqueo") == 0;
  return automatic && pir_.motionStarted() && door_.close();
}

void AutoLockRule::clearDesired(JsonObject desired) const {
  desired[KEY_DOOR] = nullptr;
  desired["origen"] = nullptr;
}
