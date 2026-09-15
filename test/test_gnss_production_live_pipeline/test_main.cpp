#include <Arduino.h>
#include <unity.h>
#include "GnssProductionPath.h"
#include "GnssRuntimeDiagnostics.h"

static const char *VALID_RMC =
    "$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*75";
static const char *INVALID_RMC =
    "$GNRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*00";

void test_production_sentence_flows_to_live_health() {
  GnssProductionPath path(5000);
  String forward;
  TEST_ASSERT_TRUE(path.process(VALID_RMC, 100, true, forward));
  TEST_ASSERT_TRUE(forward.startsWith("$GPRMC,"));

  LiveDiagnosticsCounters counters;
  GnssHealth snapshot;
  attachGnssRuntimeDiagnostics(counters, path.runtime(), 250, snapshot);

  TEST_ASSERT_NOT_NULL(counters.gnssHealth);
  TEST_ASSERT_TRUE(counters.gnssHealth->receiverOnline);
  TEST_ASSERT_FALSE(counters.gnssHealth->stale);
  TEST_ASSERT_EQUAL_UINT32(1, counters.gnssHealth->acceptedSentences);
  TEST_ASSERT_EQUAL_UINT32(0, counters.gnssHealth->rejectedSentences);
  TEST_ASSERT_EQUAL_UINT32(150, counters.gnssHealth->ageMs);
}

void test_rejected_production_sentence_is_visible_without_refreshing_liveness() {
  GnssProductionPath path(5000);
  String forward;
  TEST_ASSERT_TRUE(path.process(VALID_RMC, 100, true, forward));
  TEST_ASSERT_FALSE(path.process(INVALID_RMC, 200, true, forward));

  LiveDiagnosticsCounters counters;
  GnssHealth snapshot;
  attachGnssRuntimeDiagnostics(counters, path.runtime(), 600, snapshot);

  TEST_ASSERT_TRUE(counters.gnssHealth->receiverOnline);
  TEST_ASSERT_EQUAL_UINT32(1, counters.gnssHealth->acceptedSentences);
  TEST_ASSERT_EQUAL_UINT32(1, counters.gnssHealth->rejectedSentences);
  TEST_ASSERT_EQUAL_UINT32(500, counters.gnssHealth->ageMs);
}

void test_rejected_rmc_clears_current_fix_without_refreshing_coordinates() {
  GnssProductionPath path(5000);
  String forward;
  TEST_ASSERT_TRUE(path.process(VALID_RMC, 100, true, forward));
  GnssData before = path.currentData(150);
  TEST_ASSERT_TRUE(before.fix);
  TEST_ASSERT_TRUE(before.valid);
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 48.1173f, before.latitude);

  TEST_ASSERT_FALSE(path.process(INVALID_RMC, 200, true, forward));
  GnssData after = path.currentData(250);

  TEST_ASSERT_FALSE(after.fix);
  TEST_ASSERT_FALSE(after.valid);
  TEST_ASSERT_FLOAT_WITHIN(0.001f, before.latitude, after.latitude);
  TEST_ASSERT_FLOAT_WITHIN(0.001f, before.longitude, after.longitude);
  TEST_ASSERT_EQUAL_STRING("GPS", after.source.c_str());
  TEST_ASSERT_EQUAL_STRING("NO_FIX", path.runtime().fixState(250).c_str());
}

void test_stale_fix_is_not_exposed_as_current_live_state() {
  GnssProductionPath path(5000);
  String forward;
  TEST_ASSERT_TRUE(path.process(VALID_RMC, 100, true, forward));

  GnssData fresh = path.currentData(400);
  TEST_ASSERT_TRUE(fresh.fix);
  TEST_ASSERT_TRUE(fresh.valid);

  GnssData stale = path.currentData(5100);
  TEST_ASSERT_FALSE(stale.fix);
  TEST_ASSERT_FALSE(stale.valid);
  TEST_ASSERT_EQUAL_STRING("GPS", stale.source.c_str());
}

void test_fix_state_contract_matches_current_data_freshness() {
  GnssProductionPath path(5000);
  String forward;
  TEST_ASSERT_TRUE(path.process(VALID_RMC, 100, true, forward));

  TEST_ASSERT_EQUAL_STRING("FIX_VALID", path.runtime().fixState(400).c_str());
  TEST_ASSERT_EQUAL_STRING("FIX_STALE", path.runtime().fixState(5100).c_str());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_production_sentence_flows_to_live_health);
  RUN_TEST(test_rejected_production_sentence_is_visible_without_refreshing_liveness);
  RUN_TEST(test_rejected_rmc_clears_current_fix_without_refreshing_coordinates);
  RUN_TEST(test_stale_fix_is_not_exposed_as_current_live_state);
  RUN_TEST(test_fix_state_contract_matches_current_data_freshness);
  UNITY_END();
}

void loop() {}
