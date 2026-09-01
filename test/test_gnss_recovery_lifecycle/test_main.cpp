#include <Arduino.h>
#include <unity.h>
#include "GnssRecoveryLifecycle.h"

void test_lifecycle_recovers_after_startup_silence() {
  BridgeConfig config{};
  config.gnssBaud = 9600;
  config.gnssRecoverySilenceMs = 1000;
  config.gnssRecoveryCooldownMs = 500;

  GnssRecoveryLifecycle lifecycle(config);
  lifecycle.begin(100);

  const GnssRecoveryStatus &started = lifecycle.status();
  TEST_ASSERT_TRUE(started.monitoring);
  TEST_ASSERT_EQUAL_UINT32(100, started.lastDataMs);
  TEST_ASSERT_EQUAL_UINT32(0, started.recoveryCount);
}

void test_lifecycle_accepted_data_refreshes_watchdog() {
  BridgeConfig config{};
  config.gnssRecoverySilenceMs = 1000;
  config.gnssRecoveryCooldownMs = 500;

  GnssRecoveryLifecycle lifecycle(config);
  lifecycle.begin(0);
  lifecycle.observeAccepted(false, 500);
  TEST_ASSERT_EQUAL_UINT32(0, lifecycle.status().lastDataMs);

  lifecycle.observeAccepted(true, 500);
  TEST_ASSERT_EQUAL_UINT32(500, lifecycle.status().lastDataMs);
  TEST_ASSERT_FALSE(lifecycle.status().recovering);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_lifecycle_recovers_after_startup_silence);
  RUN_TEST(test_lifecycle_accepted_data_refreshes_watchdog);
  UNITY_END();
}

void loop() {}
