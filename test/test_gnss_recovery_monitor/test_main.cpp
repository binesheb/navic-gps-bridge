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

void test_cooldown_handles_millis_rollover() {
  GnssRecoveryMonitor monitor(1000, 5000);
  const uint32_t beforeWrap = 0xFFFFFF00UL;
  TEST_ASSERT_TRUE(monitor.shouldRecover(beforeWrap, beforeWrap - 1001));

  // After millis() wraps, only 512 ms has elapsed, so cooldown must still hold.
  TEST_ASSERT_FALSE(monitor.shouldRecover(256, 0));

  // 5 seconds after the original recovery, the cooldown may expire normally.
  const uint32_t afterCooldown = beforeWrap + 5000;
  TEST_ASSERT_TRUE(monitor.shouldRecover(afterCooldown, afterCooldown - 1001));
  TEST_ASSERT_EQUAL_UINT32(2, monitor.status().recoveryCount);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_silence_triggers_once_per_cooldown);
  RUN_TEST(test_fresh_data_clears_recovering_state);
  RUN_TEST(test_cooldown_handles_millis_rollover);
  UNITY_END();
}

void loop() {}
