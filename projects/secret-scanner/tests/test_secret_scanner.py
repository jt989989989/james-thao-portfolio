"""Tests for the Secret Scanner — every rule, plus the false positives."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from secret_scanner import check_line, main, scan_directory, shannon_entropy


def rules_of(line: str) -> set[str]:
    return {hit["rule"] for hit in check_line(line)}


class TestRuleDetection(unittest.TestCase):
    def test_aws_access_key_detected(self):
        hits = check_line('key = "AKIAIOSFODNN7EXAMPLE"')
        self.assertIn("aws-access-key", rules_of('key = "AKIAIOSFODNN7EXAMPLE"'))
        self.assertEqual(hits[0]["severity"], "high")

    def test_aws_secret_key_detected(self):
        line = (
            'aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"'
        )
        self.assertIn("aws-secret-key", rules_of(line))

    def test_github_token_detected(self):
        token = "ghp_" + "faketoken" + "0" * 27
        self.assertIn("github-token", rules_of(f'token = "{token}"'))

    def test_github_fine_grained_token_detected(self):
        token = "github_pat_11ABCDEFGH0123456789abcdEFGHijklmnop0000000000"
        self.assertIn("github-fine-grained-token", rules_of(f't = "{token}"'))

    def test_slack_token_detected(self):
        token = "xoxb-fake-slack-token-for-demo"
        self.assertIn("slack-token", rules_of(f'token = "{token}"'))

    def test_jwt_detected(self):
        jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiJleGFtcGxlLXVzZXIiLCJuYW1lIjoiSmFtZXMgRXhhbXBsZSJ9"
            ".fakeSignature0000000000000000000000"
        )
        self.assertIn("jwt", rules_of(f'auth = "Bearer {jwt}"'))

    def test_private_key_detected(self):
        self.assertIn(
            "private-key", rules_of("-----BEGIN RSA PRIVATE KEY-----")
        )

    def test_stripe_live_key_detected(self):
        self.assertIn(
            "stripe-live-key",
            rules_of('key = "sk_live_4eC39HqLyjWDarjtT1z"'),
        )

    def test_password_assignment_detected(self):
        hits = check_line('password = "S3cretP@ssw0rdExample"')
        self.assertEqual([h["rule"] for h in hits], ["password-assignment"])
        self.assertEqual(hits[0]["severity"], "medium")


class TestFalsePositives(unittest.TestCase):
    def test_password_word_in_comment_not_flagged(self):
        self.assertEqual(
            check_line("# TODO: ask the user for their password"), []
        )

    def test_placeholder_password_not_flagged(self):
        self.assertEqual(check_line('password = "changeme"'), [])

    def test_low_entropy_string_not_flagged(self):
        self.assertEqual(check_line('x = "aaaaaaaaaaaaaaaaaaaa"'), [])

    def test_short_string_not_flagged(self):
        self.assertEqual(check_line('x = "hello123"'), [])

    def test_high_entropy_string_flagged_low(self):
        hits = check_line('token = "Xk9mQ2vL8pR4tY7wN3bZ6sD1fG5hJ0"')
        self.assertEqual([h["rule"] for h in hits], ["generic-high-entropy"])
        self.assertEqual(hits[0]["severity"], "low")

    def test_entropy_function(self):
        self.assertLess(shannon_entropy("aaaaaaaaaaaaaaaaaaaa"), 1.0)
        self.assertGreater(
            shannon_entropy("Xk9mQ2vL8pR4tY7wN3bZ6sD1fG5hJ0"), 4.5
        )


class TestDirectoryScanning(unittest.TestCase):
    def test_git_directory_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            git_dir = os.path.join(tmp, ".git")
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, "config"), "w") as f:
                f.write('key = "AKIAIOSFODNN7EXAMPLE"\n')
            with open(os.path.join(tmp, "app.py"), "w") as f:
                f.write('key = "AKIAIOSFODNN7EXAMPLE"\n')
            findings = scan_directory(tmp)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].path, "app.py")

    def test_exclude_flag_skips_matching_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "secret.py"), "w") as f:
                f.write('key = "AKIAIOSFODNN7EXAMPLE"\n')
            findings = scan_directory(tmp, exclude=["secret.py"])
            self.assertEqual(findings, [])

    def test_clean_directory_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "app.py"), "w") as f:
                f.write('x = "hello world"\n')
            self.assertEqual(main([tmp]), 0)

    def test_findings_exit_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "app.py"), "w") as f:
                f.write('key = "AKIAIOSFODNN7EXAMPLE"\n')
            self.assertEqual(main([tmp]), 1)


if __name__ == "__main__":
    unittest.main()
