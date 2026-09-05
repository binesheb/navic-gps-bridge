#include "EventApi.h"

void buildEventSummaryJson(const EventEngine &engine, JsonDocument &doc) {
  const unsigned long count = engine.count();
  doc["count"] = count;
  doc["history_size"] = engine.history().size();
  doc["capacity"] = EventLog::MAX_EVENTS;
  doc["has_latest"] = count > 0;

  JsonObject latest = doc["latest"].to<JsonObject>();
  if (count == 0) {
    latest.clear();
    return;
  }

  const AlertEvent &last = engine.last();
  latest["type"] = alertTypeName(last.type);
  latest["timestamp"] = last.timestamp;
  latest["message"] = last.message;
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
