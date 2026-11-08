# clean_example.py — a file with NO secrets, for the demo scan.
# The word "password" appears here in comments, and the strings below are
# short or low-entropy, so the scanner should report nothing for this file.

# TODO: ask the user for their password on first login.
# The login form needs a password field and a "forgot password" link.

API_BASE_URL = "https://api.example.com/v1"
APP_NAME = "example-app"
WELCOME_MESSAGE = "aaaaaaaaaaaaaaaaaaaa"  # low entropy, not a secret
