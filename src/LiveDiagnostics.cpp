#include "LiveDiagnostics.h"

namespace {
const char *overallStatus(const LiveDiagnosticsCounters &counters,
                          bool hasData, bool dataFresh, bool fix) {
  if (counters.gnssRecovery && counters.gnssRecovery->recovering) {
    return "RECOVERING";
  }
  if (!hasData) {
    return "NO_DATA";
  }
  if (counters.gnssHealth && counters.gnssHealth->stale) {
    return "STALE";
  }
  if (!dataFresh) {
    return "STALE";
  }
  if (!fix) {
    return "NO_FIX";
  }
  return "HEALTHY";
}
}

void buildLiveDiagnostics(const GnssData &data, const EventEngine &events,
                          const LiveDiagnosticsCounters &counters,
                          unsigned long nowMs, JsonDocument &document) {
  const bool hasData = counters.lastDataMs != 0;
  const bool dataFresh = hasData && nowMs - counters.lastDataMs < 3000;

  document["fix"] = data.fix;
  document["latitude"] = data.latitude;
  document["longitude"] = data.longitude;
  document["altitude"] = data.altitude;
  document["speed_kmh"] = data.speedKmh;
  document["satellites"] = data.satellites;
  document["hdop"] = data.hdop;
  document["last_nmea"] = data.lastSentence;
  document["packets"] = counters.packets;
  document["invalid_packets"] = counters.invalidPackets;
  document["data_available"] = hasData;
  document["data_fresh"] = dataFresh;
  document["data_age_ms"] = hasData ? nowMs - counters.lastDataMs : 0;
  document["status"] = overallStatus(counters, hasData, dataFresh, data.fix);
  document["wifi_mode"] = counters.wifiMode;
  document["uptime_ms"] = nowMs;
  document["geofence_inside"] = counters.geofenceInside;
  document["geofence_events"] = counters.geofenceEvents;
  document["geofence_last_event_ms"] = counters.geofenceLastEventMs;
  document["geofence_last_event_age_ms"] = counters.geofenceLastEventMs == 0
      ? 0
      : nowMs - counters.geofenceLastEventMs;

  if (counters.gnssHealth) {
    JsonObject health = document["gnss_health"].to<JsonObject>();
    health["receiver_online"] = counters.gnssHealth->receiverOnline;
    health["stale"] = counters.gnssHealth->stale;
    health["fix"] = counters.gnssHealth->fix;
    health["age_ms"] = counters.gnssHealth->ageMs;
    health["accepted_sentences"] = counters.gnssHealth->acceptedSentences;
    health["rejected_sentences"] = counters.gnssHealth->rejectedSentences;
  }

  if (counters.gnssRecovery) {
    JsonObject recovery = document["gnss_recovery"].to<JsonObject>();
    recovery["monitoring"] = counters.gnssRecovery->monitoring;
    recovery["recovering"] = counters.gnssRecovery->recovering;
    recovery["attempts"] = counters.gnssRecovery->recoveryCount;
    recovery["last_recovery_ms"] = counters.gnssRecovery->lastRecoveryMs;
    recovery["last_data_ms"] = counters.gnssRecovery->lastDataMs;
    recovery["silence_ms"] = counters.gnssRecovery->silenceMs;
    recovery["cooldown_ms"] = counters.gnssRecovery->cooldownMs;
  }

  appendEventDiagnostics(events, document);
}
