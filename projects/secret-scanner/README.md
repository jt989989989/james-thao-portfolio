# Secret Scanner

A defensive Python CLI that scans a codebase for leaked secrets — AWS keys,
GitHub and Slack tokens, JWTs, private keys, Stripe live keys, passwords
stored in plain text, and suspicious high-entropy strings. Each finding
reports the file, line number, rule, severity, and what to do about it.

It only reads files. No network calls, no uploads, Python standard library
only — and it shows a redacted preview of a match, never the full secret.

## Why this exists

Secrets end up in code all the time: a key pasted into a config file, a
token left in a test, a password hardcoded "just for now". Once a secret
is committed, anyone with the code has it — and removing it from the
current files is not enough, because it lives on in the git history.
This tool catches those leaks before (or after) they are committed.

## Rules

| Rule | Severity | What it catches |
|---|---|---|
| `aws-access-key` | High | AWS access key ID (`AKIA…`) |
| `aws-secret-key` | High | AWS secret access key assignment |
| `github-token` | High | Classic GitHub token (`ghp_`, `gho_`, …) |
| `github-fine-grained-token` | High | Fine-grained GitHub token (`github_pat_…`) |
| `slack-token` | High | Slack token (`xoxb-`, `xoxp-`, `xoxa-`, …) |
| `jwt` | High | JSON Web Token (`eyJ…`) |
| `private-key` | High | Private key header (`BEGIN … PRIVATE KEY`) |
| `stripe-live-key` | High | Stripe live key (`sk_live_`, `rk_live_`) |
| `password-assignment` | Medium | Password stored in plain text in code |
| `generic-high-entropy` | Low | Long, high-entropy string — a hint, check it by hand |

The generic high-entropy check only runs on a line no specific rule
matched, so each secret is reported once, by its best rule. Placeholder
values such as `changeme` are ignored, and the word "password" in a
comment with no value does not flag.

## How to run it

```bash
# Demo: scan the fictional samples (finds 9 secrets: 7 high, 1 medium, 1 low)
python secret_scanner.py samples/

# Scan a folder you own or have permission to scan
python secret_scanner.py /path/to/your/project

# Skip files, e.g. tests or generated code
python secret_scanner.py . --exclude 'tests/*' --exclude '*.min.js'

# Machine-readable output
python secret_scanner.py . --json
```

Exit code is `1` when any high or medium finding is present, `0` when
the scan is clean (low findings are hints only and do not change the
exit code), and `2` when the path does not exist.

By default it skips binary files and the `.git`, `node_modules`,
`__pycache__`, and `.venv` directories at every depth.

## Tests

```bash
python -m unittest discover -s tests -v
```

19 tests: each rule detects its pattern, plus false-positive checks
(a bare "password" in a comment, placeholder values, and low-entropy
strings do not flag) and directory checks (`.git` is skipped,
`--exclude` works, exit codes are 0 clean / 1 on findings).

## If a real secret is found

1. **Rotate or revoke it immediately** — in the AWS console, on GitHub,
   in Slack, in Stripe, wherever it lives. Assume it is already seen.
2. **Remove it from the code** — move it to an environment variable or
   a secrets manager, never back into a file.
3. **Remove it from the git history** — deleting it from the current
   files is not enough. Rewrite the history (e.g. `git filter-repo`)
   or, if the repo is already public, treat the secret as burned and
   rely on step 1.
4. **Check what it could reach** — logs, cloud bills, and access
   history for the time it was exposed.

## Scope

Scan only code you own or have permission to scan — your own projects,
or a codebase you were explicitly asked to audit. Never point it at
someone else's private code without permission. All sample secrets in
`samples/` are fictional: AWS's documented example keys and made-up
tokens. No real secrets are in this project. The samples are also shaped
so they trigger this scanner without tripping GitHub's own push
protection, which blocks real-looking secrets: the Slack sample has no
numeric workspace IDs, and the Stripe sample is shorter than a real key.
