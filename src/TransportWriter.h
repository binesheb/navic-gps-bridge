#pragma once

#include <Arduino.h>
#include <Print.h>

// Write a complete frame or fail without spinning forever when a transport
// cannot currently accept more bytes. A timeout may leave a partial frame on
// the transport, so callers must treat false as a failed frame and reconnect
// or discard the affected stream as appropriate.
inline bool writeComplete(Print& transport, const String& frame, uint32_t timeoutMs = 250) {
  const uint8_t* data = reinterpret_cast<const uint8_t*>(frame.c_str());
  const size_t total = frame.length();
  size_t offset = 0;
  const uint32_t start = millis();

  while (offset < total) {
    const size_t written = transport.write(data + offset, total - offset);
    if (written > 0) {
      offset += written;
      continue;
    }
    if ((uint32_t)(millis() - start) >= timeoutMs) return false;
    yield();
  }
  return true;
}
