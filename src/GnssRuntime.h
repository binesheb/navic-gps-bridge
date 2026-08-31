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
      : healthMonitor(staleAfterMs) {}

  bool ingest(const String &sentence, unsigned long nowMs);
  const GnssData &data() const { return engine.data(); }
  // Keep compatibility conversion behind the same production GNSS boundary so
  // callers do not need to reach into a second parser instance.
  String gpsCompatible(const String &sentence) const {
    return engine.gpsCompatible(sentence);
  }
  GnssHealth health(unsigned long nowMs) const {
    return healthMonitor.snapshot(engine.data(), nowMs);
  }
  void reset() { healthMonitor.reset(); }

 private:
  NMEAEngine engine;
  GnssHealthMonitor healthMonitor;
};
