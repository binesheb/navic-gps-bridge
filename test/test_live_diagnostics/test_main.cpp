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

  TEST_ASSERT_TRUE(document["data_available"]);
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

  TEST_ASSERT_TRUE(document["data_available"]);
  TEST_ASSERT_EQUAL_UINT32(0x200, document["data_age_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT32(0x180, document["geofence_last_event_age_ms"].as<unsigned long>());
}

void test_live_diagnostics_distinguishes_no_data_from_stale_data() {
  LiveDiagnosticsCounters counters;
  JsonDocument document;

  counters.lastDataMs = 0;
  buildLiveDiagnostics(sampleData(), EventEngine(), counters, 5000, document);
  TEST_ASSERT_FALSE(document["data_available"]);
  TEST_ASSERT_FALSE(document["data_fresh"]);
  TEST_ASSERT_EQUAL_UINT32(0, document["data_age_ms"].as<unsigned long>());

  counters.lastDataMs = 1000;
  document.clear();
  buildLiveDiagnostics(sampleData(), EventEngine(), counters, 5000, document);
  TEST_ASSERT_TRUE(document["data_available"]);
  TEST_ASSERT_FALSE(document["data_fresh"]);
  TEST_ASSERT_EQUAL_UINT32(4000, document["data_age_ms"].as<unsigned long>());
}

void test_live_diagnostics_combines_runtime_and_event_state() {
  GnssData data;
  data.fix = true;
  data.latitude = 9.9312;
  data.longitude = 76.2673;
  data.altitude = 12.5;
  data.speedKmh = 42.0;
  data.satellites = 8;
  data.hdop = 0.9;
  data.lastSentence = "$GPGGA";

  EventEngine events;
  LiveDiagnosticsCounters counters;
  counters.packets = 17;
  counters.invalidPackets = 2;
  counters.lastDataMs = 9000;
  counters.wifiMode = "AP+STA";
  counters.geofenceInside = true;
  counters.geofenceEvents = 3;
  counters.geofenceLastEventMs = 8750;

  GnssHealth health;
  health.receiverOnline = true;
  health.stale = false;
  health.fix = true;
  health.ageMs = 250;
  health.acceptedSentences = 17;
  health.rejectedSentences = 2;
  counters.gnssHealth = &health;

  GnssRecoveryStatus recovery;
  recovery.recovering = true;
  recovery.recoveryCount = 2;
  recovery.lastRecoveryMs = 7500;
  recovery.lastDataMs = 9000;
  recovery.silenceMs = 10000;
  counters.gnssRecovery = &recovery;

  JsonDocument doc;
  buildLiveDiagnostics(data, events, counters, 10000, doc);

  TEST_ASSERT_TRUE(doc["fix"].as<bool>());
  TEST_ASSERT_DOUBLE_WITHIN(0.000001, 9.9312, doc["latitude"].as<double>());
  TEST_ASSERT_DOUBLE_WITHIN(0.000001, 76.2673, doc["longitude"].as<double>());
  TEST_ASSERT_EQUAL_UINT(8, doc["satellites"].as<unsigned int>());
  TEST_ASSERT_EQUAL_UINT(17, doc["packets"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(2, doc["invalid_packets"].as<unsigned long>());
  TEST_ASSERT_TRUE(doc["data_fresh"].as<bool>());
  TEST_ASSERT_EQUAL_UINT(10000, doc["uptime_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_STRING("AP+STA", doc["wifi_mode"].as<const char*>());
  TEST_ASSERT_TRUE(doc["geofence_inside"].as<bool>());
  TEST_ASSERT_EQUAL_UINT(3, doc["geofence_events"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(8750, doc["geofence_last_event_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(1250, doc["geofence_last_event_age_ms"].as<unsigned long>());
  TEST_ASSERT_TRUE(doc["events"].is<JsonObject>());
  TEST_ASSERT_TRUE(doc["gnss_health"]["receiver_online"].as<bool>());
  TEST_ASSERT_FALSE(doc["gnss_health"]["stale"].as<bool>());
  TEST_ASSERT_EQUAL_UINT(250, doc["gnss_health"]["age_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(17, doc["gnss_health"]["accepted_sentences"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(2, doc["gnss_health"]["rejected_sentences"].as<unsigned long>());
  TEST_ASSERT_TRUE(doc["gnss_recovery"]["recovering"].as<bool>());
  TEST_ASSERT_EQUAL_UINT(2, doc["gnss_recovery"]["attempts"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(7500, doc["gnss_recovery"]["last_recovery_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(9000, doc["gnss_recovery"]["last_data_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(10000, doc["gnss_recovery"]["silence_ms"].as<unsigned long>());
}

void test_live_diagnostics_marks_stale_data() {
  GnssData data;
  EventEngine events;
  LiveDiagnosticsCounters counters;
  counters.lastDataMs = 1000;

  JsonDocument doc;
  buildLiveDiagnostics(data, events, counters, 5000, doc);

  TEST_ASSERT_FALSE(doc["data_fresh"].as<bool>());
  TEST_ASSERT_EQUAL_UINT(0, doc["geofence_last_event_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(0, doc["geofence_last_event_age_ms"].as<unsigned long>());
  TEST_ASSERT_FALSE(doc["gnss_health"].is<JsonObject>());
  TEST_ASSERT_FALSE(doc["gnss_recovery"].is<JsonObject>());
}

void test_live_diagnostics_does_not_report_fresh_before_first_packet() {
  GnssData data;
  EventEngine events;
  LiveDiagnosticsCounters counters;
  counters.lastDataMs = 0;

  JsonDocument doc;
  buildLiveDiagnostics(data, events, counters, 1000, doc);

  TEST_ASSERT_FALSE(doc["data_fresh"].as<bool>());
}

void test_live_diagnostics_handles_millis_rollover_for_event_age() {
  GnssData data;
  EventEngine events;
  LiveDiagnosticsCounters counters;
  counters.geofenceLastEventMs = 0xFFFFFF00UL;

  JsonDocument doc;
  buildLiveDiagnostics(data, events, counters, 0x00000100UL, doc);

  TEST_ASSERT_EQUAL_UINT(512, doc["geofence_last_event_age_ms"].as<unsigned long>());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_live_diagnostics_reports_data_age_and_freshness);
  RUN_TEST(test_live_diagnostics_age_is_rollover_safe);
  RUN_TEST(test_live_diagnostics_distinguishes_no_data_from_stale_data);
  RUN_TEST(test_live_diagnostics_combines_runtime_and_event_state);
  RUN_TEST(test_live_diagnostics_marks_stale_data);
  RUN_TEST(test_live_diagnostics_does_not_report_fresh_before_first_packet);
  RUN_TEST(test_live_diagnostics_handles_millis_rollover_for_event_age);
  UNITY_END();
}

void loop() {}
