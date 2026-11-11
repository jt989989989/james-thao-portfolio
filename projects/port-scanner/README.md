# Port Scanner — v1.0.0

A basic TCP connect port scanner for **lab targets only** — the first
tool in the Wednesday cybersecurity track, built as a tool to help beginners learns
penetration testing.

It scans a target host over a port range (or a list of ports) and prints
which ports are OPEN and which are CLOSED, with a short summary.

## The authorisation rule (read this first)

This tool is ONLY for targets you own or has explicit permission to
test:

- `localhost` / `127.0.0.1` / `::1`
- Private lab addresses — `10.x.x.x`, `172.16.x.x`–`172.31.x.x`,
  `192.168.x.x`, link-local `169.254.x.x` (his own VMs and lab machines)
- Intentionally vulnerable lab apps (DVWA, Metasploitable) and
  HackTheBox / TryHackMe machines he is assigned

By default the scanner **refuses** any other target. To scan a named
target outside that list you must pass `--i-have-permission`, which means
you own the target or have the owner's written permission to test it —
and the scanner still prints a warning. Never scan a system you do not
own or have permission to test: unauthorised scanning can break the law
where you live.

The scanner never brute-forces logins, never tries exploits, and never
floods a target — it is a plain sequential TCP connect scan, one short
connection attempt per port.

## How to run it

Python 3.10+ only, standard library only, nothing to install.

```bash
# Scan the default range (ports 1–1024) on localhost
python port_scanner.py 127.0.0.1

# Scan specific ports on a lab machine
python port_scanner.py 192.168.1.10 --ports 22,80,443

# A wider range with a longer per-port timeout
python port_scanner.py localhost --ports 1-5000 --timeout 1

# Demo — scans a throwaway server on localhost, needs no target
python port_scanner.py --demo

# A target outside the lab list (only with written permission!)
python port_scanner.py scanme.example.com --ports 80,443 --i-have-permission
```

Exit codes: `0` = scan completed, `2` = usage or authorisation error.

## Tests

```bash
python -m unittest discover -s tests -v
```

20 tests: port-spec parsing, target authorisation (lab allowed, public
refused without the flag, unresolvable refused), open/closed detection
against a throwaway local server, and CLI exit codes. All network
activity in the tests is against `127.0.0.1` only.

## Roadmap

- **v1 (this release)** — basic TCP connect scan of a target + port
  range, lab targets only, prints open/closed.
- **v2** — service detection: banner grabbing, guess the service on
  open ports.
- **v3** — speed: threaded scanning + timing options.
- **v4** — output: JSON report file + scan the most common 100 ports by
  default.
- **v5+** — e.g. UDP scan, or a second offensive lab tool.
