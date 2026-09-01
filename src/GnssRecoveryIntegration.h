#pragma once

#include <Arduino.h>
#include <HardwareSerial.h>
#include "GnssRecoveryService.h"
#include "Settings.h"

// Narrow integration helpers for the production firmware loop.
// They make it explicit that only accepted GNSS input refreshes the
// recovery watchdog and keep UART parameters sourced from BridgeConfig.
namespace GnssRecoveryIntegration {

inline void observeProcessResult(GnssRecoveryService &service,
                                 bool accepted,
                                 uint32_t nowMs) {
  if (accepted) service.markData(nowMs);
}

inline bool poll(GnssRecoveryService &service,
                 uint32_t nowMs,
                 HardwareSerial &serial,
                 const BridgeConfig &config,
                 int rxPin = 16,
                 int txPin = 17) {
  return service.poll(nowMs, serial, config.gnssBaud, rxPin, txPin);
}

}  // namespace GnssRecoveryIntegration
