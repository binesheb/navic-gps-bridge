# Live NMEA Stream Validation

Use `tools/nmea_stream_check.py` from a laptop on the same network as the bridge to validate the TCP NMEA stream before connecting a downstream GPS application.

## Usage

```bash
python tools/nmea_stream_check.py BRIDGE_IP
```

Optional port and duration:

```bash
python tools/nmea_stream_check.py BRIDGE_IP 10110 60
```

The default TCP port is `10110`.

## What it checks

The checker is dependency-free and:

- connects to the bridge TCP NMEA service;
- consumes complete newline-delimited NMEA sentences;
- validates each NMEA checksum;
- extracts and counts five-character NMEA formatters such as `GPRMC`, `GNGGA`, and `GPGSV`;
- reports the observed two-character talker IDs such as `GP` and `GN`;
- reports the number of valid and invalid frames;
- exits with status `1` when no data is received or a checksum failure is detected.

Talker reporting is observational rather than a hard-coded pass/fail rule. This keeps the checker useful for both raw multi-constellation streams and the bridge's GPS-compatible output, while making an unexpected talker-ID mix visible during field validation.

A successful run ends with:

```text
PASS: NMEA stream received with valid checksums
```

This validates the transport, framing, checksum, and talker/formatter reporting path. It does not replace receiver-specific testing of fix quality, NavIC satellite visibility, antenna performance, or the bridge's web/API diagnostics.

## Field-test sequence

1. Flash the production firmware.
2. Connect the GNSS receiver to the configured UART.
3. Connect the laptop to the bridge network.
4. Run the checker for at least 30 seconds.
5. Confirm zero checksum failures.
6. Record the observed talker IDs and RMC/GGA/GSV counts.
7. Compare the observed counts with `/api/live`.
8. Then test a downstream GPS application against TCP port `10110`.

For GNSS recovery testing, disconnect the receiver after a healthy stream has been established and use the dashboard `/api/live` recovery counters alongside this checker to confirm the stream stops and resumes after UART recovery.
