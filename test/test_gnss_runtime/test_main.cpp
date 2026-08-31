#include <Arduino.h>
#include <unity.h>
#include "GnssRuntime.h"

static String withChecksum(const String &body) {
  uint8_t sum = 0;
  for (size_t i = 0; i < body.length(); ++i) sum ^= body[i];
  char suffix[4];
  snprintf(suffix, sizeof(suffix), "%02X", sum);
  return "$" + body + "*" + suffix;
}

void test_valid_sentence_updates_data_and_health() {
  GnssRuntime runtime(5000);
  String s = withChecksum("GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,,,A");
  TEST_ASSERT_TRUE(runtime.ingest(s, 100));
  TEST_ASSERT_TRUE(runtime.data().fix);
  TEST_ASSERT_TRUE(runtime.health(100).receiverOnline);
  TEST_ASSERT_EQUAL(1, runtime.health(100).acceptedSentences);
}

void test_rejected_sentence_does_not_refresh_liveness() {
  GnssRuntime runtime(5000);
  String good = withChecksum("GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,,,A");
  TEST_ASSERT_TRUE(runtime.ingest(good, 100));
  TEST_ASSERT_FALSE(runtime.ingest("$GNRMC,BAD*00", 4000));
  GnssHealth h = runtime.health(6000);
  TEST_ASSERT_TRUE(h.stale);
  TEST_ASSERT_EQUAL(1, h.acceptedSentences);
  TEST_ASSERT_EQUAL(1, h.rejectedSentences);
}

void test_runtime_produces_gps_compatible_output() {
  GnssRuntime runtime;
  String input = withChecksum("GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,,,A");
  String output = runtime.gpsCompatible(input);
  TEST_ASSERT_TRUE(output.startsWith("$GPRMC,"));
  TEST_ASSERT_NOT_EQUAL(input, output);
  TEST_ASSERT_EQUAL_STRING("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,,,A*7C", output.c_str());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_valid_sentence_updates_data_and_health);
  RUN_TEST(test_rejected_sentence_does_not_refresh_liveness);
  RUN_TEST(test_runtime_produces_gps_compatible_output);
  UNITY_END();
}
void loop() {}
