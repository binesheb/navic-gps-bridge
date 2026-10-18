#pragma once
#include <cstddef>
#include <cstdint>
#include <string>

class String {
 public:
  String(const char* value = "") : value_(value ? value : "") {}
  const char* c_str() const { return value_.c_str(); }
  std::size_t length() const { return value_.size(); }
 private:
  std::string value_;
};

std::uint32_t millis();
void yield();
