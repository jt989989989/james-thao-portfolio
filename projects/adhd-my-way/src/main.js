// ADHD My Way — Ionic app wiring.
// All data lives in localStorage on this device only. No accounts, no
// analytics, no network calls. See src/logic.js for the testable rules.
import { defineCustomElements } from '@ionic/core/loader';
import './style.css';
import {
  CATEGORIES,
  MEMORY_WIN_COINS,
  SHOP,
  STAR_TAP_COINS,
  STORAGE_KEY,
  addTask,
  applyDailyReset,
  awardMemoryWin,
  buyOrEquip,
  categoryById,
  createDefaultState,
  createMemoryDeck,
  finishFocusSession,
  isMemoryMatch,
  migrateState,
  needsDailyReset,
  removeTask,
  tasksByCategory,
  tasksDoneCount,
  toggleTask,
} from './logic.js';

defineCustomElements(window);

// ---------- state ----------
function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return createDefaultState();
    const parsed = JSON.parse(raw);
    if (!parsed || (parsed.version !== 1 && parsed.version !== 2) || !Array.isArray(parsed.tasks)) {
      return createDefaultState();
    }
    // v1 saves keep working: v2 fields (streak, categories) are filled in.
    const state = migrateState(parsed);
    if (needsDailyReset(state)) applyDailyReset(state);
    return state;
  } catch {
    return createDefaultState();
  }
}

let state = loadState();

function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Storage full or unavailable (private mode): the app still works
    // for this session, it just won't remember between visits.
  }
}

// ---------- helpers ----------
const $ = (sel) => document.querySelector(sel);

async function toast(message, color = 'success') {
  const el = document.createElement('ion-toast');
  el.message = message;
  el.duration = 2500;
  el.position = 'bottom';
  el.color = color;
  document.body.appendChild(el);
  await el.present();
  el.addEventListener('ionToastDidDismiss', () => el.remove(), { once: true });
}

function renderCoins() {
  document.querySelectorAll('.coin-count').forEach((el) => {
    el.textContent = String(state.coins);
  });
}

// ---------- avatar ----------
function hairSvg(style, color) {
  switch (style) {
    case 'curly':
      return `<circle cx="62" cy="72" r="20" fill="${color}"/><circle cx="100" cy="58" r="22" fill="${color}"/><circle cx="138" cy="72" r="20" fill="${color}"/>`;
    case 'spiky':
      return `<path d="M45 95 L58 52 L74 78 L90 48 L106 76 L122 50 L138 78 L152 58 L158 100 Q150 62 100 58 Q52 62 45 95 Z" fill="${color}"/>`;
    case 'long':
      return `<path d="M42 170 L42 105 Q42 52 100 52 Q158 52 158 105 L158 170 L142 170 L142 108 Q142 72 100 72 Q58 72 58 108 L58 170 Z" fill="${color}"/>`;
    default: // short
      return `<path d="M44 108 Q40 52 100 50 Q160 52 156 108 Q146 74 100 72 Q54 74 44 108 Z" fill="${color}"/>`;
  }
}

function hatSvg(hat) {
  switch (hat) {
    case 'cap':
      return `<path d="M48 78 Q50 42 100 40 Q150 42 152 78 L152 84 L48 84 Z" fill="#e63946"/><rect x="40" y="80" width="120" height="10" rx="5" fill="#c1121f"/>`;
    case 'beanie':
      return `<path d="M52 82 Q50 40 100 38 Q150 40 148 82 L148 88 L52 88 Z" fill="#4dabff"/><rect x="50" y="80" width="100" height="12" rx="6" fill="#2f6fb2"/><circle cx="100" cy="38" r="9" fill="#ffffff"/>`;
    case 'crown':
      return `<path d="M58 78 L58 44 L80 62 L100 38 L120 62 L142 44 L142 78 Z" fill="#f2c94c" stroke="#b8860b" stroke-width="2"/>`;
    default:
      return '';
  }
}

function accessorySvg(acc) {
  switch (acc) {
    case 'glasses':
      return `<circle cx="78" cy="112" r="16" fill="none" stroke="#222" stroke-width="4"/><circle cx="122" cy="112" r="16" fill="none" stroke="#222" stroke-width="4"/><line x1="94" y1="112" x2="106" y2="112" stroke="#222" stroke-width="4"/>`;
    case 'star':
      return `<path d="M158 158 l4 9 10 1 -7 7 2 10 -9 -5 -9 5 2 -10 -7 -7 10 -1 Z" fill="#f2c94c" stroke="#b8860b" stroke-width="1"/>`;
    case 'headphones':
      return `<path d="M52 118 Q52 52 100 52 Q148 52 148 118" fill="none" stroke="#1e88e5" stroke-width="10"/><rect x="42" y="106" width="18" height="30" rx="8" fill="#1e88e5"/><rect x="140" y="106" width="18" height="30" rx="8" fill="#1e88e5"/>`;
    default:
      return '';
  }
}

function avatarSvg() {
  const a = state.avatar;
  return `
  <svg viewBox="0 0 200 200" role="img" aria-label="Your avatar" class="avatar-svg">
    <circle cx="100" cy="118" r="58" fill="${a.skin}"/>
    <circle cx="79" cy="112" r="6" fill="#222"/>
    <circle cx="121" cy="112" r="6" fill="#222"/>
    <path d="M84 140 Q100 152 116 140" fill="none" stroke="#b3543f" stroke-width="4" stroke-linecap="round"/>
    ${hairSvg(a.hairStyle, a.hairColor)}
    ${hatSvg(a.hat)}
    ${accessorySvg(a.accessory)}
  </svg>`;
}

function renderAvatar() {
  $('#avatar-preview').innerHTML = avatarSvg();
}

function renderShop() {
  const slots = [
    ['skin', 'Skin colour'],
    ['hairStyle', 'Hair style'],
    ['hairColor', 'Hair colour'],
    ['hat', 'Hats'],
    ['accessory', 'Accessories'],
  ];
  $('#shop').innerHTML = slots
    .map(([slot, label]) => {
      const items = SHOP.filter((i) => i.slot === slot);
      const buttons = items
        .map((item) => {
          const owned = state.owned.includes(item.id);
          const equipped = state.avatar[slot] === item.value;
          const swatch =
            slot === 'skin' || slot === 'hairColor'
              ? `<span class="swatch" style="background:${item.value}"></span>`
              : '';
          const tag = equipped ? 'Wearing it!' : owned ? `Wear it` : `${item.price} coins`;
          return `<ion-button class="shop-item" data-item="${item.id}" fill="${equipped ? 'solid' : 'outline'}" color="${equipped ? 'success' : 'primary'}">${swatch}${item.name}<br><small>${tag}</small></ion-button>`;
        })
        .join('');
      return `<h3>${label}</h3><div class="shop-row">${buttons}</div>`;
    })
    .join('');

  document.querySelectorAll('.shop-item').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const result = buyOrEquip(state, btn.dataset.item);
      if (!result.ok) {
        await toast(`You need ${result.price} coins for that — finish a quest!`, 'warning');
        return;
      }
      save();
      renderCoins();
      renderAvatar();
      renderShop();
      if (result.action === 'bought') {
        await toast(`You bought it! Looking great!`, 'success');
      }
    });
  });
}

// ---------- quests ----------
let activeCategory = 'all'; // filter only — not saved, resets to "all" each visit

function renderCategoryFilters() {
  const wrap = $('#category-filters');
  const chips = [{ id: 'all', name: 'All', color: '#636e72' }, ...CATEGORIES];
  wrap.innerHTML = '';
  for (const cat of chips) {
    const chip = document.createElement('ion-chip');
    chip.textContent = cat.name;
    chip.color = activeCategory === cat.id ? 'primary' : 'medium';
    chip.setAttribute('outline', activeCategory === cat.id ? 'false' : 'true');
    chip.addEventListener('click', () => {
      activeCategory = cat.id;
      renderCategoryFilters();
      renderTasks();
    });
    wrap.append(chip);
  }
}

function renderTasks() {
  const list = $('#task-list');
  list.innerHTML = '';
  const visible = tasksByCategory(state, activeCategory);
  if (visible.length === 0) {
    const empty = document.createElement('ion-item');
    empty.innerHTML = '<ion-label><p>No quests in this group yet — add one below!</p></ion-label>';
    list.append(empty);
  }
  for (const task of visible) {
    const item = document.createElement('ion-item');
    const checkbox = document.createElement('ion-checkbox');
    checkbox.setAttribute('slot', 'start');
    checkbox.checked = task.done;
    checkbox.setAttribute('aria-label', task.title);
    checkbox.addEventListener('ionChange', async () => {
      const result = toggleTask(state, task.id);
      save();
      renderCoins();
      renderTasks();
      renderProgress();
      if (result.done) {
        const streak = state.streak.count;
        await toast(`Nice work! +${task.coins} coins!${streak > 1 ? ` 🔥 ${streak}-day streak!` : ''}`, 'success');
      }
    });
    const label = document.createElement('ion-label');
    const cat = categoryById(task.category);
    label.innerHTML = `<h2>${escapeHtml(task.title)}</h2><p>+${task.coins} coins · ${cat ? cat.name : 'Home'}</p>`;
    if (task.done) label.classList.add('task-done');
    item.append(checkbox, label);
    // Focus on this quest: the timer counts down for this one quest.
    if (!task.done) {
      const focus = document.createElement('ion-button');
      focus.setAttribute('slot', 'end');
      focus.setAttribute('fill', 'outline');
      focus.setAttribute('size', 'small');
      focus.setAttribute('color', timer.taskId === task.id ? 'success' : 'tertiary');
      focus.textContent = timer.taskId === task.id ? 'Focusing ✓' : 'Focus';
      focus.setAttribute('aria-label', `Focus on ${task.title}`);
      focus.addEventListener('click', () => {
        timer.taskId = task.id;
        renderTasks();
        renderTimer();
        document.querySelector('#timer-card')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
      item.append(focus);
    }
    if (task.custom) {
      const del = document.createElement('ion-button');
      del.setAttribute('slot', 'end');
      del.setAttribute('fill', 'clear');
      del.setAttribute('color', 'medium');
      del.textContent = '✕';
      del.setAttribute('aria-label', `Remove ${task.title}`);
      del.addEventListener('click', () => {
        if (timer.taskId === task.id) timer.taskId = null;
        removeTask(state, task.id);
        save();
        renderTasks();
        renderProgress();
        renderTimer();
      });
      item.append(del);
    }
    list.append(item);
  }
  renderProgress();
}

function renderProgress() {
  const done = tasksDoneCount(state);
  const total = state.tasks.length;
  $('#progress-label').textContent = `${done} of ${total} quests done today`;
  $('#progress-bar').value = total ? done / total : 0;
  const streak = state.streak || { count: 0, best: 0 };
  $('#streak-line').textContent =
    streak.count > 0
      ? `🔥 ${streak.count}-day streak!${streak.best > streak.count ? ` Best: ${streak.best} days.` : ' Keep it going tomorrow!'}`
      : 'Finish a quest today to start your streak! 🔥';
  $('#stats-line').textContent =
    `Quests finished: ${state.stats.tasksDone} · Games won: ${state.stats.gamesWon} · Stars tapped: ${state.stats.starsTapped} · Focus sessions: ${state.stats.timersFinished}`;
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[c]);
}

// ---------- focus timer ----------
// v2: the timer can focus on one chosen quest. Finishing the session
// ticks that quest off (its coins included) plus the +5 focus bonus.
const timer = { total: 600, left: 600, running: false, handle: null, taskId: null };

function focusedTask() {
  return timer.taskId ? state.tasks.find((t) => t.id === timer.taskId) || null : null;
}

function renderTimer() {
  const mins = Math.floor(timer.left / 60);
  const secs = String(timer.left % 60).padStart(2, '0');
  $('#timer-label').textContent = `${mins}:${secs}`;
  $('#timer-bar').value = timer.total ? 1 - timer.left / timer.total : 0;
  $('#timer-toggle').textContent = timer.running ? 'Pause' : 'Start';
  const task = focusedTask();
  $('#timer-focus-line').textContent = task
    ? `Focusing on: ${task.title} — finish the timer and this quest is done!`
    : 'No quest picked — tap Focus on a quest, or just focus on anything!';
}

function stopTimer() {
  if (timer.handle) clearInterval(timer.handle);
  timer.handle = null;
  timer.running = false;
}

// ---------- memory match ----------
const memory = { deck: [], flipped: [], matched: new Set(), lock: false, moves: 0 };

function renderMemory() {
  const grid = $('#memory-grid');
  grid.innerHTML = '';
  memory.deck.forEach((card, index) => {
    const el = document.createElement('button');
    el.className = 'memory-card';
    el.type = 'button';
    el.setAttribute('aria-label', `Memory card ${index + 1}`);
    const faceUp = memory.flipped.includes(index) || memory.matched.has(index);
    if (faceUp) {
      el.classList.add('face-up');
      el.innerHTML = `<span class="shape shape-${card.shape}" style="background:${card.color}"></span>`;
    } else {
      el.textContent = '?';
    }
    el.addEventListener('click', () => flipMemory(index));
    grid.append(el);
  });
  $('#memory-status').textContent =
    memory.matched.size === memory.deck.length && memory.deck.length > 0
      ? `You did it in ${memory.moves} tries! +${MEMORY_WIN_COINS} coins!`
      : `Pairs found: ${memory.matched.size / 2} of ${memory.deck.length / 2}`;
}

function flipMemory(index) {
  if (memory.lock || memory.flipped.includes(index) || memory.matched.has(index)) return;
  memory.flipped.push(index);
  if (memory.flipped.length === 2) {
    memory.moves += 1;
    const [a, b] = memory.flipped;
    if (isMemoryMatch(memory.deck[a], memory.deck[b])) {
      memory.matched.add(a);
      memory.matched.add(b);
      memory.flipped = [];
      renderMemory();
      if (memory.matched.size === memory.deck.length) {
        awardMemoryWin(state);
        save();
        renderCoins();
        renderProgress();
        toast(`Memory champion! +${MEMORY_WIN_COINS} coins!`, 'success');
      }
    } else {
      memory.lock = true;
      renderMemory();
      setTimeout(() => {
        memory.flipped = [];
        memory.lock = false;
        renderMemory();
      }, 900);
    }
  }
  renderMemory();
}

// ---------- tap the star ----------
const starGame = { running: false, taps: 0, left: 30, moveHandle: null, tickHandle: null };

function placeStar() {
  const area = $('#star-area');
  const star = $('#star-target');
  const maxX = area.clientWidth - 72;
  const maxY = area.clientHeight - 72;
  star.style.left = `${Math.max(0, Math.floor(Math.random() * maxX))}px`;
  star.style.top = `${Math.max(0, Math.floor(Math.random() * maxY))}px`;
}

function endStarGame() {
  starGame.running = false;
  clearInterval(starGame.moveHandle);
  clearInterval(starGame.tickHandle);
  $('#star-target').style.display = 'none';
  $('#star-start').textContent = 'Play again';
  // Coins were already added live (+2 per tap); here we only record the
  // stats and report the total — do NOT award them a second time.
  state.stats.starsTapped += starGame.taps;
  const earned = starGame.taps * STAR_TAP_COINS;
  save();
  renderCoins();
  renderProgress();
  toast(`You tapped ${starGame.taps} stars and earned ${earned} coins!`, 'success');
}

// ---------- wire up ----------
function init() {
  renderCoins();
  renderCategoryFilters();
  renderTasks();
  renderAvatar();
  renderShop();

  // Add a custom quest, in the chosen category.
  const categorySelect = $('#new-task-category');
  for (const cat of CATEGORIES) {
    const opt = document.createElement('ion-select-option');
    opt.value = cat.id;
    opt.textContent = cat.name;
    categorySelect.append(opt);
  }
  categorySelect.value = 'home';
  $('#add-task-btn').addEventListener('click', async () => {
    const input = $('#new-task-input');
    const result = addTask(state, input.value, categorySelect.value);
    if (!result.ok) {
      await toast('Type a quest first!', 'warning');
      return;
    }
    input.value = '';
    save();
    renderTasks();
  });
  $('#new-task-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') $('#add-task-btn').click();
  });

  // Focus timer.
  document.querySelectorAll('.timer-length').forEach((btn) => {
    btn.addEventListener('click', () => {
      stopTimer();
      timer.total = Number(btn.dataset.minutes) * 60;
      timer.left = timer.total;
      renderTimer();
    });
  });
  $('#timer-toggle').addEventListener('click', () => {
    if (timer.running) {
      stopTimer();
    } else {
      if (timer.left <= 0) timer.left = timer.total;
      timer.running = true;
      timer.handle = setInterval(() => {
        timer.left -= 1;
        if (timer.left <= 0) {
          stopTimer();
          timer.left = 0;
          const result = finishFocusSession(state, timer.taskId);
          timer.taskId = null;
          save();
          renderCoins();
          renderTasks();
          renderProgress();
          renderTimer();
          toast(
            result.taskDone
              ? `Focus time done! "${result.taskTitle}" is finished — +${result.coins} coins!`
              : `Focus time done! +${result.coins} coins!`,
            'success',
          );
        }
        renderTimer();
      }, 1000);
    }
    renderTimer();
  });
  $('#timer-reset').addEventListener('click', () => {
    stopTimer();
    timer.left = timer.total;
    renderTimer();
  });
  renderTimer();

  // Memory Match.
  const newMemoryGame = () => {
    memory.deck = createMemoryDeck();
    memory.flipped = [];
    memory.matched = new Set();
    memory.lock = false;
    memory.moves = 0;
    renderMemory();
  };
  newMemoryGame();
  $('#memory-again').addEventListener('click', newMemoryGame);

  // Tap the Star.
  $('#star-start').addEventListener('click', () => {
    if (starGame.running) return;
    starGame.running = true;
    starGame.taps = 0;
    starGame.left = 30;
    $('#star-score').textContent = 'Stars tapped: 0 · 30s left';
    $('#star-target').style.display = 'block';
    $('#star-start').textContent = 'Playing…';
    placeStar();
    starGame.moveHandle = setInterval(placeStar, 750);
    starGame.tickHandle = setInterval(() => {
      starGame.left -= 1;
      $('#star-score').textContent = `Stars tapped: ${starGame.taps} · ${starGame.left}s left`;
      if (starGame.left <= 0) endStarGame();
    }, 1000);
  });
  $('#star-target').addEventListener('click', () => {
    if (!starGame.running) return;
    starGame.taps += 1;
    state.coins += STAR_TAP_COINS; // instant feedback: +2 coins per tap, live on the chip
    save();
    renderCoins();
    $('#star-score').textContent = `Stars tapped: ${starGame.taps} · ${starGame.left}s left`;
    placeStar();
  });

  // Reset everything (two taps to confirm, so little fingers can't do it by accident).
  let resetArmed = false;
  $('#reset-btn').addEventListener('click', async () => {
    if (!resetArmed) {
      resetArmed = true;
      $('#reset-btn').textContent = 'Tap again to confirm reset';
      setTimeout(() => {
        resetArmed = false;
        $('#reset-btn').textContent = 'Reset everything';
      }, 4000);
      return;
    }
    state = createDefaultState();
    save();
    renderCoins();
    renderTasks();
    renderAvatar();
    renderShop();
    $('#reset-btn').textContent = 'Reset everything';
    resetArmed = false;
    await toast('All fresh! Have fun!', 'success');
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
