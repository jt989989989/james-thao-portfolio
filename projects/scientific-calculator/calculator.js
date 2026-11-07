/* Scientific Calculator — expression parser.
 *
 * Parses and evaluates math expressions WITHOUT eval().
 * Recursive-descent parser: expression -> term -> factor -> postfix -> primary.
 *
 * Supports: + - * / % ^ (right-associative), parentheses, unary minus,
 * implicit multiplication (2(3+4), 2pi), factorial (n!), constants pi / e / Ans,
 * sin cos tan asin acos atan sinh cosh tanh, log (base 10), ln, sqrt, cbrt,
 * abs, exp, floor, ceil, round.
 * Trig uses degrees when context.angleMode is 'deg', radians otherwise.
 * Works in the browser (window.Calculator) and in Node (module.exports).
 */
(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.Calculator = api;
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  function CalculatorError(message) {
    this.name = "CalculatorError";
    this.message = message;
  }
  CalculatorError.prototype = Object.create(Error.prototype);

  const FUNCTIONS = {
    sin: 1, cos: 1, tan: 1, asin: 1, acos: 1, atan: 1,
    sinh: 1, cosh: 1, tanh: 1, log: 1, ln: 1, sqrt: 1,
    cbrt: 1, abs: 1, exp: 1, floor: 1, ceil: 1, round: 1,
  };

  function tokenize(input) {
    const tokens = [];
    let i = 0;
    while (i < input.length) {
      const ch = input[i];
      if (ch === " " || ch === "\t" || ch === "\n") { i++; continue; }
      if (/[0-9.]/.test(ch)) {
        const match = /^[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?/.exec(input.slice(i));
        if (!match || match[0] === ".") {
          throw new CalculatorError("Invalid number at position " + (i + 1));
        }
        tokens.push({ type: "number", value: parseFloat(match[0]) });
        i += match[0].length;
        continue;
      }
      if (/[a-zA-Zπ]/.test(ch)) {
        const match = /^[a-zA-Zπ]+/.exec(input.slice(i));
        tokens.push({ type: "ident", value: match[0].toLowerCase() });
        i += match[0].length;
        continue;
      }
      if ("+-*/%^!(),".indexOf(ch) !== -1) {
        tokens.push({ type: "op", value: ch });
        i++;
        continue;
      }
      throw new CalculatorError("Unexpected character '" + ch + "'");
    }
    tokens.push({ type: "end", value: null });
    return tokens;
  }

  function factorial(n) {
    if (!Number.isInteger(n) || n < 0) {
      throw new CalculatorError("Factorial needs a whole number >= 0");
    }
    if (n > 170) throw new CalculatorError("Factorial result is too large");
    let result = 1;
    for (let i = 2; i <= n; i++) result *= i;
    return result;
  }

  function Parser(tokens, context) {
    this.tokens = tokens;
    this.pos = 0;
    this.angleMode = context.angleMode || "rad";
    this.ans = context.ans || 0;
  }

  Parser.prototype.peek = function () { return this.tokens[this.pos]; };
  Parser.prototype.next = function () { return this.tokens[this.pos++]; };
  Parser.prototype.expect = function (value) {
    const tok = this.next();
    if (tok.value !== value) {
      throw new CalculatorError("Expected '" + value + "'");
    }
  };

  Parser.prototype.parse = function () {
    const value = this.parseExpression();
    if (this.peek().type !== "end") {
      throw new CalculatorError("Unexpected '" + this.peek().value + "' after expression");
    }
    return value;
  };

  Parser.prototype.parseExpression = function () {
    let value = this.parseTerm();
    for (;;) {
      const tok = this.peek();
      if (tok.value === "+") { this.next(); value += this.parseTerm(); }
      else if (tok.value === "-") { this.next(); value -= this.parseTerm(); }
      else return value;
    }
  };

  Parser.prototype.parseTerm = function () {
    let value = this.parseFactor();
    for (;;) {
      const tok = this.peek();
      if (tok.value === "*") { this.next(); value *= this.parseFactor(); }
      else if (tok.value === "/") {
        this.next();
        const divisor = this.parseFactor();
        if (divisor === 0) throw new CalculatorError("Cannot divide by zero");
        value /= divisor;
      } else if (tok.value === "%") {
        this.next();
        const divisor = this.parseFactor();
        if (divisor === 0) throw new CalculatorError("Cannot divide by zero");
        value %= divisor;
      } else if (tok.type === "number" || tok.value === "(" || tok.type === "ident") {
        // Implicit multiplication: 2(3+4), 2pi, (2)(3), 2sin(30).
        value *= this.parseFactor();
      } else return value;
    }
  };

  Parser.prototype.parseFactor = function () {
    const tok = this.peek();
    if (tok.value === "-") { this.next(); return -this.parseFactor(); }
    if (tok.value === "+") { this.next(); return this.parseFactor(); }
    let base = this.parsePostfix();
    if (this.peek().value === "^") {
      this.next();
      const exponent = this.parseFactor(); // right-associative
      const result = Math.pow(base, exponent);
      if (!isFinite(result)) throw new CalculatorError("Result is too large");
      return result;
    }
    return base;
  };

  Parser.prototype.parsePostfix = function () {
    let value = this.parsePrimary();
    while (this.peek().value === "!") {
      this.next();
      value = factorial(value);
    }
    return value;
  };

  Parser.prototype.parsePrimary = function () {
    const tok = this.next();
    if (tok.type === "number") return tok.value;
    if (tok.value === "(") {
      const value = this.parseExpression();
      if (this.peek().value === ")") this.next();
      else throw new CalculatorError("Missing closing parenthesis");
      return value;
    }
    if (tok.type === "ident") {
      const name = tok.value;
      if (name === "pi" || name === "π") return Math.PI;
      if (name === "e") return Math.E;
      if (name === "ans") return this.ans;
      if (name in FUNCTIONS) {
        if (this.peek().value === "(") this.next();
        else throw new CalculatorError("Function '" + name + "' needs parentheses");
        const arg = this.parseExpression();
        if (this.peek().value === ")") this.next();
        else throw new CalculatorError("Missing closing parenthesis");
        return this.applyFunction(name, arg);
      }
      throw new CalculatorError("Unknown name '" + name + "'");
    }
    throw new CalculatorError("Expected a number, function, or '('");
  };

  Parser.prototype.applyFunction = function (name, x) {
    const toRad = (d) => (d * Math.PI) / 180;
    const toDeg = (r) => (r * 180) / Math.PI;
    const deg = this.angleMode === "deg";
    switch (name) {
      case "sin": return Math.sin(deg ? toRad(x) : x);
      case "cos": return Math.cos(deg ? toRad(x) : x);
      case "tan": return Math.tan(deg ? toRad(x) : x);
      case "asin":
        if (Math.abs(x) > 1) throw new CalculatorError("asin needs a value between -1 and 1");
        return deg ? toDeg(Math.asin(x)) : Math.asin(x);
      case "acos":
        if (Math.abs(x) > 1) throw new CalculatorError("acos needs a value between -1 and 1");
        return deg ? toDeg(Math.acos(x)) : Math.acos(x);
      case "atan": return deg ? toDeg(Math.atan(x)) : Math.atan(x);
      case "sinh": return Math.sinh(x);
      case "cosh": return Math.cosh(x);
      case "tanh": return Math.tanh(x);
      case "log":
        if (x <= 0) throw new CalculatorError("log needs a value greater than 0");
        return Math.log10(x);
      case "ln":
        if (x <= 0) throw new CalculatorError("ln needs a value greater than 0");
        return Math.log(x);
      case "sqrt":
        if (x < 0) throw new CalculatorError("sqrt needs a value >= 0");
        return Math.sqrt(x);
      case "cbrt": return Math.cbrt(x);
      case "abs": return Math.abs(x);
      case "exp": {
        const r = Math.exp(x);
        if (!isFinite(r)) throw new CalculatorError("Result is too large");
        return r;
      }
      case "floor": return Math.floor(x);
      case "ceil": return Math.ceil(x);
      case "round": return Math.round(x);
      default: throw new CalculatorError("Unknown function '" + name + "'");
    }
  };

  function calculate(expression, context) {
    if (typeof expression !== "string" || expression.trim() === "") {
      throw new CalculatorError("Enter an expression");
    }
    const parser = new Parser(tokenize(expression), context || {});
    const value = parser.parse();
    if (typeof value !== "number" || Number.isNaN(value)) {
      throw new CalculatorError("Result is not a number");
    }
    if (!isFinite(value)) throw new CalculatorError("Result is too large");
    return value;
  }

  function formatResult(value) {
    if (value === 0) return "0";
    const abs = Math.abs(value);
    if ((abs !== 0 && abs < 1e-9) || abs >= 1e12) return value.toExponential(6);
    const rounded = Math.round(value * 1e10) / 1e10;
    return String(rounded);
  }

  return { calculate: calculate, formatResult: formatResult, CalculatorError: CalculatorError };
});
