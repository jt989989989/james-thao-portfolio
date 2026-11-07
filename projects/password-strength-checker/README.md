# Password Strength Checker

A Python CLI that scores a password 0–100 and explains *why* — length, character variety, common words, and predictable patterns — so you can learn what actually makes a password strong.

Built as a beginner defensive cybersecurity project. It is **not** a cracking tool: it never guesses, tests, or attacks any account, and it never sends, saves, or logs a password. Everything runs locally, offline, with the Python standard library only.

## How scoring works

- **Length (up to 40 points):** 10 points at 8 characters, +2 per extra character, capped at 40. Length matters most.
- **Variety (up to 40 points):** 10 points each for lowercase, uppercase, digits, and symbols.
- **Penalties:** −40 for a well-known common password, −15 for containing a common word, −15 for a sequence (`abc`, `123`, `qwerty`), −10 for a character repeated 3+ times, −15 for containing your username, −10 for using only one character type.

Ratings: 0–19 Very Weak, 20–39 Weak, 40–59 Fair, 60–79 Strong, 80–100 Very Strong.

The estimated crack time is a rough offline-guess estimate (10 billion guesses/second) for learning — a password on a leaked list can fall instantly no matter its entropy, which is why the common-password check matters more than that number.

## Run it

```bash
cd projects/password-strength-checker
python password_checker.py
```

You will be prompted for a password with hidden input. It is checked in memory and discarded — nothing is written anywhere.

```bash
# Check the built-in example passwords — no real password needed
python password_checker.py --demo

# Check one password and print the result as JSON
python password_checker.py --password "Sunshine2026!" --json
```

Avoid `--password` for real passwords: it shows up in your shell history. Use the hidden prompt instead.

## Demo results

| Example password | Score | Rating | Why |
|---|---|---|---|
| `password` | 0 | Very Weak | Common password, only lowercase |
| `123456` | 0 | Very Weak | Common password, sequence, digits only |
| `Sunshine2026!` | 60 | Strong | 13 chars, all four types |
| `Tr0ub4dor&3` | 56 | Fair | Mixed types, but only 11 characters |
| `correct horse battery staple` | 60 | Strong | Long passphrase — length beats complexity |
| `J7#kP9!mQ2$vX8@wL4&zT1a` | 80 | Very Strong | 23 chars, all four types |

Run `--demo` to see these with full explanations.

## Tests

```bash
python -m unittest discover -s tests -v
```

8 unit tests, all passing: common passwords score 0, long passphrases beat short complex ones, sequences and repeats are penalized, usernames are flagged, and empty passwords are handled.

## Skills shown

Python, string analysis with regex, entropy estimation, CLI design with `argparse` and hidden input via `getpass`, clear separation between scoring logic and output, unit tests with `unittest`, defensive-security thinking.

## Safety note

Use this to learn, or to check a *new* password before you set it. Do not paste a real password you already use into any website, chat, or shared tool. A strong password is one part of account security — use a password manager, and turn on two-factor authentication wherever it is offered.
