#include "Settings.h"
#include "GnssRecoveryPolicy.h"

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
  config.outputProfile = prefs.getString("outProfile", "generic");
  config.geofenceEnabled = prefs.getBool("geoEnabled", false);
  config.geofenceLatitude = prefs.getDouble("geoLat", 0.0);
  config.geofenceLongitude = prefs.getDouble("geoLon", 0.0);
  config.geofenceRadiusM = prefs.getFloat("geoRadius", 100.0f);
  config.gnssRecoverySilenceMs = GnssRecoveryPolicy::clampSilence(prefs.getULong("recSilence", 10000));
  config.gnssRecoveryCooldownMs = GnssRecoveryPolicy::clampCooldown(prefs.getULong("recCooldown", 30000));
  return true;
}

bool SettingsManager::save(const BridgeConfig &next) {
  BridgeConfig candidate = next;
  candidate.gnssRecoverySilenceMs = GnssRecoveryPolicy::clampSilence(candidate.gnssRecoverySilenceMs);
  candidate.gnssRecoveryCooldownMs = GnssRecoveryPolicy::clampCooldown(candidate.gnssRecoveryCooldownMs);

  // Preferences::put* returns the number of bytes written. Treat a failed
  // write as a failed save instead of reporting success to the API caller.
  bool ok = true;
  ok = prefs.putULong("gnssBaud", candidate.gnssBaud) > 0 && ok;
  ok = prefs.putULong("outBaud", candidate.gpsOutBaud) > 0 && ok;
  ok = prefs.putUShort("tcpPort", candidate.tcpPort) > 0 && ok;
  ok = prefs.putBool("gpsCompat", candidate.gpsCompatibility) > 0 && ok;
  ok = prefs.putBool("apEnabled", candidate.apEnabled) > 0 && ok;
  ok = prefs.putBool("staEnabled", candidate.staEnabled) > 0 && ok;
  ok = prefs.putString("staSsid", candidate.staSsid) > 0 && ok;
  ok = prefs.putString("staPass", candidate.staPassword) > 0 && ok;
  ok = prefs.putBool("webAuth", candidate.webAuthEnabled) > 0 && ok;
  ok = prefs.putString("webUser", candidate.webUsername) > 0 && ok;
  ok = prefs.putString("webPass", candidate.webPassword) > 0 && ok;
  ok = prefs.putString("outProfile", candidate.outputProfile) > 0 && ok;
  ok = prefs.putBool("geoEnabled", candidate.geofenceEnabled) > 0 && ok;
  ok = prefs.putDouble("geoLat", candidate.geofenceLatitude) > 0 && ok;
  ok = prefs.putDouble("geoLon", candidate.geofenceLongitude) > 0 && ok;
  ok = prefs.putFloat("geoRadius", candidate.geofenceRadiusM) > 0 && ok;
  ok = prefs.putULong("recSilence", candidate.gnssRecoverySilenceMs) > 0 && ok;
  ok = prefs.putULong("recCooldown", candidate.gnssRecoveryCooldownMs) > 0 && ok;

  if (ok) config = candidate;
  return ok;
}

void SettingsManager::reset() {
  prefs.clear();
  config = BridgeConfig();
}
