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

const char *fixState(const LiveDiagnosticsCounters &counters,
                     bool hasData, bool dataFresh, bool fix) {
  if (!hasData) {
    return "NO_DATA";
  }
  if (counters.gnssHealth && counters.gnssHealth->stale) {
    return "FIX_STALE";
  }
  if (!dataFresh) {
    return "FIX_STALE";
  }
  return fix ? "FIX_VALID" : "NO_FIX";
}
}

void buildLiveDiagnostics(const GnssData &data, const EventEngine &events,
                          const LiveDiagnosticsCounters &counters,
                          unsigned long nowMs, JsonDocument &document) {
  const bool hasData = counters.lastDataMs != 0;
  const bool dataFresh = hasData && nowMs - counters.lastDataMs < 3000;
  const char *state = fixState(counters, hasData, dataFresh, data.fix);
  const bool navigationValid = strcmp(state, "FIX_VALID") == 0;

  document["fix"] = data.fix;
  document["fix_state"] = state;
  document["source"] = data.source;
  document["latitude"] = navigationValid ? data.latitude : 0.0;
  document["longitude"] = navigationValid ? data.longitude : 0.0;
  document["altitude"] = navigationValid ? data.altitude : 0.0;
  document["speed_kmh"] = navigationValid ? data.speedKmh : 0.0;
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

  if (counters.transportHealth) {
    JsonObject transport = document["transport_health"].to<JsonObject>();
    transport["state"] = counters.transportHealth->ready() ? "READY" : "FAILED";
    transport["ready"] = counters.transportHealth->ready();
    transport["writes"] = counters.transportHealth->writes();
    transport["failures"] = counters.transportHealth->failures();
    transport["recoveries"] = counters.transportHealth->recoveries();
    const bool hasFailure = counters.transportHealth->failures() != 0;
    const bool hasRecovery = counters.transportHealth->recoveries() != 0;
    transport["has_failure"] = hasFailure;
    transport["has_recovery"] = hasRecovery;
    transport["last_failure_ms"] = counters.transportHealth->lastFailureMs();
    transport["last_recovery_ms"] = counters.transportHealth->lastRecoveryMs();
    transport["failure_age_ms"] = hasFailure
        ? nowMs - counters.transportHealth->lastFailureMs()
        : 0;
    transport["recovery_age_ms"] = hasRecovery
        ? nowMs - counters.transportHealth->lastRecoveryMs()
        : 0;
  }

  appendEventDiagnostics(events, document);
}
