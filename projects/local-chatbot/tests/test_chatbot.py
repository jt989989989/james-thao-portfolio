#!/usr/bin/env python3
"""Tests for the Local Chatbot — intent matching, answers, demo, offline."""

import ast
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chatbot


class TestIntentMatching(unittest.TestCase):
    def test_services_variations(self):
        for question in ("What do you do?", "what services do you offer",
                         "SERVICES", "what can you do"):
            self.assertEqual(chatbot.match_intent(question), "services")

    def test_booking_variations(self):
        for question in ("How do I book?", "book an assessment",
                         "I want to schedule a call"):
            self.assertEqual(chatbot.match_intent(question), "booking")

    def test_pricing_never_invents_a_price(self):
        for question in ("How much does it cost?", "price", "what are your rates?"):
            reply = chatbot.answer(question)
            self.assertIn("custom", reply.lower())
            self.assertIn(chatbot.BOOKING_LINK, reply)
            self.assertNotIn("$", reply)
            self.assertNotRegex(reply, r"\d+\s*(dollars|usd|/month|per month)")

    def test_github(self):
        reply = chatbot.answer("show me your github")
        self.assertEqual(chatbot.match_intent("show me your github"), "github")
        self.assertIn(chatbot.GITHUB, reply)

    def test_projects_lists_them(self):
        reply = chatbot.answer("what projects have you built?")
        self.assertEqual(chatbot.match_intent("what projects have you built?"),
                         "projects")
        for name in ("ADHD My Way", "Orbit Hop", "Life of a Man",
                     "Phishing Email Detector"):
            self.assertIn(name, reply)

    def test_specific_project(self):
        reply = chatbot.answer("Tell me about ADHD My Way")
        self.assertEqual(chatbot.match_intent("Tell me about ADHD My Way"),
                         "adhd")
        self.assertIn("Ionic", reply)

    def test_about_james(self):
        reply = chatbot.answer("Who is James?")
        self.assertEqual(chatbot.match_intent("Who is James?"), "about_james")
        self.assertIn("CompTIA Security+", reply)
        self.assertIn("University of Wisconsin", reply)

    def test_contact(self):
        reply = chatbot.answer("How can I contact you?")
        self.assertEqual(chatbot.match_intent("How can I contact you?"),
                         "contact")
        self.assertIn(chatbot.BOOKING_LINK, reply)

    def test_fallback_for_unknown_questions(self):
        for question in ("What is the weather?", "Tell me a joke",
                         "Who won the game last night?"):
            self.assertIsNone(chatbot.match_intent(question))
            self.assertEqual(chatbot.answer(question), chatbot.FALLBACK)

    def test_greeting_and_help(self):
        self.assertEqual(chatbot.match_intent("Hello!"), "greeting")
        self.assertIn("booking", chatbot.answer("help").lower())

    def test_case_and_punctuation_do_not_matter(self):
        self.assertEqual(chatbot.match_intent("WHAT DO YOU DO?!"), "services")
        self.assertEqual(chatbot.match_intent("  Book... please?  "), "booking")
        self.assertIsNone(chatbot.match_intent(""))
        self.assertIsNone(chatbot.match_intent("   "))


class TestDemoAndOffline(unittest.TestCase):
    def test_demo_runs_all_questions(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            chatbot.run_demo()
        output = buffer.getvalue()
        for question in chatbot.DEMO_QUESTIONS:
            self.assertIn(question, output)
        self.assertNotIn(chatbot.FALLBACK, output)

    def test_no_network_imports(self):
        """The chatbot must never touch the network: no socket/urllib/etc."""
        banned = {"socket", "urllib", "urllib.request", "urllib.parse",
                  "http", "http.client", "requests", "ssl", "smtplib"}
        path = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "chatbot.py")
        tree = ast.parse(open(path, encoding="utf-8").read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(imported & banned, set())

    def test_answers_cite_real_links(self):
        self.assertIn(chatbot.WEBSITE, chatbot.answer("website"))
        self.assertIn(chatbot.LINKEDIN, chatbot.answer("linkedin"))


if __name__ == "__main__":
    unittest.main()
