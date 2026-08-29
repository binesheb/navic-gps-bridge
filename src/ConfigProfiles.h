#pragma once
#include <Arduino.h>
#include "Settings.h"

enum class OutputProfile { GenericGPS, LegacyGPS, Marine, Automotive, FlightController };

class ConfigProfiles {
 public:
  static String name(OutputProfile profile);
  static bool apply(const String &name, DeviceConfig &config);
};
