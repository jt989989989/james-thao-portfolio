/* Run with: node --test tests/calculator.test.js */
const test = require("node:test");
const assert = require("node:assert/strict");
const { calculate } = require("../calculator.js");

const deg = { angleMode: "deg" };
const rad = { angleMode: "rad" };

test("basic arithmetic and precedence", () => {
  assert.equal(calculate("2+3*4"), 14);
  assert.equal(calculate("(2+3)*4"), 20);
  assert.equal(calculate("10/4"), 2.5);
  assert.equal(calculate("10%3"), 1);
  assert.equal(calculate("2^10"), 1024);
  assert.equal(calculate("2^3^2"), 512); // right-associative: 2^(3^2)
  assert.equal(calculate("-2^2"), -4);
  assert.equal(calculate("--5"), 5);
});

test("implicit multiplication and constants", () => {
  assert.equal(calculate("2(3+4)"), 14);
  assert.equal(calculate("(2)(3)"), 6);
  assert.equal(calculate("2pi", rad), 2 * Math.PI);
  assert.equal(calculate("2e", rad), 2 * Math.E);
  assert.equal(calculate("5!", rad), 120);
  assert.equal(calculate("3!+2", rad), 8);
});

test("functions in degrees and radians", () => {
  assert.ok(Math.abs(calculate("sin(30)", deg) - 0.5) < 1e-10);
  assert.ok(Math.abs(calculate("cos(60)", deg) - 0.5) < 1e-10);
  assert.ok(Math.abs(calculate("sin(pi/2)", rad) - 1) < 1e-10);
  assert.equal(calculate("sqrt(16)"), 4);
  assert.equal(calculate("log(1000)"), 3);
  assert.ok(Math.abs(calculate("ln(e)") - 1) < 1e-10);
  assert.equal(calculate("abs(0-7)"), 7);
  assert.equal(calculate("cbrt(27)"), 3);
  assert.ok(Math.abs(calculate("asin(1)", deg) - 90) < 1e-10);
});

test("Ans reuse", () => {
  assert.equal(calculate("Ans+1", { ans: 41 }), 42);
});

test("errors are clear, not crashes", () => {
  assert.throws(() => calculate("1/0"), /divide by zero/);
  assert.throws(() => calculate("sqrt(0-1)"), /sqrt/);
  assert.throws(() => calculate("log(0)"), /log/);
  assert.throws(() => calculate("2+"), /Expected/);
  assert.throws(() => calculate("(2+3"), /closing parenthesis/);
  assert.throws(() => calculate("foo(2)"), /Unknown name/);
  assert.throws(() => calculate(""), /Enter an expression/);
});
