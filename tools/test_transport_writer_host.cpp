#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>

#include "TransportWriter.h"

static uint32_t fakeNowMs = 0;

uint32_t millis() { return fakeNowMs; }
void yield() { ++fakeNowMs; }

class FakePrint : public Print {
 public:
  size_t maxChunk = 0;
  uint32_t writeCostMs = 0;
  bool stalled = false;
  std::string captured;

  size_t write(uint8_t byte) override {
    captured.push_back(static_cast<char>(byte));
    fakeNowMs += writeCostMs;
    return 1;
  }

  size_t write(const uint8_t* data, size_t size) override {
    if (stalled) return 0;
    const size_t count = maxChunk && size > maxChunk ? maxChunk : size;
    captured.append(reinterpret_cast<const char*>(data), count);
    fakeNowMs += writeCostMs;
    return count;
  }
};

int main() {
  {
    fakeNowMs = 0;
    FakePrint transport;
    transport.maxChunk = 2;
    transport.writeCostMs = 1;
    assert(writeComplete(transport, "ABCDEF", 10));
    assert(transport.captured == "ABCDEF");
  }
  {
    fakeNowMs = 0;
    FakePrint transport;
    transport.maxChunk = 1;
    transport.writeCostMs = 1;
    assert(!writeComplete(transport, "ABC", 2));
    assert(transport.captured == "AB");
  }
  {
    fakeNowMs = 0;
    FakePrint transport;
    transport.maxChunk = 1;
    assert(!writeComplete(transport, "ABC", 0));
    assert(transport.captured.empty());
  }
  {
    fakeNowMs = 0;
    FakePrint transport;
    transport.stalled = true;
    assert(!writeComplete(transport, "ABC", 2));
    assert(transport.captured.empty());
  }
  {
    fakeNowMs = 0;
    FakePrint transport;
    assert(writeComplete(transport, "", 0));
    assert(transport.captured.empty());
  }
  std::cout << "TransportWriter host regression tests passed\n";
}
