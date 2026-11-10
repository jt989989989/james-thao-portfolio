# Flappy Bird Clone

A simple Flappy Bird–style game in a single HTML file. No build step, no
dependencies, no copied art or trademarked assets — the bird is a plain
yellow circle with an eye and beak, the pipes are flat green rectangles.

## How to play

- **Tap, click, or press Space / ↑** to flap.
- Fly through the gaps between the pipes. Each pipe you clear scores 1 point.
- Hit a pipe, the ground, or the top of the screen and the game is over.
- Your best score is saved in your browser (localStorage) and shown on the
  start and game-over screens.
- Tap / click / Space after game over to play again.

## Run it

Open `index.html` in any browser — desktop or mobile. It also works on
GitHub Pages:

https://jt989989989.github.io/james-thao-portfolio/projects/flappy-bird/

## How it works

- HTML5 Canvas, plain JavaScript, requestAnimationFrame game loop.
- Gravity pulls the bird down; each flap gives it an upward push.
- Pipes spawn on the right and scroll left; the gap height is randomized.
- Collision is checked against the pipe rectangles, the ground, and the
  ceiling. Score increments when a pipe passes behind the bird.
