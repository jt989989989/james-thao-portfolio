# Life of a Man

A satire board-game life sim: one man, one life, ages 18 to 65 — and every
quarter of it is a bad decision waiting to happen. Roll the dice, move around
the 40-square Board of Life, and pick your way through college, jobs, dating,
marriage, kids, debt, and midlife crises. Happiness is the main score; money
and stress just feed into it. The game ends when you die, with a tombstone
and a full summary of the life you lived.

This is a parody. The jokes are deliberately as offensive as possible —
satire of modern men's lifestyle is the whole point.

## How to play

Open the game in your browser (see the demo link on the repo's main README,
or open `index.html`):

1. **Roll the dice** — your token moves around the board.
2. **Land on a square** — Payday, Life Choice, Chance, Joy, or Debt.
3. **Every quarter, pick one of at least 5 choices** — or type anything into
   the "What do you do?" box and the snarky narrator will decide what happens.
4. **Watch your stats** — 😄 happiness, 💰 money, 🤯 stress, 💳 credit, plus
   age, debt, and relationships. Happiness is what your ending is scored on.
5. **Die** — at the end of your life you get a tombstone with your life
   summary, best and worst moments, ending title, and epitaph.

## The systems

- **40-square Board of Life** — dice, moving token, quarterly turns.
- **Quarterly ledger and debt system** — college loans, credit cards, car
  loans, and mortgages. Money grows slowly; debt grows fast.
- **Life branches** — military enlistment (with the girlfriend-cheats-while-
  deployed chain and the wife-spends-your-deployment-money reckoning),
  marriage, kids, divorce, and age forks at 30, 35, 40, 45, 50, and 55 —
  including the sugar daddy path at 50 if you reach it with no wife or
  girlfriend.
- **Chance events** — good and bad: divorce, credit score −50, a death in
  the family (grief, but maybe an inheritance), lottery wins, layoffs,
  surprise bills.
- **Happiness moments** — hunting, off-roading, and fishing with the boys.
  The counterweight to all the misery.
- **The narrator** — a snarky, D&D-style storyteller who narrates your life
  as you play and writes your epitaph. It runs entirely offline in the
  browser (a keyword storyteller engine, no API key, no network calls).
- **Multiple endings** — family man, divorced and broke, sugar daddy,
  bachelor forever, and more, scored by final happiness.

## Notes

- Single self-contained HTML file — no build step, no dependencies, no
  network calls. Everything runs in the browser.
- Single-screen layout (100dvh, no page scroll); all stats and the story
  panel fit on one screen.
- All characters, events, and jokes are fictional satire.
