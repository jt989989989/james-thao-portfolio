# Printed Text Reader HUD (prototype)

> "You know the saying — give a tough job to a lazy person and see how they solve it. Well, this tool is meant to do that."

I built this to make problem-solving and reading texts faster and easier — point the camera at a page and it reads each question as a whole, then solves it from the actual printed options, right there on screen. No giant center label, no word-by-word scanning, no knowledge-base section to wade through: the camera reads the paragraph, the real multiple-choice options show up just below it, and the best answer is picked for me. I built it to be faster than typing a question into Google — solving quizzes should feel like a breeze.

## What it does

- **Minimal camera-first layout** — the camera fills the top of the screen. Below it, each question it sees gets its own card. Nothing else cluttering the page.
- **Reads the question as a whole** — it understands the full English sentence or paragraph, not just each word on its own. The stem is read as one question.
- **Solves from the actual printed options** — each card shows the real multiple-choice options from the page, and the picked answer is highlighted green with a letter badge and a one-line reason.
- **Several questions in one frame** — if the camera sees more than one question at once, each gets its own card and its own answer, numbered or unnumbered. A summary line reports what it found, e.g. "3 QUESTIONS IN THIS FRAME · 3 SOLVED".
- **Math** — arithmetic, percent-of, and simple solve-for-x, worked out on the spot.
- **General knowledge and cybersecurity** — open questions answered from built-in fact banks (capitals, planets, science, history, and more), plus Security+ and CISSP question banks covering Security+ topics and all 8 CISSP domains.
- **"Text it read"** — the exact text the camera read is shown in a box below, so I can check what it saw.

Everything runs on-device in the browser. No API key, no accounts, no network calls for the logic (the display font loads from Google Fonts when online).

## How to run it

Open `index.html` in a browser. No build step, no server needed.

- **With a camera:** point it at a printed question page. The camera needs HTTPS, which GitHub Pages provides — try the live demo below.
- **Without a camera:** tap one of the built-in samples — including "Three questions at once" — and tap Solve this text.

Live demo: https://jt989989989.github.io/james-thao-portfolio/projects/printed-text-reader-hud/

## Status

This is a **prototype** for the problem-solving mode of a future pair of smart glasses — not a finished product. No hardware exists yet; this phone version stands in for the glasses: the camera reads what's in front of you and the answer appears in a heads-up panel, the way it would on the lenses.
