#!/usr/bin/env python3
"""Local Chatbot — a simple offline chatbot (AI project #2).

Answers questions about James Thao's portfolio and his business,
All Stars Automations, from a built-in knowledge base. It matches your
question to an intent with plain keyword matching — no API key, no
network calls, no model download, no data leaves your machine.

Usage:
    python chatbot.py            # interactive chat loop
    python chatbot.py --demo     # run the sample questions and print Q&A
"""

import argparse
import re
import sys

BOOKING_LINK = "https://www.allstarsai.xyz/#booking"
WEBSITE = "https://www.allstarsai.xyz/"
GITHUB = "https://github.com/jt989989989/james-thao-portfolio"
LINKEDIN = "https://www.linkedin.com/in/jamesss42/"

# Each intent: the phrases/keywords that trigger it, and the answer.
# Answers use only the facts in this knowledge base — pricing is never
# invented; it is always "custom per business, book an assessment".
INTENTS = [
    {
        "name": "greeting",
        "patterns": ["hello", "hi", "hey", "good morning", "good afternoon",
                     "good evening"],
        "answer": (
            "Hi! I'm a small offline demo chatbot for All Stars Automations "
            "and James Thao's portfolio. Ask me about the business, the "
            "services, booking, pricing, GitHub projects, or James himself — "
            "or type 'help' to see everything I can answer."
        ),
    },
    {
        "name": "identity",
        "patterns": ["who are you", "what are you", "your name",
                     "are you ai", "are you a bot"],
        "answer": (
            "I'm a simple rule-based chatbot — keyword matching over a "
            "built-in knowledge base, no API key and no network calls. I "
            "answer questions about All Stars Automations and James Thao's "
            "GitHub portfolio. I'm a portfolio demo, not a full AI assistant."
        ),
    },
    {
        "name": "services",
        "patterns": ["what do you do", "services", "what services",
                     "what can you do", "offer", "what does all stars do",
                     "all stars", "automation"],
        "answer": (
            "All Stars Automations builds AI automation for small "
            "businesses: AI voice receptionists, SMS and chat, appointment "
            "booking, CRM, and workflow automation. The idea is to capture "
            "lost opportunities, convert more prospects, and cut repetitive "
            "work. Website: " + WEBSITE
        ),
    },
    {
        "name": "booking",
        "patterns": ["book", "booking", "schedule", "assessment",
                     "appointment", "sign up", "get started",
                     "start", "consult"],
        "answer": (
            "You can book a free Systems Assessment here: " + BOOKING_LINK
            + " — pick a time and James will walk through where your "
            "business is losing revenue or wasting time on manual work."
        ),
    },
    {
        "name": "pricing",
        "patterns": ["price", "pricing", "cost", "how much", "charge",
                     "fees", "expensive", "rates"],
        "answer": (
            "Pricing is custom for each business — it depends on what "
            "systems you need, so there is no fixed price list. Book a "
            "free Systems Assessment and you'll get an itemized proposal: "
            + BOOKING_LINK
        ),
    },
    {
        "name": "github",
        "patterns": ["github", "git hub", "repo", "repository", "code",
                     "source code"],
        "answer": (
            "James's GitHub portfolio is here: " + GITHUB + " — 16 projects "
            "including ADHD My Way, Orbit Hop, Life of a Man, SOC Log "
            "Analyzer, Phishing Email Detector, SQL Detective, and the "
            "Local Chatbot."
        ),
    },
    {
        "name": "adhd",
        "patterns": ["adhd"],
        "answer": (
            "ADHD My Way is an Ionic app for children under 12: daily tasks "
            "earn coins, coins buy avatar customizations, plus mini games "
            "like Memory Match. Everything stays on the device — no "
            "accounts, no analytics, no network calls."
        ),
    },
    {
        "name": "orbit_hop",
        "patterns": ["orbit hop", "orbit"],
        "answer": (
            "Orbit Hop is a playable browser game: hop between orbit rings "
            "to dodge debris and chase a high score. JavaScript and HTML5 "
            "Canvas, plain shapes and flat colours."
        ),
    },
    {
        "name": "life_of_a_man",
        "patterns": ["life of a man"],
        "answer": (
            "Life of a Man is a satire browser board game: roll dice around "
            "a 40-square Board of Life, ages 18 to 65, with quarterly "
            "choices, debt, marriage, midlife crises, and a tombstone "
            "ending. Happiness is the main score."
        ),
    },
    {
        "name": "soc_log",
        "patterns": ["soc", "log analyzer", "log analyser"],
        "answer": (
            "The SOC Log Analyzer is a Python CLI that parses auth logs and "
            "flags brute-force attempts and success-after-failure logins — "
            "a defensive security tool from James's SOC background."
        ),
    },
    {
        "name": "phishing",
        "patterns": ["phishing"],
        "answer": (
            "The Phishing Email Detector is a local ML tool (offline, no API "
            "key): it scores an email 0–100 as legitimate, suspicious, or "
            "phishing and explains why — urgent language, credential "
            "requests, Reply-To mismatches, deceptive links, and more."
        ),
    },
    {
        "name": "sql_detective",
        "patterns": ["sql detective"],
        "answer": (
            "SQL Detective is a fun SQL practice game: solve the case of the "
            "missing mascot by writing real SQL queries against a fictional "
            "SQLite database, with hints and a checker."
        ),
    },
    {
        "name": "projects",
        "patterns": ["project", "projects", "built", "portfolio", "work",
                     "show me"],
        "answer": (
            "James's portfolio has 16 projects: ADHD My Way, Orbit Hop, "
            "Jelly Stack, Life of a Man, SOC Log Analyzer, Missed-Call "
            "Follow-Up, Scientific Calculator, Lead Generator, Password "
            "Strength Checker, Secret Scanner, Recon Scanner, SQL Detective, "
            "SQL Injection Lab, Phishing Email Detector, the Printed "
            "Text Reader HUD prototype, and the Local Chatbot. See them all at " + GITHUB
        ),
    },
    {
        "name": "about_james",
        "patterns": ["who is james", "about james", "james thao",
                     "tell me about james", "your boss", "the owner",
                     "founder"],
        "answer": (
            "James Thao is Director of All Stars Automations. He holds "
            "CompTIA Security+ and a B.S. in Computer Science from the "
            "University of Wisconsin, with a background in cloud security, "
            "vehicle cybersecurity, and IT support."
        ),
    },
    {
        "name": "linkedin",
        "patterns": ["linkedin"],
        "answer": "James is on LinkedIn at " + LINKEDIN,
    },
    {
        "name": "website",
        "patterns": ["website", "site", "web address", "web site",
                     "homepage"],
        "answer": "The All Stars Automations website is " + WEBSITE,
    },
    {
        "name": "contact",
        "patterns": ["contact", "reach", "email", "phone", "call",
                     "get in touch", "talk to"],
        "answer": (
            "The fastest way to reach James is to book a free Systems "
            "Assessment: " + BOOKING_LINK + " — or find him on LinkedIn at "
            + LINKEDIN + " and see his work at " + GITHUB
        ),
    },
    {
        "name": "help",
        "patterns": ["help", "what can i ask", "options", "topics",
                     "commands", "what do you know"],
        "answer": (
            "I can answer questions about:\n"
            "  - the business and services ('What do you do?')\n"
            "  - booking ('How do I book?')\n"
            "  - pricing ('How much does it cost?')\n"
            "  - GitHub and projects ('Show me your GitHub')\n"
            "  - individual projects ('Tell me about ADHD My Way')\n"
            "  - James himself ('Who is James?')\n"
            "  - contact and LinkedIn\n"
            "Type 'quit' to leave."
        ),
    },
]

FALLBACK = (
    "I'm not sure about that yet — I'm a small offline demo bot and I only "
    "know about All Stars Automations, James's portfolio, and booking. "
    "Type 'help' to see what I can answer."
)

DEMO_QUESTIONS = [
    "What do you do?",
    "How do I book?",
    "How much does it cost?",
    "Show me your GitHub",
    "What projects have you built?",
    "Tell me about ADHD My Way",
    "Who is James?",
    "How can I contact you?",
]


def _normalize(text):
    """Lowercase and strip punctuation so matching ignores case and noise."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _pattern_matches(pattern, normalized, words):
    """Check one pattern against a normalized question.

    Multi-word patterns match on whole-word boundaries (so "what are you"
    never matches inside "what are your rates"). Single-word patterns
    match whole words, or words starting with the pattern when the
    pattern is at least 4 letters long (so "book" matches "booking" but
    a short word like "hi" never matches inside "this" or "which").
    """
    if " " in pattern:
        return (" " + pattern + " ") in (" " + normalized + " ")
    if len(pattern) >= 4:
        return any(w == pattern or w.startswith(pattern) for w in words)
    return pattern in words


def match_intent(text):
    """Return the name of the best-matching intent, or None.

    Scores each intent by how many of its patterns appear in the
    normalized question; the highest score wins, ties go to the
    first intent listed.
    """
    normalized = _normalize(text)
    if not normalized:
        return None
    words = normalized.split()
    best_name = None
    best_score = 0
    for intent in INTENTS:
        score = sum(1 for p in intent["patterns"]
                    if _pattern_matches(p, normalized, words))
        if score > best_score:
            best_score = score
            best_name = intent["name"]
    return best_name


def answer(question):
    """Answer one question from the knowledge base."""
    name = match_intent(question)
    if name is None:
        return FALLBACK
    for intent in INTENTS:
        if intent["name"] == name:
            return intent["answer"]
    return FALLBACK


def run_demo():
    """Print the sample questions with their answers."""
    print("Local Chatbot — demo (offline, no API key)\n")
    for question in DEMO_QUESTIONS:
        print("You: " + question)
        print("Bot: " + answer(question))
        print()


def chat_loop():
    """Interactive chat: type a question, 'help' for topics, 'quit' to exit."""
    print("Local Chatbot — offline demo for All Stars Automations.")
    print("Ask me about the business, booking, pricing, GitHub, or James.")
    print("Type 'help' for topics, 'quit' to leave.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Goodbye!")
            return
        if not question:
            continue
        if _normalize(question) in ("quit", "exit", "bye", "goodbye"):
            print("Bot: Goodbye! Book a Systems Assessment at " + BOOKING_LINK)
            return
        print("Bot: " + answer(question) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Local Chatbot — offline demo chatbot (no API key).")
    parser.add_argument("--demo", action="store_true",
                        help="run the sample questions and print Q&A")
    args = parser.parse_args(argv)
    if args.demo:
        run_demo()
    else:
        chat_loop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
