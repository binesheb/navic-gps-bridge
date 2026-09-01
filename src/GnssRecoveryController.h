#pragma once
#include <Arduino.h>
#include "GnssRecoveryMonitor.h"

struct GnssRecoveryAction {
  bool restartUart = false;
  uint32_t attempt = 0;
};

class GnssRecoveryController {
 public:
  explicit GnssRecoveryController(uint32_t silenceMs = 10000, uint32_t cooldownMs = 30000)
      : monitor_(silenceMs, cooldownMs) {}

  void begin(uint32_t nowMs) { monitor_.begin(nowMs); }
  void markData(uint32_t nowMs) { monitor_.markData(nowMs); }

  void reconfigure(uint32_t silenceMs, uint32_t cooldownMs) {
    monitor_.reconfigure(silenceMs, cooldownMs);
  }

  bool poll(uint32_t nowMs, GnssRecoveryAction &action) {
    return poll(nowMs, monitor_.status().lastDataMs, action);
  }

  bool poll(uint32_t nowMs, uint32_t lastDataMs, GnssRecoveryAction &action) {
    action = {};
    if (!monitor_.shouldRecover(nowMs, lastDataMs)) return false;
    action.restartUart = true;
    action.attempt = monitor_.status().recoveryCount;
    return true;
  }

  const GnssRecoveryStatus &status() const { return monitor_.status(); }

 private:
  GnssRecoveryMonitor monitor_;
};
