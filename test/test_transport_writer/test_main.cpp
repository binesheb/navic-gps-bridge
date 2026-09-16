#include <Arduino.h>
#include <unity.h>
#include "TransportWriter.h"

class ChunkedPrint : public Print {
public:
  size_t maxChunk = 0;
  bool stall = false;
  String captured;

  size_t write(uint8_t byte) override {
    captured += static_cast<char>(byte);
    return 1;
  }

  size_t write(const uint8_t* buffer, size_t size) override {
    if (stall) return 0;
    const size_t count = maxChunk && size > maxChunk ? maxChunk : size;
    for (size_t i = 0; i < count; ++i) captured += static_cast<char>(buffer[i]);
    return count;
  }
};

static void test_partial_writes_are_retried_until_complete() {
  ChunkedPrint transport;
  transport.maxChunk = 3;

  TEST_ASSERT_TRUE(writeComplete(transport, "$GPRMC,FRAME*00\r\n", 50));
  TEST_ASSERT_EQUAL_STRING("$GPRMC,FRAME*00\r\n", transport.captured.c_str());
}

static void test_stalled_transport_times_out() {
  ChunkedPrint transport;
  transport.stall = true;

  TEST_ASSERT_FALSE(writeComplete(transport, "$GPRMC,FRAME*00\r\n", 1));
  TEST_ASSERT_EQUAL_UINT32(0, transport.captured.length());
}

static void test_empty_frame_is_a_successful_noop() {
  ChunkedPrint transport;

  TEST_ASSERT_TRUE(writeComplete(transport, "", 1));
  TEST_ASSERT_EQUAL_UINT32(0, transport.captured.length());
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_partial_writes_are_retried_until_complete);
  RUN_TEST(test_stalled_transport_times_out);
  RUN_TEST(test_empty_frame_is_a_successful_noop);
  UNITY_END();
}

void loop() {}
