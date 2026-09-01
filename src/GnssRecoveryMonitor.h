#pragma once
#include <Arduino.h>

struct GnssRecoveryStatus {
  bool recovering = false;
  uint32_t recoveryCount = 0;
  uint32_t lastRecoveryMs = 0;
};

class GnssRecoveryMonitor {
 public:
  explicit GnssRecoveryMonitor(uint32_t silenceMs = 10000, uint32_t cooldownMs = 30000)
      : silenceMs_(silenceMs), cooldownMs_(cooldownMs) {}

  bool shouldRecover(uint32_t nowMs, uint32_t lastDataMs) {
    if (lastDataMs == 0 || (uint32_t)(nowMs - lastDataMs) <= silenceMs_) return false;
    if (status_.lastRecoveryMs != 0 && (uint32_t)(nowMs - status_.lastRecoveryMs) < cooldownMs_) return false;
    status_.recovering = true;
    status_.lastRecoveryMs = nowMs;
    ++status_.recoveryCount;
    return true;
  }

  void markData(uint32_t) { status_.recovering = false; }
  const GnssRecoveryStatus& status() const { return status_; }

 private:
  uint32_t silenceMs_;
  uint32_t cooldownMs_;
  GnssRecoveryStatus status_;
};
