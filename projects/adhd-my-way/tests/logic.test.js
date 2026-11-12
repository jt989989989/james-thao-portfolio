import test from 'node:test';
import assert from 'node:assert/strict';
import {
  CATEGORIES,
  MEMORY_WIN_COINS,
  SHOP,
  STAR_TAP_COINS,
  TASK_COINS,
  TIMER_BONUS_COINS,
  addTask,
  applyDailyReset,
  awardMemoryWin,
  awardStarTaps,
  awardTimerFinish,
  buyOrEquip,
  createDefaultState,
  createMemoryDeck,
  finishFocusSession,
  isMemoryMatch,
  migrateState,
  needsDailyReset,
  recordActivity,
  removeTask,
  tasksByCategory,
  tasksDoneCount,
  toggleTask,
} from '../src/logic.js';

test('default state: 6 sample tasks, 0 coins, free shop items owned', () => {
  const s = createDefaultState(new Date('2026-11-08T10:00:00'));
  assert.equal(s.tasks.length, 6);
  assert.equal(s.coins, 0);
  assert.equal(s.date, '2026-11-08');
  assert.equal(tasksDoneCount(s), 0);
  assert.ok(s.owned.includes('skin-1'));
  assert.ok(!s.owned.includes('hat-crown'));
});

test('completing a task earns coins; unchecking takes them back', () => {
  const s = createDefaultState();
  const done = toggleTask(s, 't1');
  assert.equal(done.ok, true);
  assert.equal(done.done, true);
  assert.equal(s.coins, TASK_COINS);
  assert.equal(s.stats.tasksDone, 1);
  const undone = toggleTask(s, 't1');
  assert.equal(undone.done, false);
  assert.equal(s.coins, 0);
  // Coins never go below zero even after odd toggling.
  toggleTask(s, 't1');
  toggleTask(s, 't1');
  assert.ok(s.coins >= 0);
});

test('toggling an unknown task fails without changing coins', () => {
  const s = createDefaultState();
  assert.equal(toggleTask(s, 'nope').ok, false);
  assert.equal(s.coins, 0);
});

test('add and remove custom tasks; built-in tasks cannot be removed', () => {
  const s = createDefaultState();
  const added = addTask(s, '  Feed the dog  ', 'home', 'c1');
  assert.equal(added.ok, true);
  assert.equal(added.task.title, 'Feed the dog');
  assert.equal(s.tasks.length, 7);
  assert.equal(addTask(s, '   ').ok, false);
  assert.equal(removeTask(s, 't1').ok, false);
  assert.equal(removeTask(s, 'c1').ok, true);
  assert.equal(s.tasks.length, 6);
});

test('daily reset clears checkmarks on a new day but keeps coins', () => {
  const s = createDefaultState(new Date('2026-11-08T10:00:00'));
  toggleTask(s, 't1');
  assert.equal(needsDailyReset(s, new Date('2026-11-08T23:00:00')), false);
  assert.equal(needsDailyReset(s, new Date('2026-11-09T08:00:00')), true);
  applyDailyReset(s, new Date('2026-11-09T08:00:00'));
  assert.equal(tasksDoneCount(s), 0);
  assert.equal(s.coins, TASK_COINS);
  assert.equal(s.date, '2026-11-09');
});

test('shop: free items equip, paid items cost coins, poor players are refused', () => {
  const s = createDefaultState();
  const free = buyOrEquip(s, 'skin-3');
  assert.equal(free.ok, true);
  assert.equal(free.action, 'equipped');
  assert.equal(s.avatar.skin, '#8d5524');

  const broke = buyOrEquip(s, 'hat-crown');
  assert.equal(broke.ok, false);
  assert.equal(broke.reason, 'not enough coins');
  assert.equal(s.avatar.hat, 'none');

  s.coins = 100;
  const bought = buyOrEquip(s, 'hat-crown');
  assert.equal(bought.ok, true);
  assert.equal(bought.action, 'bought');
  assert.equal(s.coins, 0);
  assert.equal(s.avatar.hat, 'crown');

  const again = buyOrEquip(s, 'hat-crown');
  assert.equal(again.action, 'already-equipped');
  assert.equal(again.coins, 0);
});

test('shop catalogue has no duplicate ids', () => {
  const ids = SHOP.map((i) => i.id);
  assert.equal(new Set(ids).size, ids.length);
});

test('memory deck: 12 cards, 6 pairs, each shape twice', () => {
  const deck = createMemoryDeck(() => 0.5);
  assert.equal(deck.length, 12);
  const counts = {};
  for (const card of deck) counts[card.shape] = (counts[card.shape] || 0) + 1;
  assert.equal(Object.keys(counts).length, 6);
  assert.ok(Object.values(counts).every((n) => n === 2));
  const a = deck.find((c) => c.key.endsWith('-a'));
  const b = deck.find((c) => c.key === `${a.shape}-b`);
  assert.equal(isMemoryMatch(a, b), true);
  assert.equal(isMemoryMatch(a, a), false);
  assert.equal(isMemoryMatch(a, deck.find((c) => c.shape !== a.shape)), false);
});

test('rewards: memory win, star taps, timer finish', () => {
  const s = createDefaultState();
  assert.equal(awardMemoryWin(s), MEMORY_WIN_COINS);
  assert.equal(s.stats.gamesWon, 1);
  assert.equal(awardStarTaps(s, 5), 5 * STAR_TAP_COINS);
  assert.equal(s.stats.starsTapped, 5);
  assert.equal(awardTimerFinish(s), TIMER_BONUS_COINS);
  assert.equal(s.stats.timersFinished, 1);
  assert.equal(s.coins, MEMORY_WIN_COINS + 5 * STAR_TAP_COINS + TIMER_BONUS_COINS);
});

test('v2: every default quest has a valid category; filtering works', () => {
  const s = createDefaultState();
  const valid = new Set(CATEGORIES.map((c) => c.id));
  assert.ok(s.tasks.every((t) => valid.has(t.category)));
  assert.equal(tasksByCategory(s, 'all').length, 6);
  assert.equal(tasksByCategory(s, 'morning').length, 2); // brush teeth, make bed
  assert.equal(tasksByCategory(s, 'school').length, 2); // homework, reading
  assert.equal(tasksByCategory(s, 'health').length, 1); // water
  assert.equal(tasksByCategory(s, 'fun').length, 0);
});

test('v2: adding a quest picks a category; unknown categories fall back to home', () => {
  const s = createDefaultState();
  const added = addTask(s, 'Practise piano', 'fun', 'c9');
  assert.equal(added.ok, true);
  assert.equal(added.task.category, 'fun');
  assert.equal(tasksByCategory(s, 'fun').length, 1);
  const fallback = addTask(s, 'Something', 'not-a-category', 'c10');
  assert.equal(fallback.task.category, 'home');
});

test('v2: streak grows on consecutive active days, restarts after a gap', () => {
  const s = createDefaultState(new Date('2026-11-12T09:00:00'));
  assert.equal(s.streak.count, 0);
  toggleTask(s, 't1', new Date('2026-11-12T09:00:00'));
  assert.equal(s.streak.count, 1);
  assert.equal(s.streak.best, 1);
  // Same day again: no double count.
  toggleTask(s, 't2', new Date('2026-11-12T18:00:00'));
  assert.equal(s.streak.count, 1);
  // Next day: extends.
  recordActivity(s, new Date('2026-11-13T09:00:00'));
  assert.equal(s.streak.count, 2);
  assert.equal(s.streak.best, 2);
  // Skip a day (Nov 14 idle, active again Nov 15): restarts at 1.
  recordActivity(s, new Date('2026-11-15T09:00:00'));
  assert.equal(s.streak.count, 1);
  assert.equal(s.streak.best, 2);
});

test('v2: focus session finishes the focused quest plus the timer bonus', () => {
  const s = createDefaultState(new Date('2026-11-12T09:00:00'));
  const result = finishFocusSession(s, 't3', new Date('2026-11-12T09:00:00'));
  assert.equal(result.ok, true);
  assert.equal(result.taskDone, true);
  assert.equal(result.taskTitle, 'Tidy my room');
  assert.equal(result.coins, TASK_COINS + TIMER_BONUS_COINS);
  assert.equal(s.coins, TASK_COINS + TIMER_BONUS_COINS);
  assert.equal(s.stats.timersFinished, 1);
  assert.equal(s.streak.count, 1);

  // Focusing on an already-done quest pays only the bonus, never twice.
  const again = finishFocusSession(s, 't3', new Date('2026-11-12T10:00:00'));
  assert.equal(again.taskDone, false);
  assert.equal(again.coins, TIMER_BONUS_COINS);

  // No quest picked: just the bonus.
  const plain = finishFocusSession(s, null, new Date('2026-11-12T11:00:00'));
  assert.equal(plain.taskDone, false);
  assert.equal(plain.coins, TIMER_BONUS_COINS);
});

test('v2: migrating a v1 save keeps coins and adds streak + categories', () => {
  const v1 = {
    version: 1,
    coins: 45,
    date: '2026-11-11',
    tasks: [
      { id: 't1', title: 'Brush my teeth', coins: 10, custom: false, done: false },
      { id: 'c1', title: 'Feed the dog', coins: 10, custom: true, done: true },
    ],
    avatar: { skin: '#f6c89f', hairStyle: 'short', hairColor: '#5b3a1e', hat: 'none', accessory: 'none' },
    owned: ['skin-1'],
    stats: { tasksDone: 3, gamesWon: 0, starsTapped: 0, timersFinished: 1 },
  };
  const s = migrateState(v1);
  assert.equal(s.version, 2);
  assert.equal(s.coins, 45);
  assert.equal(s.streak.count, 0);
  assert.equal(s.streak.best, 0);
  assert.equal(s.streak.lastActiveDate, null);
  assert.ok(s.tasks.every((t) => typeof t.category === 'string' && t.category.length > 0));
  assert.equal(s.tasks[0].done, false);
  assert.equal(s.tasks[1].done, true);
});
