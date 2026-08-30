#include "EventDiagnostics.h"

void appendEventDiagnostics(const EventEngine &engine, JsonDocument &document) {
  JsonObject events = document["events"].to<JsonObject>();
  events["count"] = engine.count();
  events["history_size"] = engine.history().size();
  events["history_capacity"] = EventLog::MAX_EVENTS;

  const AlertEvent &latest = engine.last();
  JsonObject last = events["latest"].to<JsonObject>();
  last["type"] = alertTypeName(latest.type);
  last["timestamp"] = latest.timestamp;
  last["message"] = latest.message;
}
