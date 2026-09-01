#pragma once
#include <stdint.h>

struct GnssRecoveryPolicy {
  static constexpr uint32_t MIN_SILENCE_MS = 1000;
  static constexpr uint32_t MAX_SILENCE_MS = 300000;
  static constexpr uint32_t MIN_COOLDOWN_MS = 1000;
  static constexpr uint32_t MAX_COOLDOWN_MS = 3600000;

  static bool valid(uint32_t silenceMs, uint32_t cooldownMs) {
    return silenceMs >= MIN_SILENCE_MS && silenceMs <= MAX_SILENCE_MS &&
           cooldownMs >= MIN_COOLDOWN_MS && cooldownMs <= MAX_COOLDOWN_MS;
  }

  static uint32_t clampSilence(uint32_t value) {
    if (value < MIN_SILENCE_MS) return MIN_SILENCE_MS;
    if (value > MAX_SILENCE_MS) return MAX_SILENCE_MS;
    return value;
  }

  static uint32_t clampCooldown(uint32_t value) {
    if (value < MIN_COOLDOWN_MS) return MIN_COOLDOWN_MS;
    if (value > MAX_COOLDOWN_MS) return MAX_COOLDOWN_MS;
    return value;
  }
};
