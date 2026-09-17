#pragma once

#include <Arduino.h>

// Prevents stale GNSS frames from being emitted after a downstream transport
// failure. Recovery explicitly re-arms the gate; the first accepted fresh
// frame closes it again. Normal operation remains open until a failure occurs.
class FreshFrameGate {
 public:
  void reset() { blocked_ = false; waitingForFreshFrame_ = false; }

  bool outputAllowed() const { return !blocked_ && !waitingForFreshFrame_; }

  void onTransportFailure() {
    blocked_ = true;
    waitingForFreshFrame_ = false;
  }

  void onTransportRecovery() {
    blocked_ = false;
    waitingForFreshFrame_ = true;
  }

  // Call only after a GNSS sentence/frame has been validated as new.
  void markFreshFrame() { waitingForFreshFrame_ = false; }

  bool blocked() const { return blocked_; }
  bool waitingForFreshFrame() const { return waitingForFreshFrame_; }

 private:
  bool blocked_ = false;
  bool waitingForFreshFrame_ = false;
};
