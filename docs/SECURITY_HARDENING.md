# Deployment Security Hardening

The bridge is designed for local/embedded operation, but its Wi-Fi web UI, configuration API, TCP NMEA service, and OTA endpoint should be treated as network-exposed services whenever station mode is enabled.

## Before field deployment

- Keep the device access point disabled unless it is required for commissioning or recovery.
- If station mode is enabled, place the bridge on a trusted management/VLAN network rather than an untrusted guest network.
- Enable web authentication before exposing the web UI beyond the commissioning network.
- Use a unique administrator username and a strong password; do not reuse the Wi-Fi password.
- Treat OTA as an administrative operation and never expose the device directly to the public Internet.
- Restrict TCP port 10110 to the downstream GPS consumer where the surrounding network supports ACLs/firewall rules.
- Change credentials after transferring a device between operators or test sites.

## Current security boundaries

### Web/API

Protected routes use HTTP Basic Authentication when `webAuthEnabled` is enabled. Authentication applies to the dashboard, live diagnostics, configuration, event APIs, track exports, maintenance endpoints, and OTA endpoint.

Configuration changes are persisted in device NVS. Recovery-policy changes are applied immediately; serial/network changes require a restart to take effect.

### Wi-Fi access point

The commissioning AP uses a device-specific SSID and password derived from the ESP32 eFuse MAC address. This is useful for field identification, but it should not be treated as a substitute for application-layer authentication.

The AP password is printed to the serial console during startup. Protect access to the console during deployment.

### OTA

OTA is an administrative endpoint. Only perform firmware updates from a trusted network and use firmware artifacts produced by the project's release pipeline. Verify the release checksum before transferring a binary to the device.

## Recommended commissioning sequence

1. Power the bridge with the GNSS receiver attached but keep it on an isolated commissioning network.
2. Confirm GNSS, GPS-compatible UART output, TCP streaming, and `/api/live` diagnostics.
3. Configure station mode and required output settings.
4. Enable web authentication and set unique credentials.
5. Reconnect using the intended management network and verify authentication.
6. Disable the AP if it is not required for field recovery.
7. Verify that the downstream GPS consumer can reach only the configured TCP service.
8. Perform the hardware validation report and retain the firmware commit/tag with the test evidence.

## Known hardening gap

The current firmware exposes `webAuthEnabled` and credential fields in `BridgeConfig`, while the configuration UI/API does not yet provide a dedicated credential-management workflow. Until that workflow is implemented, enable authentication using the device's supported configuration path or firmware provisioning mechanism before exposing the bridge to an untrusted network.

This document intentionally does not claim that HTTP Basic Authentication provides transport encryption. For networks where credentials or GNSS data must be confidential in transit, isolate the bridge behind a trusted network boundary or an appropriate secure tunnel/reverse proxy rather than exposing the device directly.
