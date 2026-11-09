"""SQL Detective — solve a small mystery by writing real SQL queries.

The case: the Maplewood Mustangs' mascot costume, "Captain Clover",
vanished from the stadium locker room on Friday night, between 9 PM
and 11 PM. Five people had reason to be around. One of them did it.

You are the junior detective on the case, and the only witness is a
small SQLite database full of suspects, sightings, and alibis. Ask it
the right questions — in SQL — and the culprit gives themselves away.

How to play
------------
Run the game, then type a SQL query at the prompt and press Enter.
Useful commands (type them instead of a query):

    schema   show the tables and their columns
    hint     get a nudge for the current clue
    quit     give up (the mascot will be very disappointed)

Python 3.10+, standard library only (sqlite3). No network, no files
are written — the database lives in memory while you play.

    python sql_detective.py          # play the game
    python sql_detective.py --demo   # watch the solution play out
"""

import sqlite3
import sys

INTRO = """
=====================================
        SQL DETECTIVE
=====================================
The case: the Maplewood Mustangs' mascot costume, "Captain Clover",
vanished from the stadium locker room on Friday night, between 9 PM
and 11 PM. Five people had reason to be around. One of them did it.

You are the junior detective. Your only witness is a small database:
suspects, sightings, and alibis. Ask it the right questions — in SQL —
and the culprit gives themselves away.

Commands: type a SQL query, or 'schema' to see the tables,
'hint' for a nudge, 'quit' to give up.
"""

WIN_MESSAGE = """
*** CASE CLOSED ***

Pete Porter, the janitor, took the costume to pay off an $850 debt —
and the pawn shop ticket in his locker says the mascot head was next.
Captain Clover is back on the sidelines, and Maplewood can cheer again.

You solved it with nothing but SQL. Nice detective work.
"""

# ---------------------------------------------------------------------------
# The case file: fictional people, places, and clues. No real data.
# ---------------------------------------------------------------------------

SUSPECTS = [
    # (id, name, role, hair_color, has_locker_key, debt_dollars)
    (1, "Dana Doyle", "Head Coach", "brown", 1, 0),
    (2, "Pete Porter", "Janitor", "red", 1, 850),
    (3, "Samira Shah", "Ticket Seller", "black", 0, 0),
    (4, "Gus Green", "Groundskeeper", "blond", 1, 120),
    (5, "Lila Lane", "Mascot Performer", "red", 0, 0),
]

SIGHTINGS = [
    # (id, suspect_id, location, day, hour) — hour is a 24-hour clock
    (1, 1, "Stadium parking lot", "Friday", 21),
    (2, 2, "Stadium locker room hallway", "Friday", 22),
    (3, 5, "Stadium field", "Friday", 21),
    (4, 3, "Ticket booth", "Friday", 14),
    (5, 4, "Stadium field", "Friday", 7),
]

ALIBIS = [
    # (id, suspect_id, claim, verified) — verified = 1 means someone confirmed it
    (1, 1, "On the phone with the league office, 9:30-10:30 PM", 1),
    (2, 2, "Home watching TV all night", 0),
    (3, 3, "Worked the ticket booth until 6 PM, then home", 1),
    (4, 4, "Asleep by 9 PM", 0),
    (5, 5, "At the diner with her sister until 10:45 PM", 1),
]

CHALLENGES = [
    {
        "title": "Clue 1 — Who was at the stadium?",
        "story": (
            "The costume disappeared from the locker room between 9 PM and "
            "11 PM on Friday. Start by finding everyone who was seen at the "
            "stadium that night after 9 PM."
        ),
        "hint": (
            "Join suspects to sightings on suspect_id, then filter with "
            "WHERE location LIKE 'Stadium%' AND day = 'Friday' AND hour >= 21. "
            "You only need the name."
        ),
        "solution": (
            "SELECT s.name FROM suspects s "
            "JOIN sightings g ON g.suspect_id = s.id "
            "WHERE g.location LIKE 'Stadium%' AND g.day = 'Friday' AND g.hour >= 21"
        ),
        "expected": [("Dana Doyle",), ("Lila Lane",), ("Pete Porter",)],
    },
    {
        "title": "Clue 2 — Who had a key?",
        "story": (
            "The locker room door was locked, not forced — so the thief had "
            "a key. Of the people at the stadium that night, who has a "
            "locker-room key?"
        ),
        "hint": (
            "Same join as Clue 1, and add AND s.has_locker_key = 1. "
            "has_locker_key is 1 for yes, 0 for no."
        ),
        "solution": (
            "SELECT s.name FROM suspects s "
            "JOIN sightings g ON g.suspect_id = s.id "
            "WHERE g.location LIKE 'Stadium%' AND g.day = 'Friday' "
            "AND g.hour >= 21 AND s.has_locker_key = 1"
        ),
        "expected": [("Dana Doyle",), ("Pete Porter",)],
    },
    {
        "title": "Clue 3 — A red hair in the locker",
        "story": (
            "The lab found a single red hair in the empty locker. Of the "
            "key holders from Clue 2, who has red hair?"
        ),
        "hint": (
            "Keep the filters from Clue 2 and add AND s.hair_color = 'red'."
        ),
        "solution": (
            "SELECT s.name FROM suspects s "
            "JOIN sightings g ON g.suspect_id = s.id "
            "WHERE g.location LIKE 'Stadium%' AND g.day = 'Friday' "
            "AND g.hour >= 21 AND s.has_locker_key = 1 AND s.hair_color = 'red'"
        ),
        "expected": [("Pete Porter",)],
    },
    {
        "title": "Clue 4 — Check the alibis",
        "story": (
            "The chief wants every alibi checked. Whose alibi did nobody "
            "verify?"
        ),
        "hint": (
            "Join suspects to alibis on suspect_id and filter "
            "WHERE a.verified = 0. verified is 1 when someone confirmed "
            "the alibi, 0 when nobody did."
        ),
        "solution": (
            "SELECT s.name FROM suspects s "
            "JOIN alibis a ON a.suspect_id = s.id WHERE a.verified = 0"
        ),
        "expected": [("Gus Green",), ("Pete Porter",)],
    },
    {
        "title": "Clue 5 — Follow the money",
        "story": (
            "A pawn shop across town just sold a suspiciously familiar "
            "mascot head. The thief needed cash fast — who owes more than "
            "$500?"
        ),
        "hint": (
            "This one needs no join: SELECT name FROM suspects "
            "WHERE debt_dollars > 500."
        ),
        "solution": "SELECT name FROM suspects WHERE debt_dollars > 500",
        "expected": [("Pete Porter",)],
    },
    {
        "title": "Clue 6 — Name the culprit",
        "story": (
            "The evidence points to one person. Bring up their full record "
            "from the suspects table so the chief can make the arrest."
        ),
        "hint": (
            "SELECT * FROM suspects WHERE name = '...' — put the name you "
            "have pieced together inside the quotes."
        ),
        "solution": "SELECT * FROM suspects WHERE name = 'Pete Porter'",
        "expected": [(2, "Pete Porter", "Janitor", "red", 1, 850)],
    },
]


def build_database():
    """Create the in-memory case database and fill it with the case file."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """CREATE TABLE suspects (
               id INTEGER PRIMARY KEY,
               name TEXT NOT NULL,
               role TEXT NOT NULL,
               hair_color TEXT NOT NULL,
               has_locker_key INTEGER NOT NULL,
               debt_dollars INTEGER NOT NULL
           )"""
    )
    conn.execute(
        """CREATE TABLE sightings (
               id INTEGER PRIMARY KEY,
               suspect_id INTEGER NOT NULL,
               location TEXT NOT NULL,
               day TEXT NOT NULL,
               hour INTEGER NOT NULL,
               FOREIGN KEY (suspect_id) REFERENCES suspects (id)
           )"""
    )
    conn.execute(
        """CREATE TABLE alibis (
               id INTEGER PRIMARY KEY,
               suspect_id INTEGER NOT NULL,
               claim TEXT NOT NULL,
               verified INTEGER NOT NULL,
               FOREIGN KEY (suspect_id) REFERENCES suspects (id)
           )"""
    )
    conn.executemany("INSERT INTO suspects VALUES (?, ?, ?, ?, ?, ?)", SUSPECTS)
    conn.executemany("INSERT INTO sightings VALUES (?, ?, ?, ?, ?)", SIGHTINGS)
    conn.executemany("INSERT INTO alibis VALUES (?, ?, ?, ?)", ALIBIS)
    conn.commit()
    return conn


def list_tables(conn):
    """Names of the tables in the case database, in alphabetical order."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [row[0] for row in rows]


def schema_text(conn):
    """The CREATE TABLE statements for the case database, as text."""
    rows = conn.execute(
        "SELECT sql FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return "\n".join(row[0] + ";" for row in rows)


def normalize(rows):
    """Turn query results into a sorted list of string tuples for comparison."""
    return sorted(tuple(str(value) for value in row) for row in rows)


def check_answer(conn, challenge, sql):
    """Run the player's SQL and compare it with the expected answer.

    Returns (ok, message). Bad SQL is a wrong answer, not a crash.
    """
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        return False, f"That query did not run: {exc}"
    if normalize(rows) == normalize(challenge["expected"]):
        return True, "Correct!"
    if not rows:
        return False, "That query ran but returned no rows — try a different filter."
    shown = ", ".join(" / ".join(row) for row in normalize(rows)[:5])
    return False, f"Not quite — that returned: {shown}. Check the clue and try again."


def play():
    """The interactive game: one clue at a time until the case is closed."""
    conn = build_database()
    print(INTRO)
    for challenge in CHALLENGES:
        print(f"\n{challenge['title']}\n{challenge['story']}\n")
        while True:
            answer = input("SQL> ").strip()
            if not answer:
                continue
            command = answer.lower()
            if command == "quit":
                print("\nCase left unsolved... the mascot is still missing.")
                return
            if command == "hint":
                print(f"\nHint: {challenge['hint']}\n")
                continue
            if command == "schema":
                print(f"\n{schema_text(conn)}\n")
                continue
            ok, message = check_answer(conn, challenge, answer)
            print(message)
            if ok:
                break
    print(WIN_MESSAGE)


def run_demo():
    """Play the solution through, printing each query and its result."""
    conn = build_database()
    print(INTRO)
    for challenge in CHALLENGES:
        print(f"\n{challenge['title']}\n{challenge['story']}\n")
        print(f"Query: {challenge['solution']}")
        rows = conn.execute(challenge["solution"]).fetchall()
        for row in rows:
            print("  " + " | ".join(str(value) for value in row))
        print("Correct!")
    print(WIN_MESSAGE)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--demo" in argv:
        run_demo()
    else:
        try:
            play()
        except (EOFError, KeyboardInterrupt):
            print("\nCase left unsolved... the mascot is still missing.")


if __name__ == "__main__":
    main()
