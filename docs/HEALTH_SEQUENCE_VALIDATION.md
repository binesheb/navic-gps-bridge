# Live health-sequence validation

`tools/live_capture.py` records the bridge `/api/live` health state alongside
GNSS telemetry. `tools/analyze_health_sequence.py` turns that capture into a
small, auditable transition report.

## Intended recovery test

A controlled receiver disconnect/reconnect should produce this sequence:

`HEALTHY -> STALE -> RECOVERING -> HEALTHY`

The analyzer only reports `recovery_sequence_observed=true` when all four
states occur in order. Repeated samples of the same state are compressed, and
blank status samples are ignored. Missing recovery evidence therefore cannot
be mistaken for a successful recovery test.

## Evidence integrity

The analyzer also validates that `elapsed_s` is numeric and never moves
backwards. The report includes `recovery_duration_s`, measured from the first
observed `RECOVERING` state to the subsequent `HEALTHY` state.

For a receiver-specific acceptance test, an optional upper bound can be
applied:

```bash
python tools/analyze_health_sequence.py capture.csv \
  --max-recovery-seconds 15 --json > health-report.json
```

The limit is deliberately supplied by the test operator rather than baked into
the tool, because the acceptable recovery time depends on the receiver, UART
configuration, and deployment requirements.

## Usage

```bash
python tools/analyze_health_sequence.py capture.csv
python tools/analyze_health_sequence.py capture.csv --json > health-report.json
```

A `qualification_ready` result of `true` means the capture contains the
expected state sequence, has structurally valid elapsed-time evidence, and
satisfies any requested recovery-duration limit. It does **not** by itself
prove RF performance, position accuracy, or long-duration stability; those
remain separate hardware acceptance criteria.
