// ADHD My Way — pure app logic (no DOM, no localStorage here, so it can be
// unit-tested with plain Node). main.js wires this up to Ionic + localStorage.

export const STORAGE_KEY = 'adhd-my-way-v1';

export const TASK_COINS = 10; // coins earned for finishing one daily task
export const MEMORY_WIN_COINS = 20; // coins for winning Memory Match
export const STAR_TAP_COINS = 2; // coins per star tapped
export const TIMER_BONUS_COINS = 5; // coins for finishing a focus timer

export const DEFAULT_TASKS = [
  { id: 't1', title: 'Brush my teeth', coins: TASK_COINS, custom: false },
  { id: 't2', title: 'Do my homework', coins: TASK_COINS, custom: false },
  { id: 't3', title: 'Tidy my room', coins: TASK_COINS, custom: false },
  { id: 't4', title: 'Read for 10 minutes', coins: TASK_COINS, custom: false },
  { id: 't5', title: 'Make my bed', coins: TASK_COINS, custom: false },
  { id: 't6', title: 'Drink a glass of water', coins: TASK_COINS, custom: false },
];

// Avatar shop catalogue. `slot` is which avatar part the item changes.
// Items with price 0 are free and owned from the start.
export const SHOP = [
  // Skins (free)
  { id: 'skin-1', slot: 'skin', name: 'Peachy', value: '#f6c89f', price: 0 },
  { id: 'skin-2', slot: 'skin', name: 'Honey', value: '#e0a878', price: 0 },
  { id: 'skin-3', slot: 'skin', name: 'Cocoa', value: '#8d5524', price: 0 },
  { id: 'skin-4', slot: 'skin', name: 'Cream', value: '#ffdbac', price: 0 },
  // Hair styles
  { id: 'hair-short', slot: 'hairStyle', name: 'Short hair', value: 'short', price: 0 },
  { id: 'hair-curly', slot: 'hairStyle', name: 'Curly hair', value: 'curly', price: 15 },
  { id: 'hair-spiky', slot: 'hairStyle', name: 'Spiky hair', value: 'spiky', price: 15 },
  { id: 'hair-long', slot: 'hairStyle', name: 'Long hair', value: 'long', price: 20 },
  // Hair colours (free)
  { id: 'hair-brown', slot: 'hairColor', name: 'Brown hair', value: '#5b3a1e', price: 0 },
  { id: 'hair-black', slot: 'hairColor', name: 'Black hair', value: '#222222', price: 0 },
  { id: 'hair-blonde', slot: 'hairColor', name: 'Blonde hair', value: '#f2c94c', price: 0 },
  { id: 'hair-red', slot: 'hairColor', name: 'Red hair', value: '#c0392b', price: 0 },
  // Hats
  { id: 'hat-none', slot: 'hat', name: 'No hat', value: 'none', price: 0 },
  { id: 'hat-cap', slot: 'hat', name: 'Red cap', value: 'cap', price: 30 },
  { id: 'hat-beanie', slot: 'hat', name: 'Blue beanie', value: 'beanie', price: 40 },
  { id: 'hat-crown', slot: 'hat', name: 'Gold crown', value: 'crown', price: 100 },
  // Accessories
  { id: 'acc-none', slot: 'accessory', name: 'No accessory', value: 'none', price: 0 },
  { id: 'acc-star', slot: 'accessory', name: 'Star badge', value: 'star', price: 25 },
  { id: 'acc-glasses', slot: 'accessory', name: 'Cool glasses', value: 'glasses', price: 50 },
  { id: 'acc-headphones', slot: 'accessory', name: 'Headphones', value: 'headphones', price: 60 },
];

export const MEMORY_SHAPES = [
  { id: 'circle', color: '#ff6b6b' },
  { id: 'square', color: '#4dabff' },
  { id: 'triangle', color: '#51cf66' },
  { id: 'diamond', color: '#f2c94c' },
  { id: 'star', color: '#9775fa' },
  { id: 'heart', color: '#ff8fab' },
];

export function todayString(date = new Date()) {
  return date.toISOString().slice(0, 10); // YYYY-MM-DD, local day is fine for a demo
}

export function createDefaultState(date = new Date()) {
  return {
    version: 1,
    coins: 0,
    date: todayString(date),
    tasks: DEFAULT_TASKS.map((t) => ({ ...t, done: false })),
    avatar: {
      skin: '#f6c89f',
      hairStyle: 'short',
      hairColor: '#5b3a1e',
      hat: 'none',
      accessory: 'none',
    },
    owned: SHOP.filter((item) => item.price === 0).map((item) => item.id),
    stats: { tasksDone: 0, gamesWon: 0, starsTapped: 0, timersFinished: 0 },
  };
}

// A new day starts with a fresh, unchecked task list (coins stay).
export function needsDailyReset(state, date = new Date()) {
  return state.date !== todayString(date);
}

export function applyDailyReset(state, date = new Date()) {
  state.date = todayString(date);
  for (const task of state.tasks) task.done = false;
  return state;
}

export function findTask(state, id) {
  return state.tasks.find((t) => t.id === id);
}

// Checking a task off earns its coins; unchecking takes them back,
// so coins can never be farmed by toggling.
export function toggleTask(state, id) {
  const task = findTask(state, id);
  if (!task) return { ok: false, reason: 'no such task' };
  task.done = !task.done;
  state.coins = Math.max(0, state.coins + (task.done ? task.coins : -task.coins));
  if (task.done) state.stats.tasksDone += 1;
  return { ok: true, done: task.done, coins: state.coins };
}

export function addTask(state, title, id = `c${Date.now()}`) {
  const clean = String(title || '').trim().slice(0, 60);
  if (!clean) return { ok: false, reason: 'empty title' };
  const task = { id, title: clean, coins: TASK_COINS, custom: true, done: false };
  state.tasks.push(task);
  return { ok: true, task };
}

export function removeTask(state, id) {
  const task = findTask(state, id);
  if (!task) return { ok: false, reason: 'no such task' };
  if (!task.custom) return { ok: false, reason: 'built-in tasks cannot be removed' };
  state.tasks = state.tasks.filter((t) => t.id !== id);
  return { ok: true };
}

export function tasksDoneCount(state) {
  return state.tasks.filter((t) => t.done).length;
}

export function shopItem(id) {
  return SHOP.find((item) => item.id === id);
}

// Buy an item (spends coins) or equip an already-owned one.
// Returns { ok, action: 'bought' | 'equipped' | 'already-equipped', coins }.
export function buyOrEquip(state, id) {
  const item = shopItem(id);
  if (!item) return { ok: false, reason: 'no such item' };
  if (state.avatar[item.slot] === item.value) {
    return { ok: true, action: 'already-equipped', coins: state.coins };
  }
  let bought = false;
  if (!state.owned.includes(id)) {
    if (state.coins < item.price) {
      return { ok: false, reason: 'not enough coins', coins: state.coins, price: item.price };
    }
    state.coins -= item.price;
    state.owned.push(id);
    bought = true;
  }
  state.avatar[item.slot] = item.value;
  return { ok: true, action: bought ? 'bought' : 'equipped', coins: state.coins };
}

// Memory Match: a shuffled deck of 12 cards (6 shape pairs).
export function createMemoryDeck(random = Math.random) {
  const cards = MEMORY_SHAPES.flatMap((shape) => [
    { key: `${shape.id}-a`, shape: shape.id, color: shape.color },
    { key: `${shape.id}-b`, shape: shape.id, color: shape.color },
  ]);
  for (let i = cards.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [cards[i], cards[j]] = [cards[j], cards[i]];
  }
  return cards;
}

export function isMemoryMatch(cardA, cardB) {
  return !!cardA && !!cardB && cardA.shape === cardB.shape && cardA.key !== cardB.key;
}

// Star-tap scoring: each tap is worth STAR_TAP_COINS.
export function awardStarTaps(state, taps) {
  const earned = Math.max(0, Math.floor(taps)) * STAR_TAP_COINS;
  state.coins += earned;
  state.stats.starsTapped += Math.max(0, Math.floor(taps));
  return earned;
}

export function awardMemoryWin(state) {
  state.coins += MEMORY_WIN_COINS;
  state.stats.gamesWon += 1;
  return MEMORY_WIN_COINS;
}

export function awardTimerFinish(state) {
  state.coins += TIMER_BONUS_COINS;
  state.stats.timersFinished += 1;
  return TIMER_BONUS_COINS;
}
