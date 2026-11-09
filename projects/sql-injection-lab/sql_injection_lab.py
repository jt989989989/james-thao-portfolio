"""SQL Injection Lab — see the bypass, then see the fix.

A tiny local demo that shows, side by side, how SQL injection works
and how parameterized queries stop it. Everything runs against a
fake in-memory database with four made-up users. No network, no real
targets, no real data.

LOCAL DEMO ONLY — never test injection against any real website, app,
or system you do not own or have explicit permission to test.

    python sql_injection_lab.py           # interactive menu
    python sql_injection_lab.py --demo    # run every payload on both logins
"""

import sqlite3
import sys

USERS = [
    # (id, username, password, role) — fake demo accounts only.
    (1, "admin", "dragon99", "admin"),
    (2, "molly", "sunshine7", "member"),
    (3, "zoe", "purple42", "member"),
    (4, "ben", "qwerty123", "member"),
]

# Classic injection payloads, typed in as the username (and password).
# Each one is tried against the vulnerable login and the safe login.
PAYLOADS = [
    ("Classic always-true", "' OR '1'='1", "' OR '1'='1"),
    ("Comment out the password check", "admin' --", "does-not-matter"),
    ("Always-true with a comment", "' OR 1=1 --", "x"),
]

BANNER = """
=====================================
      SQL INJECTION LAB
=====================================
A local demo with four fake users. Try the payloads against the
vulnerable login, then against the fixed one — same input, very
different result.

LOCAL DEMO ONLY — never test injection against any real website,
app, or system you do not own or have explicit permission to test.
"""


def create_demo_db():
    """Build the fake user database (in memory, gone when the program ends)."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """CREATE TABLE users (
               id INTEGER PRIMARY KEY,
               username TEXT NOT NULL UNIQUE,
               password TEXT NOT NULL,
               role TEXT NOT NULL
           )"""
    )
    conn.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", USERS)
    conn.commit()
    return conn


def vulnerable_login(conn, username, password):
    """The BAD way: user input glued straight into the SQL string.

    The database cannot tell where the developer's SQL ends and the
    attacker's input begins, so crafted input rewrites the query.
    This login exists on purpose, in this demo only, so the bypass
    can be seen and understood. Never write a login this way.
    """
    query = (
        "SELECT id, username, role FROM users "
        f"WHERE username = '{username}' AND password = '{password}'"
    )
    return conn.execute(query).fetchall()


def safe_login(conn, username, password):
    """The GOOD way: parameterized query — input is data, never code.

    The ? placeholders are filled in by the database driver, so even
    a payload full of quotes is treated as a plain (wrong) username.
    """
    return conn.execute(
        "SELECT id, username, role FROM users WHERE username = ? AND password = ?",
        (username, password),
    ).fetchall()


def try_login(login_fn, conn, username, password):
    """Run a login attempt; a broken query comes back as an error string."""
    try:
        return login_fn(conn, username, password)
    except sqlite3.Error as exc:
        return f"Database error: {exc}"


def spot_and_fix_text():
    """How to spot injection in code, and how to fix it."""
    return """
HOW TO SPOT IT
  * The code builds SQL by gluing user input into the query string —
    f-strings, + concatenation, or % formatting with user input.
  * Typing a single quote (') into a login or search box changes the
    page or triggers a database error.
  * Database error messages leak onto the page.
  * A login succeeds with a strange username such as ' OR '1'='1.

HOW TO FIX IT
  * Use parameterized queries (placeholders like ?) — the database
    treats input as data, never as code. This is the fix; the rest
    is a bonus.
  * Validate input with allow-lists and length limits, but never rely
    on blocking "bad words" — attackers always find another spelling.
  * Give the database account the fewest permissions it needs
    (read-only where possible).
  * Log failed logins and strange input; alert on repeated attempts.
  * Never store passwords in plain text — hash them. This demo stores
    plain-text passwords only because it is a tiny local demo; real
    apps must not.
"""


def run_payloads(conn):
    """Run every payload against both logins and print the results."""
    for name, username, password in PAYLOADS:
        print(f"\nPayload: {name}  (username={username!r})")
        print(f"  Vulnerable login: {try_login(vulnerable_login, conn, username, password)}")
        print(f"  Safe login:       {try_login(safe_login, conn, username, password)}")


def run_demo():
    """The full walkthrough: a normal login, then every payload, then the guide."""
    conn = create_demo_db()
    print(BANNER)
    print("First, a normal login — molly / sunshine7:")
    print(f"  Vulnerable login: {try_login(vulnerable_login, conn, 'molly', 'sunshine7')}")
    print(f"  Safe login:       {try_login(safe_login, conn, 'molly', 'sunshine7')}")
    print("\nNow the payloads. Watch what each login returns:")
    run_payloads(conn)
    print(spot_and_fix_text())
    print("Remember: local demo only. Never test injection against a")
    print("real website, app, or system you do not own or have")
    print("explicit permission to test.")


def play():
    """Interactive menu — try the logins yourself."""
    conn = create_demo_db()
    print(BANNER)
    while True:
        print("\n1. Try the VULNERABLE login yourself")
        print("2. Try the SAFE login yourself")
        print("3. Run all payloads side by side")
        print("4. How to spot it / how to fix it")
        print("5. Quit")
        choice = input("Choose 1-5: ").strip()
        if choice == "1":
            username = input("Username: ")
            password = input("Password: ")
            result = try_login(vulnerable_login, conn, username, password)
            print(f"Vulnerable login returned: {result}")
            if isinstance(result, list) and result:
                print("Logged in! Now try the same input on the safe login (option 2).")
        elif choice == "2":
            username = input("Username: ")
            password = input("Password: ")
            result = try_login(safe_login, conn, username, password)
            print(f"Safe login returned: {result}")
            if result == []:
                print("No match — the input was treated as a plain username, not code.")
        elif choice == "3":
            run_payloads(conn)
        elif choice == "4":
            print(spot_and_fix_text())
        elif choice == "5":
            print("Lab closed. Remember: local demo only.")
            return
        else:
            print("Please choose 1-5.")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--demo" in argv:
        run_demo()
    else:
        try:
            play()
        except (EOFError, KeyboardInterrupt):
            print("\nLab closed. Remember: local demo only.")


if __name__ == "__main__":
    main()
