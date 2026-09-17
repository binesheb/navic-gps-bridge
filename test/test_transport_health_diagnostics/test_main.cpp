#include <Arduino.h>
#include <ArduinoJson.h>
#include <unity.h>
#include "TransportHealth.h"
#include "TransportHealthDiagnostics.h"

static void test_json_reports_ready_state_and_zero_ages() {
  TransportHealth health;
  health.reset();
  JsonDocument doc;
  JsonObject target = doc.to<JsonObject>();
  appendTransportHealth(target, health, 500);
  TEST_ASSERT_EQUAL_STRING("READY", target["state"] | "");
  TEST_ASSERT_TRUE(target["ready"] | false);
  TEST_ASSERT_EQUAL_UINT32(0, target["writes"] | 99);
  TEST_ASSERT_EQUAL_UINT32(0, target["failures"] | 99);
  TEST_ASSERT_EQUAL_UINT32(0, target["recoveries"] | 99);
  TEST_ASSERT_EQUAL_UINT32(0, target["failure_age_ms"] | 99);
  TEST_ASSERT_EQUAL_UINT32(0, target["recovery_age_ms"] | 99);
}

static void test_json_reports_failure_and_elapsed_age() {
  TransportHealth health;
  health.reset();
  health.recordWriteSuccess();
  health.recordWriteFailure(100);
  JsonDocument doc;
  JsonObject target = doc.to<JsonObject>();
  appendTransportHealth(target, health, 450);
  TEST_ASSERT_EQUAL_STRING("FAILED", target["state"] | "");
  TEST_ASSERT_FALSE(target["ready"] | true);
  TEST_ASSERT_EQUAL_UINT32(1, target["writes"] | 99);
  TEST_ASSERT_EQUAL_UINT32(1, target["failures"] | 99);
  TEST_ASSERT_EQUAL_UINT32(350, target["failure_age_ms"] | 0);
}

static void test_json_reports_recovery_and_elapsed_age() {
  TransportHealth health;
  health.reset();
  health.recordWriteFailure(100);
  health.recordRecovery(300);
  JsonDocument doc;
  JsonObject target = doc.to<JsonObject>();
  appendTransportHealth(target, health, 500);
  TEST_ASSERT_EQUAL_STRING("READY", target["state"] | "");
  TEST_ASSERT_TRUE(target["ready"] | false);
  TEST_ASSERT_EQUAL_UINT32(200, target["failure_age_ms"] | 0);
  TEST_ASSERT_EQUAL_UINT32(200, target["recovery_age_ms"] | 0);
  TEST_ASSERT_EQUAL_UINT32(1, target["recoveries"] | 0);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_json_reports_ready_state_and_zero_ages);
  RUN_TEST(test_json_reports_failure_and_elapsed_age);
  RUN_TEST(test_json_reports_recovery_and_elapsed_age);
  UNITY_END();
}
void loop() {}
