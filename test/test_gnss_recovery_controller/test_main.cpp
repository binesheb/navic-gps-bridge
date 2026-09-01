#include <Arduino.h>
#include <unity.h>
#include "GnssRecoveryController.h"

void test_controller_requests_restart_after_silence() {
  GnssRecoveryController controller(1000, 5000);
  GnssRecoveryAction action;
  TEST_ASSERT_FALSE(controller.poll(1000, 100, action));
  TEST_ASSERT_TRUE(controller.poll(1101, 100, action));
  TEST_ASSERT_TRUE(action.restartUart);
  TEST_ASSERT_EQUAL_UINT32(1, action.attempt);
}

void test_controller_cooldown_blocks_repeat_restart() {
  GnssRecoveryController controller(1000, 5000);
  GnssRecoveryAction action;
  TEST_ASSERT_TRUE(controller.poll(1101, 100, action));
  TEST_ASSERT_FALSE(controller.poll(2000, 100, action));
  TEST_ASSERT_TRUE(controller.poll(6200, 100, action));
  TEST_ASSERT_EQUAL_UINT32(2, action.attempt);
}

void test_fresh_data_clears_recovery_state() {
  GnssRecoveryController controller(1000, 5000);
  GnssRecoveryAction action;
  TEST_ASSERT_TRUE(controller.poll(1101, 100, action));
  TEST_ASSERT_TRUE(controller.status().recovering);
  controller.markData(1200);
  TEST_ASSERT_FALSE(controller.status().recovering);
  TEST_ASSERT_EQUAL_UINT32(1200, controller.status().lastDataMs);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_controller_requests_restart_after_silence);
  RUN_TEST(test_controller_cooldown_blocks_repeat_restart);
  RUN_TEST(test_fresh_data_clears_recovery_state);
  UNITY_END();
}

void loop() {}
