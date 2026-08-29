#pragma once
#include <Arduino.h>
#include "NMEAEngine.h"

enum class AlertType { FixLost, FixAcquired, HighHdop, LowSatellites };

struct AlertEvent {
  AlertType type;
  unsigned long timestamp;
  String message;
};

class EventEngine {
 public:
  bool update(const GnssData &data, bool fresh, unsigned long now);
  const AlertEvent &last() const { return event; }
  unsigned long count() const { return eventCount; }
 private:
  bool initialized = false;
  bool previousFix = false;
  bool hdopAlert = false;
  bool satelliteAlert = false;
  AlertEvent event{AlertType::FixLost,0,""};
  unsigned long eventCount = 0;
  void emit(AlertType type, unsigned long now, const String &message);
};
