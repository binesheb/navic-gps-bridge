#include <unity.h>
#include "GnssRecoveryMonitor.h"

void test_silence_triggers_once_per_cooldown() {
  GnssRecoveryMonitor monitor(1000, 5000);
  TEST_ASSERT_TRUE(monitor.shouldRecover(2001, 1000));
  TEST_ASSERT_FALSE(monitor.shouldRecover(3000, 1000));
  TEST_ASSERT_TRUE(monitor.shouldRecover(8002, 1000));
  TEST_ASSERT_EQUAL_UINT32(2, monitor.status().recoveryCount);
}

void test_fresh_data_clears_recovering_state() {
  GnssRecoveryMonitor monitor(1000, 5000);
  TEST_ASSERT_TRUE(monitor.shouldRecover(2001, 1000));
  monitor.markData(2002);
  TEST_ASSERT_FALSE(monitor.status().recovering);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_silence_triggers_once_per_cooldown);
  RUN_TEST(test_fresh_data_clears_recovering_state);
  UNITY_END();
}

void loop() {}
