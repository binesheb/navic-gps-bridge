#pragma once

#include <Arduino.h>
#include "GnssHealth.h"
#include "NMEAEngine.h"

// Single ingestion point for production GNSS data. Keeping parsing and health
// accounting together prevents callers from accidentally refreshing liveness
// state for rejected sentences.
class GnssRuntime {
 public:
  explicit GnssRuntime(unsigned long staleAfterMs = 5000)
      : staleAfterMs_(staleAfterMs), healthMonitor(staleAfterMs) {}

  bool ingest(const String &sentence, unsigned long nowMs);
  const GnssData &data() const { return engine.data(); }
  // Snapshot suitable for consumers that need fix validity to reflect age.
  GnssData currentData(unsigned long nowMs) const {
    return engine.currentData(nowMs, staleAfterMs_);
  }
  // Keep compatibility conversion behind the same production GNSS boundary so
  // callers do not need to reach into a second parser instance.
  String gpsCompatible(const String &sentence) const {
    return engine.gpsCompatible(sentence);
  }
  GnssHealth health(unsigned long nowMs) const {
    return healthMonitor.snapshot(currentData(nowMs), nowMs);
  }
  void reset() { healthMonitor.reset(); }

 private:
  NMEAEngine engine;
  unsigned long staleAfterMs_;
  GnssHealthMonitor healthMonitor;
};
