import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cloud_posture import Report, scan, load_demo  # noqa: E402


def clean_inventory():
    return {
        "account_id": "111111111111",
        "s3_buckets": [{
            "name": "clean", "public_access_block": True,
            "public_policy": False, "public_acl": False,
            "encryption": True, "versioning": True,
        }],
        "root": {"mfa_enabled": True, "has_access_keys": False},
        "password_policy": {
            "minimum_length": 14, "require_symbols": True,
            "require_numbers": True, "require_uppercase": True,
            "require_lowercase": True, "max_age_days": 90,
        },
        "iam_users": [{
            "name": "alice", "mfa_enabled": True,
            "access_keys": [{"id": "AKIA1", "age_days": 10,
                             "last_used_days_ago": 1}],
        }],
        "security_groups": [{
            "id": "sg-1", "ingress": [
                {"from_port": 443, "to_port": 443, "cidr": "0.0.0.0/0"}],
        }],
        "cloudtrail": {"trails": 1, "logging_enabled": True,
                       "multi_region": True, "log_file_validation": True},
        "rds_instances": [{
            "id": "db-1", "publicly_accessible": False,
            "storage_encrypted": True,
        }],
        "guardduty_enabled": True,
        "kms_keys": [{"id": "key-1", "rotation_enabled": True}],
    }


class TestCleanAccount(unittest.TestCase):
    def test_clean_account_scores_100(self):
        report = scan(clean_inventory())
        self.assertEqual(report.score, 100)
        self.assertEqual(report.grade, "A")
        self.assertEqual(report.findings, [])


class TestS3(unittest.TestCase):
    def test_public_bucket_is_high(self):
        inv = clean_inventory()
        inv["s3_buckets"][0].update(public_policy=True, public_acl=True)
        report = scan(inv)
        self.assertIn("s3-public-access",
                      [f.check for f in report.findings])
        self.assertEqual(report.by_severity("High")[0].severity, "High")

    def test_no_public_access_block_is_medium(self):
        inv = clean_inventory()
        inv["s3_buckets"][0]["public_access_block"] = False
        report = scan(inv)
        self.assertIn("s3-public-access-block",
                      [f.check for f in report.findings])

    def test_unencrypted_and_unversioned(self):
        inv = clean_inventory()
        inv["s3_buckets"][0].update(encryption=False, versioning=False)
        checks = [f.check for f in scan(inv).findings]
        self.assertIn("s3-encryption", checks)
        self.assertIn("s3-versioning", checks)


class TestIAM(unittest.TestCase):
    def test_root_without_mfa_and_with_keys(self):
        inv = clean_inventory()
        inv["root"] = {"mfa_enabled": False, "has_access_keys": True}
        checks = [f.check for f in scan(inv).findings]
        self.assertIn("root-mfa", checks)
        self.assertIn("root-access-keys", checks)

    def test_no_password_policy(self):
        inv = clean_inventory()
        inv["password_policy"] = None
        self.assertIn("iam-password-policy",
                      [f.check for f in scan(inv).findings])

    def test_weak_password_policy(self):
        inv = clean_inventory()
        inv["password_policy"]["minimum_length"] = 8
        inv["password_policy"]["require_symbols"] = False
        self.assertIn("iam-password-policy",
                      [f.check for f in scan(inv).findings])

    def test_user_without_mfa(self):
        inv = clean_inventory()
        inv["iam_users"][0]["mfa_enabled"] = False
        self.assertIn("iam-user-mfa",
                      [f.check for f in scan(inv).findings])

    def test_old_and_unused_keys(self):
        inv = clean_inventory()
        inv["iam_users"][0]["access_keys"] = [
            {"id": "AKIA2", "age_days": 200, "last_used_days_ago": 150}]
        checks = [f.check for f in scan(inv).findings]
        self.assertIn("iam-old-access-key", checks)
        self.assertIn("iam-unused-access-key", checks)


class TestNetworkAndLogging(unittest.TestCase):
    def test_ssh_open_to_world(self):
        inv = clean_inventory()
        inv["security_groups"][0]["ingress"] = [
            {"from_port": 22, "to_port": 22, "cidr": "0.0.0.0/0"}]
        self.assertIn("sg-open-sensitive-port",
                      [f.check for f in scan(inv).findings])

    def test_private_ssh_is_fine(self):
        inv = clean_inventory()
        inv["security_groups"][0]["ingress"] = [
            {"from_port": 22, "to_port": 22, "cidr": "10.0.0.0/16"}]
        self.assertEqual(scan(inv).findings, [])

    def test_https_open_to_world_is_fine(self):
        inv = clean_inventory()
        self.assertEqual(scan(inv).findings, [])

    def test_cloudtrail_off(self):
        inv = clean_inventory()
        inv["cloudtrail"] = {"trails": 0, "logging_enabled": False,
                             "multi_region": False,
                             "log_file_validation": False}
        self.assertIn("cloudtrail-enabled",
                      [f.check for f in scan(inv).findings])

    def test_cloudtrail_not_multi_region(self):
        inv = clean_inventory()
        inv["cloudtrail"]["multi_region"] = False
        self.assertIn("cloudtrail-multi-region",
                      [f.check for f in scan(inv).findings])


class TestRdsGuardDutyKms(unittest.TestCase):
    def test_public_unencrypted_rds(self):
        inv = clean_inventory()
        inv["rds_instances"][0].update(publicly_accessible=True,
                                       storage_encrypted=False)
        checks = [f.check for f in scan(inv).findings]
        self.assertIn("rds-public", checks)
        self.assertIn("rds-encryption", checks)

    def test_guardduty_off_and_kms_no_rotation(self):
        inv = clean_inventory()
        inv["guardduty_enabled"] = False
        inv["kms_keys"][0]["rotation_enabled"] = False
        checks = [f.check for f in scan(inv).findings]
        self.assertIn("guardduty-enabled", checks)
        self.assertIn("kms-rotation", checks)


class TestScoring(unittest.TestCase):
    def test_score_floors_at_zero(self):
        report = Report(account_id="x",
                        findings=[type("F", (), {"severity": "High"})()
                                  for _ in range(20)])
        self.assertEqual(report.score, 0)
        self.assertEqual(report.grade, "F")

    def test_grade_boundaries(self):
        for score, grade in [(95, "A"), (85, "B"), (75, "C"), (65, "D")]:
            report = Report(account_id="x", findings=[])
            report.findings = [
                type("F", (), {"severity": "Low"})()
                for _ in range((100 - score) // 2)]
            self.assertEqual(report.grade, grade, score)


class TestDemo(unittest.TestCase):
    def test_demo_account_scores_below_50(self):
        report = scan(load_demo())
        self.assertLess(report.score, 50)
        checks = {f.check for f in report.findings}
        for expected in ("s3-public-access", "root-mfa", "root-access-keys",
                         "iam-user-mfa", "iam-old-access-key",
                         "iam-unused-access-key", "sg-open-sensitive-port",
                         "rds-public", "guardduty-enabled"):
            self.assertIn(expected, checks)

    def test_demo_cli_runs(self):
        result = subprocess.run(
            [sys.executable, "cloud_posture.py", "--demo"],
            cwd=Path(__file__).parent.parent,
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Score:", result.stdout)

    def test_demo_json_runs(self):
        result = subprocess.run(
            [sys.executable, "cloud_posture.py", "--demo", "--json"],
            cwd=Path(__file__).parent.parent,
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["grade"], "F")
        self.assertLess(data["score"], 50)


if __name__ == "__main__":
    unittest.main()
