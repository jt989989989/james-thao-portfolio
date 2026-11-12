#!/usr/bin/env python3
"""Cloud Security Posture Checker — v1.0.0.

I built this as a defensive checker for my own AWS accounts: it reads a
snapshot of an account's configuration and flags the misconfigurations
that actually get people breached — public S3 buckets, users without MFA,
old access keys, security groups open to the world, no CloudTrail, and
unencrypted databases.

It never changes anything. It only reads, and it only reports.

Three ways to run it:

1. Demo (no AWS account, no credentials, nothing to install):

       python cloud_posture.py --demo

   Scores a built-in fictional account so you can see every check fire.

2. Snapshot file (my recommended way to check a real account):

       python cloud_posture.py --input my-account.json

   Export the account inventory yourself with the AWS CLI (read-only
   calls only — see README.md), save it in the snapshot format, and this
   tool scores it. Your credentials never touch this tool.

3. Live scan (needs boto3 and read-only AWS credentials configured):

       pip install boto3
       python cloud_posture.py --live

   Makes read-only AWS API calls (ListBuckets, ListUsers,
   DescribeSecurityGroups, DescribeTrails, and friends). If boto3 is
   not installed it says so and points you at --demo / --input instead.

Exit codes: 0 = scan completed (even with findings), 2 = usage error
or the input file / live scan could not be read.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"
SENSITIVE_PORTS = {22, 3389, 3306, 5432, 27017, 6379, 1433}
SEVERITY_DEDUCTION = {"High": 10, "Medium": 5, "Low": 2}


@dataclass
class Finding:
    """One misconfiguration, with the fix spelled out."""

    check: str
    resource: str
    severity: str  # High / Medium / Low
    message: str
    remediation: str

    def as_dict(self) -> dict:
        return {
            "check": self.check,
            "resource": self.resource,
            "severity": self.severity,
            "message": self.message,
            "remediation": self.remediation,
        }


@dataclass
class Report:
    account_id: str
    findings: list = field(default_factory=list)
    checks_run: int = 0

    @property
    def score(self) -> int:
        total = sum(SEVERITY_DEDUCTION[f.severity] for f in self.findings)
        return max(0, 100 - total)

    @property
    def grade(self) -> str:
        score = self.score
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def by_severity(self, severity: str) -> list:
        return [f for f in self.findings if f.severity == severity]

    def as_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "score": self.score,
            "grade": self.grade,
            "checks_run": self.checks_run,
            "summary": {
                "high": len(self.by_severity("High")),
                "medium": len(self.by_severity("Medium")),
                "low": len(self.by_severity("Low")),
            },
            "findings": [f.as_dict() for f in self.findings],
        }


# ---------------------------------------------------------------- checks

def check_s3(inventory: dict, findings: list) -> int:
    count = 0
    for bucket in inventory.get("s3_buckets", []):
        name = bucket.get("name", "unknown")
        count += 1
        if bucket.get("public_policy") or bucket.get("public_acl"):
            findings.append(Finding(
                "s3-public-access", name, "High",
                "Bucket is publicly accessible (public policy or public ACL).",
                "Enable Block Public Access on the bucket and remove the "
                "public policy / ACL; serve public content through CloudFront."))
        elif not bucket.get("public_access_block"):
            findings.append(Finding(
                "s3-public-access-block", name, "Medium",
                "Block Public Access is not enabled on this bucket.",
                "Enable all four Block Public Access settings on the bucket."))
        if not bucket.get("encryption"):
            findings.append(Finding(
                "s3-encryption", name, "Medium",
                "Bucket has no default encryption at rest.",
                "Turn on default encryption (SSE-S3 or SSE-KMS) for the bucket."))
        if not bucket.get("versioning"):
            findings.append(Finding(
                "s3-versioning", name, "Low",
                "Bucket versioning is off, so a deleted or overwritten object "
                "cannot be recovered.",
                "Enable versioning on the bucket."))
    return count


def check_iam(inventory: dict, findings: list) -> int:
    count = 0
    root = inventory.get("root", {})
    if root:
        count += 1
        if not root.get("mfa_enabled"):
            findings.append(Finding(
                "root-mfa", "root", "High",
                "The root account has no MFA device.",
                "Attach a hardware or virtual MFA device to the root account "
                "and lock the root credentials away."))
        if root.get("has_access_keys"):
            findings.append(Finding(
                "root-access-keys", "root", "High",
                "The root account has access keys — root should never be "
                "used with programmatic keys.",
                "Delete the root access keys and use an IAM user or role instead."))
    policy = inventory.get("password_policy")
    count += 1
    if policy is None:
        findings.append(Finding(
            "iam-password-policy", "account", "Medium",
            "No IAM password policy is set, so users can pick weak passwords.",
            "Set a password policy: at least 14 characters, symbols, numbers, "
            "mixed case, and a maximum age of 90 days."))
    else:
        weak = []
        if (policy.get("minimum_length") or 0) < 14:
            weak.append("minimum length under 14")
        for key in ("require_symbols", "require_numbers",
                    "require_uppercase", "require_lowercase"):
            if not policy.get(key):
                weak.append(key.replace("require_", "no required "))
        if weak:
            findings.append(Finding(
                "iam-password-policy", "account", "Medium",
                "Password policy is weak: " + ", ".join(weak) + ".",
                "Strengthen the policy: 14+ characters, symbols, numbers, "
                "and mixed case."))
        max_age = policy.get("max_age_days")
        if max_age is not None and max_age > 90:
            findings.append(Finding(
                "iam-password-rotation", "account", "Low",
                f"Passwords may live for {max_age} days before rotation.",
                "Set the maximum password age to 90 days or less."))
    for user in inventory.get("iam_users", []):
        name = user.get("name", "unknown")
        count += 1
        if not user.get("mfa_enabled"):
            findings.append(Finding(
                "iam-user-mfa", name, "High",
                "IAM user has no MFA device.",
                "Require MFA for this user (enforce it with an IAM policy)."))
        for key in user.get("access_keys", []):
            age = key.get("age_days")
            if age is not None and age > 90:
                findings.append(Finding(
                    "iam-old-access-key", f"{name} ({key.get('id', 'key')})",
                    "Medium",
                    f"Access key is {age} days old.",
                    "Rotate access keys at least every 90 days."))
            last_used = key.get("last_used_days_ago")
            if last_used is not None and last_used > 90:
                findings.append(Finding(
                    "iam-unused-access-key", f"{name} ({key.get('id', 'key')})",
                    "Medium",
                    f"Access key has not been used in {last_used} days.",
                    "Delete unused access keys — they are only attack surface."))
    return count


def check_security_groups(inventory: dict, findings: list) -> int:
    count = 0
    for group in inventory.get("security_groups", []):
        gid = group.get("id", "unknown")
        count += 1
        for rule in group.get("ingress", []):
            cidr = rule.get("cidr", "")
            if cidr not in ("0.0.0.0/0", "::/0"):
                continue
            from_port = rule.get("from_port")
            to_port = rule.get("to_port", from_port)
            ports = range(from_port, to_port + 1) if from_port is not None else range(0, 65536)
            exposed = sorted(set(ports) & SENSITIVE_PORTS)
            if exposed:
                findings.append(Finding(
                    "sg-open-sensitive-port", gid, "High",
                    f"Security group allows {cidr} to sensitive port(s) "
                    f"{', '.join(str(p) for p in exposed)}.",
                    "Restrict the rule to specific IPs or a bastion host / VPN; "
                    "never expose database or admin ports to the internet."))
            elif from_port is None or (from_port == 0 and to_port == 65535):
                findings.append(Finding(
                    "sg-open-all-ports", gid, "High",
                    f"Security group allows {cidr} to all ports.",
                    "Replace the open rule with only the ports the service needs."))
    return count


def check_cloudtrail(inventory: dict, findings: list) -> int:
    trail = inventory.get("cloudtrail", {})
    if not trail:
        return 0
    count = 1
    if not trail.get("logging_enabled") or not trail.get("trails"):
        findings.append(Finding(
            "cloudtrail-enabled", "account", "High",
            "No CloudTrail trail is logging — account activity is invisible.",
            "Create a multi-region trail and turn logging on."))
    else:
        if not trail.get("multi_region"):
            findings.append(Finding(
                "cloudtrail-multi-region", "account", "Medium",
                "CloudTrail is not multi-region, so activity in other "
                "regions is not recorded.",
                "Enable the trail in all regions (multi-region trail)."))
        if not trail.get("log_file_validation"):
            findings.append(Finding(
                "cloudtrail-log-validation", "account", "Low",
                "CloudTrail log file validation is off, so tampered logs "
                "would not be detected.",
                "Turn on log file validation for the trail."))
    return count


def check_rds(inventory: dict, findings: list) -> int:
    count = 0
    for db in inventory.get("rds_instances", []):
        name = db.get("id", "unknown")
        count += 1
        if db.get("publicly_accessible"):
            findings.append(Finding(
                "rds-public", name, "High",
                "RDS instance is publicly accessible from the internet.",
                "Set publicly accessible to false and reach the database "
                "only from inside the VPC."))
        if not db.get("storage_encrypted"):
            findings.append(Finding(
                "rds-encryption", name, "Medium",
                "RDS storage is not encrypted at rest.",
                "Enable storage encryption (a new encrypted instance is "
                "needed if this one was created unencrypted)."))
    return count


def check_guardduty_kms(inventory: dict, findings: list) -> int:
    count = 0
    if "guardduty_enabled" in inventory:
        count += 1
        if not inventory.get("guardduty_enabled"):
            findings.append(Finding(
                "guardduty-enabled", "account", "Medium",
                "GuardDuty threat detection is not enabled.",
                "Enable GuardDuty in every region you use."))
    for key in inventory.get("kms_keys", []):
        count += 1
        if not key.get("rotation_enabled"):
            findings.append(Finding(
                "kms-rotation", key.get("id", "unknown"), "Low",
                "KMS key does not have automatic annual rotation enabled.",
                "Enable automatic key rotation for the KMS key."))
    return count


CHECKS = [
    check_s3, check_iam, check_security_groups,
    check_cloudtrail, check_rds, check_guardduty_kms,
]


def scan(inventory: dict) -> Report:
    """Run every check over a normalized account inventory dict."""
    findings: list = []
    checks_run = 0
    for check in CHECKS:
        checks_run += check(inventory, findings)
    order = {"High": 0, "Medium": 1, "Low": 2}
    findings.sort(key=lambda f: (order[f.severity], f.check, f.resource))
    return Report(
        account_id=str(inventory.get("account_id", "unknown")),
        findings=findings,
        checks_run=checks_run,
    )


# ---------------------------------------------------------------- input

def load_demo() -> dict:
    path = Path(__file__).parent / "samples" / "demo-account.json"
    return json.loads(path.read_text())


def load_snapshot(path: str) -> dict:
    return json.loads(Path(path).read_text())


def live_scan() -> dict:
    """Read-only AWS scan via boto3. Raises RuntimeError if boto3 is missing."""
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError as exc:
        raise RuntimeError(
            "boto3 is not installed. Install it with 'pip install boto3' "
            "and configure read-only AWS credentials, or use --demo / "
            "--input instead.") from exc

    inventory: dict = {"account_id": "live"}
    try:
        sts = boto3.client("sts")
        inventory["account_id"] = sts.get_caller_identity()["Account"]
    except ClientError:
        pass

    s3 = boto3.client("s3")
    buckets = []
    for bucket in s3.list_buckets().get("Buckets", []):
        name = bucket["Name"]
        entry = {"name": name, "public_access_block": False,
                 "public_policy": False, "public_acl": False,
                 "encryption": False, "versioning": False}
        try:
            block = s3.get_public_access_block(Bucket=name)
            entry["public_access_block"] = all(
                block["PublicAccessBlockConfiguration"].values())
        except ClientError:
            pass
        try:
            s3.get_bucket_policy(Bucket=name)
            entry["public_policy"] = True
        except ClientError:
            pass
        try:
            acl = s3.get_bucket_acl(Bucket=name)
            entry["public_acl"] = any(
                g.get("Grantee", {}).get("URI", "").endswith("AllUsers")
                for g in acl.get("Grants", []))
        except ClientError:
            pass
        try:
            s3.get_bucket_encryption(Bucket=name)
            entry["encryption"] = True
        except ClientError:
            pass
        try:
            entry["versioning"] = s3.get_bucket_versioning(
                Bucket=name).get("Status") == "Enabled"
        except ClientError:
            pass
        buckets.append(entry)
    inventory["s3_buckets"] = buckets

    iam = boto3.client("iam")
    try:
        policy = iam.get_account_password_policy()["PasswordPolicy"]
        inventory["password_policy"] = {
            "minimum_length": policy.get("MinimumPasswordLength", 0),
            "require_symbols": policy.get("RequireSymbols", False),
            "require_numbers": policy.get("RequireNumbers", False),
            "require_uppercase": policy.get("RequireUppercaseCharacters", False),
            "require_lowercase": policy.get("RequireLowercaseCharacters", False),
            "max_age_days": policy.get("MaxPasswordAge"),
        }
    except ClientError:
        inventory["password_policy"] = None
    try:
        summary = iam.get_account_summary()["SummaryMap"]
        inventory["root"] = {
            "mfa_enabled": summary.get("AccountMFAEnabled") == 1,
            "has_access_keys": summary.get("AccountAccessKeysPresent", 0) > 0,
        }
    except ClientError:
        inventory["root"] = {}
    users = []
    now = datetime.now(timezone.utc)
    for user in iam.list_users().get("Users", []):
        name = user["UserName"]
        mfa = bool(iam.list_mfa_devices(UserName=name).get("MFADevices"))
        keys = []
        for key in iam.list_access_keys(UserName=name).get("AccessKeyMetadata", []):
            age = (now - key["CreateDate"]).days
            last_used = None
            try:
                used = iam.get_access_key_last_used(
                    AccessKeyId=key["AccessKeyId"]).get("AccessKeyLastUsed", {})
                if used.get("LastUsedDate"):
                    last_used = (now - used["LastUsedDate"]).days
            except ClientError:
                pass
            keys.append({"id": key["AccessKeyId"], "age_days": age,
                         "last_used_days_ago": last_used})
        users.append({"name": name, "mfa_enabled": mfa, "access_keys": keys})
    inventory["iam_users"] = users

    ec2 = boto3.client("ec2")
    groups = []
    for group in ec2.describe_security_groups().get("SecurityGroups", []):
        ingress = []
        for rule in group.get("IpPermissions", []):
            for ip_range in rule.get("IpRanges", []):
                ingress.append({"from_port": rule.get("FromPort"),
                                "to_port": rule.get("ToPort"),
                                "cidr": ip_range.get("CidrIp", "")})
            for ip_range in rule.get("Ipv6Ranges", []):
                ingress.append({"from_port": rule.get("FromPort"),
                                "to_port": rule.get("ToPort"),
                                "cidr": ip_range.get("CidrIpv6", "")})
        groups.append({"id": group["GroupId"], "ingress": ingress})
    inventory["security_groups"] = groups

    ct = boto3.client("cloudtrail")
    trails = ct.describe_trails().get("trailList", [])
    logging_on = False
    multi_region = False
    validation = False
    for trail in trails:
        try:
            status = ct.get_trail_status(Name=trail["TrailARN"])
            logging_on = logging_on or status.get("IsLogging", False)
        except ClientError:
            pass
        multi_region = multi_region or trail.get("IsMultiRegionTrail", False)
        validation = validation or trail.get("LogFileValidationEnabled", False)
    inventory["cloudtrail"] = {"trails": len(trails),
                               "logging_enabled": logging_on,
                               "multi_region": multi_region,
                               "log_file_validation": validation}

    rds = boto3.client("rds")
    dbs = []
    for db in rds.describe_db_instances().get("DBInstances", []):
        dbs.append({"id": db["DBInstanceIdentifier"],
                    "publicly_accessible": db.get("PubliclyAccessible", False),
                    "storage_encrypted": db.get("StorageEncrypted", False)})
    inventory["rds_instances"] = dbs

    try:
        gd = boto3.client("guardduty")
        inventory["guardduty_enabled"] = bool(
            gd.list_detectors().get("DetectorIds"))
    except ClientError:
        inventory["guardduty_enabled"] = False
    inventory["kms_keys"] = []
    return inventory


# ---------------------------------------------------------------- output

def print_report(report: Report) -> None:
    print(f"Cloud Security Posture — account {report.account_id}")
    print(f"Score: {report.score}/100  (Grade {report.grade})")
    print(f"Checks run: {report.checks_run}  |  "
          f"High: {len(report.by_severity('High'))}  "
          f"Medium: {len(report.by_severity('Medium'))}  "
          f"Low: {len(report.by_severity('Low'))}")
    print()
    if not report.findings:
        print("No findings — nothing misconfigured in the checks I ran.")
        return
    for finding in report.findings:
        print(f"[{finding.severity}] {finding.check} — {finding.resource}")
        print(f"    {finding.message}")
        print(f"    Fix: {finding.remediation}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Score an AWS account's security posture (read-only).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true",
                       help="score the built-in fictional account")
    group.add_argument("--input", metavar="FILE",
                       help="score an account snapshot JSON file")
    group.add_argument("--live", action="store_true",
                       help="read-only live scan via boto3")
    parser.add_argument("--json", action="store_true",
                        help="print the report as JSON")
    args = parser.parse_args(argv)

    try:
        if args.demo:
            inventory = load_demo()
        elif args.input:
            inventory = load_snapshot(args.input)
        else:
            inventory = live_scan()
    except FileNotFoundError as exc:
        print(f"Error: could not read {exc.filename}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON — {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    report = scan(inventory)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
