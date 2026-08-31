#include <unity.h>
#include "GnssProductionPath.h"

static const String RMC = "$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*7C";

void test_valid_sentence_updates_runtime_and_forwards_compatible_output() {
  GnssProductionPath path;
  String out;
  TEST_ASSERT_TRUE(path.process(RMC, 1000, true, out));
  TEST_ASSERT_TRUE(out.startsWith("$GPRMC,"));
  TEST_ASSERT_TRUE(path.runtime().health(1000).receiverOnline);
  TEST_ASSERT_EQUAL(1, path.runtime().health(1000).acceptedSentences);
}

void test_rejected_sentence_does_not_produce_forward_output() {
  GnssProductionPath path;
  String out = "unchanged";
  TEST_ASSERT_FALSE(path.process("$GNRMC,broken*00", 1000, false, out));
  TEST_ASSERT_EQUAL_STRING("unchanged", out.c_str());
  TEST_ASSERT_EQUAL(1, path.runtime().health(1000).rejectedSentences);
}

void test_raw_forwarding_preserves_sentence_when_compatibility_disabled() {
  GnssProductionPath path;
  String out;
  TEST_ASSERT_TRUE(path.process(RMC, 1000, false, out));
  TEST_ASSERT_EQUAL_STRING(RMC.c_str(), out.c_str());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_valid_sentence_updates_runtime_and_forwards_compatible_output);
  RUN_TEST(test_rejected_sentence_does_not_produce_forward_output);
  RUN_TEST(test_raw_forwarding_preserves_sentence_when_compatibility_disabled);
  UNITY_END();
}

void loop() {}
