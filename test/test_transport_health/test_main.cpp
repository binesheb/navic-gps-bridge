#include <Arduino.h>
#include <unity.h>
#include "TransportHealth.h"

static void test_health_starts_ready() {
  TransportHealth health;
  health.reset();
  TEST_ASSERT_TRUE(health.ready());
  TEST_ASSERT_EQUAL_UINT32(0, health.writes());
  TEST_ASSERT_EQUAL_UINT32(0, health.failures());
  TEST_ASSERT_EQUAL_UINT32(0, health.recoveries());
}

static void test_failure_blocks_subsequent_success() {
  TransportHealth health;
  health.reset();
  TEST_ASSERT_TRUE(health.recordWriteSuccess());
  health.recordWriteFailure(100);
  TEST_ASSERT_FALSE(health.ready());
  TEST_ASSERT_FALSE(health.recordWriteSuccess());
  TEST_ASSERT_EQUAL_UINT32(1, health.writes());
  TEST_ASSERT_EQUAL_UINT32(1, health.failures());
  TEST_ASSERT_EQUAL_UINT32(100, health.lastFailureMs());
}

static void test_recovery_reopens_stream_and_records_timestamp() {
  TransportHealth health;
  health.reset();
  health.recordWriteFailure(100);
  health.recordRecovery(250);
  TEST_ASSERT_TRUE(health.ready());
  TEST_ASSERT_TRUE(health.recordWriteSuccess());
  TEST_ASSERT_EQUAL_UINT32(1, health.recoveries());
  TEST_ASSERT_EQUAL_UINT32(250, health.lastRecoveryMs());
  TEST_ASSERT_EQUAL_UINT32(1, health.writes());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_health_starts_ready);
  RUN_TEST(test_failure_blocks_subsequent_success);
  RUN_TEST(test_recovery_reopens_stream_and_records_timestamp);
  UNITY_END();
}

void loop() {}
