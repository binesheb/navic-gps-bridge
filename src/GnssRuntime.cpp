#include "GnssRuntime.h"

bool GnssRuntime::ingest(const String &sentence, unsigned long nowMs) {
  return healthMonitor.process(engine, sentence, nowMs);
}
