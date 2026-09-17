#pragma once

#include <ArduinoJson.h>
#include "TransportHealth.h"

// Adds stable, machine-readable downstream transport health fields to a
// diagnostics JSON object. Keep this adapter separate from TransportHealth so
// the state machine remains usable without a JSON dependency.
inline void appendTransportHealth(JsonObject target,
                                  const TransportHealth &health,
                                  unsigned long nowMs) {
  const bool hasFailure = health.failures() != 0;
  const bool hasRecovery = health.recoveries() != 0;

  target["state"] = health.ready() ? "READY" : "FAILED";
  target["ready"] = health.ready();
  target["writes"] = health.writes();
  target["failures"] = health.failures();
  target["recoveries"] = health.recoveries();
  target["has_failure"] = hasFailure;
  target["has_recovery"] = hasRecovery;
  target["last_failure_ms"] = health.lastFailureMs();
  target["last_recovery_ms"] = health.lastRecoveryMs();
  target["failure_age_ms"] = hasFailure
      ? nowMs - health.lastFailureMs()
      : 0;
  target["recovery_age_ms"] = hasRecovery
      ? nowMs - health.lastRecoveryMs()
      : 0;
}
