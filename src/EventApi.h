#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include "EventEngine.h"

// Serializes the bounded EventEngine history into a stable API payload.
// Kept separate from the web server so it can be reused by HTTP, MQTT, or CLI frontends.
void buildEventsJson(const EventEngine &engine, JsonDocument &doc);
void buildEventSummaryJson(const EventEngine &engine, JsonDocument &doc);
