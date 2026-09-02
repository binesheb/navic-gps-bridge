#include <Arduino.h>
#include <unity.h>
#include <ArduinoJson.h>
#include "LiveDiagnostics.h"

static GnssData sampleData() {
  GnssData data;
  data.fix = true;
  data.latitude = 10.123456;
  data.longitude = 76.543210;
  data.altitude = 12.5;
  data.speedKmh = 42.0;
  data.satellites = 9;
  data.hdop = 0.9;
  data.lastSentence = "$GNRMC,...";
  return data;
}

void test_live_diagnostics_reports_data_age_and_freshness() {
  LiveDiagnosticsCounters counters;
  counters.lastDataMs = 1000;
  counters.geofenceLastEventMs = 1200;
  counters.geofenceEvents = 2;
  counters.geofenceInside = true;
  counters.wifiMode = "AP+STA";

  JsonDocument document;
  buildLiveDiagnostics(sampleData(), EventEngine(), counters, 2500, document);

  TEST_ASSERT_TRUE(document["data_fresh"]);
  TEST_ASSERT_EQUAL_UINT32(1500, document["data_age_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT32(2500, document["uptime_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT32(1300, document["geofence_last_event_age_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT32(2, document["geofence_events"].as<unsigned long>());
  TEST_ASSERT_TRUE(document["geofence_inside"].as<bool>());
}

void test_live_diagnostics_age_is_rollover_safe() {
  LiveDiagnosticsCounters counters;
  counters.lastDataMs = 0xFFFFFF00UL;
  counters.geofenceLastEventMs = 0xFFFFFF80UL;

  JsonDocument document;
  buildLiveDiagnostics(sampleData(), EventEngine(), counters, 0x00000100UL, document);

  TEST_ASSERT_EQUAL_UINT32(0x200, document["data_age_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT32(0x180, document["geofence_last_event_age_ms"].as<unsigned long>());
}

void test_live_diagnostics_distinguishes_no_data_from_stale_data() {
  LiveDiagnosticsCounters counters;
  JsonDocument document;

  counters.lastDataMs = 0;
  buildLiveDiagnostics(sampleData(), EventEngine(), counters, 5000, document);
  TEST_ASSERT_FALSE(document["data_fresh"]);
  TEST_ASSERT_EQUAL_UINT32(0, document["data_age_ms"].as<unsigned long>());

  counters.lastDataMs = 1000;
  document.clear();
  buildLiveDiagnostics(sampleData(), EventEngine(), counters, 5000, document);
  TEST_ASSERT_FALSE(document["data_fresh"]);
  TEST_ASSERT_EQUAL_UINT32(4000, document["data_age_ms"].as<unsigned long>());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_live_diagnostics_reports_data_age_and_freshness);
  RUN_TEST(test_live_diagnostics_age_is_rollover_safe);
  RUN_TEST(test_live_diagnostics_distinguishes_no_data_from_stale_data);
  UNITY_END();
}

void loop() {}
