#include <Arduino.h>
#include <unity.h>
#include "WebAuthPolicy.h"

void test_username_validation();
void test_password_validation();
void test_enabled_credentials_require_both();

static void test_ota_rejects_when_web_authentication_is_disabled() {
  TEST_ASSERT_FALSE(WebAuthPolicy::validOtaAuthentication(false, String("admin"), String("valid-password-123")));
}

static void test_ota_rejects_missing_or_invalid_credentials() {
  TEST_ASSERT_FALSE(WebAuthPolicy::validOtaAuthentication(true, String("admin"), String("short")));
  TEST_ASSERT_FALSE(WebAuthPolicy::validOtaAuthentication(true, String(""), String("valid-password-123")));
}

static void test_ota_accepts_only_enabled_valid_credentials() {
  TEST_ASSERT_TRUE(WebAuthPolicy::validOtaAuthentication(true, String("admin"), String("valid-password-123")));
}

void setup() {
  UNITY_BEGIN();
  RUN_TEST(test_ota_rejects_when_web_authentication_is_disabled);
  RUN_TEST(test_ota_rejects_missing_or_invalid_credentials);
  RUN_TEST(test_ota_accepts_only_enabled_valid_credentials);
  RUN_TEST(test_username_validation);
  RUN_TEST(test_password_validation);
  RUN_TEST(test_enabled_credentials_require_both);
  UNITY_END();
}

void loop() {}
