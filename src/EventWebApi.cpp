#include "EventWebApi.h"
#include "EventApi.h"

namespace {
void sendDocument(WebServer &server, JsonDocument &document) {
  String body;
  serializeJson(document, body);
  server.send(200, "application/json", body);
}

bool requireAuthorization(WebServer &server,
                          const std::function<bool()> &authorize) {
  if (authorize()) return true;

  JsonDocument document;
  document["ok"] = false;
  document["error"] = "unauthorized";
  String body;
  serializeJson(document, body);
  server.send(401, "application/json", body);
  return false;
}
}

void registerEventRoutes(WebServer &server, EventEngine &engine,
                         const std::function<bool()> &authorize) {
  server.on("/api/events", HTTP_GET, [&server, &engine, authorize]() {
    if (!requireAuthorization(server, authorize)) return;
    JsonDocument document;
    buildEventsJson(engine, document);
    sendDocument(server, document);
  });

  server.on("/api/events/clear", HTTP_POST, [&server, &engine, authorize]() {
    if (!requireAuthorization(server, authorize)) return;
    engine.clearHistory();
    JsonDocument document;
    document["ok"] = true;
    document["history_size"] = engine.history().size();
    document["count"] = engine.history().size();
    document["has_latest"] = false;
    sendDocument(server, document);
  });
}
