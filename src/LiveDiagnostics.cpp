#include "LiveDiagnostics.h"

void buildLiveDiagnostics(const GnssData &data, const EventEngine &events,
                          const LiveDiagnosticsCounters &counters,
                          unsigned long nowMs, JsonDocument &document) {
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
  document["data_fresh"] = nowMs - counters.lastDataMs < 3000;
  document["wifi_mode"] = counters.wifiMode;
  document["geofence_inside"] = counters.geofenceInside;
  document["geofence_events"] = counters.geofenceEvents;

  if (counters.gnssHealth) {
    JsonObject health = document["gnss_health"].to<JsonObject>();
    health["receiver_online"] = counters.gnssHealth->receiverOnline;
    health["stale"] = counters.gnssHealth->stale;
    health["fix"] = counters.gnssHealth->fix;
    health["age_ms"] = counters.gnssHealth->ageMs;
    health["accepted_sentences"] = counters.gnssHealth->acceptedSentences;
    health["rejected_sentences"] = counters.gnssHealth->rejectedSentences;
  }

  appendEventDiagnostics(events, document);
}
