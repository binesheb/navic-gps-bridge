#include "NMEAEngine.h"

static String fieldAt(const String &s, int index) {
  int start = 0, current = 0;
  for (int i = 0; i <= (int)s.length(); ++i) {
    if (i == s.length() || s[i] == ',') {
      if (current == index) return s.substring(start, i);
      current++; start = i + 1;
    }
  }
  return "";
}

bool NMEAEngine::checksumValid(const String &line) const {
  if (!line.startsWith("$")) return false;
  int star = line.indexOf('*');
  if (star < 0 || star + 2 >= line.length()) return true; // some receivers omit checksum
  uint8_t sum = 0;
  for (int i = 1; i < star; ++i) sum ^= (uint8_t)line[i];
  char expected[3];
  snprintf(expected, sizeof(expected), "%02X", sum);
  String actual = line.substring(star + 1, star + 3); actual.toUpperCase();
  return actual == expected;
}

double NMEAEngine::parseCoordinate(const String &value, const String &hemisphere) const {
  if (value.length() < 4) return 0;
  int degreeDigits = (hemisphere == "N" || hemisphere == "S") ? 2 : 3;
  double degrees = value.substring(0, degreeDigits).toDouble();
  double minutes = value.substring(degreeDigits).toDouble();
  double result = degrees + minutes / 60.0;
  if (hemisphere == "S" || hemisphere == "W") result = -result;
  return result;
}

bool NMEAEngine::process(const String &line) {
  if (!line.startsWith("$") || !checksumValid(line)) return false;
  state.lastSentence = line;
  int comma = line.indexOf(',');
  if (comma < 6) return false;
  String type = line.substring(3, 6);

  if (type == "RMC") {
    state.utcTime = fieldAt(line, 1);
    String status = fieldAt(line, 2);
    state.latitude = parseCoordinate(fieldAt(line, 3), fieldAt(line, 4));
    state.longitude = parseCoordinate(fieldAt(line, 5), fieldAt(line, 6));
    state.speedKmh = fieldAt(line, 7).toDouble() * 1.852;
    state.course = fieldAt(line, 8).toDouble();
    state.utcDate = fieldAt(line, 9);
    state.valid = status == "A";
    state.fix = state.valid;
    return true;
  }

  if (type == "GGA") {
    state.utcTime = fieldAt(line, 1);
    state.latitude = parseCoordinate(fieldAt(line, 2), fieldAt(line, 3));
    state.longitude = parseCoordinate(fieldAt(line, 4), fieldAt(line, 5));
    state.fixQuality = fieldAt(line, 6).toInt();
    state.satellites = fieldAt(line, 7).toInt();
    state.hdop = fieldAt(line, 8).toDouble();
    state.altitude = fieldAt(line, 9).toDouble();
    state.fix = state.fixQuality > 0;
    state.valid = state.fix;
    return true;
  }
  return false;
}

String NMEAEngine::gpsCompatible(const String &line) const {
  if (line.length() < 6 || !line.startsWith("$")) return line;
  int star = line.indexOf('*');
  String payload = star >= 0 ? line.substring(1, star) : line.substring(1);
  if (payload.startsWith("GN")) payload = "GP" + payload.substring(2);
  uint8_t sum = 0;
  for (int i = 0; i < payload.length(); ++i) sum ^= (uint8_t)payload[i];
  char checksum[4]; snprintf(checksum, sizeof(checksum), "*%02X", sum);
  return "$" + payload + String(checksum);
}
