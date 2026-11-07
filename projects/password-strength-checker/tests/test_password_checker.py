"""Unit tests for the Password Strength Checker. Run: python -m unittest discover -s tests -v"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from password_checker import analyze_password, rating_for  # noqa: E402


class TestRatings(unittest.TestCase):
    def test_rating_bands(self):
        self.assertEqual(rating_for(0), "Very Weak")
        self.assertEqual(rating_for(25), "Weak")
        self.assertEqual(rating_for(50), "Fair")
        self.assertEqual(rating_for(70), "Strong")
        self.assertEqual(rating_for(90), "Very Strong")


class TestScoring(unittest.TestCase):
    def test_common_password_scores_zero(self):
        self.assertEqual(analyze_password("password")["score"], 0)
        self.assertEqual(analyze_password("123456")["score"], 0)

    def test_empty_password(self):
        result = analyze_password("")
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["rating"], "Very Weak")

    def test_long_passphrase_beats_short_complex(self):
        passphrase = analyze_password("correct horse battery staple")
        short = analyze_password("Tr0ub4dor&3")
        self.assertGreater(passphrase["score"], short["score"])
        self.assertEqual(passphrase["rating"], "Strong")

    def test_long_random_password_is_very_strong(self):
        result = analyze_password("J7#kP9!mQ2$vX8@wL4&zT1a")
        self.assertEqual(result["score"], 80)
        self.assertEqual(result["rating"], "Very Strong")

    def test_sequence_is_penalized(self):
        with_seq = analyze_password("Abcdefgh1234!")
        # Same length/variety without a sequence scores higher.
        without_seq = analyze_password("Akdjehfi1934!")
        self.assertLess(with_seq["score"], without_seq["score"])
        self.assertTrue(any("sequence" in issue for issue in with_seq["issues"]))

    def test_username_is_flagged(self):
        result = analyze_password("JamesThao2026!", username="JamesThao")
        self.assertTrue(any("username" in issue for issue in result["issues"]))

    def test_repeated_characters_are_penalized(self):
        result = analyze_password("Aaaabbbb1234!")
        self.assertTrue(any("repeated" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
