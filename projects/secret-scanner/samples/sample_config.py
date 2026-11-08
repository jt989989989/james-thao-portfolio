# sample_config.py — FICTIONAL example file for the Secret Scanner demo.
# Every secret below is fake: AWS's documented example keys, made-up
# tokens, and placeholder values. Never put real secrets in code like this.

AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

GITHUB_TOKEN = "ghp_faketoken0000000000000000000000000000"
SLACK_BOT_TOKEN = "xoxb-fake-slack-token-for-demo"

# A fake JSON Web Token (header.payload.signature are all made up).
USER_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJleGFtcGxlLXVzZXIiLCJuYW1lIjoiSmFtZXMgRXhhbXBsZSJ9.fakeSignature0000000000000000000000"

db_password = "S3cretP@ssw0rdExample"

# A long random-looking string with no recognisable format — the generic
# high-entropy check flags this one.
api_key = "Xk9mQ2vL8pR4tY7wN3bZ6sD1fG5hJ0"
