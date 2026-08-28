const SAMPLE = {
  currency: "EUR",
  prize_pool: 10000,
  entrants: 100,
  entry_fee: 100,
  payouts: [
    { from: 1, to: 1, amount: 2500 },
    { from: 2, to: 2, amount: 1500 },
    { from: 3, to: 3, amount: 1000 },
    { from: 4, to: 5, amount: 750 },
    { from: 6, to: 10, amount: 400 },
    { from: 11, to: 20, amount: 175 },
  ],
};

const STYLE_LABEL = {
  balanced: "Engage field",
  top_heavy: "Hero 1st",
  flat: "Wide board",
};

const STYLE_OPTIONS = {
  balanced: {
    title: "Engage the field",
    subtitle: "Podium + midfield · ~15% to 1st",
    curve: "M2 38 C18 38 28 18 52 14 S88 24 98 34",
    fill: "M2 38 C18 38 28 18 52 14 S88 24 98 34 L98 46 L2 46 Z",
    p1: 0.15,
    alpha: 0.65,
  },
  top_heavy: {
    title: "Hero 1st prize",
    subtitle: "Weekend promo · ~28% to 1st",
    curve: "M2 10 C22 10 34 22 58 30 S92 38 98 42",
    fill: "M2 10 C22 10 34 22 58 30 S92 38 98 42 L98 46 L2 46 Z",
    p1: 0.28,
    alpha: 1.05,
  },
  flat: {
    title: "Wide board",
    subtitle: "Long leaderboard · ~8% to 1st",
    curve: "M2 28 C28 26 48 24 72 22 S94 20 98 18",
    fill: "M2 28 C28 26 48 24 72 22 S94 20 98 18 L98 46 L2 46 Z",
    p1: 0.08,
    alpha: 0.35,
  },
};

const RECIPES = {
  slot: {
    flash: {
      title: "Flash race",
      why: "Lobby promo · €5k · 12 places",
      values: { currency: "EUR", prize_pool: 5000, winners_mode: "count", winners_value: 12, style: "balanced", min_mode: "fixed", min_value: 1, max_buckets: 10 },
    },
    daily: {
      title: "Daily slot",
      why: "Standard daily board · €50k · 50 places",
      values: { currency: "EUR", prize_pool: 50000, winners_mode: "count", winners_value: 50, style: "balanced", min_mode: "fixed", min_value: 1, max_buckets: 12 },
    },
    weekly: {
      title: "Weekly board",
      why: "Long board · €250k · wide field",
      values: { currency: "EUR", prize_pool: 250000, winners_mode: "count", winners_value: 100, style: "flat", min_mode: "fixed", min_value: 1, max_buckets: 12 },
    },
    jackpot: {
      title: "Jackpot weekend",
      why: "Hero 1st prize · €100k marketing",
      values: { currency: "EUR", prize_pool: 100000, winners_mode: "count", winners_value: 30, style: "top_heavy", min_mode: "fixed", min_value: 2, max_buckets: 12 },
    },
    micro: {
      title: "Micro race",
      why: "Tiny guarantee, tight widget",
      values: { currency: "EUR", prize_pool: 1000, winners_mode: "count", winners_value: 8, style: "balanced", min_mode: "fixed", min_value: 0.5, max_buckets: 8 },
    },
  },
  ticketed: {
    flash: {
      title: "Sit & go style",
      why: "Small ticketed field",
      values: { currency: "EUR", prize_pool: 5000, entrants: 80, entry_fee: 50, winners_mode: "count", winners_value: 12, style: "balanced", min_mode: "entry_multiple", min_value: 1.5, max_buckets: 10 },
    },
    daily: {
      title: "Soft field MTT",
      why: "Daily ticketed volume",
      values: { currency: "EUR", prize_pool: 50000, entrants: 2000, entry_fee: 25, winners_mode: "percentage", winners_value: 15, style: "balanced", min_mode: "entry_multiple", min_value: 1.5, max_buckets: 12 },
    },
    weekly: {
      title: "Soft weekly",
      why: "Wide midfield board",
      values: { currency: "EUR", prize_pool: 250000, entrants: 20000, entry_fee: 10, winners_mode: "percentage", winners_value: 10, style: "flat", min_mode: "entry_multiple", min_value: 1.5, max_buckets: 12 },
    },
  },
};

const CONTEXT_COPY = {
  slot: "Guaranteed pool. Paid places you set. No buy-in, no field size — this is not a poker table.",
  ticketed: "Buy-in event. Field size and ticket multiple are in play.",
};

const COPY = {
  generate: ["New structure", "Generate a prize table", "Pick a template — preview updates as you edit."],
  analyze: ["Audit", "Analyze a published ladder", "Score niceness, compactness, and mid-field value."],
  optimize: ["Rewrite", "Optimize an existing table", "Keep the contract. Clean the widget."],
  recalibrate: ["Growing pool", "Recalibrate a guarantee", "Same philosophy, new prize pool."],
};

const KPI_HELP = {
  quality: "Weighted average of the quality bars below (0–100). Higher = more cashier-ready and on-style.",
  pool: "Total effective prize pool used for this ladder.",
  guarantee: "Fixed guarantee before bet contribution.",
  contribution: "Added share from % of expected tournament bets.",
  paid: "How many finishing positions receive a payout.",
  first: "Amount paid to 1st place in this ladder.",
  min: "Minimum prize floor from Advanced — every paid place must be at least this, not necessarily the lowest tier shown.",
};

let previewTimer = null;
let previewSeq = 0;
const SAVED_TEMPLATES_KEY = "kanggiten-prize-engine-templates-v1";
const MAX_SAVED_TEMPLATES = 24;

const METRIC_HELP = {
  nice_numbers: "Share of the paid pool on cashier-friendly amounts (€500, €250, …) from the nice-number profile.",
  compactness: "Fewer widget tiers vs paid places. Tighter grouping = cleaner lobby display; ~12 tiers is ideal for large fields.",
  marketing_p1: "First prize quality: nice-number check plus how close P1 is to the style target (~15% balanced, ~28% jackpot, ~8% flat).",
  midfield: "Pool share outside the top ~10% of places. Higher = more value in places 2–50. Scored against your style target.",
  curve_fit: "How closely rank-by-rank prizes follow the ideal power-law curve for this style.",
  smoothness: "Penalises harsh cliffs between adjacent tiers (e.g. one tier paying 3×+ the next). 100 = smooth steps.",
  bucket_progression: "Widget tiers should widen going down (1 → 2–3 → 4–10). 100 = no inverted grouping.",
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const toastEl = $("#toast");
function toast(message, ok = false) {
  toastEl.hidden = false;
  toastEl.textContent = message;
  toastEl.classList.toggle("is-ok", ok);
  clearTimeout(toastEl._t);
  toastEl._t = setTimeout(() => { toastEl.hidden = true; }, 4200);
}

function money(cents, currency = "EUR") {
  const symbols = { EUR: "€", USD: "$", GBP: "£" };
  const value = (cents / 100).toLocaleString(undefined, {
    minimumFractionDigits: cents % 100 ? 2 : 0,
    maximumFractionDigits: 2,
  });
  return `${symbols[currency] || currency + " "}${value}`;
}

function formatPool(amount, currency = "EUR") {
  const symbols = { EUR: "€", USD: "$", GBP: "£" };
  const n = Number(amount);
  if (n >= 1000) {
    const compact = n % 1000 === 0 ? `${n / 1000}k` : `${(n / 1000).toFixed(1)}k`;
    return `${symbols[currency] || ""}${compact}`;
  }
  return `${symbols[currency] || ""}${n}`;
}

function recipeMeta(recipe) {
  const v = recipe.values;
  const paid = v.winners_mode === "percentage"
    ? `${v.winners_value}% paid`
    : `${v.winners_value} places`;
  const parts = [formatPool(v.prize_pool, v.currency), paid, STYLE_LABEL[v.style] || v.style];
  if (v.entry_fee != null && v.entry_fee > 0) parts.splice(1, 0, `${formatPool(v.entry_fee, v.currency)} buy-in`);
  return parts.join(" · ");
}

let eventContext = "slot";
let selectedRecipeId = "flash";

function usesField() {
  return eventContext === "ticketed" || $("#known-field").checked;
}

function usesTicket() {
  return eventContext === "ticketed";
}

function usesCumulative() {
  return $("#cumulative-pool")?.checked === true;
}

function applyContext() {
  const field = usesField();
  const ticket = usesTicket();
  const cumulative = usesCumulative();
  const minMode = generateForm.elements.min_mode;
  if (!ticket && minMode.value === "entry_multiple") minMode.value = "fixed";
  $$("[data-when]").forEach((el) => {
    const when = el.dataset.when;
    const show = (when === "slot" && eventContext === "slot")
      || (when === "ticket" && ticket)
      || (when === "field" && field);
    el.hidden = !show;
  });
  const cumulativeFields = $("#cumulative-fields");
  if (cumulativeFields) cumulativeFields.hidden = !cumulative;
  const poolLabel = $("#pool-label");
  if (poolLabel) poolLabel.textContent = cumulative ? "Guarantee" : "Prize pool";
  $("#context-hint").textContent = CONTEXT_COPY[eventContext];
  const winnersMode = field ? generateForm.elements.winners_mode.value : "count";
  $("[data-label='winners']").textContent = winnersMode === "percentage" ? "Paid % of field" : "Paid places";
  const minWrap = $("#min-value-wrap");
  minWrap.hidden = minMode.value === "automatic";
  $("[data-label='min']").textContent = minMode.value === "entry_multiple" ? "Min multiple" : "Min amount";
}

function fillForm(form, data) {
  for (const [key, value] of Object.entries(data)) {
    const field = form.elements[key];
    if (field) field.value = value;
  }
  if ("pool_mode" in data || "cumulative_enabled" in data) {
    const cumulative = data.pool_mode === "cumulative" || data.cumulative_enabled === true;
    const box = form.elements.cumulative_enabled;
    if (box) box.checked = cumulative;
  }
  if ("known_field" in data) {
    const known = $("#known-field");
    if (known) known.checked = Boolean(data.known_field);
  }
  if (data.style) syncStyleCards(data.style);
  applyContext();
}

function formValuesFromForm(form) {
  return {
    currency: form.elements.currency.value,
    prize_pool: Number(form.elements.prize_pool.value),
    pool_mode: usesCumulative() ? "cumulative" : "fixed",
    cumulative_enabled: usesCumulative(),
    contribution_rate: Number(form.elements.contribution_rate?.value || 0),
    expected_total_wager: Number(form.elements.expected_total_wager?.value || 0),
    entrants: Number(form.elements.entrants?.value || 80),
    entry_fee: Number(form.elements.entry_fee?.value || 0),
    winners_mode: form.elements.winners_mode.value,
    winners_value: Number(form.elements.winners_value.value),
    style: form.elements.style.value,
    min_mode: form.elements.min_mode.value,
    min_value: Number(form.elements.min_value.value),
    max_buckets: Number(form.elements.max_buckets.value),
    nice_profile: form.elements.nice_profile.value,
    known_field: $("#known-field")?.checked || false,
  };
}

function loadSavedTemplates() {
  try {
    const raw = localStorage.getItem(SAVED_TEMPLATES_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function persistSavedTemplates(templates) {
  localStorage.setItem(SAVED_TEMPLATES_KEY, JSON.stringify(templates.slice(0, MAX_SAVED_TEMPLATES)));
}

function savedTemplateMeta(values) {
  const recipe = { values: { ...values, currency: values.currency || "EUR" } };
  return recipeMeta(recipe);
}

function saveCurrentTemplate() {
  const nameInput = $("#template-name");
  let name = (nameInput?.value || "").trim();
  if (!name) {
    name = window.prompt("Template name?")?.trim() || "";
  }
  if (!name) return;
  const templates = loadSavedTemplates();
  const id = globalThis.crypto?.randomUUID?.() || `t-${Date.now()}`;
  templates.unshift({
    id,
    name,
    context: eventContext,
    values: formValuesFromForm(generateForm),
    savedAt: new Date().toISOString(),
  });
  persistSavedTemplates(templates);
  if (nameInput) nameInput.value = "";
  selectedRecipeId = `saved:${id}`;
  renderRecipes();
  toast(`Saved team template “${name}”`, true);
}

function deleteSavedTemplate(id) {
  const templates = loadSavedTemplates().filter((t) => t.id !== id);
  persistSavedTemplates(templates);
  if (selectedRecipeId === `saved:${id}`) {
    selectedRecipeId = "flash";
    loadRecipe("flash");
  } else {
    renderRecipes();
  }
  toast("Template removed", true);
}

function styleCurveSvg(option, selected) {
  const stroke = selected ? "#d0ff43" : "#781dff";
  const fill = selected ? "rgba(208,255,67,0.12)" : "rgba(120,29,255,0.18)";
  return `<svg class="style-curve" viewBox="0 0 100 48" aria-hidden="true">
    <path d="${option.fill}" fill="${fill}" />
    <path d="${option.curve}" fill="none" stroke="${stroke}" stroke-width="2.5" stroke-linecap="round" />
  </svg>`;
}

function renderStyleCards() {
  const wrap = $("#style-cards");
  const current = generateForm.elements.style.value || "balanced";
  wrap.innerHTML = Object.entries(STYLE_OPTIONS).map(([id, opt]) => `
    <button type="button" class="style-card ${id === current ? "is-selected" : ""}" data-style="${id}" aria-pressed="${id === current}">
      ${styleCurveSvg(opt, id === current)}
      <span class="style-card-title">${opt.title}</span>
      <span class="style-card-sub">${opt.subtitle}</span>
    </button>
  `).join("");
  $$("[data-style]", wrap).forEach((btn) => {
    btn.addEventListener("click", () => selectStyle(btn.dataset.style));
  });
}

function syncStyleCards(styleId) {
  generateForm.elements.style.value = styleId;
  renderStyleCards();
}

function selectStyle(styleId) {
  if (!STYLE_OPTIONS[styleId]) return;
  syncStyleCards(styleId);
  schedulePreview();
}

function bucketSize(bucket) {
  const start = bucket.start ?? bucket.from;
  const end = bucket.end ?? bucket.to;
  if (start == null || end == null) return 0;
  return end - start + 1;
}

function rankAmounts(structure) {
  const amounts = [];
  for (const bucket of structure.buckets || []) {
    const count = bucketSize(bucket);
    for (let i = 0; i < count; i += 1) amounts.push(bucket.amount_cents);
  }
  return amounts;
}

function poolShareRows(structure) {
  const pool = structure.prize_pool_cents || 1;
  const amounts = rankAmounts(structure);
  const sum = (from, to) => amounts.slice(from, to).reduce((a, b) => a + b, 0);
  const rows = [
    { label: "1st place", cents: amounts[0] || 0 },
    { label: "Top 3", cents: sum(0, 3) },
    { label: "Top 10", cents: sum(0, Math.min(10, amounts.length)) },
    { label: "Rest", cents: Math.max(0, pool - sum(0, Math.min(10, amounts.length))) },
  ];
  return rows.map((row) => ({ ...row, pct: (100 * row.cents) / pool }));
}

function idealRankAmounts(structure) {
  const n = structure.winner_count || 1;
  const pool = structure.prize_pool_cents;
  const style = structure.style || "balanced";
  const spec = STYLE_OPTIONS[style] || STYLE_OPTIONS.balanced;
  const p1 = pool * spec.p1;
  const e = Math.max(structure.min_prize_cents || 0, pool * 0.005);
  let alpha = spec.alpha;
  const ranks = Array.from({ length: n }, (_, i) => i + 1);
  for (let iter = 0; iter < 48; iter += 1) {
    const amounts = ranks.map((i) => e + (p1 - e) / Math.pow(i, alpha));
    const total = amounts.reduce((a, b) => a + b, 0);
    if (Math.abs(total - pool) / pool < 0.002) return amounts;
    alpha += total > pool ? 0.04 : -0.04;
    if (alpha < 0.05) alpha = 0.05;
  }
  return ranks.map((i) => e + (p1 - e) / Math.pow(i, spec.alpha));
}

function distributionVizHtml(structure) {
  const amounts = rankAmounts(structure);
  if (!amounts.length) return "";
  const ideal = idealRankAmounts(structure);
  const maxVal = Math.max(...amounts, ...ideal, 1);
  const n = amounts.length;
  const w = 320;
  const h = 120;
  const pad = { l: 4, r: 4, t: 8, b: 18 };
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;
  const xAt = (rank) => pad.l + ((rank - 1) / Math.max(n - 1, 1)) * innerW;
  const yAt = (cents) => pad.t + innerH - (cents / maxVal) * innerH;

  let idealPath = "";
  ideal.forEach((cents, i) => {
    const x = xAt(i + 1);
    const y = yAt(cents);
    idealPath += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });

  let stepPath = "";
  amounts.forEach((cents, i) => {
    const x0 = xAt(i + 1) - (i === 0 ? 0 : innerW / (n - 1) / 2);
    const x1 = xAt(i + 1) + (i === n - 1 ? 0 : innerW / (n - 1) / 2);
    const y = yAt(cents);
    stepPath += `M ${x0} ${y} H ${x1} `;
    if (i < n - 1) stepPath += `V ${yAt(amounts[i + 1])} `;
  });

  const shares = poolShareRows(structure);
  const shareRows = shares.map((row) => `
    <div class="share-row">
      <span>${row.label}</span>
      <div class="share-track"><i style="width:${Math.max(2, row.pct).toFixed(1)}%"></i></div>
      <b>${row.pct.toFixed(1)}%</b>
    </div>`).join("");

  return `
    <div class="distribution">
      <div class="pool-share">
        <p class="overline">Pool split</p>
        ${shareRows}
      </div>
      <div class="dist-chart">
        <p class="overline">Prize by place</p>
        <svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Prize amount by finishing place">
          <defs>
            <linearGradient id="distFill" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="#781dff" stop-opacity="0.35" />
              <stop offset="100%" stop-color="#d043ff" stop-opacity="0.08" />
            </linearGradient>
          </defs>
          <line x1="${pad.l}" y1="${pad.t + innerH}" x2="${w - pad.r}" y2="${pad.t + innerH}" stroke="rgba(120,29,255,0.25)" />
          <path d="${idealPath}" fill="none" stroke="rgba(184,179,199,0.45)" stroke-width="1.5" stroke-dasharray="4 4" />
          <path d="${stepPath}" fill="none" stroke="#d0ff43" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <div class="chart-legend">
          <span><i class="legend-line legend-actual"></i>Published ladder</span>
          <span><i class="legend-line legend-target"></i>Style target</span>
        </div>
      </div>
    </div>`;
}

function generatePayload(form) {
  const ticket = usesTicket();
  const field = usesField();
  const winnersMode = field ? form.elements.winners_mode.value : "count";
  const winnersValue = Number(form.elements.winners_value.value);
  const paidCount = winnersMode === "count"
    ? winnersValue
    : Math.max(1, Math.round(Number(form.elements.entrants.value) * winnersValue / 100));
  let minMode = form.elements.min_mode.value;
  if (!ticket && minMode === "entry_multiple") minMode = "fixed";
  const cumulative = usesCumulative();
  return {
    currency: form.elements.currency.value,
    prize_pool: Number(form.elements.prize_pool.value),
    pool_mode: cumulative ? "cumulative" : "fixed",
    contribution_rate: cumulative ? Number(form.elements.contribution_rate.value) : 0,
    expected_total_wager: cumulative ? Number(form.elements.expected_total_wager.value) : 0,
    entrants: field ? Number(form.elements.entrants.value) : paidCount,
    entry_fee: ticket ? Number(form.elements.entry_fee.value) : 0,
    style: form.elements.style.value,
    winners: { mode: winnersMode, value: winnersValue },
    minimum_prize: { mode: minMode, value: minMode === "automatic" ? null : Number(form.elements.min_value.value) },
    top_prize: { mode: "auto" },
    constraints: {
      max_buckets: Number(form.elements.max_buckets.value),
      nice_number_profile: form.elements.nice_profile.value,
    },
  };
}

function renderRecipes() {
  const list = $("#recipe-list");
  const builtIn = RECIPES[eventContext];
  const saved = loadSavedTemplates().filter((t) => t.context === eventContext);
  const isSavedSelected = selectedRecipeId?.startsWith("saved:");
  const savedId = isSavedSelected ? selectedRecipeId.slice(6) : null;
  if (isSavedSelected && !saved.some((t) => t.id === savedId)) {
    selectedRecipeId = Object.keys(builtIn)[0];
  } else if (!isSavedSelected && !builtIn[selectedRecipeId]) {
    selectedRecipeId = Object.keys(builtIn)[0];
  }
  const builtInHtml = Object.entries(builtIn).map(([id, recipe]) => {
    const selected = selectedRecipeId === id;
    return `
    <button type="button" class="recipe ${selected ? "is-selected" : ""}" data-source="builtin" data-preset="${id}">
      <span class="recipe-title">${recipe.title}</span>
      <span class="recipe-meta">${recipeMeta(recipe)}</span>
      <span class="recipe-why">${recipe.why}</span>
    </button>`;
  }).join("");
  const savedHtml = saved.map((t) => {
    const selected = selectedRecipeId === `saved:${t.id}`;
    return `
    <button type="button" class="recipe is-saved ${selected ? "is-selected" : ""}" data-source="saved" data-preset="${t.id}">
      <span class="recipe-title">${t.name}</span>
      <span class="recipe-meta">${savedTemplateMeta(t.values)}</span>
      <span class="recipe-why">Saved ${new Date(t.savedAt).toLocaleDateString()}</span>
      <span class="recipe-delete" role="button" tabindex="0" data-delete="${t.id}" aria-label="Delete template">Remove</span>
    </button>`;
  }).join("");
  list.innerHTML = [
    saved.length ? `<p class="template-section-label">Your templates</p>${savedHtml}` : "",
    `<p class="template-section-label">Built-in</p>${builtInHtml}`,
  ].join("");
  $$("[data-preset]", list).forEach((btn) => {
    btn.addEventListener("click", (event) => {
      if (event.target.closest("[data-delete]")) return;
      loadTemplate(btn.dataset.preset, btn.dataset.source);
    });
  });
  $$("[data-delete]", list).forEach((btn) => {
    const handler = (event) => {
      event.preventDefault();
      event.stopPropagation();
      deleteSavedTemplate(btn.dataset.delete);
    };
    btn.addEventListener("click", handler);
    btn.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") handler(event);
    });
  });
}

function loadTemplate(id, source) {
  if (source === "saved") {
    const template = loadSavedTemplates().find((t) => t.id === id);
    if (!template) return;
    if (template.context !== eventContext) {
      eventContext = template.context;
      $$(".segment-btn").forEach((b) => b.classList.toggle("is-selected", b.dataset.context === eventContext));
    }
    selectedRecipeId = `saved:${id}`;
    fillForm(generateForm, template.values);
    renderRecipes();
    clearSuggestions();
    schedulePreview();
    return;
  }
  loadRecipe(id);
}

function loadRecipe(id) {
  const recipe = RECIPES[eventContext][id];
  if (!recipe) return;
  selectedRecipeId = id;
  fillForm(generateForm, recipe.values);
  renderRecipes();
  clearSuggestions();
  schedulePreview();
}

function clearSuggestions() {
  const box = $("#generate-suggestions");
  box.hidden = true;
  box.innerHTML = "";
}

function showSuggestions(items) {
  const box = $("#generate-suggestions");
  if (!items.length) {
    clearSuggestions();
    return;
  }
  box.hidden = false;
  box.innerHTML = `
    <p class="suggestions-label">Suggestions</p>
    <div class="suggestions-row">
      ${items.map((item) => `<button type="button" class="chip suggest" data-action="${item.action}" data-value="${item.value ?? ""}">${item.label}</button>`).join("")}
    </div>
  `;
  $$(".suggest", box).forEach((btn) => {
    btn.addEventListener("click", () => applySuggestion(btn.dataset.action, btn.dataset.value));
  });
}

function applySuggestion(action, value) {
  if (action === "style") {
    selectStyle(value);
    return;
  }
    if (action === "paid") {
    generateForm.elements.winners_mode.value = "count";
    generateForm.elements.winners_value.value = value;
    applyContext();
    clearSuggestions();
    schedulePreview();
    return;
  }
  if (action === "recipe") {
    loadRecipe(value);
    return;
  }
  if (action === "regenerate") {
    schedulePreview();
  }
}

function buildFormSuggestions(payload) {
  const items = [];
  const paid = payload.winners.mode === "count"
    ? payload.winners.value
    : Math.max(1, Math.round(payload.entrants * payload.winners.value / 100));
  if (payload.style === "flat" && paid < 40 && payload.prize_pool >= 100000) {
    items.push({ action: "paid", value: "50", label: "Raise paid places to 50" });
    items.push({ action: "style", value: "balanced", label: "Try Engage the field" });
  }
  if (payload.style === "top_heavy" && paid > 80) {
    items.push({ action: "style", value: "balanced", label: "Try Engage the field" });
  }
  if (eventContext === "slot" && paid < 10 && payload.prize_pool >= 10000) {
    items.push({ action: "recipe", value: "daily", label: "Load Daily slot recipe" });
  }
  return items.slice(0, 3);
}

function buildResultSuggestions(quality, payload) {
  const items = [];
  const mid = Number(quality?.metrics?.midfield ?? 100);
  if (mid < 40) {
    items.push({ action: "style", value: "flat", label: "More Wide board" });
    items.push({ action: "paid", value: String(Math.max(30, Math.round((payload.winners.value || 12) * 1.5))), label: "Widen paid places" });
  }
  const p1 = Number(quality?.metrics?.marketing_p1 ?? 100);
  if (p1 < 45) {
    items.push({ action: "style", value: "top_heavy", label: "More hero 1st prize" });
  }
  return items.slice(0, 3);
}

function parseExisting(raw) {
  const parsed = JSON.parse(raw);
  if (!parsed.payouts) throw new Error("JSON needs a payouts array.");
  return parsed;
}

async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail || res.statusText));
  }
  return data;
}

function tipLabel(text, help) {
  if (!help) return text;
  return `<span class="tip-label" title="${help.replaceAll('"', "&quot;")}">${text}</span>`;
}

function metricBars(metrics = {}) {
  return Object.entries(metrics).map(([name, value]) => {
    const label = name.replaceAll("_", " ");
    return `
    <div class="metric">
      ${tipLabel(label, METRIC_HELP[name])}
      <div class="bar"><i style="width:${Math.max(0, Math.min(100, value))}%"></i></div>
      <b>${Number(value).toFixed(0)}</b>
    </div>`;
  }).join("");
}

function tableHtml(structure) {
  const pool = structure.prize_pool_cents || 1;
  const rows = (structure.buckets || []).map((b) => {
    const start = b.start ?? b.from;
    const end = b.end ?? b.to;
    const podium = start <= 3 ? "podium" : "";
    const places = start === end ? `${start}` : `${start}–${end}`;
    const share = ((b.amount_cents * bucketSize(b)) / pool) * 100;
    return `<tr class="${podium}"><td>${places}</td><td class="money">${money(b.amount_cents, structure.currency)}</td><td class="money">${share.toFixed(1)}%</td></tr>`;
  }).join("");
  return `<div class="table-wrap"><table id="payout-table">
    <thead><tr><th>Places</th><th class="money">Prize</th><th class="money">Pool</th></tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
}

function poolKpiHtml(structure, normalized) {
  const currency = structure.currency;
  if (normalized?.pool_mode === "cumulative" && normalized.contribution_cents > 0) {
    return `
        <div class="kpi">${tipLabel("<span>Guarantee</span>", KPI_HELP.guarantee)}<strong>${money(normalized.guarantee_cents, currency)}</strong></div>
        <div class="kpi">${tipLabel("<span>+ Bets</span>", KPI_HELP.contribution)}<strong>${money(normalized.contribution_cents, currency)}</strong></div>
        <div class="kpi">${tipLabel("<span>Effective pool</span>", KPI_HELP.pool)}<strong>${money(structure.prize_pool_cents, currency)}</strong></div>
        <div class="kpi">${tipLabel("<span>Paid places</span>", KPI_HELP.paid)}<strong>${structure.winner_count}</strong></div>
        <div class="kpi">${tipLabel("<span>First prize</span>", KPI_HELP.first)}<strong>${money(structure.top_prize_cents, currency)}</strong></div>
        <div class="kpi">${tipLabel("<span>Min cash</span>", KPI_HELP.min)}<strong>${money(structure.min_prize_cents, currency)}</strong></div>`;
  }
  return `
        <div class="kpi">${tipLabel("<span>Pool</span>", KPI_HELP.pool)}<strong>${money(structure.prize_pool_cents, currency)}</strong></div>
        <div class="kpi">${tipLabel("<span>Paid places</span>", KPI_HELP.paid)}<strong>${structure.winner_count}</strong></div>
        <div class="kpi">${tipLabel("<span>First prize</span>", KPI_HELP.first)}<strong>${money(structure.top_prize_cents, currency)}</strong></div>
        <div class="kpi">${tipLabel("<span>Min cash</span>", KPI_HELP.min)}<strong>${money(structure.min_prize_cents, currency)}</strong></div>`;
}

function summaryHtml(structure, quality, extra = "", normalized = null) {
  return `
    <div class="summary">
      <div class="score">${tipLabel('<span class="overline">Quality</span>', KPI_HELP.quality)}<b>${Number(quality.score).toFixed(0)}</b></div>
      <div class="kpis">
        ${poolKpiHtml(structure, normalized)}
      </div>
    </div>
    <div class="metrics">${metricBars(quality.metrics)}</div>
    ${distributionVizHtml(structure)}
    ${extra}
    ${tableHtml(structure)}`;
}

function tableExportText(structure, normalized = null, delimiter = "\t", { includeMeta = true } = {}) {
  const pool = structure.prize_pool_cents || 1;
  const currency = structure.currency || "EUR";
  const lines = [];
  if (includeMeta) {
    lines.push(["Field", "Value"].join(delimiter));
    lines.push(["Currency", currency].join(delimiter));
    if (normalized?.pool_mode === "cumulative" && normalized.contribution_cents > 0) {
      lines.push(["Guarantee", (normalized.guarantee_cents / 100).toFixed(2)].join(delimiter));
      lines.push(["Bet contribution", (normalized.contribution_cents / 100).toFixed(2)].join(delimiter));
    }
    lines.push(["Effective pool", (pool / 100).toFixed(2)].join(delimiter));
    lines.push(["Paid places", structure.winner_count].join(delimiter));
    lines.push(["Style", structure.style || ""].join(delimiter));
    lines.push(["First prize", (structure.top_prize_cents / 100).toFixed(2)].join(delimiter));
    lines.push("");
  }
  lines.push(["Place", "Prize", "Currency", "Pool %"].join(delimiter));
  for (const b of structure.buckets || []) {
    const start = b.start ?? b.from;
    const end = b.end ?? b.to;
    const places = start === end ? `${start}` : `${start}-${end}`;
    const amt = (b.amount_cents / 100).toFixed(2);
    const share = ((b.amount_cents * bucketSize(b) / pool) * 100).toFixed(1);
    lines.push([places, amt, currency, share].join(delimiter));
  }
  return lines.join("\n");
}

async function copyTableExport(structure, normalized, delimiter) {
  const text = tableExportText(structure, normalized, delimiter);
  await navigator.clipboard.writeText(text);
  toast(delimiter === "," ? "CSV copied — paste into Sheets" : "TSV copied — paste into Google Sheets", true);
}

function downloadTableExport(structure, normalized, delimiter = ",") {
  const text = tableExportText(structure, normalized, delimiter);
  const blob = new Blob([`\uFEFF${text}`], { type: "text/csv;charset=utf-8" });
  const stamp = new Date().toISOString().slice(0, 10);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `kanggiten-ladder-${stamp}.csv`;
  link.click();
  URL.revokeObjectURL(url);
  toast("CSV downloaded", true);
}

function showResultsPanel(show) {
  const stage = $("#view-generate");
  const panel = $("#generate-results");
  stage.classList.toggle("has-results", show);
  panel.hidden = !show;
  $("#generate-submit").textContent = show ? "Refresh table" : "Generate table";
}

function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(() => runGenerate({ silent: true }), 500);
}

async function runGenerate({ silent = false } = {}) {
  const payload = generatePayload(generateForm);
  const seq = ++previewSeq;
  const btn = $("#generate-submit");
  const panel = $("#generate-results");
  if (!silent) btn.disabled = true;
  else {
    btn.classList.add("is-loading");
    if (!panel.hidden) panel.classList.add("is-loading");
  }
  try {
    const result = await api("/v1/payouts/generate", payload);
    if (seq !== previewSeq) return;
    showResultsPanel(true);
    renderGenerate(panel, result, payload, result.normalized);
    if (!silent) toast(`Table ready in ${result.runtime_ms.toFixed(0)} ms`, true);
  } catch (err) {
    if (seq !== previewSeq) return;
    showSuggestions([
      ...buildFormSuggestions(payload),
      { action: "recipe", value: "daily", label: "Load Daily recipe" },
    ].slice(0, 3));
    if (!silent) toast(err.message);
  } finally {
    if (!silent) btn.disabled = false;
    else {
      btn.classList.remove("is-loading");
      panel.classList.remove("is-loading");
    }
  }
}

function renderGenerate(target, result, payload, normalized = null) {
  const candidates = result.candidates || [];
  const paint = (index) => {
    const candidate = candidates[index];
    const structure = candidate.structure;
    const chips = candidates.map((c, i) =>
      `<button type="button" class="chip ${i === index ? "is-selected" : ""}" data-idx="${i}">Alt ${i + 1} · ${Number(c.quality.score).toFixed(0)}</button>`
    ).join("");
    const flags = [
      ...(candidate.validation.errors || []).map((e) => e.message),
      ...(structure.warnings || []),
    ];
    target.innerHTML = `
      <div class="result-actions export-menu">
        <button type="button" class="btn secondary" data-copy="tsv">Copy for Sheets</button>
        <button type="button" class="btn secondary" data-copy="csv">Copy CSV</button>
        <button type="button" class="btn secondary" data-download="csv">Download CSV</button>
        <p class="micro">Includes pool setup + ladder — ready for Google Sheets or CMS paste.</p>
      </div>
      <p class="preview-note">Live preview — ladder updates as you change the template.</p>
      <div class="candidates">${chips}</div>
      ${summaryHtml(structure, candidate.quality, flags.length ? `<ul class="flags">${flags.map((f) => `<li>${f}</li>`).join("")}</ul>` : "", normalized)}
    `;
    $$(".chip", target).forEach((chip) => chip.addEventListener("click", () => paint(Number(chip.dataset.idx))));
    $$("[data-copy]", target).forEach((btn) => {
      btn.addEventListener("click", () => {
        copyTableExport(structure, normalized, btn.dataset.copy === "csv" ? "," : "\t").catch(() => toast("Could not copy — check browser permissions"));
      });
    });
    $("[data-download]", target)?.addEventListener("click", () => downloadTableExport(structure, normalized));
    showSuggestions(buildResultSuggestions(candidate.quality, payload));
  };
  if (!candidates.length) {
    target.innerHTML = `<p class="flags">No candidate returned.</p>`;
    return;
  }
  paint(0);
}

function setView(name) {
  $$(".stage").forEach((stage) => stage.classList.toggle("is-hidden", stage.id !== `view-${name}`));
  const [kicker, title, hint] = COPY[name] || COPY.generate;
  $("#view-kicker").textContent = kicker;
  $("#view-title").textContent = title;
  $("#view-hint").textContent = hint;
}

const generateForm = $("#generate-form");

$$(".segment-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    eventContext = btn.dataset.context;
    $$(".segment-btn").forEach((b) => b.classList.toggle("is-selected", b === btn));
    if (eventContext === "ticketed") $("#known-field").checked = false;
    selectedRecipeId = "flash";
    renderRecipes();
    loadRecipe(selectedRecipeId);
  });
});

$("#known-field").addEventListener("change", () => {
  applyContext();
  clearSuggestions();
  schedulePreview();
});
generateForm.elements.winners_mode.addEventListener("change", () => {
  applyContext();
  schedulePreview();
});
generateForm.elements.min_mode.addEventListener("change", () => {
  applyContext();
  schedulePreview();
});
$("#cumulative-pool").addEventListener("change", () => {
  applyContext();
  schedulePreview();
});
["prize_pool", "winners_value", "entrants", "contribution_rate", "expected_total_wager", "currency"].forEach((name) => {
  generateForm.elements[name]?.addEventListener("input", schedulePreview);
  generateForm.elements[name]?.addEventListener("change", schedulePreview);
});
["max_buckets", "min_value"].forEach((name) => {
  generateForm.elements[name]?.addEventListener("change", schedulePreview);
});
generateForm.elements.nice_profile?.addEventListener("change", schedulePreview);

generateForm.addEventListener("submit", (event) => {
  event.preventDefault();
  runGenerate({ silent: false });
});

$("#save-template-btn")?.addEventListener("click", saveCurrentTemplate);
$("#template-name")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    saveCurrentTemplate();
  }
});

function bindJsonForm(formId, resultId, handler) {
  const form = $(formId);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    try {
      await handler(form, $(resultId));
    } catch (err) {
      toast(err.message);
    } finally {
      btn.disabled = false;
    }
  });
}

bindJsonForm("#analyze-form", "#analyze-results", async (form, target) => {
  const result = await api("/v1/payouts/analyze", parseExisting(form.payload.value));
  const flags = [...(result.issues || []), ...(result.validation.errors || []).map((e) => e.message)];
  const extra = flags.length ? `<ul class="flags">${flags.map((f) => `<li>${f}</li>`).join("")}</ul>` : "";
  target.innerHTML = summaryHtml(syntheticStructure(result, form.payload.value), result.quality, extra);
  target.dataset.empty = "false";
  toast("Audit complete", true);
});

function syntheticStructure(result, raw) {
  const existing = JSON.parse(raw);
  const buckets = (existing.payouts || []).map((row) => ({
    start: row.from,
    end: row.to,
    amount_cents: Math.round(row.amount * 100),
  }));
  const winner_count = buckets.at(-1)?.end || result.inferred?.winner_count;
  const prize_pool_cents = Math.round((existing.prize_pool || 0) * 100);
  return {
    currency: existing.currency || "EUR",
    prize_pool_cents,
    winner_count,
    top_prize_cents: buckets[0]?.amount_cents || 0,
    min_prize_cents: buckets.at(-1)?.amount_cents || 0,
    buckets,
  };
}

bindJsonForm("#optimize-form", "#optimize-results", async (form, target) => {
  const result = await api("/v1/payouts/optimize", parseExisting(form.payload.value));
  target.innerHTML = `<div class="compare">
    <div><p class="overline">Original · ${result.original_score.toFixed(0)}</p>${summaryHtml(result.original.structure, result.original.quality)}</div>
    <div><p class="overline">Optimized · ${result.optimized_score.toFixed(0)}</p>${summaryHtml(result.optimized.structure, result.optimized.quality)}</div>
  </div>`;
  target.dataset.empty = "false";
  toast("Optimization complete", true);
});

bindJsonForm("#recalibrate-form", "#recalibrate-results", async (form, target) => {
  const existing = parseExisting(form.payload.value);
  const result = await api("/v1/payouts/recalibrate", {
    existing,
    new_prize_pool: Number(form.new_prize_pool.value),
  });
  renderGenerate(target, result, generatePayload(generateForm));
  toast("Recalibrated to the new guarantee", true);
});

$$("[data-sample]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const form = btn.closest("form");
    form.payload.value = JSON.stringify(SAMPLE, null, 2);
  });
});

document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    const visible = $$(".stage").find((s) => !s.classList.contains("is-hidden"));
    visible?.querySelector("form")?.requestSubmit();
  }
});

renderStyleCards();
renderRecipes();
loadRecipe("flash");