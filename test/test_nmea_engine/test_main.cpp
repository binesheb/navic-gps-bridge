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

void test_fix_is_fresh_immediately_after_valid_sentence() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  TEST_ASSERT_TRUE(engine.fixFresh(millis(), 3000));
}

void test_fix_is_not_fresh_before_first_valid_fix() {
  NMEAEngine engine;
  TEST_ASSERT_FALSE(engine.fixFresh(millis(), 3000));
}

void test_fix_freshness_expires_by_supplied_age() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  uint32_t now = millis();
  TEST_ASSERT_FALSE(engine.fixFresh(now + 3001, 3000));
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_valid_checksum_is_accepted);
  RUN_TEST(test_missing_checksum_is_rejected);
  RUN_TEST(test_short_checksum_is_rejected);
  RUN_TEST(test_non_hex_checksum_is_rejected);
  RUN_TEST(test_bad_checksum_is_rejected);
  RUN_TEST(test_fix_is_fresh_immediately_after_valid_sentence);
  RUN_TEST(test_fix_is_not_fresh_before_first_valid_fix);
  RUN_TEST(test_fix_freshness_expires_by_supplied_age);
  UNITY_END();
}

void loop() {}
