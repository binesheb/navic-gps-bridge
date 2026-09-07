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

### Hardware qualification run scaffold

For the first physical receiver qualification, create a run directory with the exact device/receiver/firmware identity and the full H01-H14 matrix before starting the test. The scaffold intentionally records `NOT_STARTED` rather than inventing results and creates the standard evidence layout:

```bash
python tools/create_hardware_qualification_run.py evidence/bridge-01-receiver-a \
  --device bridge-01 \
  --receiver "GNSS receiver model" \
  --firmware-commit YOUR_FIRMWARE_COMMIT \
  --test-id receiver-a-2026-09-07
```

The generated `RUN_METADATA.json` is the run identity record and `FIELD_QUALIFICATION_RUN.md` is the operator checklist for H01-H14. Complete the physical test using [the hardware qualification matrix](docs/HARDWARE_QUALIFICATION_MATRIX.md), then replace the scaffold placeholders with the real captured evidence before running the existing bundle preflight, manifest verification, and qualification runner. The scaffold itself never changes a result to `PASS`.

### Direct receiver serial capture

The field kit now includes a dependency-light serial capture tool for collecting the GNSS receiver's raw NMEA stream independently of the bridge. Install the field-only dependency set first:

```bash
python -m pip install -r requirements-field.txt
```

Capture a receiver directly (Windows or Linux) and optionally emit a machine-readable capture verdict:

```bash
python tools/serial_nmea_capture.py COM5 evidence/bridge-01-receiver-a/serial.log \
  --baud 9600 \
  --seconds 60 \
  --json-output evidence/bridge-01-receiver-a/serial-verdict.json
```

The tool preserves the raw byte stream, counts checksum-valid/invalid NMEA sentences, records observed formatter types, and fails closed when no sentences arrive or any received NMEA sentence has an invalid checksum. This is evidence collection only: it does not claim NavIC reception or substitute for the H01-H14 physical procedures.

To close the final operator gap after the physical test, run:

```bash
python tools/finalize_hardware_qualification_run.py evidence/bridge-01-receiver-a
```

The finalizer is deliberately fail-closed. It requires every H01-H14 checklist row to be explicitly `PASS`, every standard evidence artifact to exist and be non-empty, and `FIELD_QUALIFICATION_RESULT.json` to contain `passed=true`. Only then does it change `RUN_METADATA.json` to `COMPLETE` and record `completed_at`. It cannot turn `NOT_RUN` or `FAIL` into a pass.

For regression testing:

```bash
pio test -e esp32-s3-tests
```

For a production firmware build:
