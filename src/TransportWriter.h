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
    // A zero timeout intentionally rejects non-empty frames without writing.
    if ((uint32_t)(millis() - start) >= timeoutMs) return false;

    const size_t remaining = total - offset;
    const size_t written = transport.write(data + offset, remaining);
    // A broken transport implementation must not be allowed to advance past
    // the end of the frame.
    if (written > remaining) return false;

    if (written > 0) {
      offset += written;
      // Check even after the final write: a blocking write can return after
      // the total deadline, in which case the frame is not considered valid.
      if ((uint32_t)(millis() - start) >= timeoutMs) return false;
      continue;
    }

    if ((uint32_t)(millis() - start) >= timeoutMs) return false;
    yield();
  }
  return true;
}
