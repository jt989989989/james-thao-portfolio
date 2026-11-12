# Printed Text Reader HUD (prototype)

> "You know the saying — give a tough job to a lazy person and see how they solve it. Well, this tool is meant to do that."

I built this to make problem-solving and reading texts faster and easier — point the camera at a page and it reads each question as a whole, then solves it from the actual printed options, right there on screen. No giant center label, no word-by-word scanning, no knowledge-base section to wade through: the camera reads the paragraph, the real multiple-choice options show up just below it, and the best answer is picked for me. I built it to be faster than typing a question into Google — solving quizzes should feel like a breeze.

Right now it can solve simple math problems and a few cybersecurity questions for me. Story problems are still hit-or-miss — that is what my next update is for.

## What it does

- **Minimal camera-first layout** — the camera fills the top of the screen. Below it, each question it sees gets its own card. Nothing else cluttering the page.
- **Reads the question as a whole** — it understands the full English sentence or paragraph, not just each word on its own. Sentence-form questions work too: number words ("twelve divided by three"), "divided by / plus / minus / times", "subtract 3 from 10", half or a quarter of a number, and story problems like sharing equally, packing into groups, or per-container counts.
- **Finds the question by its number** — every question starts with a number and a period (like "2."), so I spot that pattern to find where the question starts. Quiz titles and progress markers (like "4/5") are cut away before solving, and the question number itself can never leak into the maths.
- **Solves from the actual printed options** — each card shows the real multiple-choice options from the page, and the picked answer is highlighted green with a letter badge and a one-line reason.
- **Re-scans until it makes sense** — a read is scored on whether the answer it works out agrees with the printed choices. If the answer fits no choice, the frame is re-read (screen-cleanup pass, hard black-and-white, flipped colours) until the question and the choices agree, instead of stopping at a wrong answer.
- **Tells division from addition using the choices** — a ÷ photographed off a screen can lose its dots and read as +. When the first reading doesn't match any choice, I re-analyse the symbols against the choices, including retrying each number with its last digit dropped (a closing "?" can scan as a "7"). A rescue is only trusted when exactly one re-reading lands on a choice; if both readings match different choices, I flag it instead of guessing.
- **Highlighted answer with an explanation** — when I understand the question, the chosen option is highlighted on the camera and on its choice, with an explanation that states both readings when one was corrected (e.g. "As first read, 432+127 = 559 — not one of the choices. Re-analysed: 432 ÷ 12 = 36, which is choice B").
- **Suggested answers** — when a question is read but its choices aren't in the frame, the worked answer is shown labelled SUGGESTED ANSWER instead of nothing.
- **Several questions in one frame** — if the camera sees more than one question at once, each gets its own card and its own answer, numbered or unnumbered. A summary line reports what it found, e.g. "3 QUESTIONS IN THIS FRAME · 3 SOLVED".
- **Math** — arithmetic, fractions, percent-of, expressions with brackets, and simple solve-for-x, worked out on the spot.
- **General knowledge and cybersecurity** — open questions answered from built-in fact banks (capitals, planets, science, history, and more), plus Security+ and CISSP question banks covering Security+ topics and all 8 CISSP domains.
- **"Text it read"** — the exact text the camera read is shown in a box below, so I can check what it saw.

Everything runs on-device in the browser. No API key, no accounts, no network calls for the logic (the display font loads from Google Fonts when online).

## What it can and can't do yet

- It can solve simple math problems and a few cybersecurity questions.
- Story problems are still hit-or-miss. Some solve cleanly, some come back only as a suggestion, and some don't solve at all. My next update adds process of elimination with better logic: using the printed choices to narrow down the right answer.
- The cybersecurity bank is prototype knowledge only. It is not a claim that I hold CISSP — I hold CompTIA Security+.

## What changed — Nov 12, 2026 (this update)

Everything below is what I fixed and added today, testing against a real quiz app on my phone:

- **Frame-crop scan** — the scan now crops to exactly the green frame, and dark screens auto-invert so the reader sees dark text on light.
- **Quality-scored reads** — every read is scored (confidence, word-likeness, symbol noise, distinct choice letters). A poor read triggers a screen-cleanup re-read (median filter against screen moiré, adaptive threshold, thinning to split glow-merged letters); a read too poor to trust is reported as unreadable instead of dressed up as fake choices. A fraction-repair step fixes confusions like V4 → 1/4.
- **Division verification** — any + (or :) between two plain numbers is checked against the picture itself: the symbol is cropped out, enlarged, and re-read restricted to operator characters. A confirmed ÷ is written back before solving.
- **Sentence-form questions** — the words engine handles number words, divided-by / plus / minus / times phrasings, subtract-from, half/quarter of a number, and story problems. The question words turned into a calculation are highlighted, with a "READ AS: 12 ÷ 3 = 4" line and an amber QUESTION box on the camera next to the green answer box.
- **Story-problem solver** — equal sharing with any verb, packing into groups, per-container multiplication, profit (revenue − cost), speed (distance ÷ time), and change from a bill, plus careful two-number fallbacks. These solve even when the printed choices aren't in the frame.
- **Question anchor ("number + period")** — questions are located by their printed "N." start; titles and progress markers are cut away, and the question number can never leak into the maths.
- **Suggested answers** — no choices in the frame means a labelled SUGGESTED ANSWER instead of nothing.
- **Re-scan until it makes sense** — a read must agree with the printed choices; a no-fit read triggers re-reads (screen pass, hard black-and-white, flipped colours) until question and choices agree.
- **Division vs addition decided by the choices** — re-analysis retries each number with its last digit dropped to catch the closing "?" scanning as "7" ("432+127" → 432 ÷ 12 = 36 → B; "852−3977" → 852 − 397 = 455 → A), trusted only when exactly one re-reading lands on a choice. Quiz feedback lines ("Correct!"/"Incorrect.") are stripped from choice text.
- **Highlighted answer with explanation** — reconciled answers are highlighted on the camera and their choice, with the explanation stating both readings.

Earlier versions: full-frame scan with tappable words (Nov 11), minimal camera-first solver with the actual printed options (Nov 11), multi-question support with per-question cards (Nov 11).

## How to run it

Open `index.html` in a browser. No build step, no server needed.

- **With a camera:** point it at a printed question page. The camera needs HTTPS, which GitHub Pages provides — try the live demo below.
- **Without a camera:** tap one of the built-in samples — including "Three questions at once" — and tap Solve this text.

Live demo: https://jt989989989.github.io/james-thao-portfolio/projects/printed-text-reader-hud/

## Status

This is a **prototype** for the problem-solving mode of a future pair of smart glasses — not a finished product. No hardware exists yet; this phone version stands in for the glasses: the camera reads what's in front of you and the answer appears in a heads-up panel, the way it would on the lenses.
