# SOC Log Analyzer

A small Python CLI that reads authentication log lines and flags suspicious login activity: brute-force attempts and successful logins that follow repeated failures.

Built as a portfolio project. It uses only the Python standard library, runs on synthetic sample data, and contains no real logs, credentials, or employer systems.

## What it does

- Parses lines like `2026-11-07 10:15:22 FAILED LOGIN user=admin ip=198.51.100.23`
- Counts failed / successful logins, unique IPs and users
- Flags an IP with 5+ failed logins in 10 minutes (configurable) as a possible brute-force attempt
- Flags a successful login from a user/IP that failed just before it, for review
- Skips malformed lines instead of crashing, and reports how many were skipped
- Optionally writes a JSON report

## Run it

```bash
python log_analyzer.py sample_auth.log
python log_analyzer.py sample_auth.log --threshold 5 --window-minutes 10 --output report.json
```

Expected output on the sample file: 1 brute-force finding (`198.51.100.23`, 7 failures in 10 minutes), 2 success-after-failure cases, and 1 skipped malformed line.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Skills shown

Python, log parsing with regex, sliding-window detection, CLI design with `argparse`, JSON reporting, unit tests with `unittest`.

## Note

Sample IPs use the documentation ranges `203.0.113.x`, `198.51.100.x`, and `192.0.2.x`. They are not real addresses.
