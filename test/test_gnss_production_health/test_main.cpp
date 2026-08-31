#include <Arduino.h>
#include <unity.h>
#include "GnssProductionPath.h"

static const String kValidRmc =
    "$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*74";

void test_health_transitions_through_production_path() {
  GnssProductionPath path(5000);
  String forward;

  TEST_ASSERT_TRUE(path.process(kValidRmc, 1000, true, forward));
  GnssHealth health = path.runtime().health(1000);
  TEST_ASSERT_TRUE(health.receiverOnline);
  TEST_ASSERT_FALSE(health.stale);
  TEST_ASSERT_EQUAL_UINT32(1, health.acceptedSentences);

  health = path.runtime().health(6000);
  TEST_ASSERT_TRUE(health.receiverOnline);
  TEST_ASSERT_FALSE(health.stale);

  health = path.runtime().health(6001);
  TEST_ASSERT_FALSE(health.receiverOnline);
  TEST_ASSERT_TRUE(health.stale);
}

void test_rejected_input_does_not_refresh_production_liveness() {
  GnssProductionPath path(5000);
  String forward = "sentinel";

  TEST_ASSERT_TRUE(path.process(kValidRmc, 1000, false, forward));
  TEST_ASSERT_FALSE(path.process(
      "$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*00",
      4000, false, forward));

  GnssHealth health = path.runtime().health(6001);
  TEST_ASSERT_TRUE(health.stale);
  TEST_ASSERT_EQUAL_UINT32(1, health.acceptedSentences);
  TEST_ASSERT_EQUAL_UINT32(1, health.rejectedSentences);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_health_transitions_through_production_path);
  RUN_TEST(test_rejected_input_does_not_refresh_production_liveness);
  UNITY_END();
}

void loop() {}
