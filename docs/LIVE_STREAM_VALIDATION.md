# Live NMEA Stream Validation

Use `tools/nmea_stream_check.py` from a laptop on the same network as the bridge to validate the TCP NMEA stream before connecting a downstream GPS application.

## Usage

Basic 30-second check:

```bash
python tools/nmea_stream_check.py BRIDGE_IP
```

Explicit port and duration:

```bash
python tools/nmea_stream_check.py BRIDGE_IP 10110 60
```

The default TCP port is `10110`.

For a production-style acceptance check, require the sentence types that the downstream consumer needs and save the machine-readable verdict:

```bash
python tools/nmea_stream_check.py BRIDGE_IP 10110 60 \
  --min-sentences 30 \
  --min-valid-percent 100 \
  --require-type GPRMC \
  --require-type GPGGA \
  --json-output nmea-verdict.json
```

Use `--min-duration-s` when the required capture duration differs from the requested stream duration. The default is to require the full requested duration, which makes an early TCP disconnect fail the acceptance check.

## What it checks

The checker is dependency-free and:

- connects to the bridge TCP NMEA service;
- consumes complete newline-delimited NMEA sentences;
- validates every NMEA checksum;
- extracts and counts five-character NMEA formatters such as `GPRMC`, `GNGGA`, and `GPGSV`;
- reports observed two-character talker IDs such as `GP` and `GN`;
- reports valid and invalid frame counts and the checksum-valid percentage;
- can require a minimum sentence count;
- can require a minimum checksum-valid percentage;
- can require specific NMEA formatter types;
- verifies that the actual capture duration reaches the configured minimum;
- emits an optional JSON verdict containing the observed metrics and explicit failure reasons.

Talker reporting is observational rather than a hard-coded pass/fail rule. This keeps the checker useful for both raw multi-constellation streams and the bridge's GPS-compatible output, while making an unexpected talker-ID mix visible during field validation.

The command exits with status `1` when the stream cannot be read or when any configured acceptance gate fails.

## Field-test sequence

1. Flash the production firmware.
2. Connect the GNSS receiver to the configured UART.
3. Connect the laptop to the bridge network.
4. Run the checker for at least 30 seconds.
5. For strict validation, require `GPRMC` and `GPGGA` and require `--min-valid-percent 100`.
6. Confirm the actual capture duration reaches the requested duration.
7. Record the observed talker IDs and RMC/GGA/GSV counts from the JSON verdict.
8. Compare the observed stream behaviour with `/api/live`.
9. Then test a downstream GPS application against TCP port `10110`.

For GNSS recovery testing, disconnect the receiver after a healthy stream has been established. Use the dashboard `/api/live` recovery counters and the NMEA checker together: the API capture should show the induced silence/recovery event, while the NMEA capture should show the downstream stream stopping and subsequently resuming with valid checksums.

## Interpreting the JSON evidence

A passing `--json-output` report contains:

- `passed: true`;
- `sentences`, `valid_sentences`, and `invalid_sentences`;
- `valid_percent`;
- `duration_s` and `requested_duration_s`;
- `min_sentences`, `min_valid_percent`, and `min_duration_s`;
- `required_types`;
- formatter counts under `types`;
- talker counts under `talkers`.

A failed report retains the same evidence and adds a `failures` array. Keep this JSON file with the corresponding `/api/live` CSV/JSON capture and firmware commit/tag so a field result can be reproduced and audited later.
