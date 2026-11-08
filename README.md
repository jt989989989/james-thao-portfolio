# James Thao — Portfolio Projects

Hi, I'm James Thao — a techie with a passion for games, programming, security, AI, and more. A revolutionary.

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
| [Password Strength Checker](projects/password-strength-checker/) | Defensive CLI that scores a password 0–100 and explains why — length, variety, common words, patterns; runs locally, never sends or saves a password | Python (stdlib only) | Security / defensive |
| [ADHD My Way](projects/adhd-my-way/) | Ionic app for children under 12 — daily quests earn coins, coins buy avatar customisations, plus Memory Match and Tap the Star mini games; everything stays on the device | Ionic 8, Capacitor 7, Vite, JavaScript | Mobile / front-end |

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

ADHD My Way — 9 unit tests; web build served from www/:

```bash
cd projects/adhd-my-way
npm install
npm test
npm run build
# Demo: open www/index.html, or serve it — e.g. npx vite preview
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

# Password Strength Checker — 8 unit tests; demo checks built-in examples only
cd ../password-strength-checker
python -m unittest discover -s tests -v
python password_checker.py --demo
```

## Notes

- All sample data is fictional: documentation IPs (`203.0.113.x`, `198.51.100.x`, `192.0.2.x`) and fictional `555-010-xxxx` phone numbers.
- No secrets, credentials, API keys, or real customer / employer data are in this repo.
- The Python tools are portfolio demos. They do not claim production use at any employer.
- Orbit Hop also has a Facebook Instant Games build; the copy here runs in a normal browser, and the Facebook SDK script in it is inert outside Facebook.

## Contact

- LinkedIn: linkedin.com/in/jamesss42/
- Portfolio site: coming soon — link will be added here once published
