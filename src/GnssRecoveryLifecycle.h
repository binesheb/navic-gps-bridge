#pragma once

#include <Arduino.h>
#include <HardwareSerial.h>
#include "GnssRecoveryIntegration.h"
#include "GnssRecoveryService.h"
#include "GnssRuntimeDiagnostics.h"
#include "Settings.h"

// Owns the complete production recovery lifecycle so main.cpp only needs to
// forward startup, accepted GNSS input, loop ticks and diagnostics attachment.
class GnssRecoveryLifecycle {
 public:
  explicit GnssRecoveryLifecycle(const BridgeConfig &config)
      : service_(config) {}

  void begin(uint32_t nowMs) {
    service_.begin(nowMs);
  }

  // Apply persisted configuration after SettingsManager has loaded it. This
  // intentionally preserves monitoring state and recovery history.
  void reconfigure(const BridgeConfig &config) {
    service_.reconfigure(config);
  }

  void observeAccepted(bool accepted, uint32_t nowMs) {
    GnssRecoveryIntegration::observeProcessResult(service_, accepted, nowMs);
  }

  bool poll(uint32_t nowMs,
            HardwareSerial &serial,
            const BridgeConfig &config,
            int rxPin = 16,
            int txPin = 17) {
    return GnssRecoveryIntegration::poll(
        service_, nowMs, serial, config, rxPin, txPin);
  }

  void attachDiagnostics(LiveDiagnosticsCounters &counters) const {
    service_.attachDiagnostics(counters);
  }

  const GnssRecoveryStatus &status() const {
    return service_.controller().status();
  }

 private:
  GnssRecoveryService service_;
};
