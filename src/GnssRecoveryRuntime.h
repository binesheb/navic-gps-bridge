#pragma once

#include <Arduino.h>
#include <HardwareSerial.h>
#include "GnssRecoveryController.h"

class GnssRecoveryRuntime {
 public:
  GnssRecoveryRuntime(uint32_t silenceMs = 10000, uint32_t cooldownMs = 30000)
      : controller_(silenceMs, cooldownMs) {}

  void begin(uint32_t nowMs) { controller_.begin(nowMs); }
  void markData(uint32_t nowMs) { controller_.markData(nowMs); }

  bool pollAndRecover(uint32_t nowMs, HardwareSerial &serial,
                      uint32_t baud, int rxPin, int txPin) {
    GnssRecoveryAction action;
    if (!controller_.poll(nowMs, action) || !action.restartUart) return false;
    serial.end();
    serial.begin(baud, SERIAL_8N1, rxPin, txPin);
    return true;
  }

  GnssRecoveryController &controller() { return controller_; }
  const GnssRecoveryController &controller() const { return controller_; }

 private:
  GnssRecoveryController controller_;
};
