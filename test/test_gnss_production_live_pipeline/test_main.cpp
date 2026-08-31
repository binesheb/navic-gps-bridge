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

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_production_sentence_flows_to_live_health);
  RUN_TEST(test_rejected_production_sentence_is_visible_without_refreshing_liveness);
  UNITY_END();
}

void loop() {}
