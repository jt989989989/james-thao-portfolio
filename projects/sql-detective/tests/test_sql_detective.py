"""Tests for SQL Detective — database, challenges, and the checker."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sql_detective import (
    CHALLENGES,
    build_database,
    check_answer,
    list_tables,
    normalize,
    schema_text,
)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.conn = build_database()

    def test_tables_exist(self):
        self.assertEqual(list_tables(self.conn), ["alibis", "sightings", "suspects"])

    def test_five_suspects(self):
        count = self.conn.execute("SELECT COUNT(*) FROM suspects").fetchone()[0]
        self.assertEqual(count, 5)

    def test_sightings_and_alibis_loaded(self):
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM sightings").fetchone()[0], 5
        )
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM alibis").fetchone()[0], 5
        )

    def test_schema_text_names_all_tables(self):
        text = schema_text(self.conn)
        for table in ("suspects", "sightings", "alibis"):
            self.assertIn(table, text)


class TestChallenges(unittest.TestCase):
    def setUp(self):
        self.conn = build_database()

    def test_every_solution_returns_its_expected_answer(self):
        for challenge in CHALLENGES:
            with self.subTest(challenge=challenge["title"]):
                rows = self.conn.execute(challenge["solution"]).fetchall()
                self.assertEqual(normalize(rows), normalize(challenge["expected"]))

    def test_every_challenge_has_a_hint(self):
        for challenge in CHALLENGES:
            self.assertTrue(challenge["hint"].strip())

    def test_case_narrows_to_one_culprit(self):
        # The last challenge's answer is a single suspect's full record.
        last = CHALLENGES[-1]
        rows = self.conn.execute(last["solution"]).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "Pete Porter")


class TestChecker(unittest.TestCase):
    def setUp(self):
        self.conn = build_database()

    def test_accepts_correct_answer(self):
        ok, _ = check_answer(self.conn, CHALLENGES[0], CHALLENGES[0]["solution"])
        self.assertTrue(ok)

    def test_accepts_lowercase_sql(self):
        ok, _ = check_answer(
            self.conn,
            CHALLENGES[4],
            "select name from suspects where debt_dollars > 500",
        )
        self.assertTrue(ok)

    def test_rejects_wrong_answer(self):
        ok, message = check_answer(
            self.conn, CHALLENGES[0], "SELECT name FROM suspects"
        )
        self.assertFalse(ok)
        self.assertIn("Not quite", message)

    def test_rejects_bad_sql_without_crashing(self):
        ok, message = check_answer(
            self.conn, CHALLENGES[0], "SELEC name FORM suspects"
        )
        self.assertFalse(ok)
        self.assertIn("did not run", message)

    def test_empty_result_is_wrong(self):
        ok, message = check_answer(
            self.conn, CHALLENGES[0], "SELECT name FROM suspects WHERE 1 = 0"
        )
        self.assertFalse(ok)
        self.assertIn("no rows", message)


if __name__ == "__main__":
    unittest.main()
