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
  appendEventDiagnostics(events, document);
}
