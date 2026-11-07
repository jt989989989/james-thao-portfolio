"""Unit tests for the Lead Generator. Run: python -m unittest discover -s tests -v"""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lead_generator import (  # noqa: E402
    dedupe_leads,
    export_csv,
    filter_leads,
    niche_for,
    normalize_place,
    parse_address,
    score_lead,
)


class TestNicheAndAddress(unittest.TestCase):
    def test_niche_from_place_type(self):
        self.assertEqual(niche_for(["plumber"]), "plumbing")
        self.assertEqual(niche_for(["dentist", "dental_clinic"]), "dental")
        self.assertEqual(niche_for(["hvac_contractor"]), "hvac")

    def test_parse_address(self):
        parsed = parse_address("123 River St, Alpena, MI 49707, USA")
        self.assertEqual(parsed["city"], "Alpena")
        self.assertEqual(parsed["state"], "MI")
        self.assertEqual(parsed["zip"], "49707")
        self.assertEqual(parsed["address"], "123 River St")


class TestScoringAndNormalize(unittest.TestCase):
    def test_no_website_scores_highest(self):
        lead = {"website": "", "phone": "(555) 010-1001", "review_count": 4, "rating": 4.2}
        score, notes = score_lead(lead)
        self.assertEqual(score, 70)  # 30 no website + 10 phone + 20 few reviews + 10 mid rating
        self.assertIn("no website", notes)

    def test_closed_business_is_skipped(self):
        place = {
            "displayName": {"text": "Closed Corner Cafe"},
            "formattedAddress": "1 Main St, Alpena, MI 49707, USA",
            "businessStatus": "CLOSED_PERMANENTLY",
            "types": ["cafe"],
        }
        self.assertIsNone(normalize_place(place, "cafes"))


class TestDedupeAndFilter(unittest.TestCase):
    def test_dedupe_by_place_id(self):
        base = {"business_name": "Alpena Plumbing Pros", "phone": "(555) 010-1001",
                "address": "123 River St", "place_id": "ChIJsample0001"}
        self.assertEqual(len(dedupe_leads([base, dict(base)])), 1)

    def test_filter_only_no_website(self):
        leads = [
            {"business_name": "A", "website": "", "phone": "x", "rating": 4.0, "review_count": 5},
            {"business_name": "B", "website": "https://b.example.com", "phone": "x",
             "rating": 4.0, "review_count": 5},
        ]
        self.assertEqual([l["business_name"] for l in filter_leads(leads, only_no_website=True)], ["A"])
        self.assertEqual(len(filter_leads(leads, max_reviews=4)), 0)

    def test_export_csv_round_trip(self):
        leads = [{
            "business_name": "Alpena Plumbing Pros", "niche": "plumbing",
            "phone": "(555) 010-1001", "website": "", "address": "123 River St",
            "city": "Alpena", "state": "MI", "zip": "49707", "rating": 4.2,
            "review_count": 4, "google_maps_url": "https://maps.google.com/?cid=1001",
            "lead_score": 70, "notes": "no website; few reviews",
        }]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.csv"
            export_csv(leads, path)
            with path.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(rows[0]["business_name"], "Alpena Plumbing Pros")
            self.assertEqual(rows[0]["lead_score"], "70")


if __name__ == "__main__":
    unittest.main()
