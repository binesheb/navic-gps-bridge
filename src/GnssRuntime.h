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
  // Safe consumer view: fix validity reflects the current age of the data.
  GnssData data() const { return currentData(millis()); }
  // Explicit escape hatch for diagnostics that intentionally need raw state.
  const GnssData &rawData() const { return engine.rawData(); }
  // Snapshot suitable for consumers that need fix validity to reflect age.
  GnssData currentData(unsigned long nowMs) const {
    return engine.currentData(nowMs, staleAfterMs_);
  }
  // Deterministic fix lifecycle for external consumers.
  String fixState(unsigned long nowMs) const {
    return engine.fixState(nowMs, staleAfterMs_);
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
