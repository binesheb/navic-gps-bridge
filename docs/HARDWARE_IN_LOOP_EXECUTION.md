# Hardware-in-Loop Execution Runbook

This runbook is the execution companion to `HARDWARE_QUALIFICATION_MATRIX.md`. It is intentionally procedural: the operator should be able to perform the physical qualification without inventing test order, evidence names, or pass/fail interpretation.

## 1. Entry gate

Do not start H01-H14 until all of these are recorded in `RUN_METADATA.json`:

- bridge device identifier and ESP32-S3 board/revision;
- GNSS receiver manufacturer/model and receiver firmware version if available;
- antenna type and placement;
- bridge firmware commit SHA;
- GNSS UART pins, baud rate, and wiring;
- test ID, operator, and start timestamp;
- configured GNSS silence and recovery-cooldown limits;
- geofence center/radius when H11-H13 are in scope.

Use the scaffold first:

```bash
python tools/create_hardware_qualification_run.py evidence/bridge-01-receiver-a \
  --device bridge-01 \
  --receiver "GNSS receiver model" \
  --firmware-commit YOUR_FIRMWARE_COMMIT \
  --test-id receiver-a-2026-09-10
```

A scaffolded `NOT_STARTED` result is not evidence of a pass.

## 2. Receiver-only baseline

Before diagnosing the bridge, connect the receiver directly to the host and run a bounded serial capture:

```bash
python tools/serial_nmea_capture.py COM5 evidence/bridge-01-receiver-a/serial.log \
  --baud 9600 \
  --seconds 60 \
  --min-sentences 30 \
  --min-valid-percent 100 \
  --require-type GNRMC \
  --require-type GNGGA \
  --json-output evidence/bridge-01-receiver-a/serial-verdict.json
```

If the receiver-only baseline fails, stop. Do not attribute the failure to bridge firmware, TCP streaming, or NavIC reception until the receiver/UART path is healthy.

## 3. Run order and stop conditions

Execute the matrix in this order:

| Phase | Tests | Stop condition |
|---|---|---|
| Startup | H01-H02 | No valid baseline or recovery never arms |
| Recovery | H03-H05 | Reconnect does not restore accepted NMEA |
| Output | H06-H08 | Invalid/malformed data is propagated as valid output or client bounds fail |
| Diagnostics | H09-H10 | Live telemetry is stale or runtime policy does not take effect |
| Geofence | H11-H13 | False transition, duplicate transition, or no-fix event occurs |
| Soak | H14 | Reset, recovery loop, or sustained output/diagnostic failure |

A failed prerequisite stops dependent scenarios. Record the result as `FAIL` or `NOT_RUN`; never convert an unexecuted dependent test into `PASS`.

## 4. Recovery timing evidence

For H02-H05, the `/api/live` capture must span the induced outage and enough time after recovery to show the state transition. Record at minimum:

- last accepted GNSS timestamp before the outage;
- first detected stale/silence state;
- recovery-attempt count before and after the event;
- recovery attempt timestamp(s);
- cooldown state and elapsed cooldown;
- first accepted sentence after reconnect;
- whether rapid repeated restart attempts occurred.

The recovery qualification report is only valid when these transitions are observable in the captured sequence. A single final `/api/live` snapshot is insufficient to prove timing behaviour.

## 5. H06-H10 output and API checks

For H06, capture the downstream UART bytes and verify both converted sentence types and regenerated checksums.

For H07-H08, retain the TCP stream verdict and connection evidence. Confirm the fifth client is rejected/closed when four output slots are occupied; do not treat a connection timeout as proof of bounded rejection.

For H09-H10, retain request/response or `/api/live` telemetry showing freshness and the changed recovery policy. The policy update must occur without reboot and must not erase recovery history.

## 6. Geofence controls

For H11, cross the configured boundary once in each direction and wait for telemetry to settle between transitions. Count physical crossings and compare them with emitted events.

For H12, remove valid position updates while remaining near the boundary. No enter/exit event may be generated solely from stale or invalid position data.

For H13, use a controlled test coordinate pair around the +180/-180 longitude wrap. The expected result is based on shortest wrapped longitude distance, not raw longitude subtraction.

Record the configured center, radius, test coordinates, and observed transition timestamps in the run notes.

## 7. Soak test

H14 requires a continuous 30-minute run with the normal GNSS receiver connected and ordinary TCP/API use. Start and end timestamps must cover the complete requested duration. Record resets, recovery attempts, sentence gaps, and diagnostic failures if any occur.

Do not infer continuity from a final snapshot. The serial/NMEA/API evidence must cover the complete soak window.

## 8. Evidence closure

After all physical tests:

1. Replace scaffold placeholders with actual evidence and explicit H01-H14 results.
2. Generate the evidence manifest from stable physical artifacts.
3. Run field-bundle preflight.
4. Verify the manifest hashes.
5. Generate/verify the recovery qualification report where applicable.
6. Run the final hardware qualification finalizer.

Recommended sequence:

```bash
python tools/collect_field_evidence.py evidence/bridge-01-receiver-a \
  --file nmea-verdict.json=nmea-verdict.json \
  --file live.csv=live.csv \
  --file serial.log=serial.log \
  --firmware-commit YOUR_FIRMWARE_COMMIT \
  --device bridge-01 \
  --receiver "GNSS receiver model" \
  --test-id receiver-a-2026-09-10

python tools/validate_field_bundle.py evidence/bridge-01-receiver-a/EVIDENCE_MANIFEST.json
python tools/verify_evidence_manifest.py evidence/bridge-01-receiver-a/EVIDENCE_MANIFEST.json
python tools/finalize_hardware_qualification_run.py evidence/bridge-01-receiver-a
```

The finalizer is the closure gate, not a result generator. It must remain impossible for the tooling to turn `NOT_RUN` or `FAIL` into `PASS`.

## 9. Interpretation boundary

A successful H01-H14 physical run demonstrates behaviour of the tested hardware/receiver/wiring/firmware combination. It does not establish universal RF performance for every antenna or receiver installation.

Likewise, green GitHub Actions results establish software regression/build evidence only. They do not substitute for physical receiver recovery, electrical compatibility, geofence movement, or RF validation.

Keep the complete evidence directory immutable after finalization. If an artifact changes, regenerate the manifest and repeat verification rather than editing the recorded hash.
