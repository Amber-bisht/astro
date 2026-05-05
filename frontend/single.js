const state = {
  place: null,
  chartData: null,
  savedProfiles: [],
};

const el = {
  status: document.getElementById("status-message"),
  generateBtn: document.getElementById("generate-btn"),
  copyBtn: document.getElementById("copy-btn"),
  chartPanel: document.getElementById("chart-panel"),
  chartHeading: document.getElementById("chart-heading"),
  metaPill: document.getElementById("meta-pill"),
  metaSummary: document.getElementById("meta-summary"),
  personMetaText: document.getElementById("person-meta-text"),
  chartContent: document.getElementById("chart-content"),
  jsonOutput: document.getElementById("json-output"),
  profileSelect: document.getElementById("person-profile-select"),
  aiPromptsPanel: document.getElementById("ai-prompts-panel"),
  promptCardsGrid: document.getElementById("prompt-cards-grid"),
  promptPreviewContainer: document.getElementById("prompt-preview-container"),
  promptPreviewTitle: document.getElementById("prompt-preview-title"),
  promptPreviewText: document.getElementById("prompt-preview-text"),
  promptCopyBtn: document.getElementById("prompt-copy-btn"),
};

boot();

function boot() {
  setupPlaceAutocomplete();
  el.generateBtn.addEventListener("click", handleGenerate);
  el.copyBtn.addEventListener("click", handleCopy);
  el.profileSelect.addEventListener("change", () => handleProfileChange(el.profileSelect.value));
  refreshProfiles();
}

function setupPlaceAutocomplete() {
  const placeInput = document.getElementById("person-place");
  const suggestions = document.getElementById("person-suggestions");
  let timer;

  placeInput.addEventListener("input", () => {
    state.place = null;
    clearTimeout(timer);
    const query = placeInput.value.trim();
    if (query.length < 2) {
      suggestions.classList.add("hidden");
      suggestions.innerHTML = "";
      return;
    }
    timer = setTimeout(async () => {
      try {
        const response = await fetch(`/places/autocomplete?q=${encodeURIComponent(query)}`);
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || payload.error || "Autocomplete unavailable.");
        renderSuggestions(payload.results || []);
      } catch (error) {
        showStatus(error.message, true);
      }
    }, 280);
  });

  placeInput.addEventListener("blur", () => {
    setTimeout(() => suggestions.classList.add("hidden"), 120);
  });
}

function renderSuggestions(results) {
  const suggestions = document.getElementById("person-suggestions");
  if (!results.length) {
    suggestions.classList.add("hidden");
    suggestions.innerHTML = "";
    return;
  }
  suggestions.innerHTML = results
    .map((r, i) => `<button type="button" class="suggestion" data-index="${i}">${escapeHtml(r.label)}</button>`)
    .join("");
  suggestions.classList.remove("hidden");

  suggestions.querySelectorAll(".suggestion").forEach((btn) => {
    btn.addEventListener("click", () => {
      const result = results[Number(btn.dataset.index)];
      state.place = result;
      document.getElementById("person-place").value = result.label;
      suggestions.classList.add("hidden");
    });
  });
}

async function handleGenerate() {
  try {
    setBusy(true, "Generating birth chart…");
    const payload = collectPerson();
    const response = await fetchJson("/single-chart", payload);
    state.chartData = response;
    renderChart(response);
    renderPromptPanel(response);
    el.copyBtn.disabled = false;
    showStatus("Birth chart generated.");

    // Auto-save profile if logged in and name is provided
    if (payload.name && typeof AUTH !== "undefined" && AUTH.isLoggedIn()) {
      try {
        await fetch("/profiles", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } catch { /* silent fail */ }
    }
    refreshProfiles();
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    setBusy(false);
  }
}

async function handleCopy() {
  if (!state.chartData) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(state.chartData, null, 2));
    showStatus("Full JSON copied to clipboard.");
  } catch {
    showStatus("Clipboard copy failed.", true);
  }
}

function collectPerson() {
  const name = document.getElementById("person-name").value.trim();
  const dob = document.getElementById("person-dob").value;
  const time = document.getElementById("person-time").value;
  const placeText = document.getElementById("person-place").value.trim();

  if (!dob) throw new Error("Date of birth is required.");
  if (!time) throw new Error("Birth time is required.");
  if (!placeText) throw new Error("Place of birth is required.");

  const selectedPlace = state.place;
  const place =
    selectedPlace && selectedPlace.label === placeText
      ? { label: selectedPlace.label, lat: selectedPlace.lat, lon: selectedPlace.lon, timezone: selectedPlace.timezone }
      : { query: placeText };

  return { name: name || null, dob, time, time_accuracy: "exact", place };
}

function renderChart(data) {
  const chart = data.chart;
  el.chartPanel.classList.remove("hidden");
  el.chartHeading.textContent = chart.meta.place_name || "Birth Chart";
  el.metaPill.textContent = chart.meta.time_accuracy;

  el.metaSummary.classList.remove("hidden");
  el.personMetaText.innerHTML = `
    <strong>${escapeHtml(data.meta.label)}</strong><br>
    <small>
      ${data.meta.lat.toFixed(4)}N, ${data.meta.lon.toFixed(4)}E | ${escapeHtml(data.meta.timezone)}
      ${data.meta.is_lmt ? ' | <span class="pill" style="font-size:0.6rem;padding:2px 6px">LMT</span>' : ""}
    </small>
  `;

  el.chartContent.innerHTML = renderPersonResult(chart);
  el.jsonOutput.textContent = JSON.stringify(data, null, 2);
}

function renderPersonResult(chart) {
  const planetsRows = Object.entries(chart.planets)
    .map(([planet, d]) => `
      <tr>
        <td>${formatLabel(planet)}</td>
        <td>${escapeHtml(d.sign)}</td>
        <td>${d.house}</td>
        <td>${d.degree}</td>
        <td>${escapeHtml(d.nakshatra)}</td>
        <td>${d.pada}</td>
      </tr>
    `)
    .join("");

  const housesRows = Object.entries(chart.houses)
    .map(([house, d]) => `
      <tr>
        <td>${house}</td>
        <td>${escapeHtml(d.sign)}</td>
        <td>${escapeHtml(d.lord)}</td>
        <td>${escapeHtml((d.occupants || []).join(", ") || "None")}</td>
      </tr>
    `)
    .join("");

  return `
    <article class="result-card">
      <div class="card-header">
        <div>
          <p class="eyebrow">Birth Chart</p>
          <h3>${escapeHtml(chart.meta.place_name || "Chart")}</h3>
        </div>
        <div style="display:flex; gap:8px;">
          <span class="pill">${escapeHtml(chart.meta.time_accuracy)}</span>
          ${chart.meta.is_lmt ? '<span class="pill" style="background:rgba(187,108,47,0.15);border-color:var(--warning);color:var(--warning);">LMT</span>' : ""}
        </div>
      </div>

      <div class="summary-grid">
        ${summaryItem("Lagna", chart.core_identity.lagna)}
        ${summaryItem("Moon Sign", chart.core_identity.moon_sign)}
        ${summaryItem("Sun Sign", chart.core_identity.sun_sign)}
        ${summaryItem("Nakshatra", `${chart.core_identity.nakshatra} (Pada ${chart.core_identity.nakshatra_pada})`)}
        ${summaryItem("Tithi", chart.core_identity.tithi)}
        ${summaryItem("Yoga", chart.core_identity.yoga)}
      </div>

      ${renderWarnings(chart.meta.warnings || [])}

      <div class="section-stack">
        <div>
          <h3>Planets</h3>
          <div class="table-wrapper">
            <table>
              <thead><tr><th>Planet</th><th>Sign</th><th>House</th><th>Degree</th><th>Nakshatra</th><th>Pada</th></tr></thead>
              <tbody>${planetsRows}</tbody>
            </table>
          </div>
        </div>
        <div>
          <h3>Houses</h3>
          <div class="table-wrapper">
            <table>
              <thead><tr><th>House</th><th>Sign</th><th>Lord</th><th>Occupants</th></tr></thead>
              <tbody>${housesRows}</tbody>
            </table>
          </div>
        </div>

        <div class="dosha-grid">
          <h3>Doshas</h3>
          <div class="dosha-card">
            <strong>Manglik:</strong>
            ${chart.doshas.manglik.present ? "Present" : "Not present"} |
            Mars House ${chart.doshas.manglik.mars_house} |
            Severity ${chart.doshas.manglik.severity} |
            Cancellation ${chart.doshas.manglik.cancellation ? "Yes" : "No"}
          </div>
          <div class="dosha-card">
            <strong>Nadi:</strong> ${chart.doshas.nadi.type}
          </div>
        </div>

        <div class="dosha-grid">
          <h3>House Scores</h3>
          ${renderHouseScore("2nd House Wealth", chart.house_scores.wealth_2nd)}
          ${renderHouseScore("7th House Marriage", chart.house_scores.marriage_7th)}
          ${renderHouseScore("10th House Career", chart.house_scores.career_10th)}
          ${renderHouseScore("11th House Gains", chart.house_scores.gains_11th)}
        </div>

        <div class="dosha-grid">
          <h3>Aspects (Drishti)</h3>
          ${renderAspects(chart.aspects)}
        </div>

        <div class="dosha-grid">
          <h3>Navamsa (D9)</h3>
          ${renderNavamsa(chart.navamsa)}
        </div>

        <div class="dosha-grid">
          <h3>Transits (Current)</h3>
          ${renderTransits(chart.transits)}
        </div>

        <div class="dosha-grid">
          <h3>Dasha</h3>
          <div class="dosha-card">
            <strong>Current:</strong>
            ${chart.dasha.current.mahadasha} / ${chart.dasha.current.antardasha}
            (${chart.dasha.current.start} to ${chart.dasha.current.end})
          </div>
          <div class="dosha-card">
            <strong>Marriage Window:</strong> ${chart.derived_windows.marriage_window.join(" - ")}
          </div>
          <div class="dosha-card">
            <strong>Career Peak:</strong> ${chart.derived_windows.career_peak.join(" - ")}
          </div>
        </div>
      </div>
    </article>
  `;
}

function renderWarnings(warnings) {
  if (!warnings.length) return "";
  return `<div class="warning-stack">${warnings.map((w) => `<div class="warning-chip">${escapeHtml(w)}</div>`).join("")}</div>`;
}

function summaryItem(label, value) {
  return `<div class="summary-item"><div class="summary-label">${escapeHtml(label)}</div><div class="summary-value">${escapeHtml(String(value))}</div></div>`;
}

function renderHouseScore(label, hs) {
  const aspectedBy = hs.aspected_by.length ? hs.aspected_by.join(", ") : "None";
  const occupants = hs.occupants.length ? hs.occupants.join(", ") : "None";
  return `
    <div class="dosha-card">
      <strong>${escapeHtml(label)}:</strong> ${hs.score} / 10<br>
      <small class="muted">
        Lord: ${escapeHtml(hs.lord)} (${escapeHtml(hs.lord_strength)}) in H${hs.lord_house}<br>
        Occupants: ${escapeHtml(occupants)}<br>
        Aspected by: ${escapeHtml(aspectedBy)}
      </small>
    </div>
  `;
}

function renderAspects(aspects) {
  return Object.entries(aspects.aspects_given)
    .map(([planet, houses]) => `
      <div class="dosha-card">
        <strong>${formatLabel(planet)}:</strong> aspects H${houses.join(", H")}
      </div>
    `)
    .join("");
}

function renderNavamsa(navamsa) {
  const ascCard = `<div class="dosha-card"><strong>D9 Lagna:</strong> ${escapeHtml(navamsa.ascendant.sign)} (${navamsa.ascendant.degree}°)</div>`;
  const planetCards = Object.entries(navamsa.planets)
    .map(([planet, d]) => `
      <div class="dosha-card">
        <strong>${formatLabel(planet)}:</strong>
        ${escapeHtml(d.sign)} (H${d.navamsa_house})
        <small class="muted">${escapeHtml(d.strength)}</small>
      </div>
    `)
    .join("");
  return ascCard + planetCards;
}

function renderTransits(transits) {
  return Object.entries(transits)
    .map(([planet, d]) => `
      <div class="dosha-card">
        <strong>${formatLabel(planet)}:</strong>
        ${escapeHtml(d.sign)} ${d.degree}° (H${d.transit_house})
        ${d.retro ? '<span class="pill" style="font-size:0.7rem">R</span>' : ""}<br>
        <small class="muted">${escapeHtml(d.nakshatra)} Pada ${d.pada}</small>
      </div>
    `)
    .join("");
}

// ===== PROFILES =====

async function refreshProfiles() {
  try {
    const response = await fetch("/profiles");
    const data = await response.json();
    state.savedProfiles = data.profiles || [];
    populateProfileSelect();
  } catch (error) {
    console.error("Failed to fetch profiles:", error);
  }
}

function populateProfileSelect() {
  const select = el.profileSelect;
  const currentValue = select.value;
  select.innerHTML =
    '<option value="">-- Select a saved profile --</option>' +
    state.savedProfiles
      .map((p) => `<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)} (${p.dob})</option>`)
      .join("");
  select.value = currentValue;
}

function handleProfileChange(profileName) {
  if (!profileName) return;
  const profile = state.savedProfiles.find((p) => p.name === profileName);
  if (!profile) return;

  document.getElementById("person-name").value = profile.name || "";
  document.getElementById("person-dob").value = profile.dob || "";
  document.getElementById("person-time").value = profile.time || "";

  const placeInput = document.getElementById("person-place");
  if (typeof profile.place === "object") {
    state.place = profile.place;
    placeInput.value = profile.place.label || profile.place.query || "";
  } else {
    state.place = null;
    placeInput.value = profile.place || "";
  }
}

// ===== AI PROMPTS =====

const SYSTEM_PROMPT = `You are an expert Vedic astrologer with 30+ years of experience. You follow the Parashari system with Lahiri ayanamsa and Whole Sign house system.

RULES:
1. Use ONLY the provided chart data. Do not assume or invent any planetary positions.
2. Always consider BOTH natal (D1) and Navamsa (D9) charts together.
3. Factor in planetary aspects (Drishti) when analyzing any house.
4. Consider current transits for timing predictions.
5. Be direct and honest — do not sugarcoat bad placements.
6. Rate every analysis section with: ⭐ Excellent / ✅ Good / ⚠️ Average / ❌ Challenging / 🚫 Serious Concern
7. Structure your response with clear headings, bullet points, and ratings.`;

const PROMPT_CATEGORIES = [
  { id: "personality", icon: "🧠", title: "Personality & Nature", desc: "Core traits, strengths, weaknesses", buildPrompt: buildPersonalityPrompt },
  { id: "career", icon: "💼", title: "Career & Wealth", desc: "Professional path and financial outlook", buildPrompt: buildCareerPrompt },
  { id: "marriage", icon: "💍", title: "Marriage & Relationships", desc: "Partnership potential and timing", buildPrompt: buildMarriagePrompt },
  { id: "health", icon: "💪", title: "Health & Longevity", desc: "Health risks and remedies", buildPrompt: buildHealthPrompt },
  { id: "overall", icon: "⚡", title: "Overall Life Analysis", desc: "Complete life reading with all areas", buildPrompt: buildOverallPrompt },
  { id: "lifeblueprint", icon: "🎯", title: "Life Improvement Blueprint", desc: "Score /100, career domain & role, health, personality, love, social, do's & don'ts", buildPrompt: buildLifeBlueprintPrompt },
  { id: "family", icon: "👨‍👩‍👧‍👦", title: "Family & Relationships", desc: "Spouse, children, mother, father, family bonds", buildPrompt: buildFamilyPrompt },
];

let activePromptText = "";

function renderPromptPanel(data) {
  el.aiPromptsPanel.classList.remove("hidden");
  el.promptPreviewContainer.classList.add("hidden");
  activePromptText = "";

  el.promptCardsGrid.innerHTML = PROMPT_CATEGORIES.map(
    (cat) => `
    <div class="prompt-card" data-prompt-id="${cat.id}">
      <div class="prompt-card-icon">${cat.icon}</div>
      <div class="prompt-card-title">${escapeHtml(cat.title)}</div>
      <div class="prompt-card-desc">${escapeHtml(cat.desc)}</div>
    </div>
  `
  ).join("");

  el.promptCardsGrid.querySelectorAll(".prompt-card").forEach((card) => {
    card.addEventListener("click", () => {
      const category = PROMPT_CATEGORIES.find((c) => c.id === card.dataset.promptId);
      if (!category) return;
      el.promptCardsGrid.querySelectorAll(".prompt-card").forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      activePromptText = category.buildPrompt(data);
      el.promptPreviewTitle.textContent = `${category.icon} ${category.title} Prompt`;
      el.promptPreviewText.textContent = activePromptText;
      el.promptPreviewContainer.classList.remove("hidden");
    });
  });

  el.promptCopyBtn.addEventListener("click", async () => {
    if (!activePromptText) return;
    try {
      await navigator.clipboard.writeText(activePromptText);
      const orig = el.promptCopyBtn.textContent;
      el.promptCopyBtn.textContent = "✓ Copied!";
      showStatus("Prompt copied to clipboard!");
      setTimeout(() => { el.promptCopyBtn.textContent = orig; }, 2000);
    } catch {
      showStatus("Clipboard copy failed.", true);
    }
  });
}

// --- Data Extractors ---

function extractCore(chart) {
  return `Lagna: ${chart.core_identity.lagna} (${chart.core_identity.lagna_degree}°)
Moon Sign: ${chart.core_identity.moon_sign}
Sun Sign: ${chart.core_identity.sun_sign}
Nakshatra: ${chart.core_identity.nakshatra} (Pada ${chart.core_identity.nakshatra_pada})
Tithi: ${chart.core_identity.tithi}`;
}

function extractPlanets(chart) {
  return Object.entries(chart.planets)
    .map(([p, d]) => `${formatLabel(p)}: ${d.sign} H${d.house} ${d.degree.toFixed(1)}° ${d.nakshatra}${d.retro ? " [R]" : ""}`)
    .join("\n");
}

function extractHS(hs, label) {
  return `${label}: ${hs.score}/10 | Lord: ${hs.lord} (${hs.lord_strength}) in H${hs.lord_house}
  Occupants: ${hs.occupants.length ? hs.occupants.join(", ") : "None"}
  Aspected by: ${hs.aspected_by.length ? hs.aspected_by.join(", ") : "None"}`;
}

function extractNavamsa(nav) {
  const lines = [`D9 Lagna: ${nav.ascendant.sign}`];
  for (const [p, d] of Object.entries(nav.planets)) lines.push(`${formatLabel(p)}: ${d.sign} H${d.navamsa_house} (${d.strength})`);
  return lines.join("\n");
}

function extractDoshas(chart) {
  const m = chart.doshas.manglik;
  return `Manglik: ${m.present ? "YES" : "No"} | Mars H${m.mars_house} | Severity: ${m.severity} | Cancel: ${m.cancellation ? "Yes" : "No"}
Nadi: ${chart.doshas.nadi.type}`;
}

function extractDasha(chart) {
  const c = chart.dasha.current;
  return `Current: ${c.mahadasha}/${c.antardasha} (${c.start} to ${c.end})
Marriage Window: ${chart.derived_windows.marriage_window.join(" - ")}
Career Peak: ${chart.derived_windows.career_peak.join(" - ")}`;
}

function extractTransits(chart) {
  return Object.entries(chart.transits)
    .map(([p, d]) => `${formatLabel(p)}: ${d.sign} ${d.degree.toFixed(1)}° H${d.transit_house}${d.retro ? " [R]" : ""}`)
    .join("\n");
}

function extractAspectsReceived(aspects, houses) {
  return houses.map((h) => {
    const received = aspects.aspects_received[String(h)] || [];
    const names = received.map((a) => `${a.planet} (${a.type})`).join(", ") || "None";
    return `House ${h} aspected by: ${names}`;
  }).join("\n");
}

// --- Prompt Builders ---

function chartBlock(data) {
  const c = data.chart;
  return `--- BIRTH CHART ---
Birth: ${c.meta.local_datetime} at ${c.meta.place_name}
${extractCore(c)}

All Planets:
${extractPlanets(c)}

Planet Strength: ${JSON.stringify(c.planet_strength)}

${extractAspectsReceived(c.aspects, [1, 2, 5, 7, 8, 10, 11])}

Doshas:
${extractDoshas(c)}

Navamsa (D9):
${extractNavamsa(c.navamsa)}

House Scores:
${extractHS(c.house_scores.wealth_2nd, "2nd Wealth")}
${extractHS(c.house_scores.marriage_7th, "7th Marriage")}
${extractHS(c.house_scores.career_10th, "10th Career")}
${extractHS(c.house_scores.gains_11th, "11th Gains")}

Dasha & Timing:
${extractDasha(c)}

Current Transits:
${extractTransits(c)}`;
}

function buildPersonalityPrompt(data) {
  return `${SYSTEM_PROMPT}\n\n====== CHART DATA ======\n\n${chartBlock(data)}\n\n====== ANALYSIS REQUEST ======\n\nAnalyze the native's personality and core nature:\n\n1. **Lagna Analysis**: What does the ascendant sign and its lord placement reveal about appearance, temperament, and first impression?\n2. **Moon Sign & Nakshatra**: Emotional nature, mental tendencies, and instinctive behavior.\n3. **Sun Sign**: Ego, ambition, authority — how the person projects themselves.\n4. **Key Planetary Yogas**: Any Raj Yoga, Dhana Yoga, or Viparita Yoga present?\n5. **Strengths**: Top 3 planetary strengths and what they give.\n6. **Weaknesses**: Problem areas — afflicted planets, debilitations, combustions.\n7. **D9 Confirmation**: Does Navamsa support or weaken D1 indications?\n8. **Overall Personality Rating**: Rate with tier.`;
}

function buildCareerPrompt(data) {
  return `${SYSTEM_PROMPT}\n\n====== CHART DATA ======\n\n${chartBlock(data)}\n\n====== ANALYSIS REQUEST ======\n\nAnalyze career and wealth prospects:\n\n1. **10th House (Career)**: Sign, lord, occupants, aspects — what profession suits best?\n2. **2nd House (Wealth)**: Earning capacity, family wealth, speech/communication.\n3. **11th House (Gains)**: Income growth, networking, fulfillment of desires.\n4. **Saturn's Role**: Karma karaka analysis — hard work, delays, rewards.\n5. **Career Peak Timing**: Based on Dasha, when are the best career years?\n6. **Financial Periods**: When will wealth accumulate most?\n7. **Current Transit Impact**: How are transits affecting career right now?\n8. **Rating**: Career & wealth tier rating.`;
}

function buildMarriagePrompt(data) {
  return `${SYSTEM_PROMPT}\n\n====== CHART DATA ======\n\n${chartBlock(data)}\n\n====== ANALYSIS REQUEST ======\n\nAnalyze marriage and relationship prospects:\n\n1. **7th House Analysis**: Sign, lord, occupants, aspects — nature of spouse and married life.\n2. **Venus Analysis**: Placement, strength, aspects — romantic nature and attraction.\n3. **Jupiter Analysis**: Wisdom in relationships, for females Jupiter is husband karaka.\n4. **Manglik Dosha**: Is it present? Severity? Cancellation factors?\n5. **D9 (Navamsa) Marriage Indicators**: D9 7th house, Venus in D9, D9 lagna lord.\n6. **Marriage Timing**: Best Dasha periods for marriage.\n7. **Spouse Nature**: Likely characteristics of the spouse based on 7th house.\n8. **Rating**: Marriage prospects tier rating.`;
}

function buildHealthPrompt(data) {
  return `${SYSTEM_PROMPT}\n\n====== CHART DATA ======\n\n${chartBlock(data)}\n\n====== ANALYSIS REQUEST ======\n\nAnalyze health and longevity:\n\n1. **Lagna & Lagna Lord**: Physical constitution and vitality.\n2. **6th House (Disease)**: Chronic health risks, immunity.\n3. **8th House (Longevity)**: Lifespan indicators, sudden events.\n4. **Moon (Mental Health)**: Emotional wellbeing, stress indicators.\n5. **Afflicted Planets**: Which planets are weak and what body parts they govern.\n6. **Current Health Transits**: Any ongoing transit-related health concerns?\n7. **Remedies**: Suggest gemstones, mantras, or lifestyle changes.\n8. **Rating**: Health tier rating.`;
}

function buildOverallPrompt(data) {
  return `${SYSTEM_PROMPT}\n\n====== CHART DATA ======\n\n${chartBlock(data)}\n\n====== ANALYSIS REQUEST ======\n\nGive a COMPREHENSIVE life analysis covering ALL areas:\n\n1. **🧠 Personality** — Core nature, strengths, weaknesses\n2. **💼 Career & Wealth** — Professional path, earning capacity, financial peaks\n3. **💍 Marriage & Relationships** — Spouse nature, timing, married life quality\n4. **👶 Children** — 5th house analysis, progeny prospects, timing\n5. **💪 Health** — Physical and mental health indicators, risks\n6. **⏰ Key Life Periods** — Important Dasha transitions, major life events\n\nFor EACH section, give a clear tier rating:\n⭐ Excellent / ✅ Good / ⚠️ Average / ❌ Challenging / 🚫 Serious Concern\n\n7. **⚡ OVERALL LIFE ASSESSMENT**: Summarize the chart's overall strength, biggest blessings, and areas needing remedies. Be honest and practical.`;
}

function buildLifeBlueprintPrompt(data) {
  return `${SYSTEM_PROMPT}

ADDITIONAL RULES FOR THIS PROMPT:
- Give a LIFE SCORE out of 100 based on overall chart strength.
- Be ACTIONABLE — tell the native exactly what to START DOING from today.
- For career, be PRECISE — suggest specific domains, roles, and company types (startup vs MNC vs govt vs freelance).
- Don't just describe problems — give SOLUTIONS and daily habits.
- Use simple language a 20-year-old can understand.

====== CHART DATA ======

${chartBlock(data)}

====== ANALYSIS REQUEST ======

Create a COMPLETE LIFE IMPROVEMENT BLUEPRINT for this person. Be brutally honest and deeply practical.

## 1. 🏆 OVERALL LIFE SCORE: ___ / 100
Break down into sub-scores:
- Career Potential: __/15
- Wealth & Money: __/15
- Health & Energy: __/15
- Love & Marriage: __/15
- Personality & Charisma: __/10
- Social Life & Network: __/10
- Family Bonds: __/10
- Spiritual Growth: __/10

## 2. 💼 CAREER — Be VERY Precise
- **Best Domains**: List 3-5 specific industries/fields (e.g., "fintech", "data science", "real estate", "healthcare", "content creation").
- **Best Roles**: List specific job titles that suit this chart (e.g., "product manager", "surgeon", "investment banker", "creative director").
- **Work Style**: Should they be in a startup, MNC, government, freelance, or own business? Why?
- **Company Culture Fit**: What kind of boss/team works best? What office politics to watch for?
- **Career Dangers**: What mistakes will they naturally make in career? How to avoid them?
- **What to START doing NOW**: 3 concrete career actions for this month.

## 3. 💪 HEALTH — How to Improve
- **Weak Body Areas**: Which organs/systems are vulnerable based on afflicted planets?
- **Diet Recommendations**: Specific foods to eat and avoid based on planetary constitution.
- **Exercise Type**: What physical activity suits their chart (yoga, gym, swimming, martial arts, running)?
- **Mental Health**: Stress patterns, anxiety triggers, and how to manage them.
- **Sleep & Routine**: Best wake-up time and daily routine based on their ruling planet.
- **What to START doing NOW**: 3 concrete health actions for this week.

## 4. 🧠 PERSONALITY — How to Improve
- **Top 3 Strengths**: What natural gifts to double down on.
- **Top 3 Weaknesses**: What flaws to actively work on (anger, laziness, overthinking, etc.).
- **Communication Style**: How they come across vs how they should communicate.
- **Confidence & Charisma**: Specific tips to boost presence based on Lagna & Sun.
- **Bad Habits to Break**: Planetary patterns that create addictions or negative loops.
- **What to START doing NOW**: 3 personality development actions.

## 5. ❤️ LOVE LIFE — How to Improve
- **Attraction Pattern**: What type of partner they naturally attract (good or bad).
- **Relationship Mistakes**: Common patterns that sabotage their love life.
- **Ideal Partner Traits**: What to look for based on 7th house and Venus.
- **Red Flags to Avoid**: Types of partners that will cause suffering.
- **Romance Tips**: How to be a better partner based on their Venus & Moon.
- **What to START doing NOW**: 3 actions to improve love life.

## 6. 🤝 SOCIAL LIFE — How to Improve
- **Natural Social Style**: Introvert/extrovert/ambivert tendencies from chart.
- **Networking Strength**: 11th house analysis — how to grow their circle.
- **Friend Quality**: Do they attract genuine friends or users? How to filter.
- **Public Image**: How others perceive them vs reality.
- **What to START doing NOW**: 3 social life actions.

## 7. 🏠 FAMILY BONDS — Quick Overview
- **Relationship with Parents**: 4th house (mother) and 9th/10th house (father) brief analysis.
- **How to Strengthen Family Ties**: Practical tips.

## 8. ✅ MASTER DO's LIST (Top 10)
List the 10 most important things this person MUST do based on their chart. Be specific (e.g., "Wear a yellow sapphire on Thursday", "Wake up before 6 AM", "Avoid partnerships in business").

## 9. 🚫 MASTER DON'Ts LIST (Top 10)
List the 10 things this person must ABSOLUTELY AVOID. Be specific (e.g., "Never invest in speculative markets during Rahu Dasha", "Avoid alcohol — Moon is weak", "Don't take loans between ages 28-32").

## 10. 📅 NEXT 12 MONTHS — Action Plan
Based on current Dasha + Transits, what should they focus on in the next 12 months? Month-by-month is ideal, or at least quarter-by-quarter.`;
}

function buildFamilyPrompt(data) {
  return `${SYSTEM_PROMPT}

ADDITIONAL RULES FOR THIS PROMPT:
- Analyze EACH family member separately with dedicated sections.
- Be specific about the NATURE, BEHAVIOR, and RELATIONSHIP DYNAMICS.
- Give practical advice on how to improve each relationship.
- Include timing of key family events.

====== CHART DATA ======

${chartBlock(data)}

====== ANALYSIS REQUEST ======

Give a DEEP ANALYSIS of family and close relationships based on this birth chart.

## 1. 💍 SPOUSE / WIFE / HUSBAND — Detailed Analysis
- **Spouse Appearance & Nature**: Based on 7th house sign, lord, and Venus — what will the spouse look like? Personality traits?
- **Spouse Family Background**: 7th lord placement — wealthy family? Educated? Traditional or modern?
- **Spouse Career**: Will the spouse be working? In what field?
- **Married Life Quality**: Day-to-day married life — harmonious or conflicted? Reasons.
- **Physical Intimacy**: 8th house and Mars/Venus analysis for romantic and physical compatibility.
- **Potential Problems in Marriage**: What issues will arise? In-law problems? Trust issues? Financial disagreements?
- **Divorce/Separation Risk**: Any indicators? How to prevent them.
- **How to Be a Better Spouse**: Based on chart weaknesses, what should this person work on?
- **Best Marriage Age/Period**: Precise Dasha-based timing.
- **Rating**: ⭐/✅/⚠️/❌/🚫

## 2. 👶 CHILDREN — Detailed Analysis
- **Number of Children**: Traditional indicators from 5th house.
- **Gender Indicators**: Any lean towards sons or daughters?
- **First Child Timing**: Based on 5th house lord Dasha periods.
- **Children's Nature**: What kind of children will they have? Obedient, rebellious, talented?
- **Children's Success**: Will children be successful? In which fields?
- **Relationship with Children**: Close bond or distant? Communication issues?
- **Challenges with Children**: Health concerns, behavioral issues, or delays in childbirth.
- **How to Be a Better Parent**: Chart-based parenting advice.
- **Rating**: ⭐/✅/⚠️/❌/🚫

## 3. 👩 MOTHER — Detailed Analysis (4th House)
- **Mother's Nature & Health**: Based on 4th house and Moon.
- **Relationship Quality**: Is the bond with mother strong or strained? Why?
- **Mother's Influence**: How has the mother shaped this person's personality and decisions?
- **Mother's Health Concerns**: Any planetary indicators for mother's health issues?
- **How to Strengthen This Bond**: Practical remedies and behavioral changes.
- **Rating**: ⭐/✅/⚠️/❌/🚫

## 4. 👨 FATHER — Detailed Analysis (9th & 10th House)
- **Father's Nature & Career**: Based on 9th house, 10th house, and Sun.
- **Relationship Quality**: Close and supportive or distant and authoritarian?
- **Father's Financial Status**: Did/will father provide financial stability?
- **Father's Health Concerns**: Sun afflictions and 9th house analysis.
- **Inheritance & Property**: Will this person inherit from father? 4th house + 8th house.
- **How to Strengthen This Bond**: Practical advice.
- **Rating**: ⭐/✅/⚠️/❌/🚫

## 5. 👫 SIBLINGS — Brief Analysis (3rd House)
- **Number of Siblings**: Indicators from 3rd house.
- **Relationship Quality**: Supportive or rivalry?
- **Sibling Success**: Will siblings be successful?

## 6. 🏡 OVERALL FAMILY HAPPINESS
- **4th House Sukha (Happiness)**: Overall domestic peace and comfort.
- **Property & Home**: Will they own property? When?
- **Joint Family vs Nuclear**: What setup works better for this chart?
- **Family Reputation**: 10th house influence on family standing in society.

## 7. 💎 REMEDIES FOR FAMILY HARMONY
- **Gemstones**: Specific stones to strengthen family relationships.
- **Mantras**: Daily recitations for family peace.
- **Behavioral Changes**: 3 things to change immediately to improve family bonds.
- **Auspicious Activities**: Specific rituals or donations that strengthen family karma.`;
}

// ===== UTILITIES =====

async function fetchJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || data.error || "Request failed.");
  return data;
}

function showStatus(message, isError = false) {
  el.status.textContent = message;
  el.status.style.color = isError ? "var(--warning)" : "var(--muted)";
}

function setBusy(isBusy, message = "") {
  el.generateBtn.disabled = isBusy;
  if (message) showStatus(message);
}

function formatLabel(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

function escapeHtml(value) {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}
