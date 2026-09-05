#include <Arduino.h>
#include <unity.h>
#include <ArduinoJson.h>
#include "EventApi.h"

namespace {
EventEngine makeEngine() {
  return EventEngine();
}
}

void test_empty_history_payload_has_stable_summary() {
  EventEngine engine = makeEngine();
  JsonDocument doc;
  buildEventsJson(engine, doc);

  TEST_ASSERT_EQUAL_UINT(0, doc["count"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(0, doc["history_size"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(EventLog::MAX_EVENTS, doc["capacity"].as<unsigned long>());
  TEST_ASSERT_FALSE(doc["has_latest"].as<bool>());
  TEST_ASSERT_TRUE(doc["latest"].is<JsonObject>());
  TEST_ASSERT_EQUAL_UINT(0, doc["latest"].as<JsonObject>().size());
  TEST_ASSERT_TRUE(doc["events"].is<JsonArray>());
  TEST_ASSERT_EQUAL_UINT(0, doc["events"].as<JsonArray>().size());
}

void test_summary_matches_full_payload_metadata() {
  EventEngine engine = makeEngine();
  JsonDocument summary;
  JsonDocument full;
  buildEventSummaryJson(engine, summary);
  buildEventsJson(engine, full);

  TEST_ASSERT_EQUAL(summary["count"].as<unsigned long>(), full["count"].as<unsigned long>());
  TEST_ASSERT_EQUAL(summary["history_size"].as<unsigned long>(), full["history_size"].as<unsigned long>());
  TEST_ASSERT_EQUAL(summary["capacity"].as<unsigned long>(), full["capacity"].as<unsigned long>());
  TEST_ASSERT_EQUAL(summary["has_latest"].as<bool>(), full["has_latest"].as<bool>());
}

void test_latest_event_is_populated_after_event() {
  EventEngine engine = makeEngine();
  GnssData data{};
  data.fix = true;
  data.satellites = 8;
  data.hdop = 1.2f;

  engine.update(data, true, 1234);

  JsonDocument doc;
  buildEventSummaryJson(engine, doc);
  TEST_ASSERT_TRUE(doc["has_latest"].as<bool>());
  TEST_ASSERT_EQUAL_UINT(1, doc["count"].as<unsigned long>());
  TEST_ASSERT_EQUAL_STRING("fix_acquired", doc["latest"]["type"] | "");
  TEST_ASSERT_EQUAL_UINT(1234, doc["latest"]["timestamp"].as<unsigned long>());
}

void setup() {
  delay(1000);
  UNITY_BEGIN();
  RUN_TEST(test_empty_history_payload_has_stable_summary);
  RUN_TEST(test_summary_matches_full_payload_metadata);
  RUN_TEST(test_latest_event_is_populated_after_event);
  UNITY_END();
}

void loop() {}
