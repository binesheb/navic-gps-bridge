#include "EventEngine.h"
#include "EventLog.h"

const char *alertTypeName(AlertType type) {
  switch (type) {
    case AlertType::FixLost: return "fix_lost";
    case AlertType::FixAcquired: return "fix_acquired";
    case AlertType::HighHdop: return "high_hdop";
    case AlertType::LowSatellites: return "low_satellites";
  }
  return "unknown";
}

void EventLog::add(const AlertEvent &event) {
  add(alertTypeName(event.type), event.message, event.timestamp);
}

void EventLog::add(const String &type, const String &message, unsigned long timestamp) {
  size_t index = (start_ + count_) % MAX_EVENTS;
  if (count_ == MAX_EVENTS) {
    index = start_;
    start_ = (start_ + 1) % MAX_EVENTS;
  } else {
    count_++;
  }
  entries[index] = {timestamp, type, message};
}

void EventLog::clear() {
  start_ = 0;
  count_ = 0;
}

const LoggedEvent &EventLog::at(size_t index) const {
  static LoggedEvent empty{0, "", ""};
  if (index >= count_) return empty;
  return entries[(start_ + index) % MAX_EVENTS];
}
