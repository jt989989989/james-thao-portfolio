# Cloud Security Posture Checker — v1.0.0

A defensive CLI that scores an AWS account's security posture — the checks I run on my own accounts, in one place. It flags public S3 buckets, users without MFA, old or unused access keys, root-account risks, weak password policies, security groups open to the world, missing CloudTrail, public or unencrypted databases, GuardDuty off, and KMS keys without rotation. Every finding comes with the fix.

It never changes anything. It only reads, and it only reports.

## Why I built it

When I worked as a Cloud Security Engineer, the same misconfigurations kept showing up: a bucket left public, a key that hadn't rotated in a year, a database reachable from the internet. None of them are hard to fix — the hard part is noticing them. This tool notices them, scores the account 0–100, and tells you exactly what to fix first (High findings first).

## Use cases

- **Check my own account** — run it monthly to catch a public bucket, an old key, or SSH open to the world before anyone else finds it.
- **Audit a client's account** — hand them a scored report with the fix for each finding, instead of clicking through the AWS console.
- **Prove the fix worked** — run it before and after; the score going up is the proof.
- **Show it in an interview** — a concrete answer to "how do you secure cloud accounts?"

## How it scores

Start at 100. High findings cost 10 points, Medium cost 5, Low cost 2. Grade: 90+ A, 80+ B, 70+ C, 60+ D, below 60 F.

## How to run it

Python 3.10+ only, standard library only for demo and snapshot modes. Live mode needs `boto3` (see `requirements.txt`).

```bash
# Demo — scores a built-in fictional account, no AWS account or credentials
python cloud_posture.py --demo

# Snapshot — score a real account from a JSON inventory file you exported
# yourself with the AWS CLI (read-only calls only, see below)
python cloud_posture.py --input my-account.json

# Live — read-only scan of the account your AWS credentials point at
pip install boto3
python cloud_posture.py --live

# Machine-readable output
python cloud_posture.py --demo --json
```

Exit code is `0` when the scan completes (even with findings) and `2` when the input file can't be read or the live scan can't run.

The demo account scores **0/100 (Grade F)** on purpose — it has a public bucket, root without MFA, a user without MFA, a 120-day-old key, an unused key, SSH open to the world, a public unencrypted database, and GuardDuty off, so you can see every check fire.

## The checks

| Check | Severity | What it catches |
|---|---|---|
| `s3-public-access` | High | Bucket publicly accessible via policy or ACL |
| `s3-public-access-block` | Medium | Block Public Access not enabled |
| `s3-encryption` | Medium | No default encryption at rest |
| `s3-versioning` | Low | Versioning off, deleted objects unrecoverable |
| `root-mfa` | High | Root account has no MFA device |
| `root-access-keys` | High | Root account has access keys |
| `iam-password-policy` | Medium | No policy, or a weak one (under 14 chars, missing symbol/number/case) |
| `iam-password-rotation` | Low | Passwords may live over 90 days |
| `iam-user-mfa` | High | IAM user has no MFA device |
| `iam-old-access-key` | Medium | Access key over 90 days old |
| `iam-unused-access-key` | Medium | Access key unused for over 90 days |
| `sg-open-sensitive-port` | High | 0.0.0.0/0 to SSH, RDP, MySQL, Postgres, MongoDB, Redis, or SQL Server |
| `sg-open-all-ports` | High | 0.0.0.0/0 to all ports |
| `cloudtrail-enabled` | High | No CloudTrail trail logging |
| `cloudtrail-multi-region` | Medium | Trail is not multi-region |
| `cloudtrail-log-validation` | Low | Log file validation off |
| `rds-public` | High | RDS instance publicly accessible |
| `rds-encryption` | Medium | RDS storage not encrypted |
| `guardduty-enabled` | Medium | GuardDuty threat detection off |
| `kms-rotation` | Low | KMS key without automatic rotation |

HTTPS (443) and HTTP (80) open to the world are **not** flagged — a public website is supposed to be public. Only admin and database ports are.

## Checking a real account with a snapshot

Your credentials never touch this tool. Export the inventory yourself with read-only AWS CLI calls, save it in the snapshot format (see `samples/demo-account.json` for the exact shape — every field is optional except the ones you want checked), then run `--input` on it. Use a read-only IAM user or role for the export, and keep the snapshot file out of git — it describes your real account.

## Tests

```bash
python -m unittest discover -s tests -v
```

21 tests: a clean account scores 100, each check fires on a bad value and stays quiet on a good one, scoring floors at 0, grade boundaries, and the demo account scores 0 with all its expected findings. The CLI tests run the demo in `--demo` and `--demo --json` modes. No network calls in the tests.

## Roadmap

- **v1 (this release)** — snapshot + demo + live boto3 scan, 20 checks, 0–100 score.
- **v2** — Azure checks (public storage accounts, NSG rules, Defender) alongside AWS.
- **v3** — trend mode: compare two reports and show what got better or worse.
- **v4** — HTML report output.
