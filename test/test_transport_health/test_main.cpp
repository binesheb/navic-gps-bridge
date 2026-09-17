#include <Arduino.h>
#include <unity.h>
#include "TransportHealth.h"
#include "FreshFrameGate.h"

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

static void test_fresh_frame_gate_starts_open() {
  FreshFrameGate gate;
  gate.reset();
  TEST_ASSERT_TRUE(gate.outputAllowed());
  TEST_ASSERT_FALSE(gate.blocked());
  TEST_ASSERT_FALSE(gate.waitingForFreshFrame());
}

static void test_failure_blocks_output_and_recovery_requires_fresh_frame() {
  FreshFrameGate gate;
  gate.reset();
  gate.onTransportFailure();
  TEST_ASSERT_FALSE(gate.outputAllowed());
  TEST_ASSERT_TRUE(gate.blocked());

  gate.onTransportRecovery();
  TEST_ASSERT_FALSE(gate.blocked());
  TEST_ASSERT_TRUE(gate.waitingForFreshFrame());
  TEST_ASSERT_FALSE(gate.outputAllowed());

  gate.markFreshFrame();
  TEST_ASSERT_FALSE(gate.waitingForFreshFrame());
  TEST_ASSERT_TRUE(gate.outputAllowed());
}

static void test_recovery_does_not_allow_stale_frame_without_fresh_mark() {
  FreshFrameGate gate;
  gate.reset();
  gate.onTransportFailure();
  gate.onTransportRecovery();
  TEST_ASSERT_FALSE(gate.outputAllowed());
  gate.markFreshFrame();
  TEST_ASSERT_TRUE(gate.outputAllowed());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_health_starts_ready);
  RUN_TEST(test_failure_blocks_subsequent_success);
  RUN_TEST(test_recovery_reopens_stream_and_records_timestamp);
  RUN_TEST(test_fresh_frame_gate_starts_open);
  RUN_TEST(test_failure_blocks_output_and_recovery_requires_fresh_frame);
  RUN_TEST(test_recovery_does_not_allow_stale_frame_without_fresh_mark);
  UNITY_END();
}

void loop() {}
