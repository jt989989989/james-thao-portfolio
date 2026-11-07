#!/usr/bin/env python3
"""Password Strength Checker — a defensive, beginner cybersecurity tool.

It scores a password 0-100 and explains *why*, so you can learn what
makes a password strong: length first, then variety, then avoiding
common words and predictable patterns.

Defensive only. It does NOT crack, guess, or test passwords against
any account, and it never sends, saves, or logs a password. Everything
runs locally, offline, with the Python standard library only.
It also never stores the password you type — it is checked in memory
and then discarded.

Safety note: use this to learn, or to check a *new* password you are
about to set. Do not paste a real password you already use into any
tool, website, or chat — including this one, unless it is your own
computer and you are checking it locally. The --demo mode below checks
built-in example passwords instead, so you never have to type a real one.
"""

from __future__ import annotations

import argparse
import getpass
import json
import math
import re
import sys

# Well-known weak passwords / words, lowercased. This is the standard
# public list every strength checker uses — checking *against* it is
# defensive work, not cracking. Exact matches are the worst case.
COMMON_PASSWORDS = {
    "password", "123456", "123456789", "12345678", "12345", "1234567",
    "qwerty", "abc123", "111111", "123123", "admin", "letmein",
    "welcome", "monkey", "dragon", "football", "iloveyou", "master",
    "login", "passw0rd", "password1", "1234", "sunshine", "princess",
    "shadow", "superman", "michael", "jesus", "ninja", "mustang",
}

COMMON_WORDS = {
    "password", "admin", "welcome", "qwerty", "letmein", "monkey",
    "dragon", "football", "iloveyou", "master", "login",
    "princess", "shadow", "superman", "ninja", "mustang",
}

SEQUENCES = (
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
)

DEMO_PASSWORDS = [
    "password",
    "123456",
    "Sunshine2026!",
    "Tr0ub4dor&3",
    "correct horse battery staple",
    "J7#kP9!mQ2$vX8@wL4&zT1a",
]


def rating_for(score: int) -> str:
    if score < 20:
        return "Very Weak"
    if score < 40:
        return "Weak"
    if score < 60:
        return "Fair"
    if score < 80:
        return "Strong"
    return "Very Strong"


def _has_sequential(password: str) -> bool:
    lowered = password.lower()
    for seq in SEQUENCES:
        for i in range(len(seq) - 2):
            chunk = seq[i:i + 3]
            if chunk in lowered or chunk[::-1] in lowered:
                return True
    return False


def _pool_size(password: str) -> int:
    pool = 0
    if re.search(r"[a-z]", password):
        pool += 26
    if re.search(r"[A-Z]", password):
        pool += 26
    if re.search(r"[0-9]", password):
        pool += 10
    if re.search(r"[^A-Za-z0-9]", password):
        pool += 32  # symbols + space, roughly
    return pool or 1


def estimate_crack_time(entropy_bits: float) -> str:
    """Rough offline-guess time at 10 billion guesses/second.

    An estimate for learning, not a guarantee — a password in a leaked
    list can fall instantly no matter its entropy, which is why the
    common-password check matters more than this number.
    """
    guesses = 2 ** entropy_bits
    seconds = guesses / 10_000_000_000
    if seconds < 1:
        return "instantly"
    if seconds < 60:
        return f"about {seconds:.0f} seconds"
    if seconds < 3600:
        return f"about {seconds / 60:.0f} minutes"
    if seconds < 86400:
        return f"about {seconds / 3600:.0f} hours"
    if seconds < 31557600:
        return f"about {seconds / 86400:.0f} days"
    years = seconds / 31557600
    if years < 1000:
        return f"about {years:.0f} years"
    return "thousands of years or more"


def analyze_password(password: str, username: str = "") -> dict:
    """Score a password and explain the result. No I/O, no storage."""
    if not password:
        return {
            "score": 0, "rating": "Very Weak", "length": 0,
            "entropy_bits": 0.0, "estimated_crack_time": "instantly",
            "issues": ["empty password"],
            "suggestions": ["Choose a password at least 12 characters long."],
            "checks": {},
        }

    checks: dict[str, bool] = {
        "length_8_plus": len(password) >= 8,
        "length_12_plus": len(password) >= 12,
        "length_16_plus": len(password) >= 16,
        "has_lowercase": bool(re.search(r"[a-z]", password)),
        "has_uppercase": bool(re.search(r"[A-Z]", password)),
        "has_digit": bool(re.search(r"[0-9]", password)),
        "has_symbol": bool(re.search(r"[^A-Za-z0-9]", password)),
    }

    issues: list[str] = []
    suggestions: list[str] = []

    # Length is the biggest factor: 10 points at 8 chars, +2 per extra
    # char, capped at 40 points (reached at 23 characters).
    length_score = 0
    if len(password) >= 8:
        length_score = min(40, 10 + 2 * (len(password) - 8))
    if len(password) < 8:
        issues.append("too short (under 8 characters)")
        suggestions.append("Make it at least 12 characters long — length helps most.")
    elif len(password) < 12:
        suggestions.append("Longer is stronger — aim for 16+ characters, or a passphrase.")

    # Variety: 10 points for each character type present.
    variety_score = sum(
        10 for key in ("has_lowercase", "has_uppercase", "has_digit", "has_symbol")
        if checks[key]
    )
    for key, label in (
        ("has_lowercase", "a lowercase letter"),
        ("has_uppercase", "an uppercase letter"),
        ("has_digit", "a number"),
        ("has_symbol", "a symbol such as ! # $ or a space"),
    ):
        if not checks[key]:
            suggestions.append(f"Add {label} to increase variety.")

    score = length_score + variety_score

    lowered = password.lower()
    if lowered in COMMON_PASSWORDS:
        score -= 40
        issues.append("this is one of the most common passwords — attackers try it first")
        suggestions.append("Do not use a common password; pick something unique to you.")
    elif any(word in lowered for word in COMMON_WORDS if len(word) >= 4):
        score -= 15
        issues.append("contains a common word")
        suggestions.append("Avoid common words; a random passphrase works better.")

    if _has_sequential(password):
        score -= 15
        issues.append("contains a predictable sequence (abc, 123, qwerty, …)")
        suggestions.append("Avoid sequences and keyboard patterns.")

    if re.search(r"(.)\1{2,}", password):
        score -= 10
        issues.append("has a character repeated 3+ times in a row")
        suggestions.append("Avoid repeating the same character.")

    if username and username.lower() in lowered and len(username) >= 3:
        score -= 15
        issues.append("contains your username")
        suggestions.append("Do not put your name or username in a password.")

    types_used = sum(
        1 for key in ("has_lowercase", "has_uppercase", "has_digit", "has_symbol")
        if checks[key]
    )
    if types_used == 1 and len(password) >= 8:
        score -= 10
        issues.append("uses only one type of character")
        suggestions.append("Mix character types — letters, numbers, and symbols.")

    score = max(0, min(100, score))
    entropy = len(password) * math.log2(_pool_size(password))

    if not suggestions:
        suggestions.append("Good — keep it unique, and use a password manager to remember it.")

    return {
        "score": score,
        "rating": rating_for(score),
        "length": len(password),
        "entropy_bits": round(entropy, 1),
        "estimated_crack_time": estimate_crack_time(entropy),
        "issues": issues,
        "suggestions": suggestions,
        "checks": checks,
    }


def format_result(result: dict, *, show_password: bool = False, password: str = "") -> str:
    lines = [
        f"Score: {result['score']}/100 — {result['rating']}",
        f"Length: {result['length']} characters",
        f"Estimated entropy: {result['entropy_bits']} bits",
        f"Estimated offline crack time: {result['estimated_crack_time']} (rough estimate only)",
    ]
    if show_password:
        lines.append(f"Password checked: {password}")
    if result["issues"]:
        lines.append("Issues:")
        lines.extend(f"  - {issue}" for issue in result["issues"])
    lines.append("Suggestions:")
    lines.extend(f"  - {suggestion}" for suggestion in result["suggestions"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a password's strength locally. Nothing is sent or saved."
    )
    parser.add_argument("--password", default="",
                        help="Password to check (shows in shell history — prefer the hidden prompt)")
    parser.add_argument("--username", default="",
                        help="Your username, to warn if it appears in the password")
    parser.add_argument("--demo", action="store_true",
                        help="Check the built-in example passwords instead of a real one")
    parser.add_argument("--json", action="store_true", help="Print the result as JSON")
    args = parser.parse_args(argv)

    if args.demo:
        for example in DEMO_PASSWORDS:
            result = analyze_password(example)
            print(f"\n{example!r}")
            print(format_result(result))
        print("\nDemo done. These are example passwords, not real accounts.")
        return 0

    password = args.password
    if not password:
        try:
            password = getpass.getpass("Enter a password to check (hidden, never saved): ")
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.", file=sys.stderr)
            return 1
    elif args.password:
        print("Warning: --password shows up in shell history. "
              "Use the hidden prompt next time.", file=sys.stderr)

    if not password:
        print("error: empty password.", file=sys.stderr)
        return 2

    result = analyze_password(password, username=args.username)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_result(result))
    # The password variable goes out of scope here; nothing was written anywhere.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
