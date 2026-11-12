# Printed Text Reader HUD (prototype)

> "You know the saying — give a tough job to a lazy person and see how they solve it. Well, this tool is meant to do that."

Point your phone's camera at printed text and this tool does the hard work for you: it reads **all the words in the frame at once** — every word gets a tappable box, and tapping any word gives you an instant one-line definition. No giant center label, no staring at one word at a time — I built it to be faster than typing a word into Google.

## What it does

- **Full-frame scan** — the camera reads every word in view at once. Each word gets a tappable overlay box, and the Words in Frame panel lists them all as chips — tap any word, anywhere in the frame.
- **Multiple choice** — point at a question, get the letter + answer with a one-line reason. It flags uncertainty instead of guessing.
- **Math** — arithmetic, percent-of, and simple solve-for-x, worked out on the spot.
- **Word definitions** — tap any word on screen (or in the Words in Frame panel) and get a one-line definition instantly. No waiting, no center label — the whole frame is read at once.
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
