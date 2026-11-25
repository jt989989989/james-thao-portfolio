# Port Scanner — v3.0.0

A threaded TCP connect port scanner for **lab targets only** — the
first tool in the Wednesday cybersecurity track, built as a tool to
help beginners learn penetration testing.

It scans a target host over a port range (or a list of ports) and prints
which ports are OPEN and which are CLOSED, with a short summary and the
scan rate in ports per second.

## The authorisation rule (read this first)

This tool is ONLY for targets I own or have explicit permission to
test:

- `localhost` / `127.0.0.1` / `::1`
- Private lab addresses — `10.x.x.x`, `172.16.x.x`–`172.31.x.x`,
  `192.168.x.x`, link-local `169.254.x.x` (my own VMs and lab machines)
- Intentionally vulnerable lab apps (DVWA, Metasploitable) and
  HackTheBox / TryHackMe machines I am assigned

By default the scanner **refuses** any other target. To scan a named
target outside that list you must pass `--i-have-permission`, which means
you own the target or have the owner's written permission to test it —
and the scanner still prints a warning. Never scan a system you do not
own or have permission to test: unauthorised scanning can break the law
where you live.

The scanner never brute-forces logins, never tries exploits, and never
floods a target — it opens one short TCP connection per port, and the
threads only run those attempts in parallel. The paranoid timing preset
(5 threads, 2s timeout) is there for fragile lab machines.

## How to run it

Python 3.10+ only, standard library only, nothing to install.

```bash
# Scan the default range (ports 1–1024) on localhost
python port_scanner.py 127.0.0.1

# Scan specific ports on a lab machine
python port_scanner.py 192.168.1.10 --ports 22,80,443

# A wider range with a longer per-port timeout
python port_scanner.py localhost --ports 1-5000 --timeout 1

# Fast sweep of a responsive lab box (0.2s timeout, 200 threads)
python port_scanner.py 127.0.0.1 --ports 1-1024 --timing fast

# Gentle scan of a fragile lab machine (2s timeout, 5 threads)
python port_scanner.py 192.168.1.10 --ports 1-1024 --timing paranoid

# Pick the thread count directly (explicit flags beat the preset)
python port_scanner.py 127.0.0.1 --ports 1-1024 --threads 10 --timeout 2

# Demo — scans a throwaway server on localhost, needs no target
python port_scanner.py --demo

# A target outside the lab list (only with written permission!)
python port_scanner.py scanme.example.com --ports 80,443 --i-have-permission
```

Timing presets: `fast` (0.2s, 200 threads), `normal` (0.5s, 50
threads — the default), `slow` (1.0s, 20 threads), `paranoid` (2.0s,
5 threads). `--timeout` and `--threads` override just their own value
from the preset, so `--timing fast --timeout 1` keeps 200 threads with
a 1-second wait per port.

Exit codes: `0` = scan completed, `2` = usage or authorisation error.

## Tests

```bash
python -m unittest discover -s tests -v
```

37 tests: port-spec parsing, timing presets (values, overrides,
rejections), target authorisation (lab allowed, public refused without
the flag, unresolvable refused), open/closed detection against a
throwaway local server, threaded vs sequential agreement, results
staying in port order, and CLI exit codes. All network activity in
the tests is against `127.0.0.1` only.

## Roadmap

- **v1** — basic TCP connect scan of a target + port range, lab
  targets only, prints open/closed.
- **v2** — service detection: banner grabbing, guess the service on
  open ports. Skipped during the Nov 13–19 pause — still open for a
  future Wednesday.
- **v3 (this release)** — speed: threaded scanning + timing options
  (`--timing` presets, `--threads`, scan rate in the report).
- **v4** — output: JSON report file + scan the most common 100 ports by
  default.
- **v5+** — e.g. UDP scan, or a second offensive lab tool.
