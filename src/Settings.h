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
  String outputProfile = "generic";
  bool geofenceEnabled = false;
  double geofenceLatitude = 0.0;
  double geofenceLongitude = 0.0;
  float geofenceRadiusM = 100.0f;

  // GNSS UART recovery policy. These values are persisted so unattended
  // deployments can tune silence detection without changing firmware.
  uint32_t gnssRecoverySilenceMs = 10000;
  uint32_t gnssRecoveryCooldownMs = 30000;
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