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
    main,
    niche_for,
    normalize_place,
    parse_address,
    score_lead,
    top_leads_summary,
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


class TestRatingAndOpenNowFilters(unittest.TestCase):
    def _lead(self, name, rating, open_now=None):
        return {"business_name": name, "website": "", "phone": "x",
                "rating": rating, "review_count": 5, "open_now": open_now}

    def test_max_rating_keeps_low_rated_only(self):
        leads = [self._lead("Low", 3.2), self._lead("Mid", 4.0), self._lead("High", 4.8)]
        kept = filter_leads(leads, max_rating=4.0)
        self.assertEqual([l["business_name"] for l in kept], ["Low", "Mid"])

    def test_rating_range_combines(self):
        leads = [self._lead("Low", 3.2), self._lead("Mid", 4.0), self._lead("High", 4.8)]
        kept = filter_leads(leads, min_rating=3.5, max_rating=4.5)
        self.assertEqual([l["business_name"] for l in kept], ["Mid"])

    def test_unrated_lead_passes_rating_filters(self):
        leads = [self._lead("NoRating", "")]
        self.assertEqual(len(filter_leads(leads, min_rating=4.0)), 1)
        self.assertEqual(len(filter_leads(leads, max_rating=4.0)), 1)

    def test_open_now_keeps_only_open(self):
        leads = [self._lead("Open", 4.0, True), self._lead("Closed", 4.0, False),
                 self._lead("Unknown", 4.0, None)]
        kept = filter_leads(leads, open_now_only=True)
        self.assertEqual([l["business_name"] for l in kept], ["Open"])

    def test_normalize_captures_open_now(self):
        base = {
            "displayName": {"text": "Open Shop"},
            "formattedAddress": "1 Main St, Alpena, MI 49707, USA",
            "types": ["cafe"],
        }
        open_place = dict(base, currentOpeningHours={"openNow": True})
        self.assertIs(normalize_place(open_place, "cafes")["open_now"], True)
        closed_place = dict(base, currentOpeningHours={"openNow": False})
        self.assertIs(normalize_place(closed_place, "cafes")["open_now"], False)
        # No hours data at all -> unknown, not closed.
        self.assertIsNone(normalize_place(base, "cafes")["open_now"])


class TestTopLeadsSummary(unittest.TestCase):
    def _lead(self, name, score, niche="plumbing"):
        return {"business_name": name, "niche": niche, "phone": "(555) 010-1001",
                "website": "", "rating": 4.2, "review_count": 4,
                "lead_score": score, "notes": "no website"}

    def test_summary_ranks_and_limits(self):
        leads = [self._lead(f"Shop {i}", 100 - i) for i in range(12)]
        summary = top_leads_summary(leads)
        self.assertIn("Top 10 leads by score:", summary)
        self.assertIn(" 1. [100] Shop 0", summary)
        self.assertIn("10. [ 91] Shop 9", summary)
        self.assertNotIn("Shop 10", summary)
        self.assertIn("12 leads total, average score 94, 12 with no website.", summary)

    def test_summary_empty_list(self):
        summary = top_leads_summary([])
        self.assertIn("Top 10 leads by score:", summary)
        self.assertIn("0 leads total, average score 0, 0 with no website.", summary)


class TestDemoEndToEnd(unittest.TestCase):
    def test_demo_yields_seven_leads(self):
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "leads.csv"
            rc = main(["--demo", "--sample", str(project / "sample_places.json"),
                       "--output", str(out)])
            self.assertEqual(rc, 0)
            with out.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 7)
            self.assertEqual(rows[0]["business_name"], "Alpena Plumbing Pros")
            self.assertEqual(rows[0]["open_now"], "yes")
            self.assertEqual(rows[0]["lead_score"], "70")

    def test_demo_open_now_filter(self):
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "leads.csv"
            rc = main(["--demo", "--sample", str(project / "sample_places.json"),
                       "--output", str(out), "--open-now"])
            self.assertEqual(rc, 0)
            with out.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            names = [r["business_name"] for r in rows]
            self.assertEqual(len(rows), 5)
            self.assertNotIn("Sunrise Roofing Co", names)
            self.assertNotIn("Northwood HVAC & Heating", names)


if __name__ == "__main__":
    unittest.main()
