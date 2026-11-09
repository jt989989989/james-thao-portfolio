"""Tests for the SQL Injection Lab — bypass, fix, and demo data."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sql_injection_lab import (
    PAYLOADS,
    USERS,
    create_demo_db,
    safe_login,
    spot_and_fix_text,
    try_login,
    vulnerable_login,
)


class TestDemoData(unittest.TestCase):
    def setUp(self):
        self.conn = create_demo_db()

    def test_four_fake_users(self):
        count = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        self.assertEqual(count, 4)

    def test_admin_user_exists(self):
        row = self.conn.execute(
            "SELECT username, role FROM users WHERE username = 'admin'"
        ).fetchone()
        self.assertEqual(row, ("admin", "admin"))

    def test_every_user_has_a_role(self):
        roles = {
            row[0] for row in self.conn.execute("SELECT DISTINCT role FROM users")
        }
        self.assertEqual(roles, {"admin", "member"})


class TestVulnerableLogin(unittest.TestCase):
    def setUp(self):
        self.conn = create_demo_db()

    def test_correct_credentials_log_in(self):
        rows = vulnerable_login(self.conn, "molly", "sunshine7")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "molly")

    def test_wrong_password_fails(self):
        self.assertEqual(vulnerable_login(self.conn, "molly", "nope"), [])

    def test_classic_bypass_returns_every_user(self):
        rows = vulnerable_login(self.conn, "' OR '1'='1", "' OR '1'='1")
        self.assertEqual(len(rows), len(USERS))

    def test_comment_payload_logs_in_as_admin_without_password(self):
        rows = vulnerable_login(self.conn, "admin' --", "does-not-matter")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "admin")


class TestSafeLogin(unittest.TestCase):
    def setUp(self):
        self.conn = create_demo_db()

    def test_correct_credentials_still_work(self):
        rows = safe_login(self.conn, "molly", "sunshine7")
        self.assertEqual(len(rows), 1)

    def test_wrong_password_fails(self):
        self.assertEqual(safe_login(self.conn, "molly", "nope"), [])

    def test_every_payload_is_blocked(self):
        for name, username, password in PAYLOADS:
            with self.subTest(payload=name):
                self.assertEqual(safe_login(self.conn, username, password), [])

    def test_payloads_bypass_vulnerable_but_not_safe(self):
        for name, username, password in PAYLOADS:
            with self.subTest(payload=name):
                self.assertTrue(
                    len(vulnerable_login(self.conn, username, password)) >= 1
                )
                self.assertEqual(safe_login(self.conn, username, password), [])


class TestGuide(unittest.TestCase):
    def test_guide_names_the_fix(self):
        text = spot_and_fix_text()
        self.assertIn("parameterized queries", text)
        self.assertIn("plain text", text)

    def test_try_login_reports_broken_queries(self):
        conn = create_demo_db()
        result = try_login(vulnerable_login, conn, "x' OR", "y")
        self.assertIsInstance(result, str)
        self.assertIn("Database error", result)


if __name__ == "__main__":
    unittest.main()
