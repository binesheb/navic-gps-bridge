#pragma once
#include <Arduino.h>

struct GnssData {
  bool valid = false;
  bool fix = false;
  int fixQuality = 0;
  double latitude = 0;
  double longitude = 0;
  double altitude = 0;
  double speedKmh = 0;
  double course = 0;
  int satellites = 0;
  double hdop = 0;
  String utcTime;
  String utcDate;
  String lastSentence;
};

class NMEAEngine {
 public:
  bool process(const String &line);
  const GnssData &data() const { return state; }
  bool checksumValid(const String &line) const;
  String gpsCompatible(const String &line) const;
 private:
  GnssData state;
  double parseCoordinate(const String &value, const String &hemisphere) const;
};
