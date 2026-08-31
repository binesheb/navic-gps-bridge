#include <Arduino.h>
#include <unity.h>
#include <ArduinoJson.h>
#include "LiveDiagnostics.h"

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

  GnssHealth health;
  health.receiverOnline = true;
  health.stale = false;
  health.fix = true;
  health.ageMs = 250;
  health.acceptedSentences = 17;
  health.rejectedSentences = 2;
  counters.gnssHealth = &health;

  JsonDocument doc;
  buildLiveDiagnostics(data, events, counters, 10000, doc);

  TEST_ASSERT_TRUE(doc["fix"].as<bool>());
  TEST_ASSERT_DOUBLE_WITHIN(0.000001, 9.9312, doc["latitude"].as<double>());
  TEST_ASSERT_DOUBLE_WITHIN(0.000001, 76.2673, doc["longitude"].as<double>());
  TEST_ASSERT_EQUAL_UINT(8, doc["satellites"].as<unsigned int>());
  TEST_ASSERT_EQUAL_UINT(17, doc["packets"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(2, doc["invalid_packets"].as<unsigned long>());
  TEST_ASSERT_TRUE(doc["data_fresh"].as<bool>());
  TEST_ASSERT_EQUAL_STRING("AP+STA", doc["wifi_mode"].as<const char*>());
  TEST_ASSERT_TRUE(doc["geofence_inside"].as<bool>());
  TEST_ASSERT_EQUAL_UINT(3, doc["geofence_events"].as<unsigned long>());
  TEST_ASSERT_TRUE(doc["events"].is<JsonObject>());
  TEST_ASSERT_TRUE(doc["gnss_health"]["receiver_online"].as<bool>());
  TEST_ASSERT_FALSE(doc["gnss_health"]["stale"].as<bool>());
  TEST_ASSERT_EQUAL_UINT(250, doc["gnss_health"]["age_ms"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(17, doc["gnss_health"]["accepted_sentences"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(2, doc["gnss_health"]["rejected_sentences"].as<unsigned long>());
}

void test_live_diagnostics_marks_stale_data() {
  GnssData data;
  EventEngine events;
  LiveDiagnosticsCounters counters;
  counters.lastDataMs = 1000;

  JsonDocument doc;
  buildLiveDiagnostics(data, events, counters, 5000, doc);

  TEST_ASSERT_FALSE(doc["data_fresh"].as<bool>());
  TEST_ASSERT_FALSE(doc["gnss_health"].is<JsonObject>());
}

void setup() {
  delay(1000);
  UNITY_BEGIN();
  RUN_TEST(test_live_diagnostics_combines_runtime_and_event_state);
  RUN_TEST(test_live_diagnostics_marks_stale_data);
  UNITY_END();
}

void loop() {}
