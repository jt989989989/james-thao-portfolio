# Scientific Calculator

A scientific calculator that runs in the browser — open `index.html`, no build step or server needed.

Built as a portfolio project. The interesting part is not the buttons, it is the expression parser in `calculator.js`: a recursive-descent parser that evaluates typed expressions without ever using `eval()`.

## What it does

- Full expressions with precedence: `2+3*4`, `(2+3)*4`, `2^3^2` (right-associative, so 512)
- Operators: `+ - * / % ^`, unary minus, parentheses, implicit multiplication (`2(3+4)`, `2pi`), factorial (`5!`)
- Functions: `sin cos tan asin acos atan sinh cosh tanh log ln sqrt cbrt abs exp floor ceil round`
- Constants: `pi`, `e`, and `Ans` (the last answer)
- DEG / RAD toggle for trig, memory keys (M+, M-, MR, MC), a history list you can click to reuse, and keyboard support (type an expression, Enter to calculate)
- Clear errors instead of crashing: divide by zero, `sqrt` of a negative, `log(0)`, mismatched parentheses, unknown names

## Run it

Open `index.html` in a browser, or try the parser from the command line:

```bash
node -e "const {calculate} = require('./calculator.js'); console.log(calculate('sin(30)', {angleMode:'deg'}))"
# 0.5
```

## Tests

```bash
node --test tests/calculator.test.js
```

## Skills shown

JavaScript, recursive-descent parsing / tokenizing, operator precedence and associativity, error handling, DOM UI with keyboard support, unit tests with Node's built-in test runner. No dependencies, no `eval()`.
