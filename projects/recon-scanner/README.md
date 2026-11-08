# Recon Scanner

A passive recon CLI for bug bounty and security work — the first step of a
hunt, before any active probing. Given a domain, it:

1. **Finds subdomains** from Certificate Transparency, via crt.sh.
   Certificates are public records, so this only reads data that is
   already published.
2. **Checks DNS liveness** for each subdomain (does it resolve?).
3. **Grades security headers + TLS** on the main domain — one normal
   HTTPS request, graded like a report card (A–F).

Python 3.10+, standard library only. No dependencies to install, and
nothing is sent anywhere except the two public requests above.

## How to run it

```bash
# Full recon on a domain
python recon_scanner.py example.com

# Machine-readable output
python recon_scanner.py example.com --json

# Subdomains + DNS only (skip the headers/TLS check)
python recon_scanner.py example.com --subdomains-only

# Offline demo — no network needed, uses the saved samples
python recon_scanner.py --demo
```

Demo output (from the saved samples) finds 6 subdomains of `example.com`
and grades its headers D (3 of 6 present: HSTS, X-Frame-Options, and
X-Content-Type-Options are there; Content-Security-Policy,
Referrer-Policy, and Permissions-Policy are missing).

## What each check means

| Check | What it tells you |
|---|---|
| Subdomains (crt.sh) | Every name on a public certificate for the domain — the attack surface you can see from the outside. |
| DNS liveness | Which of those subdomains actually resolve. Dead ones are usually not worth your time; live ones are where you look next. |
| Strict-Transport-Security | Forces HTTPS, blocking downgrade attacks. |
| Content-Security-Policy | Limits where scripts can load from, blocking XSS. |
| X-Frame-Options | Stops the site being embedded in an iframe (clickjacking). |
| X-Content-Type-Options | Stops browsers guessing content types (MIME sniffing). |
| Referrer-Policy | Controls how much URL information leaks to other sites. |
| Permissions-Policy | Restricts powerful browser features like camera and microphone. |
| TLS version | TLS 1.2 or 1.3 is expected; anything older is weak. |

## Tests

```bash
python -m unittest discover -s tests -v
```

13 tests. All run offline against the saved samples, except one live
smoke test against `example.com` that skips itself when the network is
unavailable, plus one test for the `--subdomains-only` report shape.

## Scope — read this first

Passive recon only. This tool reads public Certificate Transparency data
and makes normal HTTP requests — it does not port scan, brute-force
directories, exploit anything, or log in anywhere. Only use it on domains
you own or that are in scope for a bug bounty program with a safe harbor.
Out-of-scope testing is not covered by any program's safe harbor and can
be illegal.

## Notes

- All sample data is fictional: the sample crt.sh response is a small
  hand-made example for `example.com`, not a real certificate dump.
- This is a portfolio demo. It does not claim production use at any
  employer.
