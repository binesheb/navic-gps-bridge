#include <unity.h>
#include "NMEAEngine.h"

static const String VALID_RMC = "$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*7C";
static const String VALID_NAVIC_RMC = "$GIRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*73";
static const String INVALID_RMC = "$GNRMC,123519,V,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*4D";
static const String INVALID_EMPTY_RMC = "$GNRMC,123519,A,,N,01131.000,E,022.4,084.4,230394,003.1,W*6A";
static const String INVALID_HEMISPHERE_RMC = "$GNRMC,123519,A,4807.038,X,01131.000,E,022.4,084.4,230394,003.1,W*62";
static const String INVALID_RANGE_RMC = "$GNRMC,123519,A,9100.000,N,01131.000,E,022.4,084.4,230394,003.1,W*7C";
static const String VALID_ZERO_RMC = "$GNRMC,123519,A,0000.000,N,00000.000,E,000.0,000.0,230394,000.0,W*78";
static const String VALID_GGA = "$GNGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*59";
static const String INVALID_EMPTY_GGA = "$GNGGA,123519,,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47";
static const String INVALID_HEMISPHERE_GGA = "$GNGGA,123519,4807.038,N,01131.000,X,1,08,0.9,545.4,M,46.9,M,,*44";
static const String NO_FIX_GGA = "$GNGGA,123519,4807.038,N,01131.000,E,0,00,99.9,0.0,M,0.0,M,,*5B";

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

void test_navic_talker_is_converted_to_gps_for_compatibility() {
  NMEAEngine engine;
  TEST_ASSERT_EQUAL_STRING(
      "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A",
      engine.gpsCompatible(VALID_NAVIC_RMC).c_str());
}

void test_gnss_talker_is_converted_to_gps_for_compatibility() {
  NMEAEngine engine;
  TEST_ASSERT_EQUAL_STRING(
      "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*7C",
      engine.gpsCompatible(VALID_RMC).c_str());
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

void test_current_data_preserves_a_fresh_fix() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  GnssData snapshot = engine.currentData(millis(), 3000);
  TEST_ASSERT_TRUE(snapshot.fix);
  TEST_ASSERT_TRUE(snapshot.valid);
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

void test_current_data_clears_stale_fix_flags() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  uint32_t now = millis();
  GnssData snapshot = engine.currentData(now + 3001, 3000);
  TEST_ASSERT_FALSE(snapshot.fix);
  TEST_ASSERT_FALSE(snapshot.valid);
  TEST_ASSERT_EQUAL_STRING("GNSS", snapshot.source.c_str());
}

void test_invalid_rmc_transitions_to_no_fix() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  TEST_ASSERT_TRUE(engine.process(INVALID_RMC));
  TEST_ASSERT_FALSE(engine.data().fix);
  TEST_ASSERT_FALSE(engine.data().valid);
  TEST_ASSERT_EQUAL_STRING("NO_FIX", engine.fixState(millis(), 3000).c_str());
}

void test_malformed_rmc_position_is_rejected_without_refreshing_fix() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  uint32_t now = millis();
  TEST_ASSERT_FALSE(engine.process(INVALID_EMPTY_RMC));
  TEST_ASSERT_FALSE(engine.data().fix);
  TEST_ASSERT_FALSE(engine.data().valid);
  TEST_ASSERT_FALSE(engine.fixFresh(now + 3001, 3000));
}

void test_invalid_rmc_hemisphere_is_rejected() {
  NMEAEngine engine;
  TEST_ASSERT_FALSE(engine.process(INVALID_HEMISPHERE_RMC));
  TEST_ASSERT_FALSE(engine.data().fix);
  TEST_ASSERT_FALSE(engine.data().valid);
}

void test_out_of_range_rmc_coordinate_is_rejected() {
  NMEAEngine engine;
  TEST_ASSERT_FALSE(engine.process(INVALID_RANGE_RMC));
  TEST_ASSERT_FALSE(engine.data().fix);
  TEST_ASSERT_FALSE(engine.data().valid);
}

void test_zero_rmc_coordinates_are_valid() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_ZERO_RMC));
  TEST_ASSERT_TRUE(engine.data().fix);
  TEST_ASSERT_FLOAT_WITHIN(0.0001, 0.0, engine.data().latitude);
  TEST_ASSERT_FLOAT_WITHIN(0.0001, 0.0, engine.data().longitude);
}

void test_malformed_gga_position_is_rejected() {
  NMEAEngine engine;
  TEST_ASSERT_FALSE(engine.process(INVALID_EMPTY_GGA));
  TEST_ASSERT_FALSE(engine.data().fix);
  TEST_ASSERT_FALSE(engine.data().valid);
}

void test_invalid_gga_hemisphere_is_rejected() {
  NMEAEngine engine;
  TEST_ASSERT_FALSE(engine.process(INVALID_HEMISPHERE_GGA));
  TEST_ASSERT_FALSE(engine.data().fix);
  TEST_ASSERT_FALSE(engine.data().valid);
}

void test_latest_position_sentence_wins_when_rmc_precedes_gga() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  TEST_ASSERT_TRUE(engine.process(NO_FIX_GGA));
  TEST_ASSERT_FALSE(engine.data().fix);
  TEST_ASSERT_FALSE(engine.data().valid);
  TEST_ASSERT_EQUAL_STRING("NO_FIX", engine.fixState(millis(), 3000).c_str());
}

void test_latest_position_sentence_wins_when_gga_precedes_rmc() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(NO_FIX_GGA));
  TEST_ASSERT_TRUE(engine.process(VALID_RMC));
  TEST_ASSERT_TRUE(engine.data().fix);
  TEST_ASSERT_TRUE(engine.data().valid);
  TEST_ASSERT_EQUAL_STRING("FIX_VALID", engine.fixState(millis(), 3000).c_str());
}

void test_valid_gga_can_establish_fix_and_updates_altitude() {
  NMEAEngine engine;
  TEST_ASSERT_TRUE(engine.process(VALID_GGA));
  TEST_ASSERT_TRUE(engine.data().fix);
  TEST_ASSERT_TRUE(engine.data().valid);
  TEST_ASSERT_FLOAT_WITHIN(0.01, 545.4, engine.data().altitude);
  TEST_ASSERT_EQUAL_STRING("FIX_VALID", engine.fixState(millis(), 3000).c_str());
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
  RUN_TEST(test_navic_talker_is_converted_to_gps_for_compatibility);
  RUN_TEST(test_gnss_talker_is_converted_to_gps_for_compatibility);
  RUN_TEST(test_invalid_sentence_does_not_replace_source);
  RUN_TEST(test_gsv_does_not_replace_active_fix_source);
  RUN_TEST(test_fix_is_fresh_immediately_after_valid_sentence);
  RUN_TEST(test_current_data_preserves_a_fresh_fix);
  RUN_TEST(test_fix_is_not_fresh_before_first_valid_fix);
  RUN_TEST(test_fix_freshness_expires_by_supplied_age);
  RUN_TEST(test_current_data_clears_stale_fix_flags);
  RUN_TEST(test_invalid_rmc_transitions_to_no_fix);
  RUN_TEST(test_malformed_rmc_position_is_rejected_without_refreshing_fix);
  RUN_TEST(test_invalid_rmc_hemisphere_is_rejected);
  RUN_TEST(test_out_of_range_rmc_coordinate_is_rejected);
  RUN_TEST(test_zero_rmc_coordinates_are_valid);
  RUN_TEST(test_malformed_gga_position_is_rejected);
  RUN_TEST(test_invalid_gga_hemisphere_is_rejected);
  RUN_TEST(test_latest_position_sentence_wins_when_rmc_precedes_gga);
  RUN_TEST(test_latest_position_sentence_wins_when_gga_precedes_rmc);
  RUN_TEST(test_valid_gga_can_establish_fix_and_updates_altitude);
  UNITY_END();
}

void loop() {}
