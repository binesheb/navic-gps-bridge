#include <unity.h>
#include <Arduino.h>
#include "GnssRecoveryRuntime.h"

void test_runtime_reports_no_recovery_before_silence() {
  GnssRecoveryRuntime runtime(100, 1000);
  runtime.markData(10);
  GnssRecoveryAction action;
  TEST_ASSERT_FALSE(runtime.controller().poll(50, action));
}

void test_runtime_requests_recovery_after_silence() {
  GnssRecoveryRuntime runtime(100, 1000);
  runtime.markData(10);
  GnssRecoveryAction action;
  TEST_ASSERT_TRUE(runtime.controller().poll(111, action));
  TEST_ASSERT_TRUE(action.restartUart);
  TEST_ASSERT_EQUAL_UINT32(1, action.attempt);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_runtime_reports_no_recovery_before_silence);
  RUN_TEST(test_runtime_requests_recovery_after_silence);
  UNITY_END();
}

void loop() {}
