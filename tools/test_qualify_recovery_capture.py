import csv
import json
import tempfile
import unittest
from pathlib import Path

from qualify_recovery_capture import qualify


class RecoveryCaptureTests(unittest.TestCase):
    def make_files(self, rows, events):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        live = root / "live.csv"
        with live.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["elapsed_s", "status"])
            writer.writeheader()
            writer.writerows({"elapsed_s": t, "status": status} for t, status in rows)
        timeline = root / "nmea_timeline.log"
        timeline.write_text("".join(f"{wall}\t{elapsed}\t{event}\t{payload}\n" for wall, elapsed, event, payload in events), encoding="utf-8")
        self.addCleanup(temp.cleanup)
        return live, timeline

    def test_qualifies_recovery_after_reconnect(self):
        live, timeline = self.make_files(
            [(0, "HEALTHY"), (2, "STALE"), (3, "RECOVERING"), (8, "HEALTHY")],
            [(100, 0, "CONNECT", "port=10110"), (103, 3, "DISCONNECT", "peer_closed"),
             (105, 5, "CONNECT", "port=10110")],
        )
        report = qualify(str(live), str(timeline), max_recovery_seconds=10, max_nmea_outage_seconds=5)
        self.assertTrue(report["qualification_ready"])
        self.assertEqual(report["recovery_duration_s"], 5.0)
        self.assertEqual(report["nmea_outage_duration_s"], 2.0)
        self.assertTrue(report["recovery_after_nmea_reconnect"])

    def test_recovery_without_disconnect_does_not_qualify(self):
        live, timeline = self.make_files(
            [(0, "HEALTHY"), (2, "STALE"), (3, "RECOVERING"), (5, "HEALTHY")],
            [(100, 0, "CONNECT", "port=10110")],
        )
        report = qualify(str(live), str(timeline))
        self.assertFalse(report["qualification_ready"])

    def test_health_recovery_before_reconnect_does_not_qualify(self):
        live, timeline = self.make_files(
            [(0, "HEALTHY"), (2, "STALE"), (3, "RECOVERING"), (4, "HEALTHY")],
            [(100, 0, "CONNECT", "port=10110"), (103, 3, "DISCONNECT", "peer_closed"),
             (105, 5, "CONNECT", "port=10110")],
        )
        report = qualify(str(live), str(timeline))
        self.assertFalse(report["qualification_ready"])
        self.assertFalse(report["recovery_after_nmea_reconnect"])

    def test_outage_limit_blocks_qualification(self):
        live, timeline = self.make_files(
            [(0, "HEALTHY"), (2, "STALE"), (3, "RECOVERING"), (8, "HEALTHY")],
            [(100, 0, "CONNECT", "port=10110"), (103, 3, "DISCONNECT", "peer_closed"),
             (110, 10, "CONNECT", "port=10110")],
        )
        report = qualify(str(live), str(timeline), max_nmea_outage_seconds=5)
        self.assertFalse(report["qualification_ready"])
        self.assertFalse(report["nmea_outage_within_limit"])

    def test_rejects_non_monotonic_timestamps(self):
        live, timeline = self.make_files(
            [(0, "HEALTHY"), (2, "STALE")],
            [(100, 1, "CONNECT", "port=10110"), (101, 0, "NMEA", "$GPRMC,x")],
        )
        with self.assertRaises(ValueError):
            qualify(str(live), str(timeline))


if __name__ == "__main__":
    unittest.main()
