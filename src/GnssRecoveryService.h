#pragma once

#include <Arduino.h>
#include <HardwareSerial.h>
#include "Settings.h"
#include "GnssRecoveryRuntime.h"
#include "GnssRuntimeDiagnostics.h"

// Small production facade for the complete GNSS recovery lifecycle.
// Keeping policy construction, UART recovery and live diagnostics together
// reduces the amount of recovery-specific state required in main.cpp.
class GnssRecoveryService {
 public:
  explicit GnssRecoveryService(const BridgeConfig &config)
      : runtime_(config.gnssRecoverySilenceMs, config.gnssRecoveryCooldownMs) {}

  void begin(uint32_t nowMs) { runtime_.begin(nowMs); }
  void markData(uint32_t nowMs) { runtime_.markData(nowMs); }

  // Apply new policy thresholds without clearing monitoring state or recovery
  // history. This is safe to call after a successful /api/config update.
  void reconfigure(const BridgeConfig &config) {
    runtime_.reconfigure(config.gnssRecoverySilenceMs,
                         config.gnssRecoveryCooldownMs);
  }

  bool poll(uint32_t nowMs, HardwareSerial &serial,
            uint32_t baud, int rxPin, int txPin) {
    return runtime_.pollAndRecover(nowMs, serial, baud, rxPin, txPin);
  }

  void attachDiagnostics(LiveDiagnosticsCounters &counters) const {
    attachGnssRecoveryDiagnostics(counters, runtime_.controller());
  }

  const GnssRecoveryController &controller() const {
    return runtime_.controller();
  }

 private:
  GnssRecoveryRuntime runtime_;
};
