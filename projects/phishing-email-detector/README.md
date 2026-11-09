# Phishing Email Detector

A local, offline email phishing classifier — Python, standard library only.
It scores an email as **LEGITIMATE / SUSPICIOUS / PHISHING** (0–100) and
explains every point in the score, so you can see *why* it flagged something.

## How it works

Two layers, both running entirely on your machine — no network calls, no API
key, no data leaves the device:

1. **A Naive Bayes word model**, trained at start-up on built-in fictional
   sample emails (10 phishing, 10 legitimate). It returns a phishing
   probability from the words in the message.
2. **Rule-based signals** a word model alone would miss:
   - urgent / threatening language ("account will be suspended", "within 24 hours")
   - credential or payment requests ("verify your password", "credit card number")
   - prize / free-gift lures ("you have won", "claim your prize")
   - generic greetings ("Dear Customer") instead of your name
   - a Reply-To address whose domain differs from the sender's
   - a display name claiming a brand its domain does not match
   - a company address sent from a free mailbox (Gmail, Yahoo, …)
   - link text showing a different destination than the real URL
   - URL shorteners and links to raw IP addresses
   - risky attachments (.exe, .zip, .scr, …)

The final score blends the model and the rules 50/50. Verdict bands:
**0–39 LEGITIMATE, 40–69 SUSPICIOUS, 70–100 PHISHING.**

## Run it

Python 3.10+ only, no packages to install.

```bash
# Score one email file
python phishing_detector.py samples/phishing_01_account_locked.txt

# Score every built-in sample and print a summary table
python phishing_detector.py --demo

# Score one built-in sample by name
python phishing_detector.py --sample phishing_02_prize_winner

# Machine-readable output
python phishing_detector.py samples/legit_01_order_confirmation.txt --json

# See the training-corpus stats
python phishing_detector.py --model-info
```

Exit code is `0` for LEGITIMATE and `1` for SUSPICIOUS / PHISHING (demo
mode always exits `0`).

Email files are plain text with simple headers (`From` / `Reply-To` /
`Subject` / `Date`), a blank line, then the body. Attachment lines look
like `Attachment: invoice.zip (184 KB)`.

## Demo results

```text
phishing_01_account_locked             88/100  PHISHING
phishing_02_prize_winner               78/100  PHISHING
phishing_03_invoice_attachment         75/100  PHISHING
phishing_04_password_reset             88/100  PHISHING
legit_01_order_confirmation             0/100  LEGITIMATE
legit_02_team_meeting                   0/100  LEGITIMATE
legit_03_newsletter                     0/100  LEGITIMATE
legit_04_bank_statement                 0/100  LEGITIMATE
```

## Tests

```bash
python -m unittest discover -s tests -v
```

22 unit tests: parsing, every rule signal, the word model, verdict bands,
and all 8 built-in samples classified as expected.

## Safety note

This is a portfolio demo and a learning tool, not a substitute for a real
email security gateway. All training data and samples are fictional
(brands like Northbank and CloudDesk, `.example` domains) — no real emails
or personal data are included. A low score never proves an email is safe;
a high score means stop and verify through a known-good channel (type the
site address yourself, or call the number on the back of your card).

## Roadmap

- **v2** (Mon Nov 23): lookalike-domain detection (typosquatting) +
  suspicious-URL + attachment-risk checks
- **v3**: trainable model — add your own examples, accuracy report
  (precision / recall on a test set)
- **v4**: header analysis (SPF / DKIM-style checks on sample headers) +
  HTML email parsing
- **v5+**: batch scanning a folder of emails + report export
