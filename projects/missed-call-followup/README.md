# Missed-Call Follow-Up

A small Python CLI that turns a CSV of missed calls into a prioritized follow-up queue with ready-to-send message drafts.

Built as a portfolio project. It is a demo only: it writes text files, it does not send SMS, make calls, or connect to any CRM or phone system, and the sample data is fictional. No API keys or real customer data are included.

## What it does

- Reads `name,business,phone,missed_at,reason` from CSV
- Merges duplicate numbers, keeping the newest call and counting repeats
- Prioritizes newest first, then repeat callers, then "no answer" over "voicemail left"
- Drafts a short, personal follow-up message per caller, with a STOP opt-out line
- Optionally writes the queue as CSV and the messages as Markdown

## Run it

```bash
python followup.py sample_calls.csv
python followup.py sample_calls.csv --output queue.csv --messages messages.md
```

Expected output on the sample file: 4 unique numbers from 5 calls, Maria Lopez ranked #1 as a repeat caller.

## Skills shown

Python, CSV handling, sorting / prioritization logic, CLI design with `argparse`, clear separation between data, ranking, and message drafting.

## Note

Phone numbers in the sample use the fictional `555-010-xxxx` range.
