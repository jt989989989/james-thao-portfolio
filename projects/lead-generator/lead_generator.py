#!/usr/bin/env python3
"""Lead Generator — find small-business leads from Google Maps data.

Uses the official Google Places API (New), not screen-scraping of
google.com/maps pages. Scraping Maps pages breaks Google's Terms of
Service and gets blocked; the Places API is the supported way to search
for businesses, and it returns clean, structured fields.

What it does:
  1. Searches Places for a query in a location, e.g. "plumbers in Alpena, MI"
  2. Normalizes each place into a lead: name, niche, phone, website,
     address, rating, review count, Google Maps link
  3. Scores each lead for outreach value (no website / few reviews =
     more room for a website, booking or follow-up system to help)
  4. Dedupes by Place ID, then by name + phone + address
  5. Exports a CSV ready for outreach, plus optional JSON

Needs a Google Places API key for live searches (see README.md).
Without a key, run with --demo to see the full flow on fictional
sample data — no network, no key, no real businesses.

Standard library only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
DEFAULT_RADIUS_M = 20000
DEFAULT_MAX_RESULTS = 25

# Google place types -> the niche tag All Stars Automations uses for outreach.
# Keep this in sync with the outreach niches: plumbing, electrical, hvac,
# roofing, dental, medical, law, cleaning, construction, handyman, etc.
NICHE_BY_TYPE = {
    "plumber": "plumbing",
    "electrician": "electrical",
    "hvac_contractor": "hvac",
    "heating_contractor": "hvac",
    "air_conditioning_contractor": "hvac",
    "roofing_contractor": "roofing",
    "dentist": "dental",
    "dental_clinic": "dental",
    "doctor": "medical",
    "medical_clinic": "medical",
    "lawyer": "law",
    "law_firm": "law",
    "cleaning_service": "cleaning",
    "house_cleaning_service": "cleaning",
    "general_contractor": "construction",
    "home_improvement_store": "construction",
    "handyman": "handyman",
    "pest_control": "pest control",
    "solar_energy_company": "solar",
    "real_estate_agency": "real estate",
    "insurance_agency": "insurance",
    "auto_repair": "auto repair",
    "car_dealer": "auto sales",
    "restaurant": "restaurant",
    "salon": "salon",
    "spa": "salon",
    "gym": "fitness",
    "veterinarian": "veterinary",
    "pet_store": "pet services",
    "florist": "florist",
    "bakery": "bakery",
    "cafe": "cafe",
}

CSV_FIELDS = [
    "business_name",
    "niche",
    "phone",
    "website",
    "address",
    "city",
    "state",
    "zip",
    "rating",
    "review_count",
    "google_maps_url",
    "lead_score",
    "notes",
]


def niche_for(types: list[str], query: str = "") -> str:
    """Map Google place types to a short outreach niche, else the query word."""
    for place_type in types or []:
        if place_type in NICHE_BY_TYPE:
            return NICHE_BY_TYPE[place_type]
    # Fall back to the first word of the query, e.g. "plumbers" -> "plumbing".
    first = (query or "").strip().split()
    if first:
        word = re.sub(r"s$", "", first[0].lower())
        return {"plumber": "plumbing", "dentist": "dental"}.get(word, word)
    return "general"


def parse_address(formatted_address: str) -> dict[str, str]:
    """Split '123 Main St, Alpena, MI 49707, USA' into city/state/zip."""
    parts = [p.strip() for p in (formatted_address or "").split(",")]
    city = state = zip_code = ""
    address = parts[0] if parts else ""
    # Look for a "MI 49707" style part anywhere after the street.
    for part in parts[1:]:
        match = re.match(r"^([A-Z]{2})\s+(\d{5})(?:-\d{4})?$", part)
        if match:
            state, zip_code = match.groups()
        elif not city and re.match(r"^[A-Za-z .'-]+$", part):
            city = part
    return {"address": address, "city": city, "state": state, "zip": zip_code}


def normalize_place(place: dict, query: str = "") -> dict | None:
    """Turn one Places API place into a lead dict. Returns None if unusable."""
    name = (place.get("displayName") or {}).get("text", "").strip()
    if not name:
        return None
    if place.get("businessStatus") == "CLOSED_PERMANENTLY":
        return None

    addr = parse_address(place.get("formattedAddress", ""))
    rating = place.get("rating")
    review_count = place.get("userRatingCount") or 0
    lead = {
        "business_name": name,
        "niche": niche_for(place.get("types") or [], query),
        "phone": place.get("nationalPhoneNumber", "") or "",
        "website": place.get("websiteUri", "") or "",
        "address": addr["address"],
        "city": addr["city"],
        "state": addr["state"],
        "zip": addr["zip"],
        "rating": rating if rating is not None else "",
        "review_count": review_count,
        "google_maps_url": place.get("googleMapsUri", "") or "",
        "place_id": place.get("id", "") or "",
        "lead_score": 0,
        "notes": "",
    }
    lead["lead_score"], lead["notes"] = score_lead(lead)
    return lead


def score_lead(lead: dict) -> tuple[int, str]:
    """Score 0-100 for outreach value. Higher = more likely to need help.

    No website is the strongest signal (needs a website / booking /
    follow-up system). Few reviews is next (needs visibility). Having a
    phone number makes the lead contactable, so it adds points.
    """
    score = 0
    notes: list[str] = []
    if not lead.get("website"):
        score += 30
        notes.append("no website")
    if not lead.get("phone"):
        score -= 5
        notes.append("no phone listed")
    else:
        score += 10
    reviews = lead.get("review_count") or 0
    if reviews < 10:
        score += 20
        notes.append("few reviews")
    elif reviews < 50:
        score += 10
    rating = lead.get("rating")
    if isinstance(rating, (int, float)) and 3.0 <= rating < 4.5:
        score += 10
        notes.append("mid rating — room to improve")
    return max(0, min(100, score)), "; ".join(notes)


def dedupe_leads(leads: list[dict]) -> list[dict]:
    """Dedupe by Place ID first, then by normalized name + phone + address."""
    seen_ids: set[str] = set()
    seen_keys: set[str] = set()
    out: list[dict] = []
    for lead in leads:
        place_id = lead.get("place_id", "")
        if place_id:
            if place_id in seen_ids:
                continue
            seen_ids.add(place_id)
        key = (
            re.sub(r"[^a-z0-9]", "", lead["business_name"].lower()),
            re.sub(r"\D", "", lead.get("phone", "")),
            re.sub(r"[^a-z0-9]", "", lead.get("address", "").lower()),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        out.append(lead)
    return out


def filter_leads(
    leads: list[dict],
    *,
    min_rating: float | None = None,
    max_reviews: int | None = None,
    only_no_website: bool = False,
    require_phone: bool = False,
) -> list[dict]:
    """Apply the outreach filters. Each filter only removes, never adds."""
    out = []
    for lead in leads:
        rating = lead.get("rating")
        if min_rating is not None and isinstance(rating, (int, float)):
            if rating < min_rating:
                continue
        if max_reviews is not None and (lead.get("review_count") or 0) > max_reviews:
            continue
        if only_no_website and lead.get("website"):
            continue
        if require_phone and not lead.get("phone"):
            continue
        out.append(lead)
    return out


def search_places(
    api_key: str,
    query: str,
    *,
    location: str = "",
    radius_m: int = DEFAULT_RADIUS_M,
    max_results: int = DEFAULT_MAX_RESULTS,
    delay_s: float = 1.0,
) -> list[dict]:
    """Search the Places API (New) text search, following page tokens.

    One request per page, with a short pause between pages to stay well
    inside quota. Raises RuntimeError with the API's message on failure.
    """
    text_query = f"{query} in {location}" if location else query
    places: list[dict] = []
    page_token: str | None = None
    while len(places) < max_results:
        body: dict = {
            "textQuery": text_query,
            "pageSize": min(20, max_results - len(places)),
            "fieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.nationalPhoneNumber,places.websiteUri,places.rating,"
                "places.userRatingCount,places.businessStatus,places.types,"
                "places.googleMapsUri"
            ),
        }
        # Geography comes from the location string in textQuery
        # (e.g. "plumbers in Alpena, MI"). A circle bias would need real
        # latitude/longitude, so radius_m is accepted for future use and
        # intentionally not sent as a 0,0 bias.
        if page_token:
            body["pageToken"] = page_token
        req = urllib.request.Request(
            PLACES_URL,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": body["fieldMask"],
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"Places API error {exc.code}: {detail}") from exc
        places.extend(data.get("places", []))
        page_token = data.get("nextPageToken")
        if not page_token or not data.get("places"):
            break
        time.sleep(delay_s)
    return places[:max_results]


def load_sample(path: Path) -> list[dict]:
    """Load the fictional demo places file (same shape as the API)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("places", [])
    return data


def export_csv(leads: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for lead in leads:
            writer.writerow({k: lead.get(k, "") for k in CSV_FIELDS})


def export_json(leads: list[dict], path: Path) -> None:
    public = [{k: v for k, v in lead.items() if k != "place_id"} for lead in leads]
    path.write_text(json.dumps(public, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate business leads from Google Places (Google Maps data)."
    )
    parser.add_argument("query", nargs="?", help='e.g. "plumbers" or "dentists"')
    parser.add_argument("--location", default="", help='e.g. "Alpena, MI"')
    parser.add_argument("--api-key", default=os.environ.get("GOOGLE_PLACES_API_KEY", ""),
                        help="Places API key (or set GOOGLE_PLACES_API_KEY)")
    parser.add_argument("--demo", action="store_true",
                        help="Use fictional sample_places.json — no key, no network")
    parser.add_argument("--sample", default="sample_places.json",
                        help="Sample file for --demo")
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    parser.add_argument("--min-rating", type=float, default=None)
    parser.add_argument("--max-reviews", type=int, default=None)
    parser.add_argument("--only-no-website", action="store_true")
    parser.add_argument("--require-phone", action="store_true")
    parser.add_argument("--output", default="leads.csv")
    parser.add_argument("--json-output", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.demo:
        raw = load_sample(Path(args.sample))
        print(f"Demo mode: {len(raw)} sample places (fictional data, no API call).")
    else:
        if not args.query:
            print("error: provide a query, e.g. lead_generator.py plumbers --location 'Alpena, MI'",
                  file=sys.stderr)
            return 2
        if not args.api_key:
            print("error: no API key. Set GOOGLE_PLACES_API_KEY or use --demo.",
                  file=sys.stderr)
            return 2
        try:
            raw = search_places(args.api_key, args.query, location=args.location,
                                max_results=args.max_results)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Places API returned {len(raw)} places for '{args.query}'.")

    leads = [lead for place in raw if (lead := normalize_place(place, args.query or ""))]
    leads = dedupe_leads(leads)
    leads = filter_leads(
        leads,
        min_rating=args.min_rating,
        max_reviews=args.max_reviews,
        only_no_website=args.only_no_website,
        require_phone=args.require_phone,
    )
    leads.sort(key=lambda lead: lead["lead_score"], reverse=True)

    export_csv(leads, Path(args.output))
    if args.json_output:
        export_json(leads, Path(args.json_output))

    print(f"{len(leads)} leads -> {args.output} (sorted by lead score, highest first)")
    for lead in leads[:10]:
        print(f"  {lead['lead_score']:>3}  {lead['business_name']} — {lead['niche']} — "
              f"{lead['phone'] or 'no phone'} — {lead['website'] or 'no website'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
