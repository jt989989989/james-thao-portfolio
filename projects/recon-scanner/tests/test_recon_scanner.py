"""Tests for the Passive Recon Scanner.

All tests run offline against the saved samples. The one live test at
the bottom (example.com) skips itself when the network is unavailable,
so the suite stays green on machines without internet.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import recon_scanner

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def load_crtsh_sample():
    with open(SAMPLES / "sample_crtsh.json", encoding="utf-8") as f:
        return json.load(f)


def load_headers_sample():
    with open(SAMPLES / "sample_headers.json", encoding="utf-8") as f:
        return json.load(f)


class TestCrtshParsing(unittest.TestCase):
    def test_dedupe_and_sort(self):
        # www.example.com appears twice in the sample; it must come out once.
        result = recon_scanner.parse_crtsh_response(
            load_crtsh_sample(), "example.com"
        )
        self.assertEqual(result, sorted(set(result)))
        self.assertEqual(len(result), 6)

    def test_wildcards_stripped(self):
        result = recon_scanner.parse_crtsh_response(
            load_crtsh_sample(), "example.com"
        )
        self.assertIn("api.example.com", result)
        self.assertNotIn("*.api.example.com", result)

    def test_only_matching_domain_kept(self):
        entries = [
            {"name_value": "example.com\nmail.example.com"},
            {"name_value": "otherdomain.com\nnotexample.com"},
            {"name_value": "sub.example.com.evil.com"},
        ]
        result = recon_scanner.parse_crtsh_response(entries, "example.com")
        self.assertEqual(result, ["example.com", "mail.example.com"])

    def test_empty_response(self):
        self.assertEqual(recon_scanner.parse_crtsh_response([], "example.com"), [])
        self.assertEqual(recon_scanner.parse_crtsh_response(None, "example.com"), [])


class TestHeaderGrading(unittest.TestCase):
    def test_all_present_is_grade_a(self):
        headers = {name: "present" for name in recon_scanner.GRADED_HEADERS}
        grade, present, _ = recon_scanner.grade_headers(headers)
        self.assertEqual((grade, present), ("A", 6))

    def test_sample_headers_grade(self):
        # Sample has HSTS, X-Frame-Options, X-Content-Type-Options (3 of 6).
        sample = load_headers_sample()
        headers = {k.lower(): v for k, v in sample["headers"].items()}
        grade, present, detail = recon_scanner.grade_headers(headers)
        self.assertEqual((grade, present), ("D", 3))
        self.assertTrue(detail["strict-transport-security"]["present"])
        self.assertFalse(detail["content-security-policy"]["present"])

    def test_none_present_is_grade_f(self):
        grade, present, _ = recon_scanner.grade_headers({})
        self.assertEqual((grade, present), ("F", 0))

    def test_each_header_graded(self):
        _, _, detail = recon_scanner.grade_headers({})
        self.assertEqual(
            set(detail), set(recon_scanner.GRADED_HEADERS)
        )
        for info in detail.values():
            self.assertIn("why", info)


class TestReport(unittest.TestCase):
    def test_json_output_shape(self):
        report = recon_scanner.run_demo()
        self.assertEqual(report["domain"], "example.com")
        self.assertEqual(report["subdomain_count"], 6)
        self.assertFalse(report["dns_checked"])  # demo skips DNS
        self.assertEqual(report["tls_version"], "TLSv1.3")
        self.assertTrue(report["tls_ok"])
        self.assertEqual(report["headers_grade"], "D")
        json.dumps(report)  # must be JSON-serializable

    def test_tls_version_handling(self):
        report = recon_scanner.build_report(
            "example.com", ["example.com"], {}, "TLSv1.0", dns_skipped=True
        )
        self.assertFalse(report["tls_ok"])
        report2 = recon_scanner.build_report(
            "example.com", ["example.com"], {}, "TLSv1.2", dns_skipped=True
        )
        self.assertTrue(report2["tls_ok"])
        report3 = recon_scanner.build_report(
            "example.com", ["example.com"], {}, None, dns_skipped=True
        )
        self.assertFalse(report3["tls_ok"])

    def test_demo_offline(self):
        report = recon_scanner.run_demo()
        names = [s["name"] for s in report["subdomains"]]
        self.assertEqual(
            names,
            [
                "api.example.com",
                "dev.example.com",
                "example.com",
                "mail.example.com",
                "shop.example.com",
                "www.example.com",
            ],
        )
        text = recon_scanner.format_text(report)
        self.assertIn("grade D", text)
        self.assertIn("TLSv1.3", text)

    def test_subdomains_only_report(self):
        # Headers/TLS not checked: grade must be None, never a fake F.
        report = recon_scanner.build_report(
            "example.com", ["example.com"], {}, None,
            dns_skipped=True, headers_checked=False,
        )
        self.assertIsNone(report["headers_grade"])
        self.assertIsNone(report["headers_score"])
        self.assertFalse(report["headers_checked"])
        self.assertEqual(report["headers"], {})
        text = recon_scanner.format_text(report)
        self.assertIn("skipped (--subdomains-only)", text)
        self.assertNotIn("grade F", text)

    def test_clean_domain(self):
        self.assertEqual(
            recon_scanner.clean_domain("https://www.example.com/path"), "example.com"
        )
        self.assertEqual(
            recon_scanner.clean_domain("EXAMPLE.COM."), "example.com"
        )
        self.assertEqual(
            recon_scanner.clean_domain("http://api.example.com:8080"), "api.example.com"
        )


class TestLiveSmoke(unittest.TestCase):
    def test_live_example_com(self):
        """One real request, only if the network is up."""
        import socket
        import urllib.error

        try:
            headers, tls_version = recon_scanner.fetch_headers("example.com", timeout=10)
        except (urllib.error.URLError, socket.timeout, OSError) as exc:
            self.skipTest(f"network unavailable: {exc}")
        self.assertIsInstance(headers, dict)
        self.assertIn("content-type", headers)
        self.assertIn(tls_version, ("TLSv1.2", "TLSv1.3", None))


if __name__ == "__main__":
    unittest.main()
