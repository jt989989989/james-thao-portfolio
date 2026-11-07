# Lead Generator

A Python CLI that finds small-business leads from Google Maps data — using the **official Google Places API**, not scraping.

Give it a niche and a place, like `plumbers` in `Alpena, MI`, and it returns a scored, deduped CSV of businesses: name, niche, phone, website, address, rating, review count, and a Google Maps link — ready for outreach.

Built as a portfolio project. It is a demo of the lead-generation workflow behind All Stars Automations: find businesses that could use a website, booking, or follow-up system, and rank the ones with the most room to improve first.

## Why the Places API, not scraping

Scraping google.com/maps pages breaks Google's Terms of Service, gets blocked, and breaks whenever Google changes its pages. The Places API is Google's supported way to search for businesses, returns clean structured data, and has clear quotas. This project only reads **public business listings** — no personal emails, no private data, and it never contacts a business. What you do with the leads afterward (email, calls) is a separate step with its own opt-out and compliance rules.

## What it does

- Searches Places text search for a query + location, following page tokens
- Normalizes each place into a lead: name, niche, phone, website, address, city/state/ZIP, rating, review count, Maps link
- Tags the niche from Google's place types (`plumber` → `plumbing`, `dentist` → `dental`, `electrician` → `electrical`, and more)
- Scores each lead 0–100 for outreach value:
  - **+30** no website — the strongest signal
  - **+20** fewer than 10 reviews, **+10** fewer than 50
  - **+10** has a phone number (contactable), **+10** mid rating 3.0–4.4
  - **−5** no phone listed
- Dedupes by Place ID, then by name + phone + address
- Filters: `--min-rating`, `--max-reviews`, `--only-no-website`, `--require-phone`
- Exports CSV (default `leads.csv`) and optional JSON, sorted by score, highest first
- Pauses between API pages to stay well inside quota

## Run it — demo (no key, no network)

```bash
cd projects/lead-generator
python lead_generator.py --demo
```

Expected output on the sample file: **7 leads → leads.csv** (9 sample places minus 1 closed business minus 1 duplicate), top-ranked is Alpena Plumbing Pros (score 70: no website, 4 reviews, rating 4.2). Sample data is fictional — see below.

## Run it — live (needs a Places API key)

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project, enable **Places API (New)**, and create an API key.
2. Restrict the key to the Places API and, if you use it from a server, to your server's IP. Never commit a key.
3. Set it as an environment variable, or pass `--api-key`:

```bash
export GOOGLE_PLACES_API_KEY="your-key-here"
python lead_generator.py plumbers --location "Alpena, MI" --max-results 25 --output leads.csv

# Only businesses with no website, and at most 50 reviews
python lead_generator.py dentists --location "Detroit, MI" --only-no-website --max-reviews 50

# Also write JSON
python lead_generator.py electricians --location "Milwaukee, WI" --json-output leads.json
```

Copy `.env.example` to `.env` if you use a tool that loads one — the key stays out of the repo either way. This repo contains no API key.

## Tests

```bash
python -m unittest discover -s tests -v
```

7 unit tests, all passing: niche mapping, address parsing, scoring, deduping, filtering, closed-business handling, and CSV export.

## Files

| File | What it is |
|---|---|
| `lead_generator.py` | The CLI — search, normalize, score, dedupe, filter, export |
| `sample_places.json` | 9 fictional places in Places API shape, for `--demo` (includes 1 closed business and 1 duplicate, so the demo yields 7 leads) |
| `sample_leads.csv` | Expected CSV output from the demo run |
| `tests/test_lead_generator.py` | Unit tests (stdlib `unittest`, no extra packages) |
| `.env.example` | Where the API key goes — copy, fill in, never commit the real one |

## Skills shown

Python, Google Places API (New) with field masks and pagination, data normalization and deduping, scoring / ranking logic, CLI design with `argparse`, CSV/JSON export, unit tests with `unittest`, API-key handling via environment variables.

## Note

Sample businesses use fictional names, `555-010-xxxx` phone numbers, and `example.com` websites. They are not real businesses, and the demo does not call Google at all.
