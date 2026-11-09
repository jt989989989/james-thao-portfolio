# SQL Injection Lab

An educational demo of SQL injection — and the fix — on a local
database with four fake users. Try classic payloads against a
deliberately vulnerable login, watch the bypass happen, then run
the same payloads against the parameterized version and watch them
fail. A "how to spot it / how to fix it" guide is built in.

> **LOCAL DEMO ONLY — never test injection against any real
> website, app, or system you do not own or have explicit
> permission to test.** This is defensive education, not an attack
> tool: no network calls, no real targets, no credential stuffing,
> no brute force.

## How it works

The vulnerable login builds its query by gluing user input into
the SQL string:

```python
query = f"SELECT ... WHERE username = '{username}' AND password = '{password}'"
```

The database cannot tell where the developer's SQL ends and the
input begins, so a crafted username rewrites the query. The fixed
login uses placeholders instead:

```python
conn.execute("... WHERE username = ? AND password = ?", (username, password))
```

The placeholders are filled in by the database driver, so input is
always treated as data — never as code.

## How to run it

```bash
# Run every payload against both logins, side by side
python sql_injection_lab.py --demo

# Interactive menu — try your own usernames and passwords
python sql_injection_lab.py
```

Try these payloads as the username (the demo walks you through them):

| Payload | What it does |
|---|---|
| `' OR '1'='1` | Always-true condition — logs in as every user at once |
| `admin' --` | Comments out the password check — logs in as admin |
| `' OR 1=1 --` | Always-true, with the rest of the query commented out |

## How to spot it / how to fix it

- **Spot it:** code that builds SQL with f-strings, `+`, or `%`
  formatting around user input; a single quote (`'`) typed into a
  login or search box changing the page or causing a database
  error; database errors leaking onto the page.
- **Fix it:** parameterized queries (placeholders). That is the
  fix. Validate input and limit database permissions as well, but
  never rely on blocking "bad words" — attackers always find
  another spelling.
- **Passwords:** never store them in plain text — hash them. This
  demo stores plain-text passwords only because it is a tiny local
  demo; real apps must not.

## Tests

```bash
python -m unittest discover -s tests -v
```

13 tests: the demo data loads (four fake users, admin included);
the vulnerable login works for real credentials, fails for wrong
ones, and is bypassed by every payload; the parameterized login
still works for real credentials and blocks every payload; and the
guide names the fix.

## Notes

- Python 3.10+, standard library only (`sqlite3`). No network.
- All users and passwords are fictional demo data.
- The vulnerable login exists on purpose, in this demo only, so
  the bypass can be seen and understood. Never write a login this
  way in real code.
