"""Tests for the Phishing Email Detector (v1).

Run from the project folder:
    python -m unittest discover -s tests -v
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from phishing_detector import (  # noqa: E402
    MODEL,
    analyze,
    load_sample,
    parse_email,
    rule_signals,
    verdict_for,
)

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def sample_text(name: str) -> str:
    return (SAMPLES / f"{name}.txt").read_text(encoding="utf-8")


class TestParseEmail(unittest.TestCase):
    def test_headers_and_body_split(self):
        email = parse_email(sample_text("phishing_01_account_locked"))
        self.assertIn("northbank-secure.example", email["from"])
        self.assertEqual(email["reply_to_domain"], "northbank-helpdesk.example")
        self.assertIn("suspended", email["subject"].lower())
        self.assertIn("verify your password", email["body"].lower())

    def test_markdown_link_extracted_with_text_and_url(self):
        email = parse_email(sample_text("phishing_01_account_locked"))
        self.assertEqual(len(email["links"]), 1)
        link = email["links"][0]
        self.assertEqual(link["text"], "northbank.example/account/verify")
        self.assertIn("northbank-secure.example", link["url"])

    def test_attachment_line_parsed(self):
        email = parse_email(sample_text("phishing_03_invoice_attachment"))
        self.assertEqual(email["attachments"], ["delivery-invoice.zip"])

    def test_plain_url_extracted(self):
        email = parse_email(sample_text("legit_01_order_confirmation"))
        self.assertEqual(len(email["links"]), 1)
        self.assertIn("shopsphere.example", email["links"][0]["url"])

    def test_empty_email_does_not_crash(self):
        report = analyze("")
        # No words, no signals: the model sits at its neutral prior (50%),
        # so the blended score is 25 — still firmly LEGITIMATE.
        self.assertEqual(report["verdict"], "LEGITIMATE")
        self.assertLess(report["score"], 40)
        self.assertEqual(report["signals"], [])


class TestRuleSignals(unittest.TestCase):
    def _signals_named(self, text):
        return {s["name"] for s in rule_signals(parse_email(text))}

    def test_urgency_and_credentials_fire(self):
        names = self._signals_named(sample_text("phishing_01_account_locked"))
        self.assertIn("Urgent / threatening language", names)
        self.assertIn("Asks for credentials or account verification", names)

    def test_reply_to_mismatch_fires(self):
        names = self._signals_named(sample_text("phishing_01_account_locked"))
        self.assertIn("Reply-To domain differs from sender domain", names)

    def test_link_text_mismatch_fires(self):
        names = self._signals_named(sample_text("phishing_01_account_locked"))
        self.assertIn(
            "Link text shows a different destination than the real URL", names
        )

    def test_shortener_fires(self):
        names = self._signals_named(sample_text("phishing_02_prize_winner"))
        self.assertIn("Link uses a URL shortener (destination hidden)", names)
        self.assertIn("Prize / free-gift lure", names)

    def test_ip_link_fires(self):
        names = self._signals_named(sample_text("phishing_04_password_reset"))
        self.assertIn("Link points to a raw IP address, not a domain", names)

    def test_risky_attachment_fires(self):
        names = self._signals_named(sample_text("phishing_03_invoice_attachment"))
        self.assertIn("Unexpected risky attachment", names)

    def test_brand_display_mismatch_fires(self):
        text = (
            "From: Northbank Security <alerts@some-random.example>\n"
            "Subject: Hello\n\nJust checking in, nothing to see here."
        )
        names = self._signals_named(text)
        self.assertIn(
            "Display name claims a brand its domain does not match", names
        )

    def test_free_mailbox_company_claim_fires(self):
        text = (
            "From: Northbank Support <support@gmail.com>\n"
            "Subject: Hello\n\nJust checking in, nothing to see here."
        )
        names = self._signals_named(text)
        self.assertIn(
            "Claims to be a company but sent from a free mailbox", names
        )

    def test_legit_email_triggers_no_signals(self):
        for name in ("legit_01_order_confirmation", "legit_02_team_meeting",
                     "legit_03_newsletter", "legit_04_bank_statement"):
            with self.subTest(sample=name):
                self.assertEqual(
                    rule_signals(parse_email(sample_text(name))), []
                )


class TestModel(unittest.TestCase):
    def test_training_corpus_balanced(self):
        self.assertEqual(MODEL.n_phish, 10)
        self.assertEqual(MODEL.n_legit, 10)
        self.assertGreater(len(MODEL.vocab), 50)

    def test_phishing_training_text_scores_high(self):
        prob, _ = MODEL.phishing_probability(
            "URGENT verify your password immediately or your account will be "
            "suspended within 24 hours"
        )
        self.assertGreater(prob, 0.7)

    def test_legit_training_text_scores_low(self):
        prob, _ = MODEL.phishing_probability(
            "Your monthly statement is ready. Sign in through our app if you "
            "would like to review it. No action is needed."
        )
        self.assertLess(prob, 0.4)


class TestVerdicts(unittest.TestCase):
    def test_verdict_bands(self):
        self.assertEqual(verdict_for(0), "LEGITIMATE")
        self.assertEqual(verdict_for(39), "LEGITIMATE")
        self.assertEqual(verdict_for(40), "SUSPICIOUS")
        self.assertEqual(verdict_for(69), "SUSPICIOUS")
        self.assertEqual(verdict_for(70), "PHISHING")
        self.assertEqual(verdict_for(100), "PHISHING")

    def test_all_phishing_samples_flagged(self):
        for name in ("phishing_01_account_locked", "phishing_02_prize_winner",
                     "phishing_03_invoice_attachment",
                     "phishing_04_password_reset"):
            with self.subTest(sample=name):
                report = analyze(sample_text(name))
                self.assertIn(report["verdict"], ("PHISHING", "SUSPICIOUS"))
                self.assertGreaterEqual(report["score"], 40)

    def test_all_legit_samples_pass(self):
        for name in ("legit_01_order_confirmation", "legit_02_team_meeting",
                     "legit_03_newsletter", "legit_04_bank_statement"):
            with self.subTest(sample=name):
                report = analyze(sample_text(name))
                self.assertEqual(report["verdict"], "LEGITIMATE")
                self.assertLess(report["score"], 40)

    def test_report_is_json_serializable(self):
        report = analyze(sample_text("phishing_01_account_locked"))
        parsed = json.loads(json.dumps(report))
        self.assertEqual(parsed["verdict"], report["verdict"])

    def test_load_sample_rejects_unknown_name(self):
        with self.assertRaises(FileNotFoundError):
            load_sample("no_such_sample")


if __name__ == "__main__":
    unittest.main()
