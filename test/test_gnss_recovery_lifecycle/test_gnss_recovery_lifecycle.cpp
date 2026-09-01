#include <Arduino.h>
#include <unity.h>
#include "GnssRecoveryLifecycle.h"

namespace {
BridgeConfig makeConfig() {
  BridgeConfig config{};
  config.gnssSilenceMs = 1000;
  config.gnssRecoveryCooldownMs = 500;
  config.gnssBaud = 9600;
  return config;
}

void test_lifecycle_arms_monitoring_at_startup() {
  auto config = makeConfig();
  GnssRecoveryLifecycle lifecycle(config);
  lifecycle.begin(100);
  TEST_ASSERT_TRUE(lifecycle.status().monitoring);
  TEST_ASSERT_EQUAL_UINT32(100, lifecycle.status().lastDataMs);
}

void test_lifecycle_rejected_data_does_not_refresh_watchdog() {
  auto config = makeConfig();
  GnssRecoveryLifecycle lifecycle(config);
  lifecycle.begin(100);
  lifecycle.observeAccepted(false, 900);
  TEST_ASSERT_EQUAL_UINT32(100, lifecycle.status().lastDataMs);
}

void test_lifecycle_accepted_data_refreshes_watchdog() {
  auto config = makeConfig();
  GnssRecoveryLifecycle lifecycle(config);
  lifecycle.begin(100);
  lifecycle.observeAccepted(true, 900);
  TEST_ASSERT_EQUAL_UINT32(900, lifecycle.status().lastDataMs);
}
}  // namespace

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_lifecycle_arms_monitoring_at_startup);
  RUN_TEST(test_lifecycle_rejected_data_does_not_refresh_watchdog);
  RUN_TEST(test_lifecycle_accepted_data_refreshes_watchdog);
  UNITY_END();
}

void loop() {}
