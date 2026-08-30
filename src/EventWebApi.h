#pragma once
#include <Arduino.h>
#include <WebServer.h>
#include <functional>
#include "EventEngine.h"

// Registers the HTTP endpoints for runtime event diagnostics.
// The supplied authorization callback must return true when the current request
// may be served; it is invoked independently for every route.
void registerEventRoutes(WebServer &server, EventEngine &engine,
                         const std::function<bool()> &authorize);
