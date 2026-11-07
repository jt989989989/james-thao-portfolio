# James Thao — Portfolio Projects

Hi, I'm James Thao — B.S. in Computer Science with a Cybersecurity Certification from the University of Wisconsin, CompTIA Security+, and experience as a Cloud Security Engineer at Lucid Motors, vSOC Engineer at Upstream Security, ROC Analyst at Johnson Controls, and Director at All Stars Automations.

This repository is my project index for programming and IT roles. Each project is finished, runnable, and documented — start with the README in its folder.

## Projects

| Project | What it is | Stack | Best for |
|---|---|---|---|
| [Orbit Hop](projects/orbit-hop/) | Playable browser game — hop between orbits, dodge hazards, chase a high score | JavaScript, HTML5 Canvas | Game dev / front-end |
| [Jelly Stack](projects/jelly-stack/) | Playable physics stacking game — drop soft jelly blocks, build a stable tower | JavaScript, Matter.js | Game dev / front-end |
| [SOC Log Analyzer](projects/soc-log-analyzer/) | CLI that parses auth logs and flags brute-force attempts and success-after-failure logins | Python (stdlib only) | SOC / security / IT |
| [Missed-Call Follow-Up](projects/missed-call-followup/) | CLI that turns a missed-call CSV into a prioritized follow-up queue with message drafts | Python (stdlib only) | Automation / IT |
| [Scientific Calculator](projects/scientific-calculator/) | Scientific calculator in the browser — full expressions, trig, logs, factorial, history, memory | JavaScript, no dependencies, no `eval()` | Front-end / algorithms |
| [Lead Generator](projects/lead-generator/) | CLI that finds small-business leads from Google Maps data via the official Places API — scores and dedupes them into a CSV | Python (stdlib only) | Automation / data / sales ops |

## How to run them

Games and calculator — open the project's `index.html` in a browser. No build step, no server needed.

```bash
# Orbit Hop
open projects/orbit-hop/index.html

# Jelly Stack
open projects/jelly-stack/index.html

# Scientific Calculator
open projects/scientific-calculator/index.html
```

Calculator tests — Node.js only, no extra packages:

```bash
cd projects/scientific-calculator
node --test tests/calculator.test.js
```

Python tools — Python 3.10+ only, no extra packages to install.

```bash
# SOC Log Analyzer — 5 unit tests, 1 brute-force finding on the sample log
cd projects/soc-log-analyzer
python -m unittest discover -s tests -v
python log_analyzer.py sample_auth.log

# Missed-Call Follow-Up — 4 unique numbers from 5 sample calls
cd ../missed-call-followup
python followup.py sample_calls.csv

# Lead Generator — 7 unit tests; demo yields 7 leads from 9 sample places
cd ../lead-generator
python -m unittest discover -s tests -v
python lead_generator.py --demo
# Live search (needs GOOGLE_PLACES_API_KEY, see the project's README):
# python lead_generator.py plumbers --location "Alpena, MI" --max-results 25
```

## Notes

- All sample data is fictional: documentation IPs (`203.0.113.x`, `198.51.100.x`, `192.0.2.x`) and fictional `555-010-xxxx` phone numbers.
- No secrets, credentials, API keys, or real customer / employer data are in this repo.
- The Python tools are portfolio demos. They do not claim production use at any employer.
- Orbit Hop also has a Facebook Instant Games build; the copy here runs in a normal browser, and the Facebook SDK script in it is inert outside Facebook.

## Background

- **All Stars Automations** — Director, Apr 2025–present — AI automation and workflow systems for small businesses
- **Lucid Motors** — Cloud Security Engineer, Jan 2023–Feb 2025
- **Upstream Security** — vSOC Engineer, Aug 2022–Aug 2024
- **Johnson Controls** — ROC Analyst, Jun 2020–Jul 2022

## Contact

- LinkedIn: linkedin.com/in/jamesss42/
- Portfolio site: coming soon — link will be added here once published
