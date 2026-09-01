#include <Arduino.h>
#include <unity.h>
#include "GnssRecoveryPolicy.h"

void test_defaults_are_valid() {
  TEST_ASSERT_TRUE(GnssRecoveryPolicy::valid(10000, 30000));
}

void test_silence_bounds() {
  TEST_ASSERT_FALSE(GnssRecoveryPolicy::valid(999, 30000));
  TEST_ASSERT_FALSE(GnssRecoveryPolicy::valid(300001, 30000));
  TEST_ASSERT_EQUAL_UINT32(1000, GnssRecoveryPolicy::clampSilence(0));
  TEST_ASSERT_EQUAL_UINT32(300000, GnssRecoveryPolicy::clampSilence(999999));
}

void test_cooldown_bounds() {
  TEST_ASSERT_FALSE(GnssRecoveryPolicy::valid(10000, 999));
  TEST_ASSERT_FALSE(GnssRecoveryPolicy::valid(10000, 3600001));
  TEST_ASSERT_EQUAL_UINT32(1000, GnssRecoveryPolicy::clampCooldown(0));
  TEST_ASSERT_EQUAL_UINT32(3600000, GnssRecoveryPolicy::clampCooldown(9999999));
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_defaults_are_valid);
  RUN_TEST(test_silence_bounds);
  RUN_TEST(test_cooldown_bounds);
  UNITY_END();
}

void loop() {}
