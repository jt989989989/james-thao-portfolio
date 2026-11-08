#!/usr/bin/env python3
"""Passive Recon Scanner — first-step recon for bug bounty and security work.

Given a domain, this tool does three passive things:

1. Subdomain enumeration from Certificate Transparency, via crt.sh.
   Certificates are public records, so this only reads data that is
   already published — it never probes the target directly.
2. DNS liveness check for each subdomain (does it resolve?).
3. Security headers + TLS check on the main domain — one normal HTTPS
   request, graded like a report card.

This is a *passive* tool: no port scanning, no directory brute-forcing,
no exploitation, no login attempts. Only use it on domains you own or
that are in scope for a bug bounty program with a safe harbor.

Usage:
    python recon_scanner.py example.com
    python recon_scanner.py example.com --json
    python recon_scanner.py example.com --subdomains-only
    python recon_scanner.py --demo        # offline demo from samples/
"""

import argparse
import json
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

CRT_SH_URL = "https://crt.sh/?q=%.{domain}&output=json"
USER_AGENT = "ReconScanner/1.0 (passive recon; bug-bounty research)"

# header name -> (display name, why it matters)
GRADED_HEADERS = {
    "strict-transport-security": (
        "Strict-Transport-Security",
        "Forces browsers to use HTTPS, blocking downgrade attacks.",
    ),
    "content-security-policy": (
        "Content-Security-Policy",
        "Limits where scripts and content can load from, blocking XSS.",
    ),
    "x-frame-options": (
        "X-Frame-Options",
        "Stops the site being embedded in an iframe (clickjacking).",
    ),
    "x-content-type-options": (
        "X-Content-Type-Options",
        "Stops browsers guessing content types (MIME sniffing).",
    ),
    "referrer-policy": (
        "Referrer-Policy",
        "Controls how much URL information leaks to other sites.",
    ),
    "permissions-policy": (
        "Permissions-Policy",
        "Restricts powerful browser features like camera and microphone.",
    ),
}

# Grade thresholds: how many of the 6 headers are present.
GRADE_MAP = [(6, "A"), (5, "B"), (4, "C"), (3, "D")]

DOMAIN_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$")


def clean_domain(raw):
    """Strip a scheme, path, port, or trailing dot from user input."""
    domain = raw.strip().lower()
    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.split("/")[0].split(":")[0].rstrip(".")
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def valid_domain(domain):
    """True for a plausible domain name (labels, dots, no IP, no garbage)."""
    return bool(DOMAIN_RE.match(domain))


def parse_crtsh_response(entries, domain):
    """Extract a sorted, deduped list of subdomains from crt.sh JSON.

    crt.sh returns a list of certificate records; each has a
    ``name_value`` field that can hold several names separated by
    newlines, sometimes with a ``*.`` wildcard prefix. Only names that
    are the domain itself or a subdomain of it are kept.
    """
    found = set()
    domain = domain.lower()
    for entry in entries or []:
        name_value = entry.get("name_value") or ""
        for name in name_value.splitlines():
            name = name.strip().lower().lstrip("*.")
            if not name:
                continue
            if name == domain or name.endswith("." + domain):
                found.add(name)
    return sorted(found)


def fetch_crtsh(domain, timeout=30):
    """Query crt.sh for certificates issued for %.domain. Returns a list."""
    url = CRT_SH_URL.format(domain=domain)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def check_dns(hostname, timeout=5):
    """Resolve a hostname. Returns a sorted list of IPs, or []."""
    try:
        socket.setdefaulttimeout(timeout)
        infos = socket.getaddrinfo(hostname, 443, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, socket.timeout, OSError):
        return []
    return sorted({info[4][0] for info in infos})


def fetch_headers(domain, timeout=15):
    """One HTTPS request to the main domain.

    Returns (headers_dict, tls_version). Headers are lowercased keys.
    Tries a HEAD request first, falls back to GET.
    """
    context = ssl.create_default_context()
    tls_version = None
    headers = {}
    for method in ("HEAD", "GET"):
        try:
            request = urllib.request.Request(
                "https://" + domain,
                method=method,
                headers={"User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(
                request, timeout=timeout, context=context
            ) as response:
                headers = {k.lower(): v for k, v in response.headers.items()}
                # Re-open a raw TLS connection to read the negotiated version.
                with socket.create_connection(
                    (domain, 443), timeout=timeout
                ) as sock:
                    with context.wrap_socket(
                        sock, server_hostname=domain
                    ) as tls_sock:
                        tls_version = tls_sock.version()
            return headers, tls_version
        except Exception:
            continue
    return headers, tls_version


def grade_headers(headers):
    """Grade the 6 security headers. Returns (grade, score, detail dict)."""
    detail = {}
    present = 0
    for name, (display, why) in GRADED_HEADERS.items():
        value = headers.get(name)
        is_present = value is not None and value.strip() != ""
        if is_present:
            present += 1
        detail[name] = {
            "display": display,
            "present": is_present,
            "value": value if is_present else None,
            "why": why,
        }
    grade = "F"
    for minimum, letter in GRADE_MAP:
        if present >= minimum:
            grade = letter
            break
    return grade, present, detail


def build_report(domain, subdomains, headers, tls_version, dns_skipped=False,
                 headers_checked=True):
    """Assemble the full report dict from the gathered pieces."""
    sub_list = []
    live_count = 0
    for name in subdomains:
        if dns_skipped:
            sub_list.append({"name": name, "live": None, "ips": []})
        else:
            ips = check_dns(name)
            if ips:
                live_count += 1
            sub_list.append({"name": name, "live": bool(ips), "ips": ips})
    if headers_checked:
        grade, present, detail = grade_headers(headers)
        tls_ok = tls_version in ("TLSv1.2", "TLSv1.3")
        score = f"{present}/{len(GRADED_HEADERS)}"
    else:
        grade, score, detail, tls_ok = None, None, {}, None
    return {
        "domain": domain,
        "subdomains": sub_list,
        "subdomain_count": len(sub_list),
        "live_count": live_count,
        "dns_checked": not dns_skipped,
        "headers": detail,
        "headers_checked": headers_checked,
        "headers_grade": grade,
        "headers_score": score,
        "tls_version": tls_version,
        "tls_ok": tls_ok,
    }


def format_text(report):
    """Render the report as a readable text report."""
    lines = []
    lines.append(f"Passive recon report for {report['domain']}")
    lines.append("=" * (len(lines[0])))
    lines.append("")
    if report["dns_checked"]:
        lines.append(
            f"Subdomains found: {report['subdomain_count']} "
            f"({report['live_count']} live)"
        )
    else:
        lines.append(
            f"Subdomains found: {report['subdomain_count']} "
            "[DNS check skipped]"
        )
    for sub in report["subdomains"]:
        if not report["dns_checked"]:
            status = "dns not checked"
        elif sub["live"]:
            status = "live — " + ", ".join(sub["ips"])
        else:
            status = "does not resolve"
        lines.append(f"  - {sub['name']} ({status})")
    lines.append("")
    if not report["headers_checked"]:
        lines.append("Security headers: skipped (--subdomains-only)")
        lines.append("")
        lines.append("TLS: skipped (--subdomains-only)")
        return "\n".join(lines)
    lines.append(
        f"Security headers: grade {report['headers_grade']} "
        f"({report['headers_score']} present)"
    )
    for name, info in report["headers"].items():
        mark = "OK " if info["present"] else "MISS"
        value = f" — {info['value']}" if info["present"] else ""
        lines.append(f"  [{mark}] {info['display']}{value}")
        if not info["present"]:
            lines.append(f"         {info['why']}")
    lines.append("")
    tls = report["tls_version"] or "unknown"
    tls_mark = "OK " if report["tls_ok"] else "WARN"
    lines.append(f"TLS: [{tls_mark}] {tls}")
    if not report["tls_ok"] and report["tls_version"]:
        lines.append("       TLS 1.2 or 1.3 is expected; older versions are weak.")
    return "\n".join(lines)


def run_demo():
    """Offline demo: parse the saved crt.sh sample and grade the saved headers."""
    base = Path(__file__).resolve().parent
    with open(base / "samples" / "sample_crtsh.json", encoding="utf-8") as f:
        entries = json.load(f)
    with open(base / "samples" / "sample_headers.json", encoding="utf-8") as f:
        sample = json.load(f)
    domain = sample["domain"]
    subdomains = parse_crtsh_response(entries, domain)
    headers = {k.lower(): v for k, v in sample["headers"].items()}
    return build_report(
        domain, subdomains, headers, sample.get("tls_version"), dns_skipped=True
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Passive recon scanner — subdomains (crt.sh), DNS liveness, "
        "and security headers / TLS for a domain you own or that is in scope."
    )
    parser.add_argument("domain", nargs="?", help="Domain to recon, e.g. example.com")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument(
        "--subdomains-only",
        action="store_true",
        help="Only list subdomains and DNS liveness; skip the headers/TLS check",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Offline demo using the saved samples (no network needed)",
    )
    args = parser.parse_args(argv)

    if args.demo:
        report = run_demo()
    else:
        if not args.domain:
            parser.error("a domain is required unless --demo is used")
        domain = clean_domain(args.domain)
        if not valid_domain(domain):
            print(f"error: '{args.domain}' does not look like a valid domain", file=sys.stderr)
            return 2
        try:
            entries = fetch_crtsh(domain)
        except (urllib.error.URLError, socket.timeout, OSError) as exc:
            print(f"error: could not reach crt.sh: {exc}", file=sys.stderr)
            return 1
        subdomains = parse_crtsh_response(entries, domain)
        headers, tls_version = ({}, None)
        headers_checked = not args.subdomains_only
        if headers_checked:
            headers, tls_version = fetch_headers(domain)
        report = build_report(
            domain, subdomains, headers, tls_version,
            headers_checked=headers_checked,
        )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
