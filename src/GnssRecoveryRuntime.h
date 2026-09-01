#pragma once

#include <Arduino.h>
#include <HardwareSerial.h>
#include "GnssRecoveryController.h"

// Small production adapter that turns a recovery action into a controlled UART
// restart. Keeping this outside main.cpp makes the restart sequence testable and
// prevents recovery policy from being duplicated across firmware entry points.
class GnssRecoveryRuntime {
 public:
  GnssRecoveryRuntime(uint32_t silenceMs = 10000, uint32_t cooldownMs = 30000)
      : controller_(silenceMs, cooldownMs) {}

  void markData(uint32_t nowMs) { controller_.markData(nowMs); }

  bool pollAndRecover(uint32_t nowMs, HardwareSerial &serial,
                      uint32_t baud, int rxPin, int txPin) {
    GnssRecoveryAction action;
    if (!controller_.poll(nowMs, action) || !action.restartUart) return false;
    serial.end();
    serial.begin(baud, SERIAL_8N1, rxPin, txPin);
    return true;
  }

  const GnssRecoveryController &controller() const { return controller_; }

 private:
  GnssRecoveryController controller_;
};
