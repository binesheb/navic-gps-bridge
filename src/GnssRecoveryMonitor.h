#pragma once
#include <Arduino.h>

struct GnssRecoveryStatus {
  bool recovering = false;
  bool monitoring = false;
  uint32_t recoveryCount = 0;
  uint32_t lastRecoveryMs = 0;
  uint32_t lastDataMs = 0;
  uint32_t silenceMs = 10000;
};

class GnssRecoveryMonitor {
 public:
  explicit GnssRecoveryMonitor(uint32_t silenceMs = 10000, uint32_t cooldownMs = 30000)
      : silenceMs_(silenceMs), cooldownMs_(cooldownMs) {
    status_.silenceMs = silenceMs_;
  }

  // Start silence monitoring from a known time. This lets a receiver that never
  // produces its first sentence be recovered instead of remaining permanently
  // in the uninitialised lastDataMs==0 state.
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
  uint32_t silenceMs_;
  uint32_t cooldownMs_;
  bool hasRecovered_ = false;
  GnssRecoveryStatus status_;
};
