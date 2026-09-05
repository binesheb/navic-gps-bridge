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

## Usage

```bash
python tools/analyze_health_sequence.py capture.csv
python tools/analyze_health_sequence.py capture.csv --json > health-report.json
```

A `qualification_ready` result of `true` means the capture contains the
expected state sequence. It does **not** by itself prove RF performance,
position accuracy, or long-duration stability; those remain separate hardware
acceptance criteria.
