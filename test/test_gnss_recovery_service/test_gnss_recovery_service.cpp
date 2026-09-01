#include <unity.h>
#include <Arduino.h>
#include "Settings.h"
#include "GnssRecoveryService.h"

void test_service_uses_persisted_recovery_policy() {
  BridgeConfig config;
  config.gnssRecoverySilenceMs = 100;
  config.gnssRecoveryCooldownMs = 1000;

  GnssRecoveryService service(config);
  service.begin(0);

  GnssRecoveryAction action;
  TEST_ASSERT_FALSE(service.controller().poll(99, action));
  TEST_ASSERT_TRUE(service.controller().poll(100, action));
  TEST_ASSERT_TRUE(action.restartUart);
}

void test_service_marks_fresh_data() {
  BridgeConfig config;
  config.gnssRecoverySilenceMs = 100;
  config.gnssRecoveryCooldownMs = 1000;

  GnssRecoveryService service(config);
  service.begin(0);
  service.markData(50);

  GnssRecoveryAction action;
  TEST_ASSERT_FALSE(service.controller().poll(149, action));
  TEST_ASSERT_TRUE(service.controller().poll(150, action));
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_service_uses_persisted_recovery_policy);
  RUN_TEST(test_service_marks_fresh_data);
  UNITY_END();
}

void loop() {}
