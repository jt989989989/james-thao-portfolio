# James Thao — Portfolio Projects

Hi, I'm James Thao — a technologist driven by curiosity and a love of building things that work beautifully. My work spans games, programming, security, AI, and more — the places where creativity meets engineering: playful systems, resilient software, and intelligent tools that solve real problems. I believe the best technology feels alive — crafted with care, tested in the open, and made to be explored. A revolutionary at heart, I'm here to build what comes next.

**Portfolio website:** https://jt989989989.github.io/james-thao-portfolio/ — my full portfolio site, with playable games and my work experience.

This repository is my project index for programming and IT roles. Each project is finished, runnable, and documented — start with the README in its folder.

## Projects

| Project | What it is | Stack | Best for |
|---|---|---|---|
| [Printed Text Reader HUD (prototype)](projects/printed-text-reader-hud/) | You know the saying — give a tough job to a lazy person and see how they solve it. Well, this tool is meant to do that: point a camera at printed text and get the answer in a heads-up panel — it can solve simple math problems and a few cybersecurity questions, with the picked answer highlighted and explained | JavaScript, HTML5, no dependencies | Front-end / problem-solving |
| [Orbit Hop](projects/orbit-hop/) | Playable browser game — hop between orbits, dodge hazards, chase a high score | JavaScript, HTML5 Canvas | Game dev / front-end |
| [Jelly Stack](projects/jelly-stack/) | Playable physics stacking game — drop soft jelly blocks, build a stable tower | JavaScript, Matter.js | Game dev / front-end |
| [Life of a Man](projects/life-of-a-man/) | Satire board-game life sim — roll dice around a 40-square Board of Life, ages 18 to 65, quarterly choices, debt, marriage, midlife crises, and a tombstone ending; happiness is the main score | JavaScript, HTML5, no dependencies | Game dev / front-end |
| [Flappy Bird Clone](projects/flappy-bird/) | Playable Flappy Bird–style game — tap to flap through the pipes, chase the high score; plain shapes and flat colours, no copied art | JavaScript, HTML5 Canvas | Game dev / front-end |
| [SOC Log Analyzer](projects/soc-log-analyzer/) | CLI that parses auth logs and flags brute-force attempts and success-after-failure logins | Python (stdlib only) | SOC / security / IT |
| [Missed-Call Follow-Up](projects/missed-call-followup/) | CLI that turns a missed-call CSV into a prioritized follow-up queue with message drafts | Python (stdlib only) | Automation / IT |
| [Scientific Calculator](projects/scientific-calculator/) | Scientific calculator in the browser — full expressions, trig, logs, factorial, history, memory | JavaScript, no dependencies, no `eval()` | Front-end / algorithms |
| [Lead Generator](projects/lead-generator/) | CLI that finds small-business leads from Google Maps data via the official Places API — scores and dedupes them into a CSV | Python (stdlib only) | Automation / data / sales ops |
| [Password Strength Checker](projects/password-strength-checker/) | Defensive CLI that scores a password 0–100 and explains why — length, variety, common words, patterns; runs locally, never sends or saves a password | Python (stdlib only) | Security / defensive |
| [Secret Scanner](projects/secret-scanner/) | Defensive CLI that scans a codebase for leaked secrets — AWS keys, GitHub/Slack tokens, JWTs, private keys, Stripe keys, passwords, high-entropy strings; reports file, line, rule, and severity | Python (stdlib only) | Security / defensive |
| [Recon Scanner](projects/recon-scanner/) | Passive recon CLI — finds subdomains from Certificate Transparency (crt.sh), checks DNS liveness, and grades security headers + TLS on a domain; public data and one normal request only | Python (stdlib only) | Security / bug bounty |
| [SQL Detective](projects/sql-detective/) | Fun SQL practice game — solve the case of the missing mascot by writing real SQL queries against a fictional SQLite database; hints and a checker included | Python (stdlib only, sqlite3) | SQL / databases / games |
| [SQL Injection Lab](projects/sql-injection-lab/) | Educational local-only lab — try classic injection payloads against a deliberately vulnerable login, then see the same payloads fail against parameterized queries; spot-it and fix-it guide included | Python (stdlib only, sqlite3) | Security / defensive |
| [Phishing Email Detector](projects/phishing-email-detector/) | Local ML email classifier — Naive Bayes word model trained on built-in fictional samples plus rule signals (urgency, credential requests, Reply-To mismatch, deceptive links, risky attachments); scores an email 0–100 and explains why | Python (stdlib only) | Security / AI / defensive |
| [Port Scanner](projects/port-scanner/) | TCP connect port scanner for lab targets only — scans a port range and prints open/closed; refuses public targets unless `--i-have-permission` is given | Python (stdlib only) | Security / offensive lab |
| [ADHD My Way](projects/adhd-my-way/) | Ionic app for children under 12 — daily quests earn coins, coins buy avatar customisations, plus Memory Match and Tap the Star mini games; everything stays on the device | Ionic 8, Capacitor 7, Vite, JavaScript | Mobile / front-end |
| [Local Chatbot](projects/local-chatbot/) | Simple offline chatbot — keyword/intent matching over a built-in knowledge base about All Stars Automations and my portfolio; answers services, booking, pricing (never invents a price), projects, and contact; demo mode included | Python (stdlib only) | AI / automation |
| [Expense Tracker CLI](projects/expense-tracker/) | Swift CLI expense tracker — add expenses, list them, totals by category and month; data persists to a local JSON file; money as Decimal for exact totals; demo mode with fictional samples | Swift 6.4.1, Swift Package Manager | Tools / finance |
| [Excel Report Automator](projects/excel-report-automator/) | I turn messy spreadsheet exports into clean, presentation-ready workbooks — dedupe, blank-row removal, whitespace and date cleanup, formatted sheets, and pivot summaries I compute with pandas (not native Excel PivotTables); demo mode included | Python, openpyxl + pandas | Tools / Excel |

## How to run them

Games and calculator — open the project's `index.html` in a browser. No build step, no server needed.

```bash
# Orbit Hop
open projects/orbit-hop/index.html

# Jelly Stack
open projects/jelly-stack/index.html

# Life of a Man
open projects/life-of-a-man/index.html

# Flappy Bird Clone
open projects/flappy-bird/index.html

# Scientific Calculator
open projects/scientific-calculator/index.html

# Printed Text Reader HUD (prototype)
open projects/printed-text-reader-hud/index.html
# Camera needs HTTPS (GitHub Pages provides it); or try the 4 built-in samples with no camera
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

# Secret Scanner — 19 unit tests; demo scan of samples/ finds 9 secrets
cd ../secret-scanner
python -m unittest discover -s tests -v
python secret_scanner.py samples/

# Recon Scanner — 14 unit tests; offline demo finds 6 subdomains, grades headers D
cd ../recon-scanner
python -m unittest discover -s tests -v
python recon_scanner.py --demo
# Live recon (only on domains you own or that are in scope):
# python recon_scanner.py example.com

# SQL Detective — 12 unit tests; solve the mascot mystery with SQL
cd ../sql-detective
python -m unittest discover -s tests -v
python sql_detective.py --demo
# Play it yourself: python sql_detective.py

# SQL Injection Lab — 13 unit tests; local demo only, no network
cd ../sql-injection-lab
python -m unittest discover -s tests -v
python sql_injection_lab.py --demo
# Interactive menu: python sql_injection_lab.py

# Phishing Email Detector — 22 unit tests; demo scores 4 phishing samples
# 75–88/100 (PHISHING) and 4 legit samples 0/100 (LEGITIMATE)
cd ../phishing-email-detector
python -m unittest discover -s tests -v
python phishing_detector.py --demo
# Score one email: python phishing_detector.py samples/phishing_01_account_locked.txt

# Local Chatbot — 14 unit tests; offline, no API key, no network
cd ../local-chatbot
python -m unittest discover -s tests -v
python chatbot.py --demo
# Interactive chat: python chatbot.py

# Port Scanner — 20 unit tests; lab targets only, no brute force or exploits
cd ../port-scanner
python -m unittest discover -s tests -v
python port_scanner.py --demo
# Scan localhost: python port_scanner.py 127.0.0.1 --ports 22,80,443

# Expense Tracker CLI — 14 unit tests; Swift 6.4.1, no network, no API key
cd ../expense-tracker
swift test
swift run expense-tracker --demo
# Add an expense: swift run expense-tracker add 12.50 --category Food --note "Lunch"

# Excel Report Automator — 13 unit tests; needs openpyxl + pandas
cd ../excel-report-automator
pip install -r requirements.txt
python -m unittest discover -s tests -v
python excel_report_automator.py --demo
# Clean a file: python excel_report_automator.py messy.xlsx --pivot-rows Category --pivot-cols Month --pivot-values Amount
```

## Notes

- All sample data is fictional: documentation IPs (`203.0.113.x`, `198.51.100.x`, `192.0.2.x`) and fictional `555-010-xxxx` phone numbers.
- No secrets, credentials, API keys, or real customer / employer data are in this repo.
- The Python tools are portfolio demos. They do not claim production use at any employer.
- Orbit Hop also has a Facebook Instant Games build; the copy here runs in a normal browser, and the Facebook SDK script in it is inert outside Facebook.

## Contact

- LinkedIn: linkedin.com/in/jamesss42/
- Portfolio site: coming soon — link will be added here once published
