// ADHD My Way — Ionic app wiring.
// All data lives in localStorage on this device only. No accounts, no
// analytics, no network calls. See src/logic.js for the testable rules.
import { defineCustomElements } from '@ionic/core/loader';
import './style.css';
import {
  ACHIEVEMENTS,
  CATEGORIES,
  COLOUR_GAME_BONUS_COINS,
  COLOUR_ROUNDS,
  MEMORY_WIN_COINS,
  SHOP,
  STAR_TAP_COINS,
  STORAGE_KEY,
  WEEKLY_QUEST_GOAL,
  WEEKLY_REWARD_COINS,
  addTask,
  applyDailyReset,
  awardColourGameWin,
  awardColourPick,
  awardMemoryWin,
  buyOrEquip,
  categoryById,
  claimWeeklyReward,
  createColourRound,
  createDefaultState,
  createMemoryDeck,
  finishFocusSession,
  isColourPickCorrect,
  isMemoryMatch,
  migrateState,
  needsDailyReset,
  removeTask,
  tasksByCategory,
  tasksDoneCount,
  toggleTask,
  unlockedAchievements,
  weeklyRewardStatus,
  weeklySummary,
} from './logic.js';

defineCustomElements(window);

// ---------- state ----------
function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return createDefaultState();
    const parsed = JSON.parse(raw);
    if (!parsed || (parsed.version !== 1 && parsed.version !== 2 && parsed.version !== 3 && parsed.version !== 4 && parsed.version !== 5) || !Array.isArray(parsed.tasks)) {
      return createDefaultState();
    }
    // v1/v2/v3 saves keep working: newer fields (streak, categories,
    // colour stats, weekly record, memory wins) are filled in by
    // migrateState.
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
// The chibi (v5): a big head with anime eyes and blush, and a small body
// with an outfit, pants, shoes and an optional armor overlay. Head is
// centred at (100, 74) with radius 52; the body runs from y=130 to y=244.
function hairSvg(style, color) {
  switch (style) {
    case 'curly':
      return `<circle cx="58" cy="46" r="18" fill="${color}"/><circle cx="78" cy="30" r="20" fill="${color}"/><circle cx="100" cy="26" r="20" fill="${color}"/><circle cx="122" cy="30" r="20" fill="${color}"/><circle cx="142" cy="46" r="18" fill="${color}"/><circle cx="48" cy="72" r="14" fill="${color}"/><circle cx="152" cy="72" r="14" fill="${color}"/>`;
    case 'spiky':
      return `<path d="M46 92 L52 50 L66 68 L76 36 L92 60 L100 30 L108 60 L124 36 L134 68 L148 50 L154 92 Q142 52 100 50 Q58 52 46 92 Z" fill="${color}"/>`;
    case 'long':
      return `<path d="M46 92 Q42 22 100 20 Q158 22 154 92 L154 172 L138 172 L138 96 Q138 52 100 50 Q62 52 62 96 L62 172 L46 172 Z" fill="${color}"/>`;
    case 'ponytail':
      return `<path d="M46 90 Q42 22 100 20 Q158 22 154 90 Q142 50 100 48 Q58 50 46 90 Z" fill="${color}"/><ellipse cx="160" cy="142" rx="13" ry="36" fill="${color}"/><rect x="150" y="94" width="20" height="9" rx="4" fill="#f2c94c"/>`;
    case 'twin-tails':
      return `<path d="M46 90 Q42 22 100 20 Q158 22 154 90 Q142 50 100 48 Q58 50 46 90 Z" fill="${color}"/><ellipse cx="38" cy="142" rx="13" ry="38" fill="${color}"/><ellipse cx="162" cy="142" rx="13" ry="38" fill="${color}"/><rect x="28" y="94" width="20" height="9" rx="4" fill="#ff6b9d"/><rect x="152" y="94" width="20" height="9" rx="4" fill="#ff6b9d"/>`;
    case 'bob':
      return `<path d="M44 96 Q40 20 100 18 Q160 20 156 96 L156 122 L138 122 L138 94 Q138 50 100 48 Q62 50 62 94 L62 122 L44 122 Z" fill="${color}"/>`;
    case 'messy':
      return `<path d="M46 92 L50 54 L64 70 L72 38 L88 62 L100 32 L112 62 L128 38 L136 70 L150 54 L154 92 Q142 52 100 50 Q58 52 46 92 Z" fill="${color}"/><path d="M100 30 Q96 12 110 6" fill="none" stroke="${color}" stroke-width="4" stroke-linecap="round"/>`;
    default: // short
      return `<path d="M46 90 Q42 22 100 20 Q158 22 154 90 Q142 50 100 48 Q58 50 46 90 Z" fill="${color}"/>`;
  }
}

function hatSvg(hat) {
  switch (hat) {
    case 'cap':
      return `<path d="M50 48 Q52 14 100 12 Q148 14 150 48 L150 54 L50 54 Z" fill="#e63946"/><rect x="42" y="50" width="116" height="9" rx="4" fill="#c1121f"/>`;
    case 'beanie':
      return `<path d="M54 52 Q52 14 100 12 Q148 14 146 52 L146 58 L54 58 Z" fill="#4dabff"/><rect x="52" y="50" width="96" height="12" rx="6" fill="#2f6fb2"/><circle cx="100" cy="12" r="8" fill="#ffffff"/>`;
    case 'party':
      return `<path d="M78 40 L100 4 L122 40 Z" fill="#ff6b6b"/><circle cx="100" cy="4" r="5" fill="#f2c94c"/><circle cx="92" cy="28" r="3" fill="#ffffff"/><circle cx="108" cy="32" r="3" fill="#4dabff"/>`;
    case 'wizard':
      return `<path d="M62 42 L100 2 L138 42 Z" fill="#9775fa"/><rect x="52" y="38" width="96" height="10" rx="5" fill="#6a3fb5"/><circle cx="100" cy="24" r="5" fill="#f2c94c"/>`;
    case 'crown':
      return `<path d="M58 50 L58 20 L80 36 L100 16 L120 36 L142 20 L142 50 Z" fill="#f2c94c" stroke="#b8860b" stroke-width="2"/>`;
    default:
      return '';
  }
}

function accessorySvg(acc) {
  switch (acc) {
    case 'glasses':
      return `<circle cx="80" cy="78" r="15" fill="none" stroke="#222" stroke-width="4"/><circle cx="120" cy="78" r="15" fill="none" stroke="#222" stroke-width="4"/><line x1="95" y1="78" x2="105" y2="78" stroke="#222" stroke-width="4"/>`;
    case 'sunglasses':
      return `<circle cx="80" cy="78" r="15" fill="#222"/><circle cx="120" cy="78" r="15" fill="#222"/><line x1="95" y1="78" x2="105" y2="78" stroke="#222" stroke-width="4"/><circle cx="74" cy="72" r="4" fill="#ffffff"/><circle cx="114" cy="72" r="4" fill="#ffffff"/>`;
    case 'heart':
      return `<path d="M122 170 C112 162 108 154 114 150 C118 148 122 152 122 156 C122 152 126 148 130 150 C136 154 132 162 122 170 Z" fill="#ff6b6b" stroke="#c0392b" stroke-width="1"/>`;
    case 'star':
      return `<path d="M122 148 l4 9 10 1 -7 7 2 10 -9 -5 -9 5 2 -10 -7 -7 10 -1 Z" fill="#f2c94c" stroke="#b8860b" stroke-width="1"/>`;
    case 'headphones':
      return `<path d="M50 84 Q50 12 100 12 Q150 12 150 84" fill="none" stroke="#1e88e5" stroke-width="10"/><rect x="40" y="74" width="18" height="30" rx="8" fill="#1e88e5"/><rect x="142" y="74" width="18" height="30" rx="8" fill="#1e88e5"/>`;
    case 'bow':
      return `<path d="M146 44 L128 30 L128 58 Z" fill="#ff6b9d"/><path d="M146 44 L164 30 L164 58 Z" fill="#ff6b9d"/><circle cx="146" cy="44" r="6" fill="#e63946"/>`;
    default: // 'cape' is drawn behind the body, not here; 'none' draws nothing
      return '';
  }
}

// The cape flows behind the whole body, so it is drawn first.
function capeSvg() {
  return `<path d="M66 128 Q100 120 134 128 L150 250 L50 250 Z" fill="#e63946"/><circle cx="70" cy="132" r="5" fill="#f2c94c"/><circle cx="130" cy="132" r="5" fill="#f2c94c"/>`;
}

function outfitSvg(outfit) {
  switch (outfit) {
    case 'hero':
      return `<rect x="68" y="130" width="64" height="66" rx="18" fill="#1e88e5"/><path d="M100 148 l3.5 8 9 1 -6.5 6 1.5 9 -8 -4.5 -8 4.5 1.5 -9 -6.5 -6 9 -1 Z" fill="#f2c94c"/><rect x="68" y="186" width="64" height="8" fill="#c1121f"/>`;
    case 'star-dress':
      return `<path d="M70 132 Q100 124 130 132 L142 210 Q100 218 58 210 Z" fill="#ff8fab"/><circle cx="84" cy="160" r="3" fill="#ffffff"/><circle cx="116" cy="176" r="3" fill="#ffffff"/><circle cx="96" cy="192" r="2.5" fill="#ffffff"/><rect x="66" y="170" width="68" height="6" fill="#e75480"/>`;
    case 'explorer':
      return `<rect x="68" y="130" width="64" height="66" rx="18" fill="#b08968"/><line x1="100" y1="134" x2="100" y2="196" stroke="#8d6e4a" stroke-width="3"/><rect x="76" y="160" width="16" height="14" rx="3" fill="#8d6e4a"/><rect x="108" y="160" width="16" height="14" rx="3" fill="#8d6e4a"/>`;
    case 'pajamas':
      return `<rect x="68" y="130" width="64" height="66" rx="18" fill="#9775fa"/><line x1="72" y1="146" x2="128" y2="146" stroke="#ffffff" stroke-width="4" opacity="0.6"/><line x1="72" y1="162" x2="128" y2="162" stroke="#ffffff" stroke-width="4" opacity="0.6"/><line x1="72" y1="178" x2="128" y2="178" stroke="#ffffff" stroke-width="4" opacity="0.6"/><line x1="72" y1="192" x2="128" y2="192" stroke="#ffffff" stroke-width="4" opacity="0.6"/>`;
    default: // casual — an everyday tee
      return `<rect x="68" y="130" width="64" height="66" rx="18" fill="#4dabff"/><path d="M88 130 Q100 140 112 130" fill="none" stroke="#2f6fb2" stroke-width="3"/>`;
  }
}

// Legs are skin first; the pants choice covers them (shorts leave the
// lower legs bare, the skirt flares over the top of them).
function pantsSvg(pants, skin) {
  const legs = `<rect x="78" y="196" width="18" height="34" rx="6" fill="${skin}"/><rect x="104" y="196" width="18" height="34" rx="6" fill="${skin}"/>`;
  switch (pants) {
    case 'shorts':
      return legs + `<rect x="78" y="196" width="18" height="18" rx="5" fill="#c9a227"/><rect x="104" y="196" width="18" height="18" rx="5" fill="#c9a227"/>`;
    case 'skirt':
      return legs + `<path d="M66 194 L134 194 L144 224 L56 224 Z" fill="#ff8fab"/><rect x="66" y="192" width="68" height="8" fill="#e75480"/>`;
    case 'leggings':
      return legs + `<rect x="78" y="196" width="18" height="34" rx="6" fill="#9775fa"/><rect x="104" y="196" width="18" height="34" rx="6" fill="#9775fa"/><circle cx="87" cy="214" r="2.5" fill="#ffffff"/><circle cx="113" cy="222" r="2.5" fill="#ffffff"/>`;
    default: // jeans
      return legs + `<rect x="78" y="196" width="18" height="34" rx="6" fill="#4a6fa5"/><rect x="104" y="196" width="18" height="34" rx="6" fill="#4a6fa5"/><line x1="82" y1="200" x2="82" y2="226" stroke="#2f4a6e" stroke-width="2"/><line x1="108" y1="200" x2="108" y2="226" stroke="#2f4a6e" stroke-width="2"/>`;
  }
}

function shoesSvg(shoes) {
  switch (shoes) {
    case 'boots':
      return `<rect x="76" y="216" width="22" height="26" rx="6" fill="#8d5524"/><rect x="102" y="216" width="22" height="26" rx="6" fill="#8d5524"/><rect x="76" y="216" width="22" height="6" fill="#5b3a1e"/><rect x="102" y="216" width="22" height="6" fill="#5b3a1e"/>`;
    case 'sandals':
      return `<rect x="74" y="232" width="26" height="8" rx="4" fill="#d2a679"/><rect x="100" y="232" width="26" height="8" rx="4" fill="#d2a679"/><line x1="80" y1="232" x2="94" y2="226" stroke="#8d5524" stroke-width="2"/><line x1="106" y1="232" x2="120" y2="226" stroke="#8d5524" stroke-width="2"/>`;
    case 'hero-boots':
      return `<rect x="76" y="216" width="22" height="26" rx="6" fill="#1e88e5"/><rect x="102" y="216" width="22" height="26" rx="6" fill="#1e88e5"/><rect x="76" y="216" width="22" height="6" fill="#f2c94c"/><rect x="102" y="216" width="22" height="6" fill="#f2c94c"/>`;
    default: // sneakers
      return `<rect x="74" y="228" width="26" height="14" rx="7" fill="#ffffff" stroke="#dfe6e9" stroke-width="1"/><rect x="100" y="228" width="26" height="14" rx="7" fill="#ffffff" stroke="#dfe6e9" stroke-width="1"/><rect x="74" y="232" width="26" height="4" fill="#e63946"/><rect x="100" y="232" width="26" height="4" fill="#e63946"/>`;
  }
}

// Armor is a shiny overlay: shoulder pads plus a chest plate, worn over
// the outfit. 'none' draws nothing.
function armorSvg(armor) {
  const colors = {
    knight: { main: '#b8c4cc', edge: '#7f8c8d', plate: '#cfd8dc' },
    star: { main: '#f2c94c', edge: '#b8860b', plate: '#ffe066' },
    dragon: { main: '#2e7d32', edge: '#1b5e20', plate: '#43a047' },
  }[armor];
  if (!colors) return '';
  const emblem =
    armor === 'star'
      ? `<path d="M100 152 l3 7 8 1 -6 5 1.5 8 -6.5 -4 -6.5 4 1.5 -8 -6 -5 8 -1 Z" fill="#b8860b"/>`
      : armor === 'dragon'
        ? `<path d="M88 168 Q94 158 100 168 Q106 158 112 168" fill="none" stroke="#1b5e20" stroke-width="2.5"/>`
        : `<circle cx="88" cy="154" r="2.5" fill="#7f8c8d"/><circle cx="112" cy="154" r="2.5" fill="#7f8c8d"/><circle cx="88" cy="172" r="2.5" fill="#7f8c8d"/><circle cx="112" cy="172" r="2.5" fill="#7f8c8d"/>`;
  return `<circle cx="68" cy="136" r="13" fill="${colors.main}" stroke="${colors.edge}" stroke-width="2"/><circle cx="132" cy="136" r="13" fill="${colors.main}" stroke="${colors.edge}" stroke-width="2"/><rect x="80" y="142" width="40" height="40" rx="10" fill="${colors.plate}" stroke="${colors.edge}" stroke-width="2"/>${emblem}`;
}

// Big anime eyes with a sparkle, plus blush — the chibi face.
function faceSvg() {
  return `
    <ellipse cx="80" cy="78" rx="10" ry="14" fill="#ffffff"/>
    <ellipse cx="120" cy="78" rx="10" ry="14" fill="#ffffff"/>
    <ellipse cx="80" cy="80" rx="6.5" ry="10" fill="#2b2118"/>
    <ellipse cx="120" cy="80" rx="6.5" ry="10" fill="#2b2118"/>
    <circle cx="77" cy="72" r="3.5" fill="#ffffff"/>
    <circle cx="117" cy="72" r="3.5" fill="#ffffff"/>
    <circle cx="83" cy="86" r="1.5" fill="#ffffff"/>
    <circle cx="123" cy="86" r="1.5" fill="#ffffff"/>
    <ellipse cx="62" cy="96" rx="9" ry="5" fill="#ff9aa2" opacity="0.55"/>
    <ellipse cx="138" cy="96" rx="9" ry="5" fill="#ff9aa2" opacity="0.55"/>
    <path d="M92 104 Q100 110 108 104" fill="none" stroke="#b3543f" stroke-width="3.5" stroke-linecap="round"/>`;
}

function avatarSvg() {
  const a = state.avatar;
  return `
  <svg viewBox="0 0 200 260" role="img" aria-label="Your avatar" class="avatar-svg">
    ${a.accessory === 'cape' ? capeSvg() : ''}
    ${pantsSvg(a.pants, a.skin)}
    ${shoesSvg(a.shoes)}
    ${outfitSvg(a.outfit)}
    <ellipse cx="60" cy="162" rx="9" ry="24" fill="${a.skin}" transform="rotate(8 60 162)"/>
    <ellipse cx="140" cy="162" rx="9" ry="24" fill="${a.skin}" transform="rotate(-8 140 162)"/>
    ${armorSvg(a.armor)}
    <rect x="93" y="118" width="14" height="14" fill="${a.skin}"/>
    <circle cx="48" cy="74" r="8" fill="${a.skin}"/>
    <circle cx="152" cy="74" r="8" fill="${a.skin}"/>
    <circle cx="100" cy="74" r="52" fill="${a.skin}"/>
    ${faceSvg()}
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
    ['outfit', 'Outfits'],
    ['pants', 'Pants'],
    ['shoes', 'Shoes'],
    ['armor', 'Armor'],
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
      const before = unlockedAchievements(state);
      const result = buyOrEquip(state, btn.dataset.item);
      if (!result.ok) {
        await toast(`You need ${result.price} coins for that — finish a quest!`, 'warning');
        return;
      }
      save();
      renderCoins();
      renderAvatar();
      renderShop();
      renderStars();
      announceNewBadges(before);
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
      const before = unlockedAchievements(state);
      const result = toggleTask(state, task.id);
      save();
      renderCoins();
      renderTasks();
      renderProgress();
      renderStars();
      announceNewBadges(before);
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
    `Quests finished: ${state.stats.tasksDone} · Games won: ${state.stats.gamesWon} · Stars tapped: ${state.stats.starsTapped} · Focus sessions: ${state.stats.timersFinished} · Colour Match right: ${state.stats.colourCorrect || 0} of ${state.stats.colourPlayed || 0}`;
}

// ---------- v4: weekly rewards, achievements, summary ----------
// Snapshot the unlocked badges before an action, then celebrate any
// badge the action just earned.
function announceNewBadges(before) {
  const now = unlockedAchievements(state);
  for (const id of now) {
    if (before.includes(id)) continue;
    const badge = ACHIEVEMENTS.find((a) => a.id === id);
    if (badge) toast(`New badge! ${badge.icon} ${badge.title} — ${badge.text}`, 'success');
  }
}

// The "My Stars" tab: this week's reward progress, the badge wall, and
// a summary of everything the child has done so far.
function renderStars() {
  const status = weeklyRewardStatus(state);
  const summary = weeklySummary(state);
  $('#weekly-line').textContent = status.claimed
    ? `You claimed your ${WEEKLY_REWARD_COINS}-coin star reward this week! Come back next week for a new one.`
    : status.claimable
      ? `You did it! ${status.quests} of ${WEEKLY_QUEST_GOAL} quests this week — tap below to claim your ${WEEKLY_REWARD_COINS}-coin star reward!`
      : `Finish ${WEEKLY_QUEST_GOAL} quests this week to earn a ${WEEKLY_REWARD_COINS}-coin star reward!`;
  $('#weekly-progress-label').textContent = `${status.quests} of ${WEEKLY_QUEST_GOAL} quests this week`;
  $('#weekly-progress-bar').value = Math.min(1, status.quests / WEEKLY_QUEST_GOAL);
  const claimBtn = $('#weekly-claim-btn');
  claimBtn.disabled = !status.claimable;
  claimBtn.textContent = status.claimed
    ? 'Reward claimed! ⭐'
    : `Claim my ${WEEKLY_REWARD_COINS} coins! ⭐`;
  const unlocked = unlockedAchievements(state);
  $('#achievements-grid').innerHTML = ACHIEVEMENTS.map((badge) => {
    const got = unlocked.includes(badge.id);
    return `<div class="badge ${got ? 'badge-unlocked' : 'badge-locked'}" aria-label="${got ? 'Earned: ' : 'Not yet earned: '}${badge.title}">
      <span class="badge-icon">${got ? badge.icon : '🔒'}</span>
      <span class="badge-title">${badge.title}</span>
      <span class="badge-text">${badge.text}</span>
    </div>`;
  }).join('');
  $('#achievements-line').textContent = `${summary.badgesUnlocked} of ${summary.badgesTotal} badges earned — keep going!`;
  $('#summary-line').innerHTML =
    `Quests finished: <b>${summary.tasksDone}</b> · Games won: <b>${summary.gamesWon}</b> (Memory Match: <b>${summary.memoryWins}</b>)<br>` +
    `Stars tapped: <b>${summary.starsTapped}</b> · Focus sessions: <b>${summary.timersFinished}</b><br>` +
    `Colour Match right: <b>${summary.colourCorrect}</b> of <b>${summary.colourPlayed}</b> · Best streak: <b>${summary.bestStreak} days</b><br>` +
    `This week: <b>${summary.weeklyQuests}</b> quests · <b>${summary.weeklyGames}</b> games won · <b>${summary.weeklyFocus}</b> focus sessions`;
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
        const before = unlockedAchievements(state);
        awardMemoryWin(state);
        save();
        renderCoins();
        renderProgress();
        renderStars();
        announceNewBadges(before);
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
  const before = unlockedAchievements(state);
  state.stats.starsTapped += starGame.taps;
  const earned = starGame.taps * STAR_TAP_COINS;
  save();
  renderCoins();
  renderProgress();
  renderStars();
  announceNewBadges(before);
  toast(`You tapped ${starGame.taps} stars and earned ${earned} coins!`, 'success');
}

// ---------- colour match ----------
// v3: read the colour word, tap the button in that colour. 10 rounds;
// +2 coins per right tap, +10 bonus for finishing the game.
const colourGame = { playing: false, round: 0, correct: 0, current: null };

function renderColour() {
  const target = $('#colour-target');
  const options = $('#colour-options');
  const status = $('#colour-status');
  if (!colourGame.playing) {
    target.textContent = 'Press Start and match the colour!';
    options.innerHTML = '';
    status.textContent = `${COLOUR_ROUNDS} rounds · +2 coins for every right tap · finish all ${COLOUR_ROUNDS} for a +${COLOUR_GAME_BONUS_COINS} bonus!`;
    $('#colour-start').textContent = 'Start game';
    return;
  }
  target.textContent = `Tap the ${colourGame.current.target.name.toUpperCase()} button!`;
  options.innerHTML = '';
  for (const colour of colourGame.current.options) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'colour-btn';
    btn.style.background = colour.color;
    btn.setAttribute('aria-label', `${colour.name} button`);
    btn.addEventListener('click', () => pickColour(colour.id));
    options.append(btn);
  }
  status.textContent = `Round ${colourGame.round} of ${COLOUR_ROUNDS} · ${colourGame.correct} right so far`;
  $('#colour-start').textContent = 'Playing…';
}

function pickColour(id) {
  if (!colourGame.playing || !colourGame.current) return;
  const right = isColourPickCorrect(colourGame.current, id);
  awardColourPick(state, right);
  if (right) colourGame.correct += 1;
  save();
  renderCoins();
  if (colourGame.round >= COLOUR_ROUNDS) {
    colourGame.playing = false;
    const before = unlockedAchievements(state);
    const bonus = awardColourGameWin(state);
    save();
    renderCoins();
    renderProgress();
    renderStars();
    announceNewBadges(before);
    renderColour();
    toast(`Colour Match done! ${colourGame.correct} of ${COLOUR_ROUNDS} right — +${bonus} bonus coins!`, 'success');
    return;
  }
  colourGame.round += 1;
  colourGame.current = createColourRound();
  renderColour();
}

// ---------- wire up ----------
function init() {
  renderCoins();
  renderCategoryFilters();
  renderTasks();
  renderAvatar();
  renderShop();
  renderStars();

  // Weekly star reward: claim the coins once the week's quest goal is met.
  $('#weekly-claim-btn').addEventListener('click', async () => {
    const result = claimWeeklyReward(state);
    if (!result.ok) {
      await toast(
        result.reason === 'already claimed this week'
          ? 'You already claimed this week\'s reward — come back next week!'
          : `Finish ${WEEKLY_QUEST_GOAL} quests this week to claim the reward!`,
        'warning',
      );
      return;
    }
    save();
    renderCoins();
    renderStars();
    await toast(`Star reward claimed! +${result.coins} coins! ⭐`, 'success');
  });

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
          const before = unlockedAchievements(state);
          const result = finishFocusSession(state, timer.taskId);
          timer.taskId = null;
          save();
          renderCoins();
          renderTasks();
          renderProgress();
          renderStars();
          announceNewBadges(before);
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

  // Colour Match.
  $('#colour-start').addEventListener('click', () => {
    if (colourGame.playing) return;
    colourGame.playing = true;
    colourGame.round = 1;
    colourGame.correct = 0;
    colourGame.current = createColourRound();
    renderColour();
  });
  renderColour();

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
    renderStars();
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
