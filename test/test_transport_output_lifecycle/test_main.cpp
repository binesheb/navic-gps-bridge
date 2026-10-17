#include <Arduino.h>
#include <unity.h>
#include "TransportOutputLifecycle.h"

static void test_startup_allows_complete_frame_writes() {
  TransportOutputLifecycle output;
  output.reset();
  TEST_ASSERT_TRUE(output.outputAllowed());
  TEST_ASSERT_TRUE(output.recordWriteSuccess());
  TEST_ASSERT_EQUAL_UINT32(1, output.health().writes());
  TEST_ASSERT_EQUAL_UINT32(0, output.health().failures());
}

static void test_failure_blocks_until_recovery_and_fresh_frame() {
  TransportOutputLifecycle output;
  output.reset();
  output.recordWriteFailure(100);
  TEST_ASSERT_TRUE(output.failed());
  TEST_ASSERT_FALSE(output.outputAllowed());
  TEST_ASSERT_FALSE(output.recordWriteSuccess());
  output.markFreshFrame();
  TEST_ASSERT_FALSE(output.outputAllowed());
  output.recordRecovery(200);
  TEST_ASSERT_FALSE(output.failed());
  TEST_ASSERT_TRUE(output.waitingForFreshFrame());
  TEST_ASSERT_FALSE(output.outputAllowed());
  TEST_ASSERT_FALSE(output.recordWriteSuccess());
  output.markFreshFrame();
  TEST_ASSERT_FALSE(output.waitingForFreshFrame());
  TEST_ASSERT_TRUE(output.outputAllowed());
  TEST_ASSERT_TRUE(output.recordWriteSuccess());
  TEST_ASSERT_EQUAL_UINT32(1, output.health().writes());
  TEST_ASSERT_EQUAL_UINT32(1, output.health().failures());
  TEST_ASSERT_EQUAL_UINT32(1, output.health().recoveries());
}

static void test_repeated_failure_and_recovery_calls_are_idempotent() {
  TransportOutputLifecycle output;
  output.reset();
  output.recordWriteFailure(0);
  output.recordWriteFailure(10);
  TEST_ASSERT_EQUAL_UINT32(1, output.health().failures());
  TEST_ASSERT_EQUAL_UINT32(0, output.health().lastFailureMs());
  output.recordRecovery(20);
  output.recordRecovery(30);
  TEST_ASSERT_EQUAL_UINT32(1, output.health().recoveries());
  TEST_ASSERT_EQUAL_UINT32(20, output.health().lastRecoveryMs());
  TEST_ASSERT_TRUE(output.waitingForFreshFrame());
}

static void test_each_failure_requires_a_new_fresh_frame() {
  TransportOutputLifecycle output;
  output.reset();
  output.recordWriteFailure(100);
  output.recordRecovery(150);
  output.markFreshFrame();
  TEST_ASSERT_TRUE(output.recordWriteSuccess());
  output.recordWriteFailure(200);
  TEST_ASSERT_FALSE(output.outputAllowed());
  output.recordRecovery(250);
  TEST_ASSERT_FALSE(output.outputAllowed());
  TEST_ASSERT_FALSE(output.recordWriteSuccess());
  output.markFreshFrame();
  TEST_ASSERT_TRUE(output.outputAllowed());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_startup_allows_complete_frame_writes);
  RUN_TEST(test_failure_blocks_until_recovery_and_fresh_frame);
  RUN_TEST(test_repeated_failure_and_recovery_calls_are_idempotent);
  RUN_TEST(test_each_failure_requires_a_new_fresh_frame);
  UNITY_END();
}
void loop() {}
