#pragma once

#include <ArduinoJson.h>
#include "GnssRecoveryPolicy.h"
#include "Settings.h"

// Applies only GNSS recovery settings from an API payload. Keeping this
// separate from the HTTP handler prevents unrelated configuration writes from
// accidentally changing recovery behavior and guarantees persisted values are
// normalized to the policy bounds.
namespace GnssRecoveryConfig {

inline void addToJson(const BridgeConfig &config, JsonDocument &json) {
  json["gnss_recovery_silence_ms"] = config.gnssRecoverySilenceMs;
  json["gnss_recovery_cooldown_ms"] = config.gnssRecoveryCooldownMs;
}

inline bool applyFromJson(const JsonDocument &json, BridgeConfig &config) {
  uint32_t silence = config.gnssRecoverySilenceMs;
  uint32_t cooldown = config.gnssRecoveryCooldownMs;

  if (json["gnss_recovery_silence_ms"].is<uint32_t>()) {
    silence = json["gnss_recovery_silence_ms"].as<uint32_t>();
  }
  if (json["gnss_recovery_cooldown_ms"].is<uint32_t>()) {
    cooldown = json["gnss_recovery_cooldown_ms"].as<uint32_t>();
  }

  config.gnssRecoverySilenceMs = GnssRecoveryPolicy::clampSilence(silence);
  config.gnssRecoveryCooldownMs = GnssRecoveryPolicy::clampCooldown(cooldown);
  return true;
}

}  // namespace GnssRecoveryConfig
