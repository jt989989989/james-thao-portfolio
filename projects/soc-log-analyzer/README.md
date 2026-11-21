# SOC Log Analyzer

I built a small Python CLI that reads authentication log lines and flags suspicious login activity: brute-force attempts, successful logins that follow repeated failures, and successful logins outside normal hours.

I use only the Python standard library, run it on synthetic sample data, and it contains no real logs, credentials, or employer systems.

## What it does

- Parses lines like `2026-11-07 10:15:22 FAILED LOGIN user=admin ip=198.51.100.23`
- Counts failed / successful logins, unique IPs and users
- Flags an IP with 5+ failed logins in 10 minutes (configurable) as a possible brute-force attempt
- Flags a successful login from a user/IP that failed just before it, for review
- **v3 — flags successful logins outside normal hours** (default 06:00–22:00, configurable with `--normal-hours`). A 3am login is not proof of compromise — people work odd shifts — but it is worth a look, so logins between midnight and 5am are medium severity and other off-hours logins are low. Failed logins are not flagged here; brute-force detection already covers those. Overnight windows work too, e.g. `--normal-hours 22:00-06:00` for a night-shift team.
- Skips malformed lines instead of crashing, and reports how many were skipped
- Optionally writes a JSON report

## Run it

```bash
python log_analyzer.py sample_auth.log
python log_analyzer.py sample_auth.log --threshold 5 --window-minutes 10 --output report.json
python log_analyzer.py sample_auth.log --normal-hours 07:00-19:00
```

Expected output on the sample file: 1 brute-force finding (`198.51.100.23`, 7 failures in 10 minutes), 2 success-after-failure cases, 2 unusual-hours logins (`admin` at 03:12, medium; `mlee` at 23:47, low), and 1 skipped malformed line.

## Tests

```bash
python -m unittest discover -s tests -v
```

15 tests: parsing, brute-force thresholds, and unusual-hours detection — including the 06:00/22:00 boundaries, overnight windows, failed-logins-not-flagged, bad `--normal-hours` values, and the exact counts on the sample file.

## Skills shown

Python, log parsing with regex, sliding-window detection, time-window logic, CLI design with `argparse`, JSON reporting, unit tests with `unittest`.

## Note

Sample IPs use the documentation ranges `203.0.113.x`, `198.51.100.x`, and `192.0.2.x`. They are not real addresses.
