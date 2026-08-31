#include "GnssHealth.h"

bool GnssHealthMonitor::process(NMEAEngine &engine, const String &sentence,
                                unsigned long now) {
  if (!engine.process(sentence)) {
    rejected++;
    return false;
  }

  accepted++;
  lastSentenceAt = now;
  hasSentence = true;
  return true;
}

GnssHealth GnssHealthMonitor::snapshot(const GnssData &data,
                                       unsigned long now) const {
  GnssHealth health;
  health.receiverOnline = hasSentence;
  health.lastSentenceAt = lastSentenceAt;
  health.acceptedSentences = accepted;
  health.rejectedSentences = rejected;
  health.fix = data.fix;

  if (!hasSentence) {
    health.ageMs = 0;
    health.stale = true;
    return health;
  }

  health.ageMs = now - lastSentenceAt;
  health.stale = health.ageMs > staleAfter;
  health.receiverOnline = !health.stale;
  return health;
}

void GnssHealthMonitor::reset() {
  lastSentenceAt = 0;
  accepted = 0;
  rejected = 0;
  hasSentence = false;
}
