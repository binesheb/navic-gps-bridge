#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include "EventEngine.h"

// Appends a compact, stable event summary to an existing diagnostics payload.
// Keeping this separate from the HTTP layer lets /api/live, MQTT and CLI
// diagnostics share the same counters without duplicating EventEngine access.
void appendEventDiagnostics(const EventEngine &engine, JsonDocument &document);
