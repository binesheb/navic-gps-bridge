#include <Arduino.h>
#include <unity.h>
#include <ArduinoJson.h>
#include "LiveDiagnostics.h"

void test_no_data_has_explicit_no_data_state() {
  GnssData data;
  LiveDiagnosticsCounters counters;
  JsonDocument document;

  buildLiveDiagnostics(data, EventEngine(), counters, 1000, document);

  TEST_ASSERT_EQUAL_STRING("NO_DATA", document["fix_state"].as<const char*>());
}

void test_fresh_fix_reports_valid_state_and_source() {
  GnssData data;
  data.fix = true;
  data.valid = true;
  data.source = "NavIC";
  LiveDiagnosticsCounters counters;
  counters.lastDataMs = 1000;
  JsonDocument document;

  buildLiveDiagnostics(data, EventEngine(), counters, 1500, document);

  TEST_ASSERT_EQUAL_STRING("FIX_VALID", document["fix_state"].as<const char*>());
  TEST_ASSERT_EQUAL_STRING("NavIC", document["source"].as<const char*>());
  TEST_ASSERT_TRUE(document["fix"].as<bool>());
}

void test_expired_stream_reports_stale_state() {
  GnssData data;
  data.fix = false;
  data.valid = false;
  data.source = "GPS";
  LiveDiagnosticsCounters counters;
  counters.lastDataMs = 1000;
  JsonDocument document;

  buildLiveDiagnostics(data, EventEngine(), counters, 5000, document);

  TEST_ASSERT_EQUAL_STRING("FIX_STALE", document["fix_state"].as<const char*>());
  TEST_ASSERT_EQUAL_STRING("GPS", document["source"].as<const char*>());
  TEST_ASSERT_FALSE(document["fix"].as<bool>());
}

void test_fresh_no_fix_is_distinct_from_stale() {
  GnssData data;
  data.source = "GNSS";
  LiveDiagnosticsCounters counters;
  counters.lastDataMs = 1000;
  JsonDocument document;

  buildLiveDiagnostics(data, EventEngine(), counters, 1500, document);

  TEST_ASSERT_EQUAL_STRING("NO_FIX", document["fix_state"].as<const char*>());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_no_data_has_explicit_no_data_state);
  RUN_TEST(test_fresh_fix_reports_valid_state_and_source);
  RUN_TEST(test_expired_stream_reports_stale_state);
  RUN_TEST(test_fresh_no_fix_is_distinct_from_stale);
  UNITY_END();
}

void loop() {}
