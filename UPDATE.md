# Updating NavIC GPS Bridge

NavIC GPS Bridge runs on an ESP32-S3, so firmware updates should always preserve a physical recovery path.

## Safe manual update

1. Keep a USB data cable and the PlatformIO environment available for recovery.
2. Record the currently running commit or firmware build before changing anything.
3. Update the local checkout without rewriting history:

   ```bash
   git fetch origin
   git status
   git pull --ff-only origin main
   ```

4. Build the firmware:

   ```bash
   pio run
   ```

5. Upload it over USB:

   ```bash
   pio run -t upload
   ```

6. Monitor boot and GNSS input:

   ```bash
   pio device monitor
   ```

7. Verify the web dashboard, `/api/live`, TCP NMEA output, and GPS-compatible UART output before returning the bridge to service.

## Rollback

If the new firmware is not healthy, check out the previously recorded known-good commit locally, rebuild, and flash it over USB. Do not erase flash or reset persistent settings unless that is specifically required for recovery.

## Automatic updates

The current firmware is **not configured for unattended OTA updates**. That is intentional until a release workflow, signed or integrity-verified firmware artifacts, rollback behavior, and a safe update trigger are implemented together. The USB/PlatformIO path above remains the authoritative recovery mechanism.
