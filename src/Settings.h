#pragma once
#include <Arduino.h>
#include <Preferences.h>

struct BridgeConfig {
  uint32_t gnssBaud = 9600;
  uint32_t gpsOutBaud = 9600;
  uint16_t tcpPort = 10110;
  bool gpsCompatibility = true;
  bool apEnabled = true;
  bool staEnabled = false;
  String staSsid;
  String staPassword;
  bool webAuthEnabled = false;
  String webUsername = "admin";
  String webPassword;
};

class SettingsManager {
 public:
  bool begin();
  const BridgeConfig &get() const { return config; }
  bool save(const BridgeConfig &next);
  void reset();
 private:
  Preferences prefs;
  BridgeConfig config;
};