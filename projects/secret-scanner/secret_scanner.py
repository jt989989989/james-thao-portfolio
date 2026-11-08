#!/usr/bin/env python3
"""Secret Scanner — a defensive tool that finds leaked secrets in code.

It recursively scans a directory for common secret patterns — AWS keys,
GitHub and Slack tokens, JWTs, private keys, Stripe live keys, password
assignments, and suspicious high-entropy strings — and reports each one
with its file, line number, rule, severity, and a short explanation.

Defensive only. It does NOT crack, guess, or test secrets against any
account, and it never sends anything anywhere: no network calls, no
uploads, everything runs locally with the Python standard library only.
It only reads files, and it only shows a redacted preview of a match,
never the full secret.

Scope: scan only code you own or have permission to scan — your own
projects, or a codebase you were explicitly asked to audit. Never point
it at someone else's private code without permission.

Usage:
    python secret_scanner.py [path] [--exclude PATTERN ...] [--json]

    python secret_scanner.py samples/   # demo scan of the fictional samples
    python secret_scanner.py . --json   # scan this folder, JSON output

Exit code is 1 when any high or medium finding is present, 0 when the
scan is clean (or only low-severity findings, which are just hints).
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import math
import os
import re
import sys
from dataclasses import dataclass

# Directories skipped at every depth, unless the user points at one directly.
DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
}

# Values that look like a password assignment but are clearly placeholders.
PLACEHOLDER_VALUES = {
    "changeme",
    "change-me",
    "change_me",
    "your-password",
    "your_password",
    "your-password-here",
    "your_password_here",
    "password",
    "passw0rd",
    "xxx",
    "xxxx",
    "todo",
    "example",
    "placeholder",
    "secret",
}

# (rule id, compiled pattern, severity, explanation)
# Severity: high = almost certainly a live secret; medium = a real
# credential that should not be in code; low = suspicious, needs a look.
REGEX_RULES: list[tuple[str, "re.Pattern[str]", str, str]] = [
    (
        "aws-access-key",
        re.compile(r"AKIA[0-9A-Z]{16}"),
        "high",
        "AWS access key ID — identifies an AWS account and is half of a"
        " credential pair. Revoke it and issue a new one.",
    ),
    (
        "aws-secret-key",
        re.compile(
            r"aws_secret_access_key\s*[:=]\s*['\"][A-Za-z0-9/+=]{40}['\"]",
            re.IGNORECASE,
        ),
        "high",
        "AWS secret access key — the other half of an AWS credential pair."
        " Revoke it immediately; anyone with both keys controls the account.",
    ),
    (
        "github-token",
        re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}"),
        "high",
        "Classic GitHub personal access token — grants access to the"
        " account or organisation it was made for. Revoke it on GitHub.",
    ),
    (
        "github-fine-grained-token",
        re.compile(r"github_pat_[A-Za-z0-9_]{22,}"),
        "high",
        "Fine-grained GitHub personal access token — grants access to the"
        " repositories it was scoped to. Revoke it on GitHub.",
    ),
    (
        "slack-token",
        re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
        "high",
        "Slack token — can read messages and act as the user or bot that"
        " owns it. Revoke it in the Slack admin settings.",
    ),
    (
        "jwt",
        re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
        "high",
        "JSON Web Token — a bearer token. Anyone holding it can act as"
        " the user it was issued to until it expires. Invalidate the"
        " session and rotate the signing secret.",
    ),
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
        "high",
        "Private key — the key itself must never be in a codebase. Rotate"
        " it and replace every certificate or login that used it.",
    ),
    (
        "stripe-live-key",
        re.compile(r"(?:sk|rk)_live_[A-Za-z0-9]{16,}"),
        "high",
        "Stripe live secret key — can move real money. Roll it in the"
        " Stripe dashboard immediately.",
    ),
]

# password = "something", password: 'something', passwd, pwd — case-insensitive.
PASSWORD_RE = re.compile(
    r"(?:password|passwd|pwd)\s*[:=]\s*['\"](?P<value>[^'\"]+)['\"]",
    re.IGNORECASE,
)

# Quoted strings, for the generic high-entropy check.
QUOTED_RE = re.compile(r"""['"`]([^'"`]{20,})['"`]""")

ENTROPY_MIN_LENGTH = 20
ENTROPY_THRESHOLD = 4.5


@dataclass
class Finding:
    path: str
    line_no: int
    rule: str
    severity: str
    message: str
    snippet: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line_no,
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "match": self.snippet,
        }


def redact(match: str) -> str:
    """Show only the edges of a match, so the secret itself stays hidden."""
    if len(match) <= 8:
        return "********"
    return f"{match[:4]}***{match[-2:]}"


def shannon_entropy(text: str) -> float:
    """Shannon entropy in bits per character; random strings score high."""
    if not text:
        return 0.0
    counts: dict[str, int] = {}
    for ch in text:
        counts[ch] = counts.get(ch, 0) + 1
    entropy = 0.0
    for count in counts.values():
        p = count / len(text)
        entropy -= p * math.log2(p)
    return entropy


def check_line(line: str) -> list[dict]:
    """Return the findings on one line (rule, severity, message, snippet).

    The generic high-entropy check only runs when no specific rule
    matched the line, so one secret is reported once, by its best rule.
    """
    findings: list[dict] = []
    matched_specific = False

    for rule_id, pattern, severity, message in REGEX_RULES:
        match = pattern.search(line)
        if match:
            findings.append(
                {
                    "rule": rule_id,
                    "severity": severity,
                    "message": message,
                    "snippet": redact(match.group(0)),
                }
            )
            matched_specific = True

    match = PASSWORD_RE.search(line)
    if match:
        value = match.group("value")
        if len(value) >= 4 and value.lower() not in PLACEHOLDER_VALUES:
            findings.append(
                {
                    "rule": "password-assignment",
                    "severity": "medium",
                    "message": "Password stored in plain text in code."
                    " Move it to an environment variable or a secrets"
                    " manager, and change the password itself.",
                    "snippet": redact(value),
                }
            )
            matched_specific = True

    if not matched_specific:
        for quoted in QUOTED_RE.findall(line):
            if len(quoted) >= ENTROPY_MIN_LENGTH and (
                shannon_entropy(quoted) >= ENTROPY_THRESHOLD
            ):
                findings.append(
                    {
                        "rule": "generic-high-entropy",
                        "severity": "low",
                        "message": "Long, high-entropy string — it looks"
                        " random, which often means a token or key. Check"
                        " whether it is a secret; ignore it if it is just"
                        " data.",
                        "snippet": redact(quoted),
                    }
                )
                break

    return findings


def _is_binary(path: str) -> bool:
    """True if the file looks binary (a NUL byte in the first chunk)."""
    try:
        with open(path, "rb") as handle:
            return b"\x00" in handle.read(8192)
    except OSError:
        return True


def scan_file(path: str, display_path: str | None = None) -> list[Finding]:
    """Scan one file, returning its findings (empty for binary files)."""
    if _is_binary(path):
        return []
    findings: list[Finding] = []
    try:
        with open(path, encoding="utf-8", errors="strict") as handle:
            lines = handle.readlines()
    except (OSError, UnicodeDecodeError):
        return []
    for line_no, line in enumerate(lines, start=1):
        for hit in check_line(line):
            findings.append(
                Finding(
                    path=display_path or path,
                    line_no=line_no,
                    rule=hit["rule"],
                    severity=hit["severity"],
                    message=hit["message"],
                    snippet=hit["snippet"],
                )
            )
    return findings


def _excluded(rel_path: str, exclude: list[str]) -> bool:
    parts = rel_path.replace(os.sep, "/").split("/")
    return any(
        fnmatch.fnmatch(rel_path, pattern)
        or fnmatch.fnmatch(rel_path.replace(os.sep, "/"), pattern)
        or any(fnmatch.fnmatch(part, pattern) for part in parts)
        for pattern in exclude
    )


def scan_directory(root: str, exclude: list[str] | None = None) -> list[Finding]:
    """Recursively scan a directory, skipping VCS, deps, and caches."""
    exclude = exclude or []
    findings: list[Finding] = []
    if os.path.isfile(root):
        return scan_file(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in DEFAULT_SKIP_DIRS
        )
        for name in sorted(filenames):
            full_path = os.path.join(dirpath, name)
            rel_path = os.path.relpath(full_path, root)
            if _excluded(rel_path, exclude):
                continue
            findings.extend(scan_file(full_path, display_path=rel_path))
    return findings


def format_text(findings: list[Finding]) -> str:
    lines = []
    for finding in findings:
        lines.append(
            f"{finding.path}:{finding.line_no} [{finding.severity.upper()}]"
            f" {finding.rule} — {finding.message} (match: {finding.snippet})"
        )
    high = sum(1 for f in findings if f.severity == "high")
    medium = sum(1 for f in findings if f.severity == "medium")
    low = sum(1 for f in findings if f.severity == "low")
    lines.append(
        f"\n{len(findings)} finding(s): {high} high, {medium} medium,"
        f" {low} low."
    )
    if high or medium:
        lines.append("Secrets found — rotate or revoke them, then remove"
                    " them from the code and its history.")
    else:
        lines.append("No high or medium findings. Low findings are hints"
                    " only — check them, then ignore them if they are data.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan a directory for leaked secrets (defensive tool;"
        " reads only, no network, stdlib only)."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="File or directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Skip files matching this glob (repeatable), e.g."
        " --exclude 'tests/*'.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print findings as JSON instead of text.",
    )
    args = parser.parse_args(argv)

    if not os.path.exists(args.path):
        print(f"error: no such file or directory: {args.path}", file=sys.stderr)
        return 2

    findings = scan_directory(args.path, exclude=args.exclude)

    if args.json:
        print(json.dumps([f.to_dict() for f in findings], indent=2))
    else:
        print(format_text(findings))

    if any(f.severity in ("high", "medium") for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
