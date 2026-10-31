#pragma once
#include <cstddef>
#include <cstdint>

class Print {
 public:
  virtual ~Print() = default;
  virtual std::size_t write(std::uint8_t byte) = 0;
  virtual std::size_t write(const std::uint8_t* buffer, std::size_t size) {
    std::size_t count = 0;
    while (count < size && write(buffer[count]) == 1) ++count;
    return count;
  }
};
