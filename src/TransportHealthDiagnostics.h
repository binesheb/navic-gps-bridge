#pragma once

#include <ArduinoJson.h>
#include "TransportHealth.h"

// Adds stable, machine-readable downstream transport health fields to a
// diagnostics JSON object. Keep this adapter separate from TransportHealth so
// the state machine remains usable without a JSON dependency.
inline void appendTransportHealth(JsonObject target,
                                  const TransportHealth &health,
                                  unsigned long nowMs) {
  target["state"] = health.ready() ? "READY" : "FAILED";
  target["ready"] = health.ready();
  target["writes"] = health.writes();
  target["failures"] = health.failures();
  target["recoveries"] = health.recoveries();
  target["last_failure_ms"] = health.lastFailureMs();
  target["last_recovery_ms"] = health.lastRecoveryMs();
  target["failure_age_ms"] = health.lastFailureMs() == 0
      ? 0
      : nowMs - health.lastFailureMs();
  target["recovery_age_ms"] = health.lastRecoveryMs() == 0
      ? 0
      : nowMs - health.lastRecoveryMs();
}
