#!/usr/bin/env python3
"""
Missed-Call Follow-Up — my portfolio project for turning missed calls into a follow-up queue.

Turns a CSV of missed calls into a prioritized follow-up queue with
ready-to-send message drafts. Demo only: it writes text, it does not
send SMS, make calls, or connect to any CRM or phone system, and it
contains no real customer data or API keys.

Input CSV columns: name,business,phone,missed_at,reason
  missed_at format: 2026-11-07 09:12

Usage:
    python followup.py sample_calls.csv
    python followup.py sample_calls.csv --output queue.csv --messages messages.md

Priority: newest missed calls first, then repeat callers, then
"no answer" over "voicemail left". Duplicates (same phone) are merged,
keeping the newest entry.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

TS_FORMAT = "%Y-%m-%d %H:%M"
REASON_PRIORITY = {"no answer": 0, "voicemail left": 1, "hung up": 2}


@dataclass
class MissedCall:
    name: str
    business: str
    phone: str
    missed_at: datetime
    reason: str
    count: int = 1


def load_calls(path: Path) -> list[MissedCall]:
    calls: dict[str, MissedCall] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"name", "business", "phone", "missed_at", "reason"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"CSV must have columns: {', '.join(sorted(required))}")
        for row in reader:
            phone = (row["phone"] or "").strip()
            if not phone:
                continue
            missed_at = datetime.strptime((row["missed_at"] or "").strip(), TS_FORMAT)
            call = MissedCall(
                name=(row["name"] or "").strip(),
                business=(row["business"] or "").strip(),
                phone=phone,
                missed_at=missed_at,
                reason=(row["reason"] or "").strip().lower(),
            )
            if phone in calls:
                existing = calls[phone]
                existing.count += 1
                if call.missed_at > existing.missed_at:
                    existing.missed_at = call.missed_at
                    existing.reason = call.reason
            else:
                calls[phone] = call
    return list(calls.values())


def prioritize(calls: list[MissedCall]) -> list[MissedCall]:
    """Newest first, then most calls, then reason priority."""
    return sorted(
        calls,
        key=lambda c: (
            -c.missed_at.timestamp(),
            -c.count,
            REASON_PRIORITY.get(c.reason, 99),
        ),
    )


def draft_message(call: MissedCall, business_name: str = "All Stars Automations") -> str:
    first = call.name.split()[0] if call.name else "there"
    repeat = " I see you tried us a couple of times, sorry we missed you." if call.count > 1 else ""
    return (
        f"Hi {first}, this is James with {business_name}.{repeat} "
        f"We missed your call — sorry about that. "
        f"Want a quick 15-minute call this week to see if we can help with missed calls and follow-up? "
        f"Reply STOP to opt out."
    )


def build_queue(calls: list[MissedCall]) -> list[dict]:
    ordered = prioritize(calls)
    return [
        {
            "rank": i + 1,
            "name": c.name,
            "business": c.business,
            "phone": c.phone,
            "missed_at": c.missed_at.strftime(TS_FORMAT),
            "reason": c.reason,
            "times_called": c.count,
            "message": draft_message(c),
        }
        for i, c in enumerate(ordered)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a missed-call follow-up queue from CSV.")
    parser.add_argument("csvfile", type=Path, help="Input CSV of missed calls")
    parser.add_argument("--output", type=Path, default=None, help="Optional output CSV path")
    parser.add_argument("--messages", type=Path, default=None, help="Optional output Markdown path")
    args = parser.parse_args(argv)

    if not args.csvfile.exists():
        print(f"CSV file not found: {args.csvfile}", file=sys.stderr)
        return 2
    try:
        calls = load_calls(args.csvfile)
    except (ValueError, KeyError) as exc:
        print(f"Error reading CSV: {exc}", file=sys.stderr)
        return 2

    queue = build_queue(calls)
    print(f"Missed calls: {len(calls)} unique numbers "
          f"({sum(c.count for c in calls)} total calls)")
    print(f"Repeat callers: {sum(1 for c in calls if c.count > 1)}")
    for item in queue:
        print(f"\n#{item['rank']} {item['name']} — {item['business']} ({item['phone']})")
        print(f"   Missed {item['missed_at']} · {item['reason']} · called {item['times_called']}x")
        print(f"   {item['message']}")

    if args.output:
        with args.output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["rank", "name", "business", "phone", "missed_at", "reason", "times_called", "message"])
            writer.writeheader()
            writer.writerows(queue)
        print(f"\nQueue written to {args.output}")
    if args.messages:
        lines = ["# Follow-up messages\n"]
        for item in queue:
            lines.append(f"## #{item['rank']} {item['name']} ({item['phone']})\n\n{item['message']}\n")
        args.messages.write_text("\n".join(lines), encoding="utf-8")
        print(f"Messages written to {args.messages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
