// ADHD My Way — pure app logic (no DOM, no localStorage here, so it can be
// unit-tested with plain Node). main.js wires this up to Ionic + localStorage.

export const STORAGE_KEY = 'adhd-my-way-v1';

// Quest categories — v2. Every quest belongs to one, so a child (or a
// grown-up helping) can filter the list to just "morning" or "school".
export const CATEGORIES = [
  { id: 'morning', name: 'Morning', color: '#ffb703' },
  { id: 'school', name: 'School', color: '#4dabff' },
  { id: 'home', name: 'Home', color: '#51cf66' },
  { id: 'health', name: 'Health', color: '#ff6b6b' },
  { id: 'fun', name: 'Fun', color: '#9775fa' },
];

export function categoryById(id) {
  return CATEGORIES.find((c) => c.id === id) || null;
}

export function validCategory(id) {
  return categoryById(id) ? id : 'home';
}

export const TASK_COINS = 10; // coins earned for finishing one daily task
export const MEMORY_WIN_COINS = 20; // coins for winning Memory Match
export const STAR_TAP_COINS = 2; // coins per star tapped
export const TIMER_BONUS_COINS = 5; // coins for finishing a focus timer
export const COLOUR_MATCH_COINS = 2; // coins per correct Colour Match tap
export const COLOUR_GAME_BONUS_COINS = 10; // bonus for finishing all Colour Match rounds
export const COLOUR_ROUNDS = 10; // rounds in one Colour Match game

// Colour Match (v3): read the colour word, tap the button in that colour.
// Words are the challenge — the word is shown in plain dark text, so a
// child has to read it, not just match the ink colour.
export const COLOUR_WORDS = [
  { id: 'red', name: 'Red', color: '#ff6b6b' },
  { id: 'blue', name: 'Blue', color: '#4dabff' },
  { id: 'green', name: 'Green', color: '#51cf66' },
  { id: 'yellow', name: 'Yellow', color: '#f2c94c' },
  { id: 'purple', name: 'Purple', color: '#9775fa' },
  { id: 'orange', name: 'Orange', color: '#fb8c00' },
  { id: 'pink', name: 'Pink', color: '#ff8fab' },
];

export const DEFAULT_TASKS = [
  { id: 't1', title: 'Brush my teeth', category: 'morning', coins: TASK_COINS, custom: false },
  { id: 't2', title: 'Do my homework', category: 'school', coins: TASK_COINS, custom: false },
  { id: 't3', title: 'Tidy my room', category: 'home', coins: TASK_COINS, custom: false },
  { id: 't4', title: 'Read for 10 minutes', category: 'school', coins: TASK_COINS, custom: false },
  { id: 't5', title: 'Make my bed', category: 'morning', coins: TASK_COINS, custom: false },
  { id: 't6', title: 'Drink a glass of water', category: 'health', coins: TASK_COINS, custom: false },
];

// Avatar shop catalogue. `slot` is which avatar part the item changes.
// Items with price 0 are free and owned from the start.
export const SHOP = [
  // Skins (free)
  { id: 'skin-1', slot: 'skin', name: 'Peachy', value: '#f6c89f', price: 0 },
  { id: 'skin-2', slot: 'skin', name: 'Honey', value: '#e0a878', price: 0 },
  { id: 'skin-3', slot: 'skin', name: 'Cocoa', value: '#8d5524', price: 0 },
  { id: 'skin-4', slot: 'skin', name: 'Cream', value: '#ffdbac', price: 0 },
  { id: 'skin-5', slot: 'skin', name: 'Golden', value: '#e8b06a', price: 0 },
  // Hair styles
  { id: 'hair-short', slot: 'hairStyle', name: 'Short hair', value: 'short', price: 0 },
  { id: 'hair-curly', slot: 'hairStyle', name: 'Curly hair', value: 'curly', price: 15 },
  { id: 'hair-spiky', slot: 'hairStyle', name: 'Spiky hair', value: 'spiky', price: 15 },
  { id: 'hair-long', slot: 'hairStyle', name: 'Long hair', value: 'long', price: 20 },
  { id: 'hair-ponytail', slot: 'hairStyle', name: 'Ponytail', value: 'ponytail', price: 25 },
  // Hair colours (free)
  { id: 'hair-brown', slot: 'hairColor', name: 'Brown hair', value: '#5b3a1e', price: 0 },
  { id: 'hair-black', slot: 'hairColor', name: 'Black hair', value: '#222222', price: 0 },
  { id: 'hair-blonde', slot: 'hairColor', name: 'Blonde hair', value: '#f2c94c', price: 0 },
  { id: 'hair-red', slot: 'hairColor', name: 'Red hair', value: '#c0392b', price: 0 },
  { id: 'hair-purple', slot: 'hairColor', name: 'Purple hair', value: '#9775fa', price: 0 },
  // Hats
  { id: 'hat-none', slot: 'hat', name: 'No hat', value: 'none', price: 0 },
  { id: 'hat-cap', slot: 'hat', name: 'Red cap', value: 'cap', price: 30 },
  { id: 'hat-beanie', slot: 'hat', name: 'Blue beanie', value: 'beanie', price: 40 },
  { id: 'hat-party', slot: 'hat', name: 'Party hat', value: 'party', price: 45 },
  { id: 'hat-wizard', slot: 'hat', name: 'Wizard hat', value: 'wizard', price: 80 },
  { id: 'hat-crown', slot: 'hat', name: 'Gold crown', value: 'crown', price: 100 },
  // Accessories
  { id: 'acc-none', slot: 'accessory', name: 'No accessory', value: 'none', price: 0 },
  { id: 'acc-star', slot: 'accessory', name: 'Star badge', value: 'star', price: 25 },
  { id: 'acc-heart', slot: 'accessory', name: 'Heart badge', value: 'heart', price: 30 },
  { id: 'acc-glasses', slot: 'accessory', name: 'Cool glasses', value: 'glasses', price: 50 },
  { id: 'acc-headphones', slot: 'accessory', name: 'Headphones', value: 'headphones', price: 60 },
  { id: 'acc-sunglasses', slot: 'accessory', name: 'Sunglasses', value: 'sunglasses', price: 70 },
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

export function yesterdayString(date = new Date()) {
  return todayString(new Date(date.getTime() - 24 * 60 * 60 * 1000));
}

export function createDefaultState(date = new Date()) {
  return {
    version: 3,
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
    // v2 streak: consecutive days with at least one quest finished.
    streak: { count: 0, best: 0, lastActiveDate: null },
    stats: { tasksDone: 0, gamesWon: 0, starsTapped: 0, timersFinished: 0, colourPlayed: 0, colourCorrect: 0 },
  };
}

// Fill in any stats keys an older save is missing (v1/v2 saves have no
// colour stats); never wipes a count that is already there.
function ensureStats(state) {
  if (!state.stats || typeof state.stats !== 'object') {
    state.stats = { tasksDone: 0, gamesWon: 0, starsTapped: 0, timersFinished: 0 };
  }
  for (const [key, fallback] of Object.entries({ tasksDone: 0, gamesWon: 0, starsTapped: 0, timersFinished: 0, colourPlayed: 0, colourCorrect: 0 })) {
    if (typeof state.stats[key] !== 'number') state.stats[key] = fallback;
  }
  return state.stats;
}

// Bring a saved v1/v2 state up to v3 without losing coins, quests or avatar:
// adds the streak record, a category for any quest that lacks one, and the
// v3 colour-game stats.
export function migrateState(state) {
  if (!state || typeof state !== 'object') return createDefaultState();
  if (!state.streak || typeof state.streak !== 'object') {
    state.streak = { count: 0, best: 0, lastActiveDate: null };
  }
  if (typeof state.streak.count !== 'number') state.streak.count = 0;
  if (typeof state.streak.best !== 'number') state.streak.best = 0;
  if (Array.isArray(state.tasks)) {
    for (const task of state.tasks) {
      if (!categoryById(task.category)) task.category = validCategory(task.category);
    }
  }
  ensureStats(state);
  state.version = 3;
  return state;
}

// Streak rule (kid-friendly): a day counts when at least one quest is
// finished that day. Finishing a quest on the day right after the last
// active day extends the streak; any longer gap restarts it at 1.
export function recordActivity(state, date = new Date()) {
  const today = todayString(date);
  const streak = state.streak || (state.streak = { count: 0, best: 0, lastActiveDate: null });
  if (streak.lastActiveDate === today) return streak;
  if (streak.lastActiveDate === yesterdayString(date)) {
    streak.count += 1;
  } else {
    streak.count = 1;
  }
  streak.lastActiveDate = today;
  if (streak.count > streak.best) streak.best = streak.count;
  return streak;
}

// Filter quests by category ('all' returns every quest).
export function tasksByCategory(state, category) {
  if (!category || category === 'all') return state.tasks;
  return state.tasks.filter((t) => t.category === category);
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
export function toggleTask(state, id, date = new Date()) {
  const task = findTask(state, id);
  if (!task) return { ok: false, reason: 'no such task' };
  task.done = !task.done;
  state.coins = Math.max(0, state.coins + (task.done ? task.coins : -task.coins));
  if (task.done) {
    state.stats.tasksDone += 1;
    recordActivity(state, date);
  }
  return { ok: true, done: task.done, coins: state.coins };
}

export function addTask(state, title, category = 'home', id = `c${Date.now()}`) {
  const clean = String(title || '').trim().slice(0, 60);
  if (!clean) return { ok: false, reason: 'empty title' };
  const task = { id, title: clean, category: validCategory(category), coins: TASK_COINS, custom: true, done: false };
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

// v2 per-quest focus: finishing a focus session earns the timer bonus,
// and if the session was focused on a quest that is still open, that
// quest is ticked off too (its coins included). Already-done quests
// are never paid twice.
export function finishFocusSession(state, taskId = null, date = new Date()) {
  let taskDone = false;
  let taskTitle = null;
  let taskCoins = 0;
  const task = taskId ? findTask(state, taskId) : null;
  if (task && !task.done) {
    task.done = true;
    state.coins += task.coins;
    state.stats.tasksDone += 1;
    recordActivity(state, date);
    taskDone = true;
    taskTitle = task.title;
    taskCoins = task.coins;
  }
  const bonus = awardTimerFinish(state);
  return { ok: true, coins: bonus + taskCoins, bonus, taskDone, taskTitle };
}

// ---------- v3: Colour Match ----------
// One round: a target colour word plus 4 colour buttons to choose from
// (the target plus 3 distractors, shuffled). The word is the challenge —
// the buttons are plain colours, so the child has to read the word.
export function createColourRound(random = Math.random) {
  const target = COLOUR_WORDS[Math.floor(random() * COLOUR_WORDS.length)];
  const others = COLOUR_WORDS.filter((c) => c.id !== target.id);
  for (let i = others.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [others[i], others[j]] = [others[j], others[i]];
  }
  const options = [target, ...others.slice(0, 3)];
  for (let i = options.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [options[i], options[j]] = [options[j], options[i]];
  }
  return { target, options };
}

export function isColourPickCorrect(round, colourId) {
  return !!round && !!round.target && round.target.id === colourId;
}

// A correct tap earns COLOUR_MATCH_COINS; a wrong tap earns nothing.
// Every tap is counted, so the stats line can show how a child is doing.
export function awardColourPick(state, correct) {
  ensureStats(state);
  state.stats.colourPlayed += 1;
  if (!correct) return 0;
  state.stats.colourCorrect += 1;
  state.coins += COLOUR_MATCH_COINS;
  return COLOUR_MATCH_COINS;
}

// Finishing all COLOUR_ROUNDS rounds pays a bonus and counts as a game won.
export function awardColourGameWin(state) {
  ensureStats(state);
  state.coins += COLOUR_GAME_BONUS_COINS;
  state.stats.gamesWon += 1;
  return COLOUR_GAME_BONUS_COINS;
}
