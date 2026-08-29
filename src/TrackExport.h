#pragma once
#include <Arduino.h>
#include "GnssLogger.h"

String trackToGpx(const GnssLogger &logger, const String &name = "NavIC GPS Bridge Track");
String trackToKml(const GnssLogger &logger, const String &name = "NavIC GPS Bridge Track");
