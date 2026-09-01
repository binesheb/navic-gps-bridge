#pragma once
#include <Arduino.h>
#include "GnssRecoveryPolicy.h"

struct GnssRecoveryStatus {
  bool recovering = false;
  bool monitoring = false;
  uint32_t recoveryCount = 0;
  uint32_t lastRecoveryMs = 0;
  uint32_t lastDataMs = 0;
  uint32_t silenceMs = 10000;
  uint32_t cooldownMs = 30000;
};

class GnssRecoveryMonitor {
 public:
  explicit GnssRecoveryMonitor(uint32_t silenceMs = 10000, uint32_t cooldownMs = 30000)
      : silenceMs_(GnssRecoveryPolicy::clampSilence(silenceMs)),
        cooldownMs_(GnssRecoveryPolicy::clampCooldown(cooldownMs)) {
    syncPolicyStatus();
  }

  // Update thresholds without resetting monitoring, recovery history, or the
  // last-data timestamp. This allows /api/config changes to take effect safely
  // while the bridge is running.
  void reconfigure(uint32_t silenceMs, uint32_t cooldownMs) {
    silenceMs_ = GnssRecoveryPolicy::clampSilence(silenceMs);
    cooldownMs_ = GnssRecoveryPolicy::clampCooldown(cooldownMs);
    syncPolicyStatus();
  }

  void begin(uint32_t nowMs) {
    status_.monitoring = true;
    status_.lastDataMs = nowMs;
    status_.recovering = false;
  }

  bool shouldRecover(uint32_t nowMs, uint32_t lastDataMs) {
    status_.monitoring = true;
    status_.lastDataMs = lastDataMs;
    // Unsigned subtraction intentionally handles the ESP32 millis() rollover.
    if ((uint32_t)(nowMs - lastDataMs) <= silenceMs_) return false;
    if (hasRecovered_ && (uint32_t)(nowMs - status_.lastRecoveryMs) < cooldownMs_) return false;
    status_.recovering = true;
    status_.lastRecoveryMs = nowMs;
    hasRecovered_ = true;
    ++status_.recoveryCount;
    return true;
  }

  void markData(uint32_t nowMs) {
    status_.monitoring = true;
    status_.lastDataMs = nowMs;
    status_.recovering = false;
  }

  const GnssRecoveryStatus& status() const { return status_; }

 private:
  void syncPolicyStatus() {
    status_.silenceMs = silenceMs_;
    status_.cooldownMs = cooldownMs_;
  }

  uint32_t silenceMs_;
  uint32_t cooldownMs_;
  bool hasRecovered_ = false;
  GnssRecoveryStatus status_;
};
