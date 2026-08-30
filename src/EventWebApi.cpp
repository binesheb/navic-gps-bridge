#include "EventWebApi.h"
#include "EventApi.h"

namespace {
void sendDocument(WebServer &server, JsonDocument &document) {
  String body;
  serializeJson(document, body);
  server.send(200, "application/json", body);
}
}

void registerEventRoutes(WebServer &server, EventEngine &engine,
                         const std::function<bool()> &authorize) {
  server.on("/api/events", HTTP_GET, [&server, &engine, authorize]() {
    if (!authorize()) return;
    JsonDocument document;
    buildEventsJson(engine, document);
    sendDocument(server, document);
  });

  server.on("/api/events/clear", HTTP_POST, [&server, &engine, authorize]() {
    if (!authorize()) return;
    engine.clearHistory();
    JsonDocument document;
    document["ok"] = true;
    document["history_size"] = 0;
    document["count"] = engine.count();
    sendDocument(server, document);
  });
}
