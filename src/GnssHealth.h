#pragma once

#include <Arduino.h>
#include "NMEAEngine.h"

struct GnssHealth {
  bool receiverOnline = false;
  bool stale = true;
  bool fix = false;
  unsigned long lastSentenceAt = 0;
  unsigned long ageMs = 0;
  unsigned long acceptedSentences = 0;
  unsigned long rejectedSentences = 0;
};

class GnssHealthMonitor {
 public:
  explicit GnssHealthMonitor(unsigned long staleAfterMs = 5000)
      : staleAfter(staleAfterMs) {}

  bool process(NMEAEngine &engine, const String &sentence, unsigned long now);
  GnssHealth snapshot(const GnssData &data, unsigned long now) const;
  void reset();

 private:
  unsigned long staleAfter;
  unsigned long lastSentenceAt = 0;
  unsigned long accepted = 0;
  unsigned long rejected = 0;
  bool hasSentence = false;
};
