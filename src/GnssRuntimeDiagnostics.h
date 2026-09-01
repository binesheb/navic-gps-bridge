#pragma once

#include "GnssRuntime.h"
#include "GnssRecoveryController.h"
#include "LiveDiagnostics.h"

// Populate the GNSS health portion of the live diagnostics counters from the
// single production GNSS ingestion object. The snapshot is owned by the caller
// so its lifetime safely spans buildLiveDiagnostics().
inline void attachGnssRuntimeDiagnostics(LiveDiagnosticsCounters &counters,
                                         const GnssRuntime &runtime,
                                         unsigned long nowMs,
                                         GnssHealth &snapshot) {
  snapshot = runtime.health(nowMs);
  counters.gnssHealth = &snapshot;
}

// Attach recovery state without copying it so live diagnostics always reflects
// the controller that is driving production UART recovery.
inline void attachGnssRecoveryDiagnostics(
    LiveDiagnosticsCounters &counters,
    const GnssRecoveryController &controller) {
  counters.gnssRecovery = &controller.status();
}
