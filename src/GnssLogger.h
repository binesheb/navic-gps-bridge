#pragma once
#include <Arduino.h>

class GnssLogger {
 public:
  static const size_t MAX_POINTS = 128;
  struct Point {
    double lat;
    double lon;
    double altitude;
    double speedKmh;
    uint32_t timestamp;
  };

  void add(double lat, double lon, double altitude, double speedKmh, uint32_t timestamp) {
    if (lat == 0 && lon == 0) return;
    points[head] = {lat, lon, altitude, speedKmh, timestamp};
    head = (head + 1) % MAX_POINTS;
    if (count < MAX_POINTS) count++;
  }

  size_t size() const { return count; }
  const Point &at(size_t index) const {
    size_t start = (head + MAX_POINTS - count) % MAX_POINTS;
    return points[(start + index) % MAX_POINTS];
  }

  void clear() { head = 0; count = 0; }

 private:
  Point points[MAX_POINTS]{};
  size_t head = 0;
  size_t count = 0;
};
