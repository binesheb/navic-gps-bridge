#pragma once

#include <Arduino.h>
#include "FreshFrameGate.h"
#include "TransportHealth.h"

// Couples one downstream stream's write health to the fresh-frame gate.
// A failed write blocks the stream until explicit recovery; after recovery,
// only a subsequently accepted GNSS frame may reopen output.
class TransportOutputLifecycle {
 public:
  void reset() { health_.reset(); gate_.reset(); }
  bool outputAllowed() const { return health_.ready() && gate_.outputAllowed(); }
  bool failed() const { return !health_.ready(); }
  bool waitingForFreshFrame() const { return gate_.waitingForFreshFrame(); }
  void markFreshFrame() { if (health_.ready()) gate_.markFreshFrame(); }
  bool recordWriteSuccess() {
    if (!outputAllowed()) return false;
    return health_.recordWriteSuccess();
  }
  void recordWriteFailure(unsigned long nowMs) {
    if (!health_.ready()) return;
    health_.recordWriteFailure(nowMs);
    gate_.onTransportFailure();
  }
  void recordRecovery(unsigned long nowMs) {
    if (health_.ready()) return;
    health_.recordRecovery(nowMs);
    gate_.onTransportRecovery();
  }
  const TransportHealth &health() const { return health_; }
 private:
  TransportHealth health_;
  FreshFrameGate gate_;
};
