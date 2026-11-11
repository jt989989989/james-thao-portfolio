# Local Chatbot

A simple offline chatbot — Python, standard library only. It answers
questions about All Stars Automations and my GitHub portfolio
from a built-in knowledge base, using plain keyword/intent matching.

No API key, no network calls, no model download, no data leaves your
machine. It is a portfolio demo of the kind of chatbot All Stars
Automations builds for small businesses — just a small, local version.

## What it knows

- The business and its services (AI voice receptionists, SMS/chat,
  appointment booking, CRM, workflow automation)
- How to book a free Systems Assessment
- Pricing: always custom per business — the bot never invents a price,
  it points to the booking link for an itemized proposal
- The GitHub portfolio and individual projects (ADHD My Way, Orbit Hop,
  Life of a Man, SOC Log Analyzer, Phishing Email Detector, SQL
  Detective, and more)
- About me (Director, All Stars Automations; CompTIA Security+;
  B.S. Computer Science, University of Wisconsin)
- Contact and LinkedIn

## Run it

Python 3.10+, no packages to install.

```bash
# Interactive chat — type a question, 'help' for topics, 'quit' to leave
python chatbot.py

# Run the sample questions and print the Q&A
python chatbot.py --demo
```

## How it works

Your question is lowercased and stripped of punctuation, then scored
against each intent's keyword patterns — the highest score wins, ties go
to the first intent listed. Short words like "hi" only match whole words
(so "this" never triggers the greeting), while longer words also match
their prefixes ("book" matches "booking"). Anything with no match gets a
friendly fallback that points you to `help`.

## Tests

```bash
python -m unittest discover -s tests -v
```

14 tests: intent matching including phrasings and case/punctuation
variations, pricing never inventing a price, project answers, the
fallback for unknown questions, demo mode, and a check that the code
imports no networking modules at all.
