#pragma once

#include <Arduino.h>
#include "GnssRuntime.h"

// Small production adapter for the UART loop. It keeps ingestion and optional
// GPS-compatible forwarding on the same boundary and returns false for rejected
// input without exposing the parser directly to the application loop.
class GnssProductionPath {
 public:
  explicit GnssProductionPath(unsigned long staleAfterMs = 5000)
      : runtime_(staleAfterMs) {}

  bool process(const String &sentence, unsigned long nowMs,
               bool gpsCompatibility, String &forward) {
    if (!runtime_.ingest(sentence, nowMs)) return false;
    forward = gpsCompatibility ? runtime_.gpsCompatible(sentence) : sentence;
    return true;
  }

  const GnssData &data() const { return runtime_.data(); }
  const GnssRuntime &runtime() const { return runtime_; }
  GnssRuntime &runtime() { return runtime_; }

 private:
  GnssRuntime runtime_;
};
