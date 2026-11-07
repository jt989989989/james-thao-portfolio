"""Tests for log_analyzer.py — run with: python -m unittest discover -s tests -v"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from log_analyzer import find_brute_force, parse_line, parse_log


class TestParseLine(unittest.TestCase):
    def test_parses_failed_login(self):
        event = parse_line("2026-11-07 10:15:22 FAILED LOGIN user=admin ip=198.51.100.23")
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.result, "FAILED")
        self.assertEqual(event.user, "admin")
        self.assertEqual(event.ip, "198.51.100.23")
        self.assertEqual(event.timestamp, datetime(2026, 11, 7, 10, 15, 22))

    def test_rejects_malformed_line(self):
        self.assertIsNone(parse_line("not a log line"))
        self.assertIsNone(parse_line(""))

    def test_parse_log_counts_skipped(self):
        events, skipped = parse_log(
            "2026-11-07 10:15:22 FAILED LOGIN user=admin ip=198.51.100.23\n"
            "bad line\n"
            "2026-11-07 10:16:02 SUCCESS LOGIN user=admin ip=198.51.100.23\n"
        )
        self.assertEqual(len(events), 2)
        self.assertEqual(skipped, 1)


class TestBruteForce(unittest.TestCase):
    def test_flags_ip_over_threshold(self):
        text = "\n".join(
            f"2026-11-07 10:15:{i:02d} FAILED LOGIN user=admin ip=198.51.100.23"
            for i in range(0, 30, 5)
        )
        events, _ = parse_log(text)
        findings = find_brute_force(events, threshold=5, window_minutes=10)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["ip"], "198.51.100.23")
        self.assertEqual(findings[0]["failed_in_window"], 6)

    def test_does_not_flag_below_threshold(self):
        events, _ = parse_log(
            "2026-11-07 10:15:22 FAILED LOGIN user=admin ip=198.51.100.23\n"
            "2026-11-07 10:16:02 FAILED LOGIN user=admin ip=198.51.100.23\n"
        )
        self.assertEqual(find_brute_force(events, threshold=5, window_minutes=10), [])


if __name__ == "__main__":
    unittest.main()
