#pragma once

#include <Arduino.h>

// Tracks the health of one downstream output stream. A failed stream stays
// blocked until an explicit recovery is recorded, preventing stale or
// partially-written frames from being treated as healthy output.
class TransportHealth {
 public:
  enum State : uint8_t { READY = 0, FAILED = 1 };

  void reset() {
    state_ = READY;
    writes_ = 0;
    failures_ = 0;
    recoveries_ = 0;
    lastFailureMs_ = 0;
    lastRecoveryMs_ = 0;
  }

  bool ready() const { return state_ == READY; }
  State state() const { return state_; }

  bool recordWriteSuccess() {
    if (!ready()) return false;
    ++writes_;
    return true;
  }

  void recordWriteFailure(unsigned long nowMs) {
    state_ = FAILED;
    ++failures_;
    lastFailureMs_ = nowMs;
  }

  void recordRecovery(unsigned long nowMs) {
    state_ = READY;
    ++recoveries_;
    lastRecoveryMs_ = nowMs;
  }

  uint32_t writes() const { return writes_; }
  uint32_t failures() const { return failures_; }
  uint32_t recoveries() const { return recoveries_; }
  unsigned long lastFailureMs() const { return lastFailureMs_; }
  unsigned long lastRecoveryMs() const { return lastRecoveryMs_; }

 private:
  State state_ = READY;
  uint32_t writes_ = 0;
  uint32_t failures_ = 0;
  uint32_t recoveries_ = 0;
  unsigned long lastFailureMs_ = 0;
  unsigned long lastRecoveryMs_ = 0;
};
