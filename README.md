  --duration 1800 \
  --min-http-success 95 \
  --min-fresh 90 \
  --min-valid-percent 100 \
  --require-type GPRMC \
  --require-type GNGGA
```

The combined report is deliberately conservative: `passed=true` means the HTTP and TCP checks both met their configured thresholds, while `physical_recovery_verified` remains false until the controlled disconnect/reconnect health-sequence qualification is separately performed.

### Reproducible field evidence bundle

Keep the machine-readable NMEA verdict, `/api/live` capture, serial log, and exact firmware commit together. The dependency-free collector copies selected evidence files and writes `EVIDENCE_MANIFEST.json` with byte sizes and SHA-256 hashes. The manifest can also preserve the device, GNSS receiver, and operator-assigned test ID so the evidence package has one traceability record:

```bash
python tools/collect_field_evidence.py evidence/ \
  --file nmea-verdict.json=nmea-verdict.json \
  --file live.csv=live.csv \
  --file serial.log=serial.log \
  --firmware-commit YOUR_FIRMWARE_COMMIT \
  --device bridge-01 \
  --receiver "GNSS receiver model" \
  --test-id recovery-2026-09-06-01
```

Before trusting a bundle for qualification, run the lightweight preflight validator:

```bash
python tools/validate_field_bundle.py evidence/EVIDENCE_MANIFEST.json
```

The preflight requires complete traceability (`firmware_commit`, `device`, `receiver`, and `test_id`) and the standard `nmea-verdict.json`, `live.csv`, and `serial.log` evidence files. It intentionally runs before the hash verifier: it answers whether the bundle is structurally complete for a field test, while `verify_evidence_manifest.py` answers whether the archived files still match their recorded hashes.

The manifest is intentionally separate from the hashed evidence files, avoiding a self-referential checksum and making the evidence directory straightforward to archive and audit. After copying or archiving a bundle, independently verify every listed file with:

```bash
python tools/verify_evidence_manifest.py evidence/EVIDENCE_MANIFEST.json
```

The verifier checks manifest schema, safe unique filenames, recorded byte counts, lowercase SHA-256 digests, file existence, and file contents. A changed or replaced evidence file fails verification before it can be treated as the original captured bundle.

For a completed recovery qualification bundle, the machine-readable qualification report can be independently checked with `tools/verify_recovery_report.py`. To produce an operator-facing Markdown summary after verification, use the same manifest as the source of traceability metadata:

```bash
python tools/field_qualification_report.py \
  evidence/recovery-qualification.json \
  evidence/FIELD_QUALIFICATION.md \
  --verification-report evidence/recovery-verification.json \
  --manifest evidence/EVIDENCE_MANIFEST.json
```

For the complete offline pipeline, use the runner. It performs preflight, verifies the archived manifest, qualifies the simultaneous recovery capture, verifies the generated qualification evidence, and writes a machine-readable result plus the operator-facing report:

```bash
python tools/run_field_qualification.py evidence/ qualification-output/
```

Optional recovery and outage limits can be supplied with `--max-recovery-seconds` and `--max-nmea-outage-seconds`. The runner fails closed: a structurally incomplete, tampered, or non-qualifying bundle does not produce a successful qualification result.

The generated report preserves the qualification verdict, test identity metadata, health sequence, recovery/outage timing, evidence SHA-256 fingerprints, and post-test verification result. If CLI identity metadata is also supplied, it must agree with the manifest; mismatches are rejected to prevent traceability drift.

For regression testing:

```bash
pio test -e esp32-s3-tests
```

For a production firmware build:

```bash
pio run -e esp32-s3-devkitc-1
```

GitHub Actions runs the ESP32-S3 regression build and the production firmware build on pushes and pull requests targeting `main`. Hosted CI compiles embedded test environments without attempting to flash a physical board. Actual ESP32-S3 test execution remains part of hardware validation.

## Current status

The GNSS recovery subsystem is implemented, integrated into the production firmware, and covered by the embedded regression configuration. The geofence subsystem is integrated into configuration, live diagnostics, dashboard status, transition timing, and regression coverage. The CI path compiles embedded tests without requiring physical hardware and publishes traceable firmware artifacts with integrity metadata. Field-test evidence can now be packaged with a deterministic SHA-256 manifest carrying device, receiver, and test identity metadata, independently verified after archival, preflighted for required field-test completeness, and processed through one fail-closed qualification runner. The combined acceptance runner provides one operator-facing verdict across HTTP diagnostics and TCP NMEA streaming. Recovery qualification reports can be independently verified and rendered as auditable operator-facing field reports without duplicating or overriding manifest identity.

The next milestone is physical receiver validation under startup failure, cable disconnect, prolonged silence, UART recovery, recovery cooldown, and controlled geofence boundary-crossing conditions. Keep the generated evidence bundle together for each hardware/receiver combination.
