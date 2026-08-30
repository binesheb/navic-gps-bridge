#pragma once
#include <Arduino.h>
#include "EventEngine.h"

struct LoggedEvent {
  unsigned long timestamp;
  String type;
  String message;
};

class EventLog {
 public:
  static constexpr size_t MAX_EVENTS = 32;
  void add(const AlertEvent &event);
  void add(const String &type, const String &message, unsigned long timestamp);
  void clear();
  size_t size() const { return count_; }
  const LoggedEvent &at(size_t index) const;
 private:
  LoggedEvent entries[MAX_EVENTS];
  size_t start_ = 0;
  size_t count_ = 0;
};

const char *alertTypeName(AlertType type);
