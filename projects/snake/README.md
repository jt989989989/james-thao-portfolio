# Snake

I built this classic Snake game to practice game loops and grid logic in plain JavaScript — no libraries, no copied art, just a snake made of green squares chasing red food squares around a board.

## How to play

- **Swipe** on a phone, or use the **arrow keys / WASD** on a keyboard, to steer the snake.
- Eat the red squares to grow and score 1 point each. The snake speeds up a little with every square you eat.
- Hit a wall or bite your own tail and the game is over.
- Your best score is saved in your browser (localStorage) and shown on the start and game-over screens.
- **Tap / click / Space** to start, and again after game over to play again.

## Run it

Open `index.html` in any browser — desktop or mobile. It also works on GitHub Pages:

https://jt989989989.github.io/james-thao-portfolio/projects/snake/

## How it works

- HTML5 Canvas, plain JavaScript, a timer-driven game loop (the step delay shrinks as you eat, so the snake gets faster).
- The board is a 20×20 grid. The snake is a list of grid cells; each step adds a new head cell in the current direction and drops the tail — unless it eats, in which case it grows by one.
- Direction changes are queued and applied on the next step, so a fast double-turn can't reverse the snake into itself in a single tick.
- Collision is checked against the walls and the snake's own body (the tail cell is safe to enter, since it moves away that step).
- The game logic (`createGame`, `step`, `setDirection`) is kept separate from the rendering code, so I can test it headlessly in Node.
