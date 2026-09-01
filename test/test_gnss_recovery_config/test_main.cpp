#include <Arduino.h>
#include <unity.h>
#include <ArduinoJson.h>
#include "GnssRecoveryConfig.h"

void test_recovery_config_exports_current_policy() {
  BridgeConfig config{};
  JsonDocument json;

  GnssRecoveryConfig::addToJson(config, json);

  TEST_ASSERT_EQUAL_UINT32(config.gnssRecoverySilenceMs,
                           json["gnss_recovery_silence_ms"].as<uint32_t>());
  TEST_ASSERT_EQUAL_UINT32(config.gnssRecoveryCooldownMs,
                           json["gnss_recovery_cooldown_ms"].as<uint32_t>());
}

void test_recovery_config_clamps_unsafe_api_values() {
  BridgeConfig config{};
  JsonDocument json;
  json["gnss_recovery_silence_ms"] = 1u;
  json["gnss_recovery_cooldown_ms"] = 0u;

  TEST_ASSERT_TRUE(GnssRecoveryConfig::applyFromJson(json, config));
  TEST_ASSERT_EQUAL_UINT32(GnssRecoveryPolicy::MIN_SILENCE_MS,
                           config.gnssRecoverySilenceMs);
  TEST_ASSERT_EQUAL_UINT32(GnssRecoveryPolicy::MIN_COOLDOWN_MS,
                           config.gnssRecoveryCooldownMs);
}

void test_recovery_config_preserves_omitted_values() {
  BridgeConfig config{};
  const uint32_t silence = config.gnssRecoverySilenceMs;
  const uint32_t cooldown = config.gnssRecoveryCooldownMs;
  JsonDocument json;

  TEST_ASSERT_TRUE(GnssRecoveryConfig::applyFromJson(json, config));
  TEST_ASSERT_EQUAL_UINT32(silence, config.gnssRecoverySilenceMs);
  TEST_ASSERT_EQUAL_UINT32(cooldown, config.gnssRecoveryCooldownMs);
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_recovery_config_exports_current_policy);
  RUN_TEST(test_recovery_config_clamps_unsafe_api_values);
  RUN_TEST(test_recovery_config_preserves_omitted_values);
  UNITY_END();
}

void loop() {}
