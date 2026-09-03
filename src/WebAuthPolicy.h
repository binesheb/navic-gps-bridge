#pragma once
#include <Arduino.h>

namespace WebAuthPolicy {
constexpr size_t MIN_PASSWORD_LENGTH = 12;

inline bool validUsername(const String &username) {
  return username.length() >= 1 && username.length() <= 32;
}

inline bool validPassword(const String &password) {
  return password.length() >= MIN_PASSWORD_LENGTH && password.length() <= 64;
}

inline bool validEnabledCredentials(const String &username, const String &password) {
  return validUsername(username) && validPassword(password);
}
}
