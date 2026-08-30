#include <Arduino.h>
#include <unity.h>
#include "EventLog.h"

static void test_empty_log() {
  EventLog log;
  TEST_ASSERT_EQUAL_UINT32(0, log.size());
  log.clear();
  TEST_ASSERT_EQUAL_UINT32(0, log.size());
}

static void test_retains_events_in_order() {
  EventLog log;
  log.add("fix_acquired", "GNSS fix acquired", 100);
  log.add("high_hdop", "HDOP is high", 200);
  TEST_ASSERT_EQUAL_UINT32(2, log.size());
  TEST_ASSERT_EQUAL_STRING("fix_acquired", log.at(0).type.c_str());
  TEST_ASSERT_EQUAL_STRING("high_hdop", log.at(1).type.c_str());
  TEST_ASSERT_EQUAL_UINT32(100, log.at(0).timestamp);
}

static void test_circular_rollover_keeps_latest_events() {
  EventLog log;
  for (size_t i = 0; i < EventLog::MAX_EVENTS + 5; ++i) {
    log.add(String("event_") + String(i), "test", i);
  }
  TEST_ASSERT_EQUAL_UINT32(EventLog::MAX_EVENTS, log.size());
  TEST_ASSERT_EQUAL_STRING("event_5", log.at(0).type.c_str());
  TEST_ASSERT_EQUAL_STRING("event_36", log.at(EventLog::MAX_EVENTS - 1).type.c_str());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_empty_log);
  RUN_TEST(test_retains_events_in_order);
  RUN_TEST(test_circular_rollover_keeps_latest_events);
  UNITY_END();
}

void loop() {}
