#!/usr/bin/env python3
"""
SOC Log Analyzer — my portfolio project for flagging suspicious login activity.

Parses authentication log lines and flags suspicious login activity:
brute-force attempts, logins after repeated failures, and unknown users.

This is a portfolio demo built from synthetic sample data. It does not
claim production use at any employer and contains no real logs or credentials.

Usage:
    python log_analyzer.py sample_auth.log
    python log_analyzer.py sample_auth.log --threshold 5 --window-minutes 10 --output report.json

Log line format (one event per line):
    2026-11-07 10:15:22 FAILED LOGIN user=jthao ip=203.0.113.10
    2026-11-07 10:16:01 SUCCESS LOGIN user=jthao ip=203.0.113.10
    2026-11-07 10:17:44 FAILED LOGIN user=admin ip=198.51.100.23

Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<result>FAILED|SUCCESS)\s+LOGIN\s+"
    r"user=(?P<user>\S+)\s+ip=(?P<ip>\S+)\s*$"
)
TS_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class LoginEvent:
    timestamp: datetime
    result: str  # "FAILED" or "SUCCESS"
    user: str
    ip: str


def parse_line(line: str) -> LoginEvent | None:
    """Parse one log line. Returns None for blank / unparsable lines."""
    match = LINE_RE.match(line.strip())
    if not match:
        return None
    return LoginEvent(
        timestamp=datetime.strptime(match.group("ts"), TS_FORMAT),
        result=match.group("result"),
        user=match.group("user"),
        ip=match.group("ip"),
    )


def parse_log(text: str) -> tuple[list[LoginEvent], int]:
    """Parse full log text. Returns (events, skipped_line_count)."""
    events: list[LoginEvent] = []
    skipped = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        event = parse_line(line)
        if event is None:
            skipped += 1
        else:
            events.append(event)
    events.sort(key=lambda e: e.timestamp)
    return events, skipped


def find_brute_force(
    events: list[LoginEvent],
    threshold: int = 5,
    window_minutes: int = 10,
) -> list[dict]:
    """
    Flag IPs with >= threshold FAILED logins inside a sliding window.
    Returns one finding per IP with first/last seen and failure count.
    """
    failures_by_ip: dict[str, list[datetime]] = defaultdict(list)
    for event in events:
        if event.result == "FAILED":
            failures_by_ip[event.ip].append(event.timestamp)

    window = timedelta(minutes=window_minutes)
    findings: list[dict] = []
    for ip, times in failures_by_ip.items():
        times.sort()
        worst = 0
        worst_start: datetime | None = None
        for i, start in enumerate(times):
            count = sum(1 for t in times[i:] if t - start <= window)
            if count > worst:
                worst = count
                worst_start = start
        if worst >= threshold and worst_start is not None:
            findings.append(
                {
                    "ip": ip,
                    "type": "brute_force",
                    "failed_in_window": worst,
                    "window_minutes": window_minutes,
                    "window_start": worst_start.strftime(TS_FORMAT),
                    "total_failed": len(times),
                    "severity": "high" if worst >= threshold * 2 else "medium",
                }
            )
    return sorted(findings, key=lambda f: f["failed_in_window"], reverse=True)


def find_success_after_failures(events: list[LoginEvent]) -> list[dict]:
    """Flag SUCCESS logins where the same user/IP failed just before."""
    failed: set[tuple[str, str]] = set()
    findings: list[dict] = []
    for event in events:
        key = (event.user, event.ip)
        if event.result == "FAILED":
            failed.add(key)
        elif event.result == "SUCCESS" and key in failed:
            findings.append(
                {
                    "user": event.user,
                    "ip": event.ip,
                    "type": "success_after_failures",
                    "timestamp": event.timestamp.strftime(TS_FORMAT),
                    "note": "Successful login after earlier failures from same user/IP — review, do not assume compromise.",
                }
            )
            failed.discard(key)
    return findings


def summarize(events: list[LoginEvent]) -> dict:
    total = len(events)
    failed = sum(1 for e in events if e.result == "FAILED")
    success = total - failed
    return {
        "total_events": total,
        "failed_logins": failed,
        "successful_logins": success,
        "unique_ips": len({e.ip for e in events}),
        "unique_users": len({e.user for e in events}),
        "top_failed_ips": [
            {"ip": ip, "failed": count}
            for ip, count in Counter(
                e.ip for e in events if e.result == "FAILED"
            ).most_common(5)
        ],
        "top_failed_users": [
            {"user": user, "failed": count}
            for user, count in Counter(
                e.user for e in events if e.result == "FAILED"
            ).most_common(5)
        ],
    }


def analyze(
    events: list[LoginEvent], threshold: int = 5, window_minutes: int = 10
) -> dict:
    return {
        "summary": summarize(events),
        "brute_force": find_brute_force(events, threshold, window_minutes),
        "success_after_failures": find_success_after_failures(events),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze auth logs for suspicious logins.")
    parser.add_argument("logfile", type=Path, help="Path to auth log file")
    parser.add_argument("--threshold", type=int, default=5,
                        help="Failed logins in window to flag (default: 5)")
    parser.add_argument("--window-minutes", type=int, default=10,
                        help="Sliding window in minutes (default: 10)")
    parser.add_argument("--output", type=Path, default=None,
                        help="Optional JSON report path")
    args = parser.parse_args(argv)

    if not args.logfile.exists():
        print(f"Log file not found: {args.logfile}", file=sys.stderr)
        return 2

    events, skipped = parse_log(args.logfile.read_text(encoding="utf-8"))
    report = analyze(events, args.threshold, args.window_minutes)
    report["skipped_lines"] = skipped
    report["source_file"] = str(args.logfile)

    print(f"Events: {report['summary']['total_events']} "
          f"({report['summary']['failed_logins']} failed, "
          f"{report['summary']['successful_logins']} successful)")
    print(f"Unique IPs: {report['summary']['unique_ips']}  "
          f"Unique users: {report['summary']['unique_users']}")
    if skipped:
        print(f"Skipped unparsable lines: {skipped}")
    print(f"\nBrute-force findings: {len(report['brute_force'])}")
    for finding in report["brute_force"]:
        print(f"  [{finding['severity']}] {finding['ip']} — "
              f"{finding['failed_in_window']} failures in "
              f"{finding['window_minutes']} min "
              f"(total {finding['total_failed']})")
    print(f"Success-after-failure: {len(report['success_after_failures'])}")
    for finding in report["success_after_failures"]:
        print(f"  {finding['user']} from {finding['ip']} at {finding['timestamp']}")

    if args.output:
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nReport written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
