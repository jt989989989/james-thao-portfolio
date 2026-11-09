#!/usr/bin/env python3
"""Phishing Email Detector — local, offline email phishing classifier.

Scores an email as LEGITIMATE / SUSPICIOUS / PHISHING and explains why.

How it works
------------
Two layers, both running entirely on your machine (no network, no API key,
no data leaves the device):

1. A small Naive Bayes word model, trained at start-up on built-in
   fictional sample emails (10 phishing, 10 legitimate). It returns a
   phishing probability from the words in the message.
2. Rule-based signals a word model alone would miss: urgent or threatening
   language, credential / payment requests, a Reply-To address that does
   not match the sender, links whose shown text differs from their real
   destination, URL shorteners and IP-literal hosts, and risky attachments.

The final 0-100 score blends the two layers 50/50. Verdict bands:
0-39 LEGITIMATE, 40-69 SUSPICIOUS, 70-100 PHISHING.

Usage
-----
    python phishing_detector.py <email-file.txt>
    python phishing_detector.py --demo          # score every built-in sample
    python phishing_detector.py --sample phishing_01_account_locked
    python phishing_detector.py email.txt --json
    python phishing_detector.py --model-info

Email files are plain text with simple headers (From / Reply-To / Subject /
Date), a blank line, then the body. Attachment lines look like
"Attachment: invoice.zip (184 KB)".

Safety note
-----------
This is a portfolio demo and a learning tool. The built-in training data and
samples are fictional (brands like Northbank and CloudDesk, .example
domains). It is not a substitute for a real email security gateway — a
low score never proves an email is safe, and a high score is a reason to
stop and check through a known-good channel, not proof of a crime.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Built-in training corpus (fictional emails only — no real mail, no personal data)
# ---------------------------------------------------------------------------

PHISHING_TRAINING = [
    "URGENT: Your account will be suspended within 24 hours. Verify your "
    "password immediately by clicking the link below or you will lose access.",
    "Congratulations! You have won a $1,000 gift card. Claim your prize now "
    "before it expires. Pay only a small shipping fee with your credit card.",
    "Your payment failed. Update your billing details and credit card number "
    "now to avoid service interruption. Confirm your account immediately.",
    "Dear Customer, unusual activity detected on your account. Your account "
    "has been locked for your security. Sign in here to restore access now.",
    "Action required: your mailbox is almost full. Click here to verify your "
    "login credentials and increase your storage, otherwise your email will "
    "be disabled today.",
    "You have received a secure document. Download the attachment and enter "
    "your password to view it. This link expires in 2 hours, act now.",
    "Your package could not be delivered. Pay the customs fee now using the "
    "link below or your parcel will be returned. Urgent, do not delay.",
    "Final warning: your subscription will be cancelled today unless you "
    "confirm your payment information. Update now to keep your account.",
    "We detected a login attempt from an unknown device. If this was not "
    "you, verify your identity immediately by entering your password here.",
    "Your refund of $450 is ready. Confirm your bank account details now to "
    "receive the money. This offer expires tonight, claim it immediately.",
]

LEGIT_TRAINING = [
    "Hi Alex, thanks for your order. Your parcel shipped this morning and "
    "should arrive Thursday. You can track it from your account on our site.",
    "Team, a reminder that our weekly planning meeting is Tuesday at 10am "
    "in room 3. Please bring your updates and any blockers to discuss.",
    "Hello, your monthly statement is ready. Sign in through our app or "
    "website as usual if you would like to review it. No action is needed.",
    "Welcome to the newsletter. This month we cover the new dashboard, a "
    "guide to keyboard shortcuts, and a look at what is coming next.",
    "Hi Sam, great to meet you yesterday. As promised, here is the slide "
    "deck from the talk and a link to the recording for the team.",
    "Your appointment is confirmed for Friday at 2pm with Dr. Patel at the "
    "Riverside clinic. Reply to this message if you need to reschedule.",
    "The build finished successfully and all tests passed. The release notes "
    "for version 2.4 are attached for review before we ship on Monday.",
    "Hi, just confirming our lunch on Saturday at noon at the cafe on Main "
    "Street. Let me know if anything changes. Looking forward to it.",
    "Your library book is due back next week. You can renew it online or at "
    "the front desk. Thank you for using the library.",
    "Quarterly report attached. Revenue grew 4 percent and churn fell "
    "slightly. We will walk through the numbers at the all-hands on Friday.",
]

# ---------------------------------------------------------------------------
# Signal word lists
# ---------------------------------------------------------------------------

URGENCY_PHRASES = [
    "urgent", "immediately", "act now", "within 24 hours", "expires today",
    "expires tonight", "expires in", "final warning", "suspended",
    "will be locked", "will be disabled", "will be cancelled", "do not delay",
    "last chance", "account will be closed", "lose access", "right now",
    "as soon as possible", "limited time",
]

CREDENTIAL_PHRASES = [
    "verify your password", "enter your password", "confirm your password",
    "update your password", "verify your account", "confirm your account",
    "verify your identity", "enter your login", "sign in here",
    "login credentials", "your password", "reset your password",
]

PAYMENT_PHRASES = [
    "credit card number", "card details", "payment information",
    "billing details", "bank account details", "pay the fee",
    "shipping fee", "customs fee", "confirm your payment",
    "update your billing", "payment failed",
]

PRIZE_PHRASES = [
    "you have won", "congratulations", "claim your prize", "free gift",
    "you won", "gift card", "lottery", "claim your reward", "free iphone",
    "selected as a winner",
]

GENERIC_GREETINGS = [
    "dear customer", "dear user", "dear valued customer", "dear account holder",
    "dear sir/madam", "hello customer", "attention user",
]

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
    "cutt.ly", "shorte.st", "tiny.cc", "rb.gy", "shorturl.at",
}

RISKY_ATTACHMENT_EXTS = {
    ".exe", ".scr", ".bat", ".cmd", ".vbs", ".js", ".jar", ".msi", ".ps1",
    ".zip", ".rar", ".iso", ".lnk", ".hta", ".com", ".pif",
}

FREE_MAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "proton.me",
    "protonmail.com", "icloud.com", "aol.com", "mail.com",
}

# Fictional brands used in the samples, mapped to their real domain fragment.
KNOWN_BRANDS = {
    "northbank": "northbank",
    "clouddesk": "clouddesk",
    "shopsphere": "shopsphere",
    "parcelpost": "parcelpost",
    "riverside clinic": "riverside",
}

STOPWORDS = {
    "the", "and", "for", "you", "your", "are", "with", "this", "that",
    "have", "has", "will", "our", "from", "not", "but", "all", "can",
    "was", "were", "been", "its", "they", "them", "their", "his", "her",
    "she", "him", "who", "what", "when", "where", "how", "why", "into",
    "about", "after", "before", "over", "under", "out", "now", "please",
}

TOKEN_RE = re.compile(r"[a-z][a-z0-9']{2,}")
URL_RE = re.compile(r"https?://[^\s<>\")\]]+")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
HTML_LINK_RE = re.compile(
    r'<a\s[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
ATTACHMENT_RE = re.compile(
    r"attachment:\s*([^\s(]+\.[a-z0-9]+)", re.IGNORECASE
)
DOMAIN_LIKE_RE = re.compile(r"^[\w-]+(?:\.[\w-]+)+(?:/\S*)?$")
EMAIL_RE = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")


# ---------------------------------------------------------------------------
# Email parsing
# ---------------------------------------------------------------------------

def parse_email(text: str) -> dict:
    """Split a plain-text email into headers, body, links and attachments."""
    header_block, _, body = text.partition("\n\n")
    headers: dict[str, str] = {}
    for line in header_block.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            headers[key.strip().lower()] = value.strip()

    links = []
    for match in MD_LINK_RE.finditer(body):
        links.append({"text": match.group(1).strip(), "url": match.group(2)})
    for match in HTML_LINK_RE.finditer(body):
        clean_text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        links.append({"text": clean_text, "url": match.group(1)})
    seen_urls = {link["url"] for link in links}
    for match in URL_RE.finditer(body):
        url = match.group(1) if match.groups() else match.group(0)
        url = url.rstrip(".,;!")
        if url not in seen_urls:
            links.append({"text": url, "url": url})

    attachments = ATTACHMENT_RE.findall(body)

    sender = headers.get("from", "")
    reply_to = headers.get("reply-to", "")

    def domain_of(address: str) -> str:
        match = EMAIL_RE.search(address)
        return match.group(1).lower() if match else ""

    return {
        "from": sender,
        "from_domain": domain_of(sender),
        "reply_to": reply_to,
        "reply_to_domain": domain_of(reply_to),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "body": body.strip(),
        "links": links,
        "attachments": attachments,
    }


# ---------------------------------------------------------------------------
# Naive Bayes word model (trained on the built-in fictional corpus)
# ---------------------------------------------------------------------------

def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


class WordModel:
    """Bernoulli-style Naive Bayes over words, Laplace-smoothed."""

    def __init__(self, phishing_texts: list[str], legit_texts: list[str]) -> None:
        self.phish_counts: Counter = Counter()
        self.legit_counts: Counter = Counter()
        for text in phishing_texts:
            self.phish_counts.update(set(tokenize(text)))
        for text in legit_texts:
            self.legit_counts.update(set(tokenize(text)))
        self.n_phish = len(phishing_texts)
        self.n_legit = len(legit_texts)
        self.vocab = set(self.phish_counts) | set(self.legit_counts)

    def phishing_probability(self, text: str) -> tuple[float, list[str]]:
        """Return (probability 0..1 the text is phishing, top phishing words)."""
        words = set(tokenize(text))
        log_odds = math.log(self.n_phish / self.n_legit)  # equal priors
        word_scores: dict[str, float] = {}
        for word in words & self.vocab:
            p_word_given_phish = (self.phish_counts[word] + 1) / (
                self.n_phish + 2
            )
            p_word_given_legit = (self.legit_counts[word] + 1) / (
                self.n_legit + 2
            )
            score = math.log(p_word_given_phish / p_word_given_legit)
            log_odds += score
            word_scores[word] = score
        probability = 1.0 / (1.0 + math.exp(-log_odds))
        top_words = sorted(word_scores, key=word_scores.get, reverse=True)[:5]
        top_words = [w for w in top_words if word_scores[w] > 0]
        return probability, top_words


MODEL = WordModel(PHISHING_TRAINING, LEGIT_TRAINING)


# ---------------------------------------------------------------------------
# Rule-based signals
# ---------------------------------------------------------------------------

def _find_phrases(text: str, phrases: list[str]) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in phrases if phrase in lowered]


def _domain_of_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().split(":")[0]
    except ValueError:
        return ""


def _is_ip_host(host: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host))


def rule_signals(email: dict) -> list[dict]:
    """Return a list of triggered signals: {name, points, detail}."""
    signals: list[dict] = []
    body = email["body"]
    subject = email["subject"]
    full_text = f"{subject}\n{body}"

    urgency = _find_phrases(full_text, URGENCY_PHRASES)
    if urgency:
        signals.append({
            "name": "Urgent / threatening language",
            "points": 15,
            "detail": f"found: {', '.join(repr(u) for u in urgency[:3])}",
        })

    credentials = _find_phrases(full_text, CREDENTIAL_PHRASES)
    if credentials:
        signals.append({
            "name": "Asks for credentials or account verification",
            "points": 20,
            "detail": f"found: {', '.join(repr(c) for c in credentials[:3])}",
        })

    payment = _find_phrases(full_text, PAYMENT_PHRASES)
    if payment:
        signals.append({
            "name": "Asks for payment / card / bank details",
            "points": 15,
            "detail": f"found: {', '.join(repr(p) for p in payment[:3])}",
        })

    prize = _find_phrases(full_text, PRIZE_PHRASES)
    if prize:
        signals.append({
            "name": "Prize / free-gift lure",
            "points": 10,
            "detail": f"found: {', '.join(repr(p) for p in prize[:3])}",
        })

    greeting = _find_phrases(body, GENERIC_GREETINGS)
    if greeting:
        signals.append({
            "name": "Generic greeting instead of your name",
            "points": 5,
            "detail": f"found: {greeting[0]!r}",
        })

    # Sender checks
    if email["reply_to_domain"] and email["from_domain"]:
        if email["reply_to_domain"] != email["from_domain"]:
            signals.append({
                "name": "Reply-To domain differs from sender domain",
                "points": 20,
                "detail": (
                    f"From: {email['from_domain']}, "
                    f"Reply-To: {email['reply_to_domain']}"
                ),
            })

    display = email["from"].split("<")[0].strip().lower()
    for brand, fragment in KNOWN_BRANDS.items():
        if brand in display and fragment not in email["from_domain"]:
            signals.append({
                "name": "Display name claims a brand its domain does not match",
                "points": 10,
                "detail": (
                    f"display name says {brand!r} but sender domain is "
                    f"{email['from_domain'] or '(none)'}"
                ),
            })
            break

    if (
        email["from_domain"] in FREE_MAIL_DOMAINS
        and any(word in display for word in ("support", "security", "team", "service"))
    ):
        signals.append({
            "name": "Claims to be a company but sent from a free mailbox",
            "points": 10,
            "detail": f"sender domain is {email['from_domain']}",
        })

    # Link checks
    for link in email["links"]:
        host = _domain_of_url(link["url"])
        text_domain = ""
        text_match = EMAIL_RE.search(link["text"]) or URL_RE.search(link["text"])
        if text_match:
            text_domain = _domain_of_url(text_match.group(0))
        if not text_domain and DOMAIN_LIKE_RE.match(link["text"].strip()):
            # Bare domain in the shown text, e.g. "northbank.example/verify"
            text_domain = link["text"].strip().lower().split("/")[0]
        if text_domain and text_domain != host:
            signals.append({
                "name": "Link text shows a different destination than the real URL",
                "points": 15,
                "detail": f"text shows {text_domain!r}, link goes to {host!r}",
            })
            break
    else:
        for link in email["links"]:
            host = _domain_of_url(link["url"])
            if host in URL_SHORTENERS:
                signals.append({
                    "name": "Link uses a URL shortener (destination hidden)",
                    "points": 15,
                    "detail": f"shortened link to {host}",
                })
                break
            if _is_ip_host(host):
                signals.append({
                    "name": "Link points to a raw IP address, not a domain",
                    "points": 15,
                    "detail": f"link goes to {host}",
                })
                break
            if email["from_domain"] and host != email["from_domain"]:
                labels = host.split(".")
                if len(labels) > 3:
                    signals.append({
                        "name": "Link hides behind many subdomains",
                        "points": 10,
                        "detail": f"link goes to {host}",
                    })
                    break

    # Attachment checks
    risky = [
        att for att in email["attachments"]
        if Path(att).suffix.lower() in RISKY_ATTACHMENT_EXTS
    ]
    if risky:
        signals.append({
            "name": "Unexpected risky attachment",
            "points": 15,
            "detail": f"attachment: {', '.join(risky)}",
        })

    return signals


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def verdict_for(score: int) -> str:
    if score >= 70:
        return "PHISHING"
    if score >= 40:
        return "SUSPICIOUS"
    return "LEGITIMATE"


def analyze(text: str) -> dict:
    """Score one email (raw text) and return the full report dict."""
    email = parse_email(text)
    full_text = f"{email['subject']}\n{email['body']}"
    model_prob, top_words = MODEL.phishing_probability(full_text)
    model_score = round(model_prob * 100)

    signals = rule_signals(email)
    rule_score = min(100, sum(signal["points"] for signal in signals))

    score = round(0.5 * model_score + 0.5 * rule_score)
    return {
        "from": email["from"],
        "subject": email["subject"],
        "model_score": model_score,
        "model_top_words": top_words,
        "rule_score": rule_score,
        "signals": signals,
        "score": score,
        "verdict": verdict_for(score),
        "links": email["links"],
        "attachments": email["attachments"],
    }


# ---------------------------------------------------------------------------
# Reporting / CLI
# ---------------------------------------------------------------------------

def format_report(report: dict, source: str) -> str:
    lines = [
        f"From:    {report['from'] or '(none)'}",
        f"Subject: {report['subject'] or '(none)'}",
        f"Score:   {report['score']}/100 — {report['verdict']}",
        f"Model:   phishing probability {report['model_score']}% "
        f"(top words: {', '.join(report['model_top_words']) or 'none'})",
        f"Rules:   {report['rule_score']}/100 from "
        f"{len(report['signals'])} signal(s)",
        "Why:",
    ]
    if report["signals"]:
        for signal in report["signals"]:
            lines.append(
                f"  • {signal['name']} (+{signal['points']}) — {signal['detail']}"
            )
    else:
        lines.append("  • No suspicious signals found.")
    if report["links"]:
        lines.append("Links:")
        for link in report["links"]:
            shown = f" (shown as {link['text']!r})" if link["text"] != link["url"] else ""
            lines.append(f"  • {link['url']}{shown}")
    if report["attachments"]:
        lines.append(f"Attachments: {', '.join(report['attachments'])}")
    return "\n".join(lines)


def samples_dir() -> Path:
    return Path(__file__).resolve().parent / "samples"


def load_sample(name: str) -> str:
    path = samples_dir() / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"No sample named {name!r} in samples/")
    return path.read_text(encoding="utf-8")


def run_demo() -> int:
    print("Phishing Email Detector — demo on built-in fictional samples\n")
    rows = []
    for path in sorted(samples_dir().glob("*.txt")):
        report = analyze(path.read_text(encoding="utf-8"))
        rows.append((path.stem, report["score"], report["verdict"]))
        print(f"{path.name}")
        print(format_report(report, path.name))
        print()
    print("Summary:")
    for stem, score, verdict in rows:
        print(f"  {stem:<38} {score:>3}/100  {verdict}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score an email as phishing or legitimate (local ML, offline)."
    )
    parser.add_argument("file", nargs="?", help="Email file to analyze")
    parser.add_argument("--demo", action="store_true",
                        help="Score every built-in fictional sample")
    parser.add_argument("--sample", metavar="NAME",
                        help="Score one built-in sample by name (without .txt)")
    parser.add_argument("--list-samples", action="store_true",
                        help="List the built-in sample emails")
    parser.add_argument("--json", action="store_true",
                        help="Print the report as JSON")
    parser.add_argument("--model-info", action="store_true",
                        help="Show training-corpus stats and exit")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    args = parser.parse_args(argv)

    if args.model_info:
        print(f"Phishing Email Detector {VERSION} — local Naive Bayes word model")
        print(f"  Training emails: {MODEL.n_phish} phishing, {MODEL.n_legit} legitimate")
        print(f"  Vocabulary: {len(MODEL.vocab)} words")
        print("  Training data: built-in fictional samples only. No network, no API key.")
        return 0

    if args.list_samples:
        for path in sorted(samples_dir().glob("*.txt")):
            print(path.stem)
        return 0

    if args.demo:
        return run_demo()

    if args.sample:
        try:
            text = load_sample(args.sample)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        report = analyze(text)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(format_report(report, args.sample))
        return 0 if report["verdict"] == "LEGITIMATE" else 1

    if not args.file:
        parser.error("give an email file, --demo, or --sample NAME")

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 2
    report = analyze(path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_report(report, args.file))
    return 0 if report["verdict"] == "LEGITIMATE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
