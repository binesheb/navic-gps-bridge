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
  TEST_ASSERT_TRUE(full["latest"].is<JsonObject>());
}

void setup() {
  delay(1000);
  UNITY_BEGIN();
  RUN_TEST(test_empty_history_payload_has_stable_summary);
  RUN_TEST(test_summary_matches_full_payload_metadata);
  UNITY_END();
}

void loop() {}
