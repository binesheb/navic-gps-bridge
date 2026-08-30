# Firmware Releases

## Automated release process

The repository builds a release automatically when a version tag beginning with `v` is pushed, for example:

```text
v0.1.0
v1.0.0
```

The release workflow:

1. Checks out the tagged source.
2. Builds the `esp32-s3-devkitc-1` environment with PlatformIO.
3. Publishes the firmware binary as a GitHub Release asset.
4. Publishes a SHA-256 checksum manifest for integrity verification.

## Release assets

- `navic-gps-bridge-vX.Y.Z.bin` — application firmware for browser-based OTA updates.
- `bootloader.bin` — bootloader image when produced by the PlatformIO environment.
- `partitions.bin` — partition table when produced by the PlatformIO environment.
- `SHA256SUMS.txt` — checksums for published assets.

## OTA safety notes

For routine OTA updates, use the versioned `navic-gps-bridge-vX.Y.Z.bin` application image. Verify the SHA-256 checksum before distributing firmware to devices.

The device should remain powered throughout the OTA operation. A production hardware revision should also provide a physical recovery/reset path so a failed network update can always be recovered through USB serial flashing.
