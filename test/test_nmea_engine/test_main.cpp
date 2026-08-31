#include <Arduino.h>
#include <unity.h>
#include "NMEAEngine.h"

static void test_rmc_parses_position_speed_and_course() {
  NMEAEngine nmea;
  TEST_ASSERT_TRUE(nmea.process("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"));
  const auto &d = nmea.data();
  TEST_ASSERT_TRUE(d.valid);
  TEST_ASSERT_TRUE(d.fix);
  TEST_ASSERT_DOUBLE_WITHIN(0.00001, 48.1173, d.latitude);
  TEST_ASSERT_DOUBLE_WITHIN(0.00001, 11.5166667, d.longitude);
  TEST_ASSERT_DOUBLE_WITHIN(0.001, 41.4848, d.speedKmh);
  TEST_ASSERT_DOUBLE_WITHIN(0.001, 84.4, d.course);
}

static void test_gga_updates_fix_quality_altitude_and_hdop() {
  NMEAEngine nmea;
  TEST_ASSERT_TRUE(nmea.process("$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"));
  const auto &d = nmea.data();
  TEST_ASSERT_TRUE(d.valid);
  TEST_ASSERT_TRUE(d.fix);
  TEST_ASSERT_EQUAL_INT(1, d.fixQuality);
  TEST_ASSERT_EQUAL_INT(8, d.satellites);
  TEST_ASSERT_DOUBLE_WITHIN(0.001, 0.9, d.hdop);
  TEST_ASSERT_DOUBLE_WITHIN(0.001, 545.4, d.altitude);
}

static void test_invalid_checksum_is_rejected() {
  NMEAEngine nmea;
  TEST_ASSERT_FALSE(nmea.process("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*00"));
}

static void test_gsv_tracks_navic_satellites() {
  NMEAEngine nmea;
  TEST_ASSERT_TRUE(nmea.process("$GIGSV,1,1,01,401,45,180,42"));
  TEST_ASSERT_EQUAL_INT(1, nmea.satelliteCount());
  const SatelliteData *sat = nmea.satellites();
  TEST_ASSERT_EQUAL_STRING("NavIC", sat[0].constellation.c_str());
  TEST_ASSERT_EQUAL_INT(401, sat[0].prn);
  TEST_ASSERT_EQUAL_INT(45, sat[0].elevation);
  TEST_ASSERT_EQUAL_INT(180, sat[0].azimuth);
  TEST_ASSERT_EQUAL_INT(42, sat[0].snr);
}

static void test_gn_talker_is_converted_to_gp_with_recomputed_checksum() {
  NMEAEngine nmea;
  const String converted = nmea.gpsCompatible("$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6B");
  TEST_ASSERT_TRUE(converted.startsWith("$GPRMC,"));
  TEST_ASSERT_TRUE(nmea.checksumValid(converted));
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_rmc_parses_position_speed_and_course);
  RUN_TEST(test_gga_updates_fix_quality_altitude_and_hdop);
  RUN_TEST(test_invalid_checksum_is_rejected);
  RUN_TEST(test_gsv_tracks_navic_satellites);
  RUN_TEST(test_gn_talker_is_converted_to_gp_with_recomputed_checksum);
  UNITY_END();
}

void loop() {}
