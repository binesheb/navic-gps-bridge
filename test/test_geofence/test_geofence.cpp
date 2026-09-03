#include <Arduino.h>
#include <unity.h>
#include "GeofenceEngine.h"

static Geofence makeFence(double latitude, double longitude, double radiusMeters = 100.0) {
  Geofence fence;
  fence.enabled = true;
  fence.latitude = latitude;
  fence.longitude = longitude;
  fence.radiusMeters = radiusMeters;
  return fence;
}

void test_disabled_geofence_does_not_change_state() {
  GeofenceEngine engine;
  Geofence fence = makeFence(10.0, 76.0);
  fence.enabled = false;
  engine.set(fence);

  TEST_ASSERT_FALSE(engine.update(10.0, 76.0, true, 1000));
  TEST_ASSERT_FALSE(engine.inside());
  TEST_ASSERT_EQUAL_UINT(0, engine.eventCount());
  TEST_ASSERT_EQUAL_UINT(0, engine.lastEventAt());
}

void test_initial_fix_establishes_state_without_event() {
  GeofenceEngine engine;
  engine.set(makeFence(10.0, 76.0, 100.0));

  TEST_ASSERT_FALSE(engine.update(10.0, 76.0, true, 1000));
  TEST_ASSERT_TRUE(engine.inside());
  TEST_ASSERT_EQUAL_UINT(0, engine.eventCount());
  TEST_ASSERT_EQUAL_UINT(0, engine.lastEventAt());
}

void test_crossing_boundary_generates_enter_and_exit_events() {
  GeofenceEngine engine;
  engine.set(makeFence(10.0, 76.0, 100.0));

  TEST_ASSERT_FALSE(engine.update(10.0, 76.0, true, 1000));
  TEST_ASSERT_TRUE(engine.inside());

  TEST_ASSERT_TRUE(engine.update(10.002, 76.0, true, 2000));
  TEST_ASSERT_FALSE(engine.inside());
  TEST_ASSERT_EQUAL_UINT(1, engine.eventCount());
  TEST_ASSERT_EQUAL_STRING("Geofence exited", engine.lastEvent().c_str());
  TEST_ASSERT_EQUAL_UINT(2000, engine.lastEventAt());

  TEST_ASSERT_TRUE(engine.update(10.0, 76.0, true, 3000));
  TEST_ASSERT_TRUE(engine.inside());
  TEST_ASSERT_EQUAL_UINT(2, engine.eventCount());
  TEST_ASSERT_EQUAL_STRING("Geofence entered", engine.lastEvent().c_str());
  TEST_ASSERT_EQUAL_UINT(3000, engine.lastEventAt());
}

void test_invalid_fix_is_ignored_without_losing_last_state() {
  GeofenceEngine engine;
  engine.set(makeFence(10.0, 76.0, 100.0));

  TEST_ASSERT_FALSE(engine.update(10.0, 76.0, true, 1000));
  TEST_ASSERT_TRUE(engine.inside());

  TEST_ASSERT_FALSE(engine.update(20.0, 86.0, false, 2000));
  TEST_ASSERT_TRUE(engine.inside());
  TEST_ASSERT_EQUAL_UINT(0, engine.eventCount());
  TEST_ASSERT_EQUAL_UINT(0, engine.lastEventAt());
}

void test_longitude_wrap_distance_across_dateline() {
  GeofenceEngine engine;
  engine.set(makeFence(0.0, 179.999, 250.0));

  TEST_ASSERT_FALSE(engine.update(0.0, -179.999, true, 1000));
  TEST_ASSERT_TRUE(engine.inside());
  TEST_ASSERT_EQUAL_UINT(0, engine.eventCount());
}

void test_polar_boundary_remains_finite() {
  GeofenceEngine engine;
  engine.set(makeFence(89.999, 0.0, 250.0));

  // Near the pole, the longitude term is highly sensitive to rounding.
  // A valid fix must still produce a deterministic inside/outside state.
  TEST_ASSERT_FALSE(engine.update(89.999, 180.0, true, 1000));
  TEST_ASSERT_TRUE(engine.inside());
  TEST_ASSERT_EQUAL_UINT(0, engine.eventCount());
}

void setup() {
  delay(1000);
  UNITY_BEGIN();
  RUN_TEST(test_disabled_geofence_does_not_change_state);
  RUN_TEST(test_initial_fix_establishes_state_without_event);
  RUN_TEST(test_crossing_boundary_generates_enter_and_exit_events);
  RUN_TEST(test_invalid_fix_is_ignored_without_losing_last_state);
  RUN_TEST(test_longitude_wrap_distance_across_dateline);
  RUN_TEST(test_polar_boundary_remains_finite);
  UNITY_END();
}

void loop() {}
