# Printed Text Reader HUD (prototype)

> "You know the saying — give a tough job to a lazy person and see how they solve it. Well, this tool is meant to do that."

Point your phone's camera at printed text and this tool does the hard work for you: it reads the text and gives you the answer in a heads-up panel — the lazy way to solve hard questions.

## What it does

- **Multiple choice** — point at a question, get the letter + answer with a one-line reason. It flags uncertainty instead of guessing.
- **Math** — arithmetic, percent-of, and simple solve-for-x, worked out on the spot.
- **Word definitions** — stare at a word in the center reticle for about 3 seconds and get a one-line definition; look away and it clears.
- **General knowledge** — open questions answered from a built-in fact bank (capitals, planets, science, history, and more).
- **Security+ and CISSP question banks** — cybersecurity questions answered from built-in banks covering Security+ topics and all 8 CISSP domains.

Everything runs on-device in the browser. No API key, no accounts, no network calls for the logic (the display font loads from Google Fonts when online).

## How to run it

Open `index.html` in a browser. No build step, no server needed.

- **With a camera:** tap Capture & Read. The camera needs HTTPS, which GitHub Pages provides — try the live demo below.
- **Without a camera:** tap one of the 4 built-in samples (multiple choice, algebra, geography, science) and tap Solve this text.

Live demo: https://jt989989989.github.io/james-thao-portfolio/projects/printed-text-reader-hud/

## Status

This is a **prototype** for the problem-solving mode of a future pair of smart glasses — not a finished product. No hardware exists yet; this phone version stands in for the glasses: the camera reads what's in front of you and the answer appears in a heads-up panel, the way it would on the lenses.
