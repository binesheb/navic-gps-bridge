#include <Arduino.h>
#include <unity.h>
#include <ArduinoJson.h>
#include "EventDiagnostics.h"

void test_diagnostics_has_stable_empty_shape() {
  EventEngine engine;
  JsonDocument doc;
  appendEventDiagnostics(engine, doc);

  JsonObject events = doc["events"].as<JsonObject>();
  TEST_ASSERT_TRUE(events);
  TEST_ASSERT_EQUAL_UINT(0, events["count"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(0, events["history_size"].as<unsigned long>());
  TEST_ASSERT_EQUAL_UINT(EventLog::MAX_EVENTS, events["history_capacity"].as<unsigned long>());
  TEST_ASSERT_TRUE(events["latest"].is<JsonObject>());
  TEST_ASSERT_NOT_NULL(events["latest"]["type"].as<const char*>());
  TEST_ASSERT_NOT_NULL(events["latest"]["message"].as<const char*>());
}

void setup() {
  delay(1000);
  UNITY_BEGIN();
  RUN_TEST(test_diagnostics_has_stable_empty_shape);
  UNITY_END();
}

void loop() {}
