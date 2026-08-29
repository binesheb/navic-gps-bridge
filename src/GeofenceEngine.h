#pragma once
#include <Arduino.h>

struct Geofence {
  bool enabled = false;
  double latitude = 0;
  double longitude = 0;
  double radiusMeters = 100;
};

class GeofenceEngine {
 public:
  void set(const Geofence &value) { fence = value; initialized = false; }
  const Geofence &get() const { return fence; }
  bool update(double latitude, double longitude, bool fix, unsigned long now);
  bool inside() const { return insideFence; }
  unsigned long eventCount() const { return events; }
  String lastEvent() const { return last; }
 private:
  Geofence fence;
  bool initialized = false;
  bool insideFence = false;
  unsigned long events = 0;
  String last = "No geofence events";
  double distance(double lat1, double lon1, double lat2, double lon2) const;
};
