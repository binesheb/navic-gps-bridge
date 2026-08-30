#include "EventApi.h"

void buildEventSummaryJson(const EventEngine &engine, JsonDocument &doc) {
  doc["count"] = engine.count();
  doc["history_size"] = engine.history().size();
  doc["capacity"] = EventLog::MAX_EVENTS;
  const AlertEvent &last = engine.last();
  doc["latest"]["type"] = alertTypeName(last.type);
  doc["latest"]["timestamp"] = last.timestamp;
  doc["latest"]["message"] = last.message;
}

void buildEventsJson(const EventEngine &engine, JsonDocument &doc) {
  buildEventSummaryJson(engine, doc);
  JsonArray items = doc["events"].to<JsonArray>();
  const EventLog &history = engine.history();
  for (size_t i = 0; i < history.size(); ++i) {
    const LoggedEvent &event = history.at(i);
    JsonObject item = items.add<JsonObject>();
    item["type"] = event.type;
    item["timestamp"] = event.timestamp;
    item["message"] = event.message;
  }
}
