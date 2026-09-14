#include <unity.h>
#include "NMEAEngine.h"

static const String VALID_RMC = "$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*7C";

void test_valid_checksum_is_accepted() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.checksumValid(VALID_RMC));
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
}

void test_missing_checksum_is_rejected() {
  NMEAEngine engine;
  TEST_ASSERT_FALSE(engine.checksumValid("$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W"));
}

void test_short_checksum_is_rejected() {
  NMEAEngine engine;
  TEST_ASSERT_FALSE(engine.checksumValid("$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*7"));
}

void test_non_hex_checksum_is_rejected() {
  NMEAEngine engine;
  TEST_ASSERT_FALSE(engine.checksumValid("$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*ZZ"));
}

void test_bad_checksum_is_rejected() {
  NMEAEngine engine;
  TEST_ASSERT_FALSE(engine.process("$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*7D"));
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_valid_checksum_is_accepted);
  RUN_TEST(test_missing_checksum_is_rejected);
  RUN_TEST(test_short_checksum_is_rejected);
  RUN_TEST(test_non_hex_checksum_is_rejected);
  RUN_TEST(test_bad_checksum_is_rejected);
  UNITY_END();
}

void loop() {}
