#include <Arduino.h>
#include <unity.h>
#include "GnssRuntimeDiagnostics.h"

void test_runtime_health_is_attached_to_live_counters() {
  GnssRuntime runtime(5000);
  TEST_ASSERT_TRUE(runtime.ingest("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A", 100));

  LiveDiagnosticsCounters counters;
  GnssHealth snapshot;
  attachGnssRuntimeDiagnostics(counters, runtime, 250, snapshot);

  TEST_ASSERT_NOT_NULL(counters.gnssHealth);
  TEST_ASSERT_TRUE(counters.gnssHealth->receiverOnline);
  TEST_ASSERT_FALSE(counters.gnssHealth->stale);
  TEST_ASSERT_EQUAL_UINT32(1, counters.gnssHealth->acceptedSentences);
  TEST_ASSERT_EQUAL_UINT32(150, counters.gnssHealth->ageMs);
}

void test_runtime_health_snapshot_stales_without_new_data() {
  GnssRuntime runtime(5000);
  TEST_ASSERT_TRUE(runtime.ingest("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A", 100));

  LiveDiagnosticsCounters counters;
  GnssHealth snapshot;
  attachGnssRuntimeDiagnostics(counters, runtime, 5101, snapshot);

  TEST_ASSERT_FALSE(counters.gnssHealth->receiverOnline);
  TEST_ASSERT_TRUE(counters.gnssHealth->stale);
  TEST_ASSERT_EQUAL_UINT32(5001, counters.gnssHealth->ageMs);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_runtime_health_is_attached_to_live_counters);
  RUN_TEST(test_runtime_health_snapshot_stales_without_new_data);
  UNITY_END();
}

void loop() {}
