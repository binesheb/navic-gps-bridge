#pragma once
#include <Arduino.h>
#include "GnssLogger.h"

String trackToCsv(const GnssLogger &logger);
String trackToGpx(const GnssLogger &logger, const String &name = "NavIC GPS Bridge Track");
String trackToKml(const GnssLogger &logger, const String &name = "NavIC GPS Bridge Track");
