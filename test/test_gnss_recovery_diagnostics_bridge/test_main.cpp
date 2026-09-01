#include <Arduino.h>
#include <unity.h>
#include "GnssRuntimeDiagnostics.h"

void test_recovery_diagnostics_attaches_live_controller_status() {
  GnssRecoveryController controller(1000, 5000);
  GnssRecoveryAction action;
  TEST_ASSERT_TRUE(controller.poll(1101, 100, action));

  LiveDiagnosticsCounters counters;
  attachGnssRecoveryDiagnostics(counters, controller);

  TEST_ASSERT_NOT_NULL(counters.gnssRecovery);
  TEST_ASSERT_TRUE(counters.gnssRecovery->recovering);
  TEST_ASSERT_EQUAL_UINT32(1, counters.gnssRecovery->recoveryCount);
  TEST_ASSERT_EQUAL_UINT32(1101, counters.gnssRecovery->lastRecoveryMs);
  TEST_ASSERT_EQUAL_UINT32(100, counters.gnssRecovery->lastDataMs);
  TEST_ASSERT_EQUAL_UINT32(1000, counters.gnssRecovery->silenceMs);
  TEST_ASSERT_EQUAL_UINT32(5000, counters.gnssRecovery->cooldownMs);
}

void test_recovery_diagnostics_reports_monitoring_policy() {
  GnssRecoveryController controller(1500, 7000);
  controller.begin(42);

  LiveDiagnosticsCounters counters;
  attachGnssRecoveryDiagnostics(counters, controller);

  TEST_ASSERT_NOT_NULL(counters.gnssRecovery);
  TEST_ASSERT_TRUE(counters.gnssRecovery->monitoring);
  TEST_ASSERT_EQUAL_UINT32(1500, counters.gnssRecovery->silenceMs);
  TEST_ASSERT_EQUAL_UINT32(7000, counters.gnssRecovery->cooldownMs);
}

void test_recovery_diagnostics_clears_when_data_returns() {
  GnssRecoveryController controller(1000, 5000);
  GnssRecoveryAction action;
  TEST_ASSERT_TRUE(controller.poll(1101, 100, action));
  controller.markData(1200);

  LiveDiagnosticsCounters counters;
  attachGnssRecoveryDiagnostics(counters, controller);

  TEST_ASSERT_NOT_NULL(counters.gnssRecovery);
  TEST_ASSERT_FALSE(counters.gnssRecovery->recovering);
  TEST_ASSERT_EQUAL_UINT32(1200, counters.gnssRecovery->lastDataMs);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_recovery_diagnostics_attaches_live_controller_status);
  RUN_TEST(test_recovery_diagnostics_reports_monitoring_policy);
  RUN_TEST(test_recovery_diagnostics_clears_when_data_returns);
  UNITY_END();
}

void loop() {}
