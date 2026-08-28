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
  balanced: "Balanced",
  top_heavy: "Jackpot",
  flat: "Flat",
};

const RECIPES = {
  slot: {
    flash: {
      title: "Flash race",
      why: "Short promo / lobby race",
      values: { currency: "EUR", prize_pool: 5000, winners_mode: "count", winners_value: 12, style: "balanced", min_mode: "fixed", min_value: 1, max_buckets: 10 },
    },
    daily: {
      title: "Daily slot",
      why: "Standard daily leaderboard",
      values: { currency: "EUR", prize_pool: 50000, winners_mode: "count", winners_value: 50, style: "balanced", min_mode: "fixed", min_value: 1, max_buckets: 12 },
    },
    weekly: {
      title: "Weekly board",
      why: "Long board, more midfield",
      values: { currency: "EUR", prize_pool: 250000, winners_mode: "count", winners_value: 100, style: "flat", min_mode: "fixed", min_value: 1, max_buckets: 12 },
    },
    jackpot: {
      title: "Jackpot weekend",
      why: "Marketing first prize",
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
  generate: ["New structure", "Generate a prize table", "Pick a recipe, then publish."],
  analyze: ["Audit", "Analyze a published ladder", "Score niceness, compactness, and mid-field value."],
  optimize: ["Rewrite", "Optimize an existing table", "Keep the contract. Clean the widget."],
  recalibrate: ["Growing pool", "Recalibrate a guarantee", "Same philosophy, new prize pool."],
};

const KPI_HELP = {
  quality: "Weighted average of the quality bars below (0–100). Higher = more cashier-ready and on-style.",
  pool: "Total guaranteed prize pool for this structure.",
  paid: "How many finishing positions receive a payout.",
  first: "Amount paid to 1st place in this ladder.",
  min: "Minimum prize floor from Advanced — every paid place must be at least this, not necessarily the lowest tier shown.",
};

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

function applyContext() {
  const field = usesField();
  const ticket = usesTicket();
  const minMode = generateForm.elements.min_mode;
  if (!ticket && minMode.value === "entry_multiple") minMode.value = "fixed";
  $$("[data-when]").forEach((el) => {
    const when = el.dataset.when;
    const show = (when === "slot" && eventContext === "slot")
      || (when === "ticket" && ticket)
      || (when === "field" && field);
    el.hidden = !show;
  });
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
  return {
    currency: form.elements.currency.value,
    prize_pool: Number(form.elements.prize_pool.value),
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
  const recipes = RECIPES[eventContext];
  if (!recipes[selectedRecipeId]) selectedRecipeId = Object.keys(recipes)[0];
  list.innerHTML = Object.entries(recipes).map(([id, recipe]) => `
    <button type="button" class="recipe ${id === selectedRecipeId ? "is-selected" : ""}" data-preset="${id}">
      <span class="recipe-title">${recipe.title}</span>
      <span class="recipe-meta">${recipeMeta(recipe)}</span>
      <span class="recipe-why">${recipe.why}</span>
    </button>
  `).join("");
  $$("[data-preset]", list).forEach((btn) => {
    btn.addEventListener("click", () => loadRecipe(btn.dataset.preset));
  });
}

function loadRecipe(id) {
  const recipe = RECIPES[eventContext][id];
  if (!recipe) return;
  selectedRecipeId = id;
  fillForm(generateForm, recipe.values);
  renderRecipes();
  applyContext();
  clearSuggestions();
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
    generateForm.elements.style.value = value;
    clearSuggestions();
    return;
  }
  if (action === "paid") {
    generateForm.elements.winners_mode.value = "count";
    generateForm.elements.winners_value.value = value;
    applyContext();
    clearSuggestions();
    return;
  }
  if (action === "recipe") {
    loadRecipe(value);
    return;
  }
  if (action === "regenerate") {
    generateForm.requestSubmit();
  }
}

function buildFormSuggestions(payload) {
  const items = [];
  const paid = payload.winners.mode === "count"
    ? payload.winners.value
    : Math.max(1, Math.round(payload.entrants * payload.winners.value / 100));
  if (payload.style === "flat" && paid < 40 && payload.prize_pool >= 100000) {
    items.push({ action: "paid", value: "50", label: "Raise paid places to 50" });
    items.push({ action: "style", value: "balanced", label: "Switch to Balanced" });
  }
  if (payload.style === "top_heavy" && paid > 80) {
    items.push({ action: "style", value: "balanced", label: "Try Balanced for midfield" });
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
    items.push({ action: "style", value: "flat", label: "More midfield (Flat)" });
    items.push({ action: "paid", value: String(Math.max(30, Math.round((payload.winners.value || 12) * 1.5))), label: "Widen paid places" });
  }
  const p1 = Number(quality?.metrics?.marketing_p1 ?? 100);
  if (p1 < 45) {
    items.push({ action: "style", value: "top_heavy", label: "More jackpot feel" });
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
    const podium = b.start <= 3 ? "podium" : "";
    const places = b.start === b.end ? `${b.start}` : `${b.start}–${b.end}`;
    const share = ((b.amount_cents * ((b.end - b.start) + 1)) / pool) * 100;
    return `<tr class="${podium}"><td>${places}</td><td class="money">${money(b.amount_cents, structure.currency)}</td><td class="money">${share.toFixed(1)}%</td></tr>`;
  }).join("");
  return `<div class="table-wrap"><table>
    <thead><tr><th>Places</th><th class="money">Prize</th><th class="money">Pool</th></tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
}

function summaryHtml(structure, quality, extra = "") {
  return `
    <div class="summary">
      <div class="score">${tipLabel('<span class="overline">Quality</span>', KPI_HELP.quality)}<b>${Number(quality.score).toFixed(0)}</b></div>
      <div class="kpis">
        <div class="kpi">${tipLabel("<span>Pool</span>", KPI_HELP.pool)}<strong>${money(structure.prize_pool_cents, structure.currency)}</strong></div>
        <div class="kpi">${tipLabel("<span>Paid places</span>", KPI_HELP.paid)}<strong>${structure.winner_count}</strong></div>
        <div class="kpi">${tipLabel("<span>First prize</span>", KPI_HELP.first)}<strong>${money(structure.top_prize_cents, structure.currency)}</strong></div>
        <div class="kpi">${tipLabel("<span>Min cash</span>", KPI_HELP.min)}<strong>${money(structure.min_prize_cents, structure.currency)}</strong></div>
      </div>
    </div>
    <div class="metrics">${metricBars(quality.metrics)}</div>
    ${extra}
    ${tableHtml(structure)}`;
}

function renderGenerate(target, result, payload) {
  const candidates = result.candidates || [];
  const paint = (index) => {
    const candidate = candidates[index];
    const chips = candidates.map((c, i) =>
      `<button type="button" class="chip ${i === index ? "is-selected" : ""}" data-idx="${i}">Alt ${i + 1} · ${Number(c.quality.score).toFixed(0)}</button>`
    ).join("");
    const flags = [
      ...(candidate.validation.errors || []).map((e) => e.message),
      ...(candidate.structure.warnings || []),
    ];
    target.innerHTML = `
      <div class="candidates">${chips}</div>
      ${summaryHtml(candidate.structure, candidate.quality, flags.length ? `<ul class="flags">${flags.map((f) => `<li>${f}</li>`).join("")}</ul>` : "")}
    `;
    target.dataset.empty = "false";
    $$(".chip", target).forEach((chip) => chip.addEventListener("click", () => paint(Number(chip.dataset.idx))));
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
});
generateForm.elements.winners_mode.addEventListener("change", applyContext);
generateForm.elements.min_mode.addEventListener("change", applyContext);
["prize_pool", "winners_value", "style", "entrants"].forEach((name) => {
  generateForm.elements[name]?.addEventListener("change", () => {
    showSuggestions(buildFormSuggestions(generatePayload(generateForm)));
  });
});

generateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const btn = $("#generate-submit");
  const payload = generatePayload(generateForm);
  btn.disabled = true;
  try {
    const result = await api("/v1/payouts/generate", payload);
    renderGenerate($("#generate-results"), result, payload);
    toast(`Table ready in ${result.runtime_ms.toFixed(0)} ms`, true);
  } catch (err) {
    showSuggestions([
      ...buildFormSuggestions(payload),
      { action: "recipe", value: "daily", label: "Load Daily recipe" },
    ].slice(0, 3));
    toast(err.message);
  } finally {
    btn.disabled = false;
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

renderRecipes();
loadRecipe("flash");
