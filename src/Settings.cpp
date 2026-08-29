#include "Settings.h"

bool SettingsManager::begin() {
  if (!prefs.begin("navicbridge", false)) return false;
  config.gnssBaud = prefs.getULong("gnssBaud", 9600);
  config.gpsOutBaud = prefs.getULong("outBaud", 9600);
  config.tcpPort = prefs.getUShort("tcpPort", 10110);
  config.gpsCompatibility = prefs.getBool("gpsCompat", true);
  config.apEnabled = prefs.getBool("apEnabled", true);
  config.staEnabled = prefs.getBool("staEnabled", false);
  config.staSsid = prefs.getString("staSsid", "");
  config.staPassword = prefs.getString("staPass", "");
  config.webAuthEnabled = prefs.getBool("webAuth", false);
  config.webUsername = prefs.getString("webUser", "admin");
  config.webPassword = prefs.getString("webPass", "");
  return true;
}

bool SettingsManager::save(const BridgeConfig &next) {
  config = next;
  prefs.putULong("gnssBaud", config.gnssBaud);
  prefs.putULong("outBaud", config.gpsOutBaud);
  prefs.putUShort("tcpPort", config.tcpPort);
  prefs.putBool("gpsCompat", config.gpsCompatibility);
  prefs.putBool("apEnabled", config.apEnabled);
  prefs.putBool("staEnabled", config.staEnabled);
  prefs.putString("staSsid", config.staSsid);
  prefs.putString("staPass", config.staPassword);
  prefs.putBool("webAuth", config.webAuthEnabled);
  prefs.putString("webUser", config.webUsername);
  prefs.putString("webPass", config.webPassword);
  return true;
}

void SettingsManager::reset() {
  prefs.clear();
  config = BridgeConfig();
}