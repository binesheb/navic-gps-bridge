#include <Arduino.h>
#include <unity.h>
#include "NMEAEngine.h"
#include "GnssHealth.h"

static const String VALID_RMC =
    "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A";

static void test_valid_sentence_marks_receiver_online() {
  NMEAEngine nmea;
  GnssHealthMonitor health(5000);
  TEST_ASSERT_TRUE(health.process(nmea, VALID_RMC, 1000));

  GnssHealth snapshot = health.snapshot(nmea.data(), 2000);
  TEST_ASSERT_TRUE(snapshot.receiverOnline);
  TEST_ASSERT_FALSE(snapshot.stale);
  TEST_ASSERT_TRUE(snapshot.fix);
  TEST_ASSERT_EQUAL_UINT32(1, snapshot.acceptedSentences);
  TEST_ASSERT_EQUAL_UINT32(0, snapshot.rejectedSentences);
  TEST_ASSERT_EQUAL_UINT32(1000, snapshot.ageMs);
}

static void test_invalid_sentence_is_counted_without_refreshing_age() {
  NMEAEngine nmea;
  GnssHealthMonitor health(5000);
  TEST_ASSERT_TRUE(health.process(nmea, VALID_RMC, 1000));
  TEST_ASSERT_FALSE(health.process(nmea,
      "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*00",
      2000));

  GnssHealth snapshot = health.snapshot(nmea.data(), 3000);
  TEST_ASSERT_EQUAL_UINT32(1, snapshot.acceptedSentences);
  TEST_ASSERT_EQUAL_UINT32(1, snapshot.rejectedSentences);
  TEST_ASSERT_EQUAL_UINT32(2000, snapshot.ageMs);
}

static void test_receiver_becomes_stale_after_timeout() {
  NMEAEngine nmea;
  GnssHealthMonitor health(5000);
  TEST_ASSERT_TRUE(health.process(nmea, VALID_RMC, 1000));

  GnssHealth fresh = health.snapshot(nmea.data(), 6000);
  TEST_ASSERT_FALSE(fresh.stale);
  TEST_ASSERT_TRUE(fresh.receiverOnline);

  GnssHealth stale = health.snapshot(nmea.data(), 6001);
  TEST_ASSERT_TRUE(stale.stale);
  TEST_ASSERT_FALSE(stale.receiverOnline);
}

static void test_reset_clears_runtime_counters() {
  NMEAEngine nmea;
  GnssHealthMonitor health;
  TEST_ASSERT_TRUE(health.process(nmea, VALID_RMC, 100));
  health.reset();

  GnssHealth snapshot = health.snapshot(nmea.data(), 200);
  TEST_ASSERT_FALSE(snapshot.receiverOnline);
  TEST_ASSERT_TRUE(snapshot.stale);
  TEST_ASSERT_EQUAL_UINT32(0, snapshot.acceptedSentences);
  TEST_ASSERT_EQUAL_UINT32(0, snapshot.rejectedSentences);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_valid_sentence_marks_receiver_online);
  RUN_TEST(test_invalid_sentence_is_counted_without_refreshing_age);
  RUN_TEST(test_receiver_becomes_stale_after_timeout);
  RUN_TEST(test_reset_clears_runtime_counters);
  UNITY_END();
}

void loop() {}
