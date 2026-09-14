#include <unity.h>
#include "NMEAEngine.h"

static const String VALID_RMC = "$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*7C";
static const String VALID_NAVIC_RMC = "$GIRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*73";
static const String INVALID_RMC = "$GNRMC,123519,V,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*4D";

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

void test_gnss_source_is_exposed_for_mixed_talker() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  TEST_ASSERT_EQUAL_STRING("GNSS", engine.data().source.c_str());
}

void test_navic_source_is_exposed_for_gi_talker() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_NAVIC_RMC));
  TEST_ASSERT_EQUAL_STRING("NavIC", engine.data().source.c_str());
}

void test_invalid_sentence_does_not_replace_source() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_NAVIC_RMC));
  TEST_ASSERT_FALSE(engine.process("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*00"));
  TEST_ASSERT_EQUAL_STRING("NavIC", engine.data().source.c_str());
}

void test_gsv_does_not_replace_active_fix_source() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_NAVIC_RMC));
  TEST_ASSERT_TRUE(engine.process("$GPGSV,1,1,01,01,40,100,30*49"));
  TEST_ASSERT_EQUAL_STRING("NavIC", engine.data().source.c_str());
}

void test_fix_is_fresh_immediately_after_valid_sentence() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  TEST_ASSERT_TRUE(engine.fixFresh(millis(), 3000));
  TEST_ASSERT_EQUAL_STRING("FIX_VALID", engine.fixState(millis(), 3000).c_str());
}

void test_fix_is_not_fresh_before_first_valid_fix() {
  NMEAEngine engine;
  TEST_ASSERT_FALSE(engine.fixFresh(millis(), 3000));
  TEST_ASSERT_EQUAL_STRING("NO_FIX", engine.fixState(millis(), 3000).c_str());
}

void test_fix_freshness_expires_by_supplied_age() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  uint32_t now = millis();
  TEST_ASSERT_FALSE(engine.fixFresh(now + 3001, 3000));
  TEST_ASSERT_EQUAL_STRING("FIX_STALE", engine.fixState(now + 3001, 3000).c_str());
}

void test_invalid_rmc_transitions_to_no_fix() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  TEST_ASSERT_TRUE(engine.process(INVALID_RMC));
  TEST_ASSERT_FALSE(engine.data().fix);
  TEST_ASSERT_FALSE(engine.data().valid);
  TEST_ASSERT_EQUAL_STRING("NO_FIX", engine.fixState(millis(), 3000).c_str());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_valid_checksum_is_accepted);
  RUN_TEST(test_missing_checksum_is_rejected);
  RUN_TEST(test_short_checksum_is_rejected);
  RUN_TEST(test_non_hex_checksum_is_rejected);
  RUN_TEST(test_bad_checksum_is_rejected);
  RUN_TEST(test_gnss_source_is_exposed_for_mixed_talker);
  RUN_TEST(test_navic_source_is_exposed_for_gi_talker);
  RUN_TEST(test_invalid_sentence_does_not_replace_source);
  RUN_TEST(test_gsv_does_not_replace_active_fix_source);
  RUN_TEST(test_fix_is_fresh_immediately_after_valid_sentence);
  RUN_TEST(test_fix_is_not_fresh_before_first_valid_fix);
  RUN_TEST(test_fix_freshness_expires_by_supplied_age);
  RUN_TEST(test_invalid_rmc_transitions_to_no_fix);
  UNITY_END();
}

void loop() {}
