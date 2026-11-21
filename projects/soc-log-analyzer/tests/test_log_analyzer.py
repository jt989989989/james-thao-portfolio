"""Tests for log_analyzer.py — run with: python -m unittest discover -s tests -v"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from log_analyzer import (
    analyze,
    find_brute_force,
    find_unusual_hours,
    is_outside_normal_hours,
    parse_line,
    parse_log,
    parse_normal_hours,
)
from datetime import time


class TestUnusualHours(unittest.TestCase):
    def _events(self, text):
        events, _ = parse_log(text)
        return events

    def test_flags_success_outside_normal_hours(self):
        events = self._events(
            "2026-11-07 03:12:44 SUCCESS LOGIN user=admin ip=198.51.100.23\n"
        )
        findings = find_unusual_hours(events)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["user"], "admin")
        self.assertEqual(findings[0]["severity"], "medium")  # small hours
        self.assertEqual(findings[0]["timestamp"], "2026-11-07 03:12:44")

    def test_does_not_flag_success_inside_normal_hours(self):
        events = self._events(
            "2026-11-07 09:02:11 SUCCESS LOGIN user=jthao ip=203.0.113.10\n"
            "2026-11-07 21:59:59 SUCCESS LOGIN user=jthao ip=203.0.113.10\n"
        )
        self.assertEqual(find_unusual_hours(events), [])

    def test_boundary_start_is_normal_end_is_unusual(self):
        events = self._events(
            "2026-11-07 06:00:00 SUCCESS LOGIN user=a ip=192.0.2.1\n"
            "2026-11-07 22:00:00 SUCCESS LOGIN user=b ip=192.0.2.2\n"
        )
        findings = find_unusual_hours(events)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["user"], "b")

    def test_evening_login_is_low_severity(self):
        events = self._events(
            "2026-11-07 23:47:19 SUCCESS LOGIN user=mlee ip=203.0.113.42\n"
        )
        findings = find_unusual_hours(events)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "low")

    def test_failed_logins_are_not_flagged(self):
        events = self._events(
            "2026-11-07 02:00:00 FAILED LOGIN user=admin ip=198.51.100.23\n"
        )
        self.assertEqual(find_unusual_hours(events), [])

    def test_overnight_window(self):
        # Night-shift team: normal hours 22:00-06:00.
        self.assertFalse(
            is_outside_normal_hours(datetime(2026, 11, 7, 23, 30), time(22, 0), time(6, 0))
        )
        self.assertFalse(
            is_outside_normal_hours(datetime(2026, 11, 7, 2, 0), time(22, 0), time(6, 0))
        )
        self.assertTrue(
            is_outside_normal_hours(datetime(2026, 11, 7, 12, 0), time(22, 0), time(6, 0))
        )
        events = self._events(
            "2026-11-07 23:30:00 SUCCESS LOGIN user=night ip=192.0.2.9\n"
            "2026-11-07 12:00:00 SUCCESS LOGIN user=day ip=192.0.2.9\n"
        )
        findings = find_unusual_hours(events, time(22, 0), time(6, 0))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["user"], "day")

    def test_parse_normal_hours_valid(self):
        self.assertEqual(parse_normal_hours("06:00-22:00"), (time(6, 0), time(22, 0)))
        self.assertEqual(parse_normal_hours("22:00-06:00"), (time(22, 0), time(6, 0)))

    def test_parse_normal_hours_invalid(self):
        for bad in ("6-22", "06:00", "25:00-22:00", "06:60-22:00", "06:00/22:00", ""):
            with self.assertRaises(ValueError, msg=bad):
                parse_normal_hours(bad)

    def test_analyze_includes_unusual_hours(self):
        events = self._events(
            "2026-11-07 03:12:44 SUCCESS LOGIN user=admin ip=198.51.100.23\n"
            "2026-11-07 09:02:11 SUCCESS LOGIN user=jthao ip=203.0.113.10\n"
        )
        report = analyze(events)
        self.assertEqual(len(report["unusual_hours_logins"]), 1)
        self.assertEqual(report["unusual_hours_logins"][0]["user"], "admin")

    def test_sample_file_counts(self):
        sample = Path(__file__).resolve().parents[1] / "sample_auth.log"
        events, skipped = parse_log(sample.read_text(encoding="utf-8"))
        report = analyze(events)
        self.assertEqual(len(report["brute_force"]), 1)
        self.assertEqual(len(report["success_after_failures"]), 2)
        self.assertEqual(len(report["unusual_hours_logins"]), 2)
        self.assertEqual(skipped, 1)


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
