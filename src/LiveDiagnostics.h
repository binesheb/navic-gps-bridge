#pragma once
#include <ArduinoJson.h>
#include "NMEAEngine.h"
#include "EventDiagnostics.h"
#include "GnssHealth.h"
#include "GnssRecoveryMonitor.h"

struct LiveDiagnosticsCounters {
  unsigned long packets = 0;
  unsigned long invalidPackets = 0;
  unsigned long lastDataMs = 0;
  const char *wifiMode = "OFFLINE";
  bool geofenceInside = false;
  unsigned long geofenceEvents = 0;
  unsigned long geofenceLastEventMs = 0;
  const GnssHealth *gnssHealth = nullptr;
  const GnssRecoveryStatus *gnssRecovery = nullptr;
};

void buildLiveDiagnostics(const GnssData &data, const EventEngine &events,
                          const LiveDiagnosticsCounters &counters,
                          unsigned long nowMs, JsonDocument &document);
