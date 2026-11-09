# SQL Detective

A fun SQL practice game: solve the case of the missing mascot by
writing real SQL queries against a small fictional SQLite database.
Five suspects, three tables, six clues — and the culprit gives
themselves away if you ask the database the right questions.

## The case

The Maplewood Mustangs' mascot costume, "Captain Clover", vanished
from the stadium locker room on Friday night, between 9 PM and
11 PM. Five people were around. One of them did it.

## How to play

```bash
python sql_detective.py
```

Type a SQL query at the prompt and press Enter. Commands:

- `schema` — show the tables and their columns
- `hint` — get a nudge for the current clue
- `quit` — give up (the mascot will be very disappointed)

Each clue narrows the suspect list. Solve all six and the case
is closed.

```bash
# Watch the solution play out without typing anything
python sql_detective.py --demo
```

## The database

| Table | What it holds |
|---|---|
| `suspects` | id, name, role, hair_color, has_locker_key, debt_dollars |
| `sightings` | id, suspect_id, location, day, hour (24-hour clock) |
| `alibis` | id, suspect_id, claim, verified (1 = someone confirmed it) |

## The clues (spoilers!)

1. Who was at the stadium on Friday night after 9 PM?
2. Of those, who had a locker-room key?
3. A red hair was found in the locker — who is left?
4. Whose alibi did nobody verify?
5. The costume turned up at a pawn shop — who owes more than $500?
6. Show the culprit's full record.

## Tests

```bash
python -m unittest discover -s tests -v
```

12 tests: the database builds with all tables and rows, every
challenge's solution query returns its expected answer, and the
checker accepts correct SQL (even lowercase), rejects wrong
answers, and handles broken SQL without crashing.

## Notes

- Python 3.10+, standard library only (`sqlite3`). No network, no
  files are written — the database lives in memory while you play.
- All people, places, and clues are fictional. No real data.
