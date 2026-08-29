# Configuration and deployment

## Hardware defaults

- GNSS input UART: GPIO 16 (RX), GPIO 17 (TX)
- GPS-compatible output UART: GPIO 18 (TX)
- Default serial speed is loaded from persistent settings.

## Network access

The bridge starts its local access point as `NavIC-GPS-Bridge`. Connect to the device and open the local web dashboard.

## TCP NMEA stream

The bridge exposes NMEA output on TCP port `10110` and supports multiple connected consumers.

## Operational APIs

- `/api/live` — current navigation state
- `/api/diagnostics` — health and runtime diagnostics
- `/api/alerts` — GNSS events
- `/api/track` — rolling track status
- `/api/track.csv` — CSV export
- `/api/track.gpx` — GPX export
- `/api/track.kml` — KML export
- `/api/track/clear` — clear rolling track
- `/api/security` — authentication status
- `/api/ota` — browser firmware upload

## Security

Web/API authentication is optional and stored in device settings. Authentication should be enabled before exposing the device on a shared or routed network.

## Build validation

Every push and pull request to `main` runs a PlatformIO firmware build through GitHub Actions. Successful builds publish the firmware binary as a workflow artifact.
