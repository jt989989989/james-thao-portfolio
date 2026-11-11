#!/usr/bin/env python3
"""Port Scanner v1 — a basic TCP connect scanner for lab targets only.

Scans a target host over a port range (or a list of ports) and prints
which ports are OPEN and which are CLOSED, with a short summary.

This is an offensive-security learning tool I built for my own
penetration-testing practice. It is ONLY for targets I own or have
explicit permission to test:

  - localhost / 127.0.0.1 / ::1
  - private lab addresses (10.x.x.x, 172.16.x.x–172.31.x.x, 192.168.x.x,
    link-local 169.254.x.x) — my own VMs and lab machines
  - intentionally vulnerable lab apps (DVWA, Metasploitable) and
    HackTheBox / TryHackMe machines I am assigned

By default the scanner REFUSES any other target. To scan a named target
outside that list you must pass --i-have-permission, which means you
have the owner's written permission to test it — and the scanner still
prints a warning reminding you of that. Never scan a system you do not
own or have permission to test: unauthorised scanning can break the law
where you live.

The scanner never brute-forces logins, never tries exploits, and never
floods a target — it is a plain sequential TCP connect scan, one short
connection attempt per port.

Usage:
    python port_scanner.py 127.0.0.1 --ports 1-1024
    python port_scanner.py localhost --ports 22,80,443
    python port_scanner.py 192.168.1.10 --ports 1-100 --timeout 1
    python port_scanner.py scanme.example.com --ports 80,443 --i-have-permission
    python port_scanner.py --demo        # scans a local test server; needs no target

Exit codes: 0 = scan completed, 2 = usage or authorisation error.
Python 3.10+ only, standard library only, no network calls except the
scan itself.
"""

from __future__ import annotations

import argparse
import ipaddress
import socket
import sys
import threading
import time
from dataclasses import dataclass

VERSION = "1.0.0"

DEFAULT_PORT_SPEC = "1-1024"
DEFAULT_TIMEOUT = 0.5
MAX_PORTS = 65535

# Lab networks the scanner will touch without the permission flag:
# loopback, RFC 1918 private ranges, and link-local. Everything else
# needs --i-have-permission.
LAB_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fe80::/10"),
]

LAB_TARGET_EXAMPLES = (
    "localhost, your own VMs, DVWA / Metasploitable, or a "
    "HackTheBox / TryHackMe machine"
)


@dataclass
class PortResult:
    port: int
    is_open: bool


def parse_ports(spec: str) -> list[int]:
    """Parse a port spec like '80', '1-1024', or '22,80,443' into a
    sorted list of unique port numbers. Raises ValueError on bad input.
    """
    ports: set[int] = set()
    if not spec or not spec.strip():
        raise ValueError("empty port specification")
    for part in spec.split(","):
        part = part.strip()
        if not part:
            raise ValueError(f"empty item in port specification: {spec!r}")
        if "-" in part:
            start_s, _, end_s = part.partition("-")
            try:
                start, end = int(start_s), int(end_s)
            except ValueError:
                raise ValueError(f"not a port range: {part!r}") from None
            if not (1 <= start <= 65535 and 1 <= end <= 65535):
                raise ValueError(f"ports must be 1-65535: {part!r}")
            if start > end:
                raise ValueError(f"range starts after it ends: {part!r}")
            ports.update(range(start, end + 1))
        else:
            try:
                port = int(part)
            except ValueError:
                raise ValueError(f"not a port number: {part!r}") from None
            if not 1 <= port <= 65535:
                raise ValueError(f"port must be 1-65535: {port}")
            ports.add(port)
    if len(ports) > MAX_PORTS:
        raise ValueError(f"too many ports (max {MAX_PORTS})")
    return sorted(ports)


def resolve_target(target: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Resolve a hostname or IP string to an IP address.

    Raises ValueError if it cannot be resolved.
    """
    try:
        return ipaddress.ip_address(target)
    except ValueError:
        pass
    try:
        info = socket.getaddrinfo(target, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise ValueError(f"cannot resolve target: {target!r}") from None
    return ipaddress.ip_address(info[0][4][0])


def is_lab_target(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True if the address is loopback, private (RFC 1918), or link-local."""
    return any(address in network for network in LAB_NETWORKS)


def authorize_target(
    target: str, i_have_permission: bool
) -> tuple[bool, str]:
    """Check whether a target may be scanned.

    Returns (allowed, message). Lab targets are always allowed; any other
    target needs --i-have-permission, and unresolvable targets are refused.
    """
    try:
        address = resolve_target(target)
    except ValueError as exc:
        return False, str(exc)
    if is_lab_target(address):
        return True, f"{target} resolves to {address} (lab target — allowed)"
    if i_have_permission:
        return (
            True,
            f"WARNING: {target} resolves to {address}, which is NOT a lab"
            " target. Scanning because you passed --i-have-permission —"
            " make sure you really have the owner's permission.",
        )
    return (
        False,
        f"refusing to scan {target} ({address}): not a lab target."
        f" Lab targets are {LAB_TARGET_EXAMPLES}. If you own this target"
        " or have written permission to test it, re-run with"
        " --i-have-permission.",
    )


def scan_port(host: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> bool:
    """True if a TCP connect to host:port succeeds (port is open)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def scan(
    host: str, ports: list[int], timeout: float = DEFAULT_TIMEOUT
) -> tuple[list[PortResult], float]:
    """Scan ports on host in order. Returns (results, elapsed seconds)."""
    started = time.monotonic()
    results = [PortResult(port, scan_port(host, port, timeout)) for port in ports]
    return results, time.monotonic() - started


def format_results(
    host: str, results: list[PortResult], elapsed: float
) -> str:
    """Human-readable scan report."""
    lines = [f"Scan of {host} — {len(results)} port(s) in {elapsed:.2f}s:"]
    for result in results:
        state = "OPEN  " if result.is_open else "closed"
        lines.append(f"  {result.port:>5}/tcp  {state}")
    open_ports = [r.port for r in results if r.is_open]
    lines.append(
        f"\n{len(open_ports)} open, {len(results) - len(open_ports)} closed."
    )
    if open_ports:
        lines.append("Open ports: " + ", ".join(str(p) for p in open_ports))
    return "\n".join(lines)


def run_demo() -> int:
    """Demo: start a throwaway TCP server on localhost, scan it and its
    neighbours, and show the open port being found. No external target.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    demo_port = server.getsockname()[1]

    def _accept_forever() -> None:
        while True:
            try:
                conn, _ = server.accept()
                conn.close()
            except OSError:
                return

    thread = threading.Thread(target=_accept_forever, daemon=True)
    thread.start()
    try:
        ports = [demo_port - 1, demo_port, demo_port + 1]
        ports = [p for p in ports if 1 <= p <= 65535]
        print(f"Demo server listening on 127.0.0.1:{demo_port}")
        results, elapsed = scan("127.0.0.1", ports, timeout=DEFAULT_TIMEOUT)
        print(format_results("127.0.0.1 (demo server)", results, elapsed))
        return 0
    finally:
        server.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Basic TCP connect port scanner — lab targets only"
        " unless --i-have-permission (see README for the rules)."
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Host to scan (IP or hostname). Lab targets only by default.",
    )
    parser.add_argument(
        "--ports",
        default=DEFAULT_PORT_SPEC,
        help="Ports to scan: '80', '1-1024', or '22,80,443'"
        f" (default: {DEFAULT_PORT_SPEC}).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Seconds to wait per port (default: {DEFAULT_TIMEOUT}).",
    )
    parser.add_argument(
        "--i-have-permission",
        action="store_true",
        help="Confirm you own the target or have written permission to"
        " test it. Required for any target that is not a lab target.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Scan a throwaway server on localhost; needs no target.",
    )
    args = parser.parse_args(argv)

    if args.demo:
        return run_demo()
    if not args.target:
        parser.error("a target is required (or use --demo)")
    if args.timeout <= 0:
        print("error: --timeout must be greater than 0", file=sys.stderr)
        return 2

    try:
        ports = parse_ports(args.ports)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    allowed, message = authorize_target(args.target, args.i_have_permission)
    print(message)
    if not allowed:
        return 2

    results, elapsed = scan(args.target, ports, timeout=args.timeout)
    print(format_results(args.target, results, elapsed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
