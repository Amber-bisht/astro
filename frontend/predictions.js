// Shared JS for Daily / Monthly / Yearly prediction pages.
// The page sets window.PREDICTION_MODE before this script loads.

const MODE = window.PREDICTION_MODE || "daily";

const state = { place: null, savedProfiles: [] };

const el = {
  status: document.getElementById("status-message"),
  generateBtn: document.getElementById("generate-btn"),
  profileSelect: document.getElementById("person-profile-select"),
  promptResult: document.getElementById("prompt-result"),
  promptText: document.getElementById("prompt-text"),
  copyBtn: document.getElementById("copy-prompt-btn"),
};

boot();

function boot() {
  setupPlaceAutocomplete();
  el.generateBtn.addEventListener("click", handleGenerate);
  el.copyBtn.addEventListener("click", handleCopy);
  el.profileSelect.addEventListener("change", () => handleProfileChange(el.profileSelect.value));
  refreshProfiles();
}

// ===== AUTOCOMPLETE =====

function setupPlaceAutocomplete() {
  const placeInput = document.getElementById("person-place");
  const suggestions = document.getElementById("person-suggestions");
  let timer;
  placeInput.addEventListener("input", () => {
    state.place = null;
    clearTimeout(timer);
    const q = placeInput.value.trim();
    if (q.length < 2) { suggestions.classList.add("hidden"); suggestions.innerHTML = ""; return; }
    timer = setTimeout(async () => {
      try {
        const res = await fetch(`/places/autocomplete?q=${encodeURIComponent(q)}`);
        const p = await res.json();
        if (!res.ok) throw new Error(p.detail || p.error || "Autocomplete unavailable.");
        renderSuggestions(p.results || []);
      } catch (e) { showStatus(e.message, true); }
    }, 280);
  });
  placeInput.addEventListener("blur", () => setTimeout(() => suggestions.classList.add("hidden"), 120));
}

function renderSuggestions(results) {
  const box = document.getElementById("person-suggestions");
  if (!results.length) { box.classList.add("hidden"); box.innerHTML = ""; return; }
  box.innerHTML = results.map((r, i) => `<button type="button" class="suggestion" data-index="${i}">${esc(r.label)}</button>`).join("");
  box.classList.remove("hidden");
  box.querySelectorAll(".suggestion").forEach(btn => {
    btn.addEventListener("click", () => {
      state.place = results[Number(btn.dataset.index)];
      document.getElementById("person-place").value = state.place.label;
      box.classList.add("hidden");
    });
  });
}

// ===== PROFILES =====

async function refreshProfiles() {
  try {
    const res = await fetch("/profiles");
    const data = await res.json();
    state.savedProfiles = data.profiles || [];
    const sel = el.profileSelect, cur = sel.value;
    sel.innerHTML = '<option value="">-- Select a saved profile --</option>' +
      state.savedProfiles.map(p => `<option value="${esc(p.name)}">${esc(p.name)} (${p.dob})</option>`).join("");
    sel.value = cur;
  } catch (e) { console.error(e); }
}

function handleProfileChange(name) {
  if (!name) return;
  const p = state.savedProfiles.find(x => x.name === name);
  if (!p) return;
  document.getElementById("person-name").value = p.name || "";
  document.getElementById("person-dob").value = p.dob || "";
  document.getElementById("person-time").value = p.time || "";
  const pi = document.getElementById("person-place");
  if (typeof p.place === "object") { state.place = p.place; pi.value = p.place.label || p.place.query || ""; }
  else { state.place = null; pi.value = p.place || ""; }
}

// ===== GENERATE =====

async function handleGenerate() {
  try {
    setBusy(true, "Calculating chart & building prompt…");
    const person = collectPerson();
    const res = await fetch("/single-chart", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(person) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.error || "Request failed.");

    const prompt = buildPrompt(data);
    el.promptText.textContent = prompt;
    el.promptResult.classList.remove("hidden");
    el.copyBtn.disabled = false;
    showStatus("Prompt ready — copy and paste into ChatGPT.");

    // Auto-save profile if logged in and name is provided
    if (person.name && typeof AUTH !== "undefined" && AUTH.isLoggedIn()) {
      try {
        await fetch("/profiles", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(person),
        });
      } catch { /* silent fail */ }
    }
    refreshProfiles();
  } catch (e) {
    showStatus(e.message, true);
  } finally { setBusy(false); }
}

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(el.promptText.textContent);
    const orig = el.copyBtn.textContent;
    el.copyBtn.textContent = "✓ Copied!";
    showStatus("Prompt copied to clipboard!");
    setTimeout(() => { el.copyBtn.textContent = orig; }, 2000);
  } catch { showStatus("Clipboard copy failed.", true); }
}

function collectPerson() {
  const name = document.getElementById("person-name").value.trim();
  const dob = document.getElementById("person-dob").value;
  const time = document.getElementById("person-time").value;
  const placeText = document.getElementById("person-place").value.trim();
  if (!dob) throw new Error("Date of birth is required.");
  if (!time) throw new Error("Birth time is required.");
  if (!placeText) throw new Error("Place of birth is required.");
  const sp = state.place;
  const place = sp && sp.label === placeText
    ? { label: sp.label, lat: sp.lat, lon: sp.lon, timezone: sp.timezone }
    : { query: placeText };

  const yearLengthElement = document.getElementById("dasha-year-length");
  const year_length = yearLengthElement ? parseFloat(yearLengthElement.value) : null;

  return { name: name || null, dob, time, time_accuracy: "exact", place, year_length };
}

// ===== PROMPT BUILDERS =====

const SYS = `You are an expert Vedic astrologer with 30+ years of experience. Parashari system, Lahiri Ayanamsa, Whole Sign houses. Use ONLY the chart data provided. Be direct and practical. Use simple language.`;

function chartData(data) {
  const c = data.chart;
  const planets = Object.entries(c.planets)
    .map(([p, d]) => {
      const type = d.is_benefic ? "Benefic" : "Malefic";
      return `${fmt(p)} (${type}): ${d.sign} H${d.house} ${d.degree.toFixed(1)}° ${d.nakshatra}${d.retro ? " [R]" : ""}`;
    })
    .join("\n");
  const transits = Object.entries(c.transits)
    .map(([p, d]) => `${fmt(p)}: ${d.sign} ${d.degree.toFixed(1)}° H${d.transit_house}${d.retro ? " [R]" : ""}`)
    .join("\n");
  const da = c.dasha.current;
  const yogasStr = (c.yogas || []).map(y => `- ${y.name} (${y.strength}): ${y.description}`).join("\n") || "None";
  return `Birth: ${c.meta.local_datetime} at ${c.meta.place_name} (Ayanamsa: ${c.meta.ayanamsa}, Dasha Year Length: ${c.meta.year_length || '365.24 days'})
Lagna: ${c.core_identity.lagna} | Moon: ${c.core_identity.moon_sign} | Sun: ${c.core_identity.sun_sign}
Nakshatra: ${c.core_identity.nakshatra} (Pada ${c.core_identity.nakshatra_pada})

Planets:
${planets}

Planet Strength: ${JSON.stringify(c.planet_strength)}

Yogas:
${yogasStr}

Current Dasha: ${da.mahadasha}/${da.antardasha} (${da.start} to ${da.end})

Current Transits:
${transits}

House Scores: Wealth ${c.house_scores.wealth_2nd.score}/10 | Marriage ${c.house_scores.marriage_7th.score}/10 | Career ${c.house_scores.career_10th.score}/10 | Gains ${c.house_scores.gains_11th.score}/10`;
}

function buildPrompt(data) {
  const today = new Date();
  const monthNames = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  const todayStr = today.toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" });
  const monthStr = `${monthNames[today.getMonth()]} ${today.getFullYear()}`;
  const yearStr = `${today.getFullYear()}`;

  if (MODE === "daily") return buildDailyPrompt(data, todayStr);
  if (MODE === "monthly") return buildMonthlyPrompt(data, monthStr);
  return buildYearlyPrompt(data, yearStr);
}

function buildDailyPrompt(data, todayStr) {
  return `${SYS}

IMPORTANT: Keep your response under 100 words. Be concise — bullet points only, no paragraphs.

====== CHART DATA ======

${chartData(data)}

Today's date: ${todayStr}

====== REQUEST ======

Give today's daily guidance in under 100 words. Cover ONLY these in 1-2 bullet points each:

- 🌟 **Today's Energy**: One-line overall vibe
- ✅ **Do**: 2 things to do today
- 🚫 **Avoid**: 2 things to avoid today
- 💰 **Money**: One-line financial tip
- ❤️ **Relationships**: One-line tip
- 💪 **Health**: One-line tip
- 🎯 **Lucky**: Color, number, direction`;
}

function buildMonthlyPrompt(data, monthStr) {
  return `${SYS}

IMPORTANT: Keep your response under 200 words. Use short bullet points, no long paragraphs.

====== CHART DATA ======

${chartData(data)}

Current month: ${monthStr}

====== REQUEST ======

Give this month's forecast in under 200 words. Cover each area in 2-3 bullet points:

## 🌙 ${monthStr} — Monthly Forecast

- **📊 Overall Month Rating**: One line — Good / Average / Challenging and why
- **✅ Things to DO this month**: 3 specific actions
- **🚫 Things to AVOID this month**: 3 specific warnings
- **💼 Career & Work**: What to expect, any opportunities or problems?
- **💰 Money & Finance**: Spending, saving, investments — brief
- **❤️ Relationships & Love**: How is love/social life this month?
- **💪 Health**: What to watch out for, one quick remedy
- **📅 Key Dates**: 2-3 important dates this month (good or bad) based on transits
- **🎯 Month's Mantra**: One motivational line based on chart`;
}

function buildYearlyPrompt(data, yearStr) {
  return `${SYS}

Keep your response structured and practical. Use bullet points. Max 500 words.

====== CHART DATA ======

${chartData(data)}

Year: ${yearStr}

====== REQUEST ======

Give a complete yearly forecast for ${yearStr}.

## 🗓️ ${yearStr} — Yearly Forecast

### 📊 Year Rating: __/10
One-line summary of what kind of year this will be.

### 💼 Career & Work
- Major career shifts, promotions, or challenges this year
- Best months for career moves
- Months to be careful

### 💰 Money & Finance
- Overall financial trend (growth / stable / tight)
- Best months for investments or big purchases
- Months to avoid financial risks

### ❤️ Love & Relationships
- Relationship energy this year
- Best period for marriage / new relationships
- Potential conflicts and how to handle them

### 💪 Health
- Health vulnerabilities this year
- Best and worst months for health
- One key remedy or habit to adopt

### 👨‍👩‍👧 Family
- Family dynamics — harmony or tensions?
- Any family events (property, travel, celebrations)?

### ✅ Year's Top 5 DO's
5 specific actions for the year

### 🚫 Year's Top 5 DON'Ts
5 specific things to avoid

### 📅 Quarter-by-Quarter Breakdown
- **Q1 (Jan-Mar)**: 2-line summary
- **Q2 (Apr-Jun)**: 2-line summary
- **Q3 (Jul-Sep)**: 2-line summary
- **Q4 (Oct-Dec)**: 2-line summary

### 🎯 Year's Key Message
One powerful takeaway for the entire year.`;
}

// ===== UTILITIES =====

function showStatus(msg, err = false) {
  el.status.textContent = msg;
  el.status.style.color = err ? "var(--warning)" : "var(--muted)";
}

function setBusy(busy, msg = "") {
  el.generateBtn.disabled = busy;
  if (msg) showStatus(msg);
}

function fmt(v) { return v.replaceAll("_", " ").replace(/\b\w/g, l => l.toUpperCase()); }

function esc(v) { return v.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;"); }
