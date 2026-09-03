#include <Arduino.h>
#include <unity.h>
#include "WebAuthPolicy.h"

void test_username_validation() {
  TEST_ASSERT_FALSE(WebAuthPolicy::validUsername(String("")));
  TEST_ASSERT_TRUE(WebAuthPolicy::validUsername(String("admin")));
  TEST_ASSERT_FALSE(WebAuthPolicy::validUsername(String("123456789012345678901234567890123")));
}

void test_password_validation() {
  TEST_ASSERT_FALSE(WebAuthPolicy::validPassword(String("short")));
  TEST_ASSERT_TRUE(WebAuthPolicy::validPassword(String("NavIC-strong-pass")));
  TEST_ASSERT_FALSE(WebAuthPolicy::validPassword(String("12345678901234567890123456789012345678901234567890123456789012345")));
}

void test_enabled_credentials_require_both() {
  TEST_ASSERT_FALSE(WebAuthPolicy::validEnabledCredentials(String("admin"), String("short")));
  TEST_ASSERT_TRUE(WebAuthPolicy::validEnabledCredentials(String("admin"), String("NavIC-strong-pass")));
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_username_validation);
  RUN_TEST(test_password_validation);
  RUN_TEST(test_enabled_credentials_require_both);
  UNITY_END();
}

void loop() {}
