const state = {
  places: { boy: null, girl: null },
  fullData: null,
  savedProfiles: [],
};

const elements = {
  status: document.getElementById("status-message"),
  compatibilityPanel: document.getElementById("compatibility-panel"),
  scoreHeading: document.getElementById("score-heading"),
  verdictPill: document.getElementById("verdict-pill"),
  scoreProgress: document.getElementById("score-progress"),
  breakdownBody: document.getElementById("breakdown-body"),
  compatibilityWarnings: document.getElementById("compatibility-warnings"),
  fullDataPanel: document.getElementById("full-data-panel"),
  fullDataContent: document.getElementById("full-data-content"),
  jsonOutput: document.getElementById("json-output"),
  copyButton: document.getElementById("copy-btn"),
  calculateButton: document.getElementById("calculate-btn"),
  fullDataButton: document.getElementById("full-data-btn"),
  metaSummaryGrid: document.getElementById("meta-summary-grid"),
  boyMetaText: document.getElementById("boy-meta-text"),
  girlMetaText: document.getElementById("girl-meta-text"),
  boyProfileSelect: document.getElementById("boy-profile-select"),
  girlProfileSelect: document.getElementById("girl-profile-select"),
  aiPromptsPanel: document.getElementById("ai-prompts-panel"),
  promptCardsGrid: document.getElementById("prompt-cards-grid"),
  promptPreviewContainer: document.getElementById("prompt-preview-container"),
  promptPreviewTitle: document.getElementById("prompt-preview-title"),
  promptPreviewText: document.getElementById("prompt-preview-text"),
  promptCopyBtn: document.getElementById("prompt-copy-btn"),
};

const persons = ["boy", "girl"];

boot();

function boot() {
  persons.forEach(setupPersonForm);
  elements.calculateButton.addEventListener("click", handleCompatibility);
  elements.fullDataButton.addEventListener("click", handleFullData);
  elements.copyButton.addEventListener("click", handleCopy);
  refreshProfiles();
}

function setupPersonForm(person) {
  const placeInput = document.getElementById(`${person}-place`);
  const suggestions = document.getElementById(`${person}-suggestions`);
  const timeInput = document.getElementById(`${person}-time`);
  const profileSelect = document.getElementById(`${person}-profile-select`);

  profileSelect.addEventListener("change", () => handleProfileChange(person, profileSelect.value));

  let timer;
  placeInput.addEventListener("input", () => {
    state.places[person] = null;
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
        if (!response.ok) {
          throw new Error(payload.detail || payload.error || "Autocomplete is unavailable.");
        }
        renderSuggestions(person, payload.results || []);
      } catch (error) {
        showStatus(error.message, true);
      }
    }, 280);
  });

  placeInput.addEventListener("blur", () => {
    setTimeout(() => suggestions.classList.add("hidden"), 120);
  });
}

function renderSuggestions(person, results) {
  const suggestions = document.getElementById(`${person}-suggestions`);
  if (!results.length) {
    suggestions.classList.add("hidden");
    suggestions.innerHTML = "";
    return;
  }

  suggestions.innerHTML = results
    .map(
      (result, index) =>
        `<button type="button" class="suggestion" data-person="${person}" data-index="${index}">${escapeHtml(result.label)}</button>`
    )
    .join("");
  suggestions.classList.remove("hidden");

  suggestions.querySelectorAll(".suggestion").forEach((button) => {
    button.addEventListener("click", () => {
      const result = results[Number(button.dataset.index)];
      state.places[person] = result;
      document.getElementById(`${person}-place`).value = result.label;
      suggestions.classList.add("hidden");
    });
  });
}

async function handleCompatibility() {
  try {
    setBusy(true, "Calculating compatibility...");
    const payload = collectPayload();
    const response = await fetchJson("/guna-milan", payload);
    renderCompatibility(response);
    showStatus("Compatibility calculated.");
    refreshProfiles(); // Refresh in case new profile was auto-saved
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    setBusy(false);
  }
}

async function handleFullData() {
  try {
    setBusy(true, "Generating validated chart data...");
    const payload = collectPayload();
    const response = await fetchJson("/full-data", payload);
    state.fullData = response;
    renderFullData(response);
    renderPromptPanel(response);
    elements.copyButton.disabled = false;
    showStatus("Full chart data generated.");
    refreshProfiles(); // Refresh in case new profile was auto-saved
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    setBusy(false);
  }
}

async function handleCopy() {
  if (!state.fullData) {
    return;
  }
  try {
    await navigator.clipboard.writeText(JSON.stringify(state.fullData, null, 2));
    showStatus("Full JSON copied to clipboard.");
  } catch (error) {
    showStatus("Clipboard copy failed. Your browser may block clipboard access.", true);
  }
}

function collectPayload() {
  return {
    boy: collectPerson("boy"),
    girl: collectPerson("girl"),
  };
}

function collectPerson(person) {
  const name = document.getElementById(`${person}-name`).value.trim();
  const dob = document.getElementById(`${person}-dob`).value;
  const timeInput = document.getElementById(`${person}-time`);
  const placeText = document.getElementById(`${person}-place`).value.trim();

  if (!dob) {
    throw new Error(`${capitalize(person)} date of birth is required.`);
  }
  if (!timeInput.value) {
    throw new Error(`${capitalize(person)} birth time is required.`);
  }
  if (!placeText) {
    throw new Error(`${capitalize(person)} place of birth is required.`);
  }

  const selectedPlace = state.places[person];
  const place =
    selectedPlace && selectedPlace.label === placeText
      ? {
          label: selectedPlace.label,
          lat: selectedPlace.lat,
          lon: selectedPlace.lon,
          timezone: selectedPlace.timezone,
        }
      : { query: placeText };

  return {
    name: name || null,
    gender: person === "boy" ? "male" : "female",
    dob,
    time: timeInput.value,
    time_accuracy: "exact",
    place,
  };
}

function renderCompatibility(data) {
  elements.compatibilityPanel.classList.remove("hidden");
  elements.scoreHeading.textContent = `${data.score} / ${data.max_score}`;
  elements.verdictPill.textContent = data.verdict;
  elements.scoreProgress.style.width = `${(data.score / data.max_score) * 100}%`;

  // Render Meta Summary
  elements.metaSummaryGrid.classList.remove("hidden");
  elements.boyMetaText.innerHTML = `
    ${escapeHtml(data.boy_meta.label)}<br>
    <small>${data.boy_meta.lat.toFixed(4)}N, ${data.boy_meta.lon.toFixed(4)}E | ${escapeHtml(data.boy_meta.timezone)}</small>
  `;
  elements.girlMetaText.innerHTML = `
    ${escapeHtml(data.girl_meta.label)}<br>
    <small>${data.girl_meta.lat.toFixed(4)}N, ${data.girl_meta.lon.toFixed(4)}E | ${escapeHtml(data.girl_meta.timezone)}</small>
  `;

  // Render Detailed Table
  elements.breakdownBody.innerHTML = Object.entries(data.breakdown)
    .map(([key, details]) => `
      <tr>
        <td><strong>${formatLabel(key)}</strong></td>
        <td>${escapeHtml(String(details.boy))}</td>
        <td>${escapeHtml(String(details.girl))}</td>
        <td>${details.max}</td>
        <td><strong style="color: ${details.obtained === 0 ? "var(--warning)" : "inherit"}">${details.obtained}</strong></td>
        <td class="muted" style="font-size: 0.85rem">${escapeHtml(details.area)}</td>
      </tr>
    `)
    .join("");

  const warnings = data.warnings || [];
  elements.compatibilityWarnings.innerHTML = warnings.map((warning) => `<div class="warning-chip">${escapeHtml(warning)}</div>`).join("");
  elements.compatibilityWarnings.classList.toggle("hidden", warnings.length === 0);
}

function renderFullData(data) {
  elements.fullDataPanel.classList.remove("hidden");
  elements.fullDataContent.innerHTML = persons.map((person) => renderPersonResult(person, data[person])).join("");
  elements.jsonOutput.textContent = JSON.stringify(data, null, 2);
}

function renderPersonResult(person, chart) {
  const planetsRows = Object.entries(chart.planets)
    .map(
      ([planet, details]) => `
        <tr>
          <td>${formatLabel(planet)}</td>
          <td>${escapeHtml(details.sign)}</td>
          <td>${details.house}</td>
          <td>${details.degree}</td>
          <td>${escapeHtml(details.nakshatra)}</td>
          <td>${details.pada}</td>
        </tr>
      `
    )
    .join("");

  const housesRows = Object.entries(chart.houses)
    .map(
      ([house, details]) => `
        <tr>
          <td>${house}</td>
          <td>${escapeHtml(details.sign)}</td>
          <td>${escapeHtml(details.lord)}</td>
          <td>${escapeHtml((details.occupants || []).join(", ") || "None")}</td>
        </tr>
      `
    )
    .join("");

  return `
    <article class="result-card">
      <div class="card-header">
        <div>
          <p class="eyebrow">${capitalize(person)} Chart</p>
          <h3>${escapeHtml(chart.meta.place_name || capitalize(person))}</h3>
        </div>
        <span class="pill">${escapeHtml(chart.meta.time_accuracy)}</span>
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
              <thead>
                <tr>
                  <th>Planet</th>
                  <th>Sign</th>
                  <th>House</th>
                  <th>Degree</th>
                  <th>Nakshatra</th>
                  <th>Pada</th>
                </tr>
              </thead>
              <tbody>${planetsRows}</tbody>
            </table>
          </div>
        </div>

        <div>
          <h3>Houses</h3>
          <div class="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>House</th>
                  <th>Sign</th>
                  <th>Lord</th>
                  <th>Occupants</th>
                </tr>
              </thead>
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
          <div class="dosha-card">
            <strong>Bhakoot:</strong> Distance ${chart.doshas.bhakoot.rashi_distance} |
            ${chart.doshas.bhakoot.compatible ? "Compatible" : "Needs attention"}
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
  if (!warnings.length) {
    return "";
  }
  return `<div class="warning-stack">${warnings.map((warning) => `<div class="warning-chip">${escapeHtml(warning)}</div>`).join("")}</div>`;
}

function summaryItem(label, value) {
  return `
    <div class="summary-item">
      <div class="summary-label">${escapeHtml(label)}</div>
      <div class="summary-value">${escapeHtml(String(value))}</div>
    </div>
  `;
}

async function fetchJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Request failed.");
  }
  return data;
}

function showStatus(message, isError = false) {
  elements.status.textContent = message;
  elements.status.style.color = isError ? "var(--warning)" : "var(--muted)";
}

function setBusy(isBusy, message = "") {
  elements.calculateButton.disabled = isBusy;
  elements.fullDataButton.disabled = isBusy;
  if (message) {
    showStatus(message);
  }
}

async function refreshProfiles() {
  try {
    const response = await fetch("/profiles");
    const data = await response.json();
    state.savedProfiles = data.profiles || [];
    populateProfileSelects();
  } catch (error) {
    console.error("Failed to fetch profiles:", error);
  }
}

function populateProfileSelects() {
  persons.forEach((person) => {
    const select = document.getElementById(`${person}-profile-select`);
    const currentValue = select.value;
    const targetGender = person === "boy" ? "male" : "female";
    
    const filteredProfiles = state.savedProfiles.filter((p) => {
      // If profile has no gender, show it in both (legacy compatibility)
      // If it has gender, filter strictly
      return !p.gender || p.gender === targetGender;
    });

    select.innerHTML = '<option value="">-- Select a saved profile --</option>' +
      filteredProfiles
        .map((p) => `<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)} (${p.dob})</option>`)
        .join("");
    select.value = currentValue;
  });
}

function handleProfileChange(person, profileName) {
  if (!profileName) return;
  const profile = state.savedProfiles.find((p) => p.name === profileName);
  if (!profile) return;

  document.getElementById(`${person}-name`).value = profile.name || "";
  document.getElementById(`${person}-dob`).value = profile.dob || "";
  document.getElementById(`${person}-time`).value = profile.time || "";
  
  const placeInput = document.getElementById(`${person}-place`);
  if (typeof profile.place === "object") {
    state.places[person] = profile.place;
    placeInput.value = profile.place.label || profile.place.query || "";
  } else {
    state.places[person] = null;
    placeInput.value = profile.place || "";
  }
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
  const ascCard = `
    <div class="dosha-card">
      <strong>D9 Lagna:</strong> ${escapeHtml(navamsa.ascendant.sign)} (${navamsa.ascendant.degree}°)
    </div>
  `;
  const planetCards = Object.entries(navamsa.planets)
    .map(([planet, details]) => `
      <div class="dosha-card">
        <strong>${formatLabel(planet)}:</strong>
        ${escapeHtml(details.sign)} (H${details.navamsa_house})
        <small class="muted">${escapeHtml(details.strength)}</small>
      </div>
    `)
    .join("");
  return ascCard + planetCards;
}

function renderTransits(transits) {
  return Object.entries(transits)
    .map(([planet, details]) => `
      <div class="dosha-card">
        <strong>${formatLabel(planet)}:</strong>
        ${escapeHtml(details.sign)} ${details.degree}° (H${details.transit_house})
        ${details.retro ? '<span class="pill" style="font-size:0.7rem">R</span>' : ""}<br>
        <small class="muted">${escapeHtml(details.nakshatra)} Pada ${details.pada}</small>
      </div>
    `)
    .join("");
}

// ============================================================
// AI PROMPT GENERATOR SYSTEM
// ============================================================

const SYSTEM_PROMPT = `You are an expert Vedic astrologer with 30+ years of experience in marriage compatibility analysis (Kundali Milan). You follow the Parashari system with Lahiri ayanamsa and Whole Sign house system.

RULES:
1. Use ONLY the provided chart data. Do not assume or invent any planetary positions.
2. Always consider BOTH natal (D1) and Navamsa (D9) charts together.
3. Factor in planetary aspects (Drishti) when analyzing any house.
4. Consider current transits for timing predictions.
5. Be direct and honest — do not sugarcoat bad combinations.
6. Rate every analysis section with: ⭐ Excellent / ✅ Good / ⚠️ Average / ❌ Challenging / 🚫 Serious Concern
7. At the end, give a CLEAR VERDICT using one of these tiers:
   🟢 BEST MATCH — rare celestial alignment, highly favorable
   🟡 GOOD MATCH — solid foundation, minor issues manageable
   🟠 AVERAGE — proceed with awareness, some areas need work
   🔴 CHALLENGING — serious remedies needed before proceeding
   ⛔ AVOID — major fundamental incompatibility
8. If there are doshas, always mention whether cancellation applies and what remedies exist.
9. Speak in simple language that a non-astrologer can understand, but include the technical reasoning in parentheses.
10. Structure your response with clear headings, bullet points, and the tier rating for each section.`;

const PROMPT_CATEGORIES = [
  {
    id: "marriage",
    icon: "💍",
    title: "Marriage Compatibility",
    desc: "Overall match verdict, strengths & red flags",
    buildPrompt: buildMarriagePrompt,
  },
  {
    id: "wealth",
    icon: "💰",
    title: "Wealth & Finance",
    desc: "Combined financial outlook post-marriage",
    buildPrompt: buildWealthPrompt,
  },
  {
    id: "health",
    icon: "💪",
    title: "Health & Longevity",
    desc: "Health risks, Nadi dosha impact",
    buildPrompt: buildHealthPrompt,
  },
  {
    id: "children",
    icon: "👶",
    title: "Children & Family",
    desc: "Progeny prospects & timing",
    buildPrompt: buildChildrenPrompt,
  },
  {
    id: "career",
    icon: "💼",
    title: "Career & Growth",
    desc: "Combined career trajectory & support",
    buildPrompt: buildCareerPrompt,
  },
  {
    id: "verdict",
    icon: "⚡",
    title: "Overall Verdict",
    desc: "Complete proceed / caution / avoid rating",
    buildPrompt: buildOverallPrompt,
  },
];

let activePromptText = "";

function renderPromptPanel(data) {
  elements.aiPromptsPanel.classList.remove("hidden");
  elements.promptPreviewContainer.classList.add("hidden");
  activePromptText = "";

  elements.promptCardsGrid.innerHTML = PROMPT_CATEGORIES.map(
    (cat) => `
    <div class="prompt-card" data-prompt-id="${cat.id}">
      <div class="prompt-card-icon">${cat.icon}</div>
      <div class="prompt-card-title">${escapeHtml(cat.title)}</div>
      <div class="prompt-card-desc">${escapeHtml(cat.desc)}</div>
    </div>
  `
  ).join("");

  elements.promptCardsGrid.querySelectorAll(".prompt-card").forEach((card) => {
    card.addEventListener("click", () => {
      const category = PROMPT_CATEGORIES.find((c) => c.id === card.dataset.promptId);
      if (!category) return;

      // Mark active
      elements.promptCardsGrid.querySelectorAll(".prompt-card").forEach((c) => c.classList.remove("active"));
      card.classList.add("active");

      // Build and show preview
      activePromptText = category.buildPrompt(data);
      elements.promptPreviewTitle.textContent = `${category.icon} ${category.title} Prompt`;
      elements.promptPreviewText.textContent = activePromptText;
      elements.promptPreviewContainer.classList.remove("hidden");
    });
  });

  elements.promptCopyBtn.addEventListener("click", async () => {
    if (!activePromptText) return;
    try {
      await navigator.clipboard.writeText(activePromptText);
      const originalText = elements.promptCopyBtn.textContent;
      elements.promptCopyBtn.textContent = "✓ Copied!";
      showStatus("Prompt copied to clipboard! Paste into ChatGPT.");
      setTimeout(() => {
        elements.promptCopyBtn.textContent = originalText;
      }, 2000);
    } catch {
      showStatus("Clipboard copy failed.", true);
    }
  });
}

// --- Data Extractors ---

function extractCoreIdentity(chart) {
  return `Lagna: ${chart.core_identity.lagna} (${chart.core_identity.lagna_degree}°)
Moon Sign: ${chart.core_identity.moon_sign}
Sun Sign: ${chart.core_identity.sun_sign}
Nakshatra: ${chart.core_identity.nakshatra} (Pada ${chart.core_identity.nakshatra_pada})
Tithi: ${chart.core_identity.tithi}`;
}

function extractPlanetsCompact(chart) {
  return Object.entries(chart.planets)
    .map(([planet, d]) => {
      const retro = d.retro ? " [R]" : "";
      return `${formatLabel(planet)}: ${d.sign} H${d.house} ${d.degree.toFixed(1)}° ${d.nakshatra}${retro}`;
    })
    .join("\n");
}

function extractHouseScore(hs, label) {
  return `${label}: ${hs.score}/10 | Lord: ${hs.lord} (${hs.lord_strength}) in H${hs.lord_house}
  Occupants: ${hs.occupants.length ? hs.occupants.join(", ") : "None"}
  Benefics: ${hs.benefic_occupants.length ? hs.benefic_occupants.join(", ") : "None"}
  Malefics: ${hs.malefic_occupants.length ? hs.malefic_occupants.join(", ") : "None"}
  Aspected by: ${hs.aspected_by.length ? hs.aspected_by.join(", ") : "None"}`;
}

function extractNavamsaCompact(navamsa) {
  const lines = [`D9 Lagna: ${navamsa.ascendant.sign}`];
  for (const [planet, d] of Object.entries(navamsa.planets)) {
    lines.push(`${formatLabel(planet)}: ${d.sign} H${d.navamsa_house} (${d.strength})`);
  }
  return lines.join("\n");
}

function extractAspectsReceived(aspects, houseNumbers) {
  return houseNumbers.map((h) => {
    const received = aspects.aspects_received[String(h)] || [];
    const names = received.map((a) => `${a.planet} (${a.type})`).join(", ") || "None";
    return `House ${h} aspected by: ${names}`;
  }).join("\n");
}

function extractTransits(transits, label) {
  return Object.entries(transits)
    .map(([planet, d]) => {
      const retro = d.retro ? " [R]" : "";
      return `${formatLabel(planet)}: ${d.sign} ${d.degree.toFixed(1)}° H${d.transit_house}${retro} (${d.nakshatra})`;
    })
    .join("\n");
}

function extractGunaMilan(data) {
  if (!data.guna_milan) return "Guna Milan data not available.";
  const gm = data.guna_milan;
  const lines = [`Score: ${gm.score}/${gm.max_score} — ${gm.verdict}`];
  for (const [key, details] of Object.entries(gm.breakdown)) {
    lines.push(`${formatLabel(key)}: ${details.obtained}/${details.max} (Boy: ${details.boy}, Girl: ${details.girl}) — ${details.area}`);
  }
  return lines.join("\n");
}

function extractDoshas(chart) {
  const m = chart.doshas.manglik;
  const lines = [
    `Manglik: ${m.present ? "YES" : "No"} | Mars in H${m.mars_house} | Severity: ${m.severity} | Cancellation: ${m.cancellation ? "Yes" : "No"}`,
    `Nadi: ${chart.doshas.nadi.type}`,
    `Bhakoot: Distance ${chart.doshas.bhakoot.rashi_distance} | ${chart.doshas.bhakoot.compatible ? "Compatible" : "NOT compatible"}`,
  ];
  return lines.join("\n");
}

function extractDasha(chart) {
  const c = chart.dasha.current;
  return `Current Dasha: ${c.mahadasha}/${c.antardasha} (${c.start} to ${c.end})
Marriage Window: ${chart.derived_windows.marriage_window.join(" - ")}
Career Peak: ${chart.derived_windows.career_peak.join(" - ")}`;
}

// --- Prompt Builders ---

function buildMarriagePrompt(data) {
  return `${SYSTEM_PROMPT}

====== CHART DATA ======

--- BOY ---
${extractCoreIdentity(data.boy)}

Planets:
${extractPlanetsCompact(data.boy)}

7th House (Marriage):
${extractHouseScore(data.boy.house_scores.marriage_7th, "Marriage")}

${extractAspectsReceived(data.boy.aspects, [1, 7, 8])}

Doshas:
${extractDoshas(data.boy)}

Navamsa (D9):
${extractNavamsaCompact(data.boy.navamsa)}

Dasha & Timing:
${extractDasha(data.boy)}

--- GIRL ---
${extractCoreIdentity(data.girl)}

Planets:
${extractPlanetsCompact(data.girl)}

7th House (Marriage):
${extractHouseScore(data.girl.house_scores.marriage_7th, "Marriage")}

${extractAspectsReceived(data.girl.aspects, [1, 7, 8])}

Doshas:
${extractDoshas(data.girl)}

Navamsa (D9):
${extractNavamsaCompact(data.girl.navamsa)}

Dasha & Timing:
${extractDasha(data.girl)}

--- GUNA MILAN (Ashtakoota) ---
${extractGunaMilan(data)}

--- CURRENT TRANSITS ---
Boy's transits: ${extractTransits(data.boy.transits)}
Girl's transits: ${extractTransits(data.girl.transits)}

====== ANALYSIS REQUEST ======

Analyze this marriage compatibility in detail. Cover:

1. **Guna Milan Analysis**: Interpret each of the 8 gunas — which are strong, which are weak, and what it means practically for daily married life.

2. **7th House Cross-Analysis**: Compare both 7th houses. Who has the stronger marriage house? What challenges does each partner bring?

3. **Venus & Jupiter Analysis**: Analyze the Karaka planets for marriage (Venus for wife/romance, Jupiter for husband/wisdom) in both charts. Are they well-placed?

4. **Manglik Dosha**: Is there a Manglik mismatch? If yes, does cancellation apply? What remedies exist?

5. **Nadi & Bhakoot Dosha**: Assess health and emotional compatibility based on these doshas.

6. **Navamsa (D9) Confirmation**: Does the D9 chart support or contradict the D1 marriage indications? Check D9 7th house and Venus placement.

7. **Timing**: When is the best period for marriage based on both Dashas?

8. **Final Verdict**: Give a clear tier rating (🟢/🟡/🟠/🔴/⛔) with reasoning.`;
}

function buildWealthPrompt(data) {
  return `${SYSTEM_PROMPT}

====== CHART DATA ======

--- BOY ---
${extractCoreIdentity(data.boy)}

2nd House (Wealth):
${extractHouseScore(data.boy.house_scores.wealth_2nd, "Wealth")}

11th House (Gains):
${extractHouseScore(data.boy.house_scores.gains_11th, "Gains")}

${extractAspectsReceived(data.boy.aspects, [2, 6, 10, 11])}

Dasha & Timing:
${extractDasha(data.boy)}

--- GIRL ---
${extractCoreIdentity(data.girl)}

2nd House (Wealth):
${extractHouseScore(data.girl.house_scores.wealth_2nd, "Wealth")}

11th House (Gains):
${extractHouseScore(data.girl.house_scores.gains_11th, "Gains")}

${extractAspectsReceived(data.girl.aspects, [2, 6, 10, 11])}

Dasha & Timing:
${extractDasha(data.girl)}

--- CURRENT TRANSITS ---
Boy: ${extractTransits(data.boy.transits)}
Girl: ${extractTransits(data.girl.transits)}

====== ANALYSIS REQUEST ======

Analyze the COMBINED financial outlook for this couple after marriage:

1. **Individual Wealth Potential**: Who has the stronger 2nd house? Who earns more easily?
2. **11th House Gains**: Whose gains house is stronger? Will income grow steadily?
3. **Malefic Impact**: Are there malefics aspecting or sitting in wealth houses? What does that mean for savings and debts?
4. **Combined Assessment**: Will this couple be financially comfortable together? Will marriage improve or worsen their financial situation?
5. **Timing**: When are the best financial periods for each based on Dasha?
6. **Rating**: Give a tier rating for financial compatibility (🟢/🟡/🟠/🔴/⛔).`;
}

function buildHealthPrompt(data) {
  return `${SYSTEM_PROMPT}

====== CHART DATA ======

--- BOY ---
${extractCoreIdentity(data.boy)}

Planets:
${extractPlanetsCompact(data.boy)}

Planet Strength: ${JSON.stringify(data.boy.planet_strength)}

${extractAspectsReceived(data.boy.aspects, [1, 6, 8])}

Doshas:
${extractDoshas(data.boy)}

Navamsa:
${extractNavamsaCompact(data.boy.navamsa)}

--- GIRL ---
${extractCoreIdentity(data.girl)}

Planets:
${extractPlanetsCompact(data.girl)}

Planet Strength: ${JSON.stringify(data.girl.planet_strength)}

${extractAspectsReceived(data.girl.aspects, [1, 6, 8])}

Doshas:
${extractDoshas(data.girl)}

Navamsa:
${extractNavamsaCompact(data.girl.navamsa)}

--- NADI DOSHA CHECK ---
Boy Nadi: ${data.boy.doshas.nadi.type}
Girl Nadi: ${data.girl.doshas.nadi.type}
Same Nadi: ${data.boy.doshas.nadi.type === data.girl.doshas.nadi.type ? "YES — NADI DOSHA PRESENT" : "No — Different Nadis (Good)"}

--- CURRENT TRANSITS ---
Boy: ${extractTransits(data.boy.transits)}
Girl: ${extractTransits(data.girl.transits)}

====== ANALYSIS REQUEST ======

Analyze health and longevity for both individuals and as a couple:

1. **1st House (Body/Self)**: Analyze the lagna and its lord for both. Any afflictions? Malefic aspects on lagna?
2. **6th House (Disease)**: What health challenges does each chart indicate? Chronic issues?
3. **8th House (Longevity)**: Any serious concerns? Malefics in 8th? 8th lord afflicted?
4. **Nadi Dosha Impact**: If same Nadi exists, what are the health implications for the couple and their children? Are there cancellation factors?
5. **Mental Health**: Analyze Moon strength and afflictions for emotional/mental wellbeing of both.
6. **Children's Health Indicators**: Based on 5th house and Jupiter, any concerns for offspring health?
7. **Rating**: Give a tier rating for health compatibility (🟢/🟡/🟠/🔴/⛔).`;
}

function buildChildrenPrompt(data) {
  const boyH5 = data.boy.houses["5"];
  const girlH5 = data.girl.houses["5"];
  return `${SYSTEM_PROMPT}

====== CHART DATA ======

--- BOY ---
${extractCoreIdentity(data.boy)}

5th House (Children): Sign: ${boyH5.sign}, Lord: ${boyH5.lord}, Occupants: ${boyH5.occupants.length ? boyH5.occupants.join(", ") : "None"}
${extractAspectsReceived(data.boy.aspects, [5])}
Jupiter (Putra Karaka): ${data.boy.planets.jupiter.sign} H${data.boy.planets.jupiter.house} (${data.boy.planet_strength.jupiter})

Navamsa 5th house & Jupiter:
${data.boy.navamsa.planets.jupiter ? `D9 Jupiter: ${data.boy.navamsa.planets.jupiter.sign} H${data.boy.navamsa.planets.jupiter.navamsa_house} (${data.boy.navamsa.planets.jupiter.strength})` : "N/A"}

Dasha:
${extractDasha(data.boy)}

--- GIRL ---
${extractCoreIdentity(data.girl)}

5th House (Children): Sign: ${girlH5.sign}, Lord: ${girlH5.lord}, Occupants: ${girlH5.occupants.length ? girlH5.occupants.join(", ") : "None"}
${extractAspectsReceived(data.girl.aspects, [5])}
Jupiter (Putra Karaka): ${data.girl.planets.jupiter.sign} H${data.girl.planets.jupiter.house} (${data.girl.planet_strength.jupiter})

Navamsa 5th house & Jupiter:
${data.girl.navamsa.planets.jupiter ? `D9 Jupiter: ${data.girl.navamsa.planets.jupiter.sign} H${data.girl.navamsa.planets.jupiter.navamsa_house} (${data.girl.navamsa.planets.jupiter.strength})` : "N/A"}

Dasha:
${extractDasha(data.girl)}

--- CURRENT TRANSITS ---
Boy: ${extractTransits(data.boy.transits)}
Girl: ${extractTransits(data.girl.transits)}

====== ANALYSIS REQUEST ======

Analyze progeny (children) prospects for this couple:

1. **5th House Analysis**: Both charts — is the 5th house strong? Any malefic affliction?
2. **Jupiter (Putra Karaka)**: Is Jupiter well-placed in both D1 and D9?
3. **5th Lord Strength**: Where is the 5th lord placed? Strong or weak?
4. **Timing for Children**: Based on Dasha periods, when are children most likely?
5. **Number & Gender Indicators**: Any traditional indicators for number or gender of children?
6. **Challenges**: Are there any doshas or afflictions that could delay or deny children?
7. **Rating**: Give a tier rating for children prospects (🟢/🟡/🟠/🔴/⛔).`;
}

function buildCareerPrompt(data) {
  return `${SYSTEM_PROMPT}

====== CHART DATA ======

--- BOY ---
${extractCoreIdentity(data.boy)}

10th House (Career):
${extractHouseScore(data.boy.house_scores.career_10th, "Career")}

${extractAspectsReceived(data.boy.aspects, [2, 10, 11])}

Planet Strength: ${JSON.stringify(data.boy.planet_strength)}

Dasha & Timing:
${extractDasha(data.boy)}

--- GIRL ---
${extractCoreIdentity(data.girl)}

10th House (Career):
${extractHouseScore(data.girl.house_scores.career_10th, "Career")}

${extractAspectsReceived(data.girl.aspects, [2, 10, 11])}

Planet Strength: ${JSON.stringify(data.girl.planet_strength)}

Dasha & Timing:
${extractDasha(data.girl)}

--- CURRENT TRANSITS ---
Boy: ${extractTransits(data.boy.transits)}
Girl: ${extractTransits(data.girl.transits)}

====== ANALYSIS REQUEST ======

Analyze the combined career outlook for this couple:

1. **Individual Career Strength**: Whose 10th house is stronger? Who has better professional prospects?
2. **Mutual Support**: Will this marriage help or hinder each person's career? Look at 7th lord's connection to 10th house.
3. **Career Peak Timing**: Each person's best career period based on Dasha.
4. **Saturn's Role**: Saturn is the Karma karaka — how is Saturn placed in both charts?
5. **Combined Growth**: Will this couple grow professionally together? Or will one partner's career suffer?
6. **Rating**: Give a tier rating for career compatibility (🟢/🟡/🟠/🔴/⛔).`;
}

function buildOverallPrompt(data) {
  return `${SYSTEM_PROMPT}

====== COMPLETE CHART DATA ======

--- BOY ---
Birth: ${data.boy.meta.local_datetime} at ${data.boy.meta.place_name}
${extractCoreIdentity(data.boy)}

All Planets:
${extractPlanetsCompact(data.boy)}

Planet Strength: ${JSON.stringify(data.boy.planet_strength)}

House Scores:
${extractHouseScore(data.boy.house_scores.wealth_2nd, "2nd Wealth")}
${extractHouseScore(data.boy.house_scores.marriage_7th, "7th Marriage")}
${extractHouseScore(data.boy.house_scores.career_10th, "10th Career")}
${extractHouseScore(data.boy.house_scores.gains_11th, "11th Gains")}

Doshas:
${extractDoshas(data.boy)}

Navamsa (D9):
${extractNavamsaCompact(data.boy.navamsa)}

Dasha & Timing:
${extractDasha(data.boy)}

--- GIRL ---
Birth: ${data.girl.meta.local_datetime} at ${data.girl.meta.place_name}
${extractCoreIdentity(data.girl)}

All Planets:
${extractPlanetsCompact(data.girl)}

Planet Strength: ${JSON.stringify(data.girl.planet_strength)}

House Scores:
${extractHouseScore(data.girl.house_scores.wealth_2nd, "2nd Wealth")}
${extractHouseScore(data.girl.house_scores.marriage_7th, "7th Marriage")}
${extractHouseScore(data.girl.house_scores.career_10th, "10th Career")}
${extractHouseScore(data.girl.house_scores.gains_11th, "11th Gains")}

Doshas:
${extractDoshas(data.girl)}

Navamsa (D9):
${extractNavamsaCompact(data.girl.navamsa)}

Dasha & Timing:
${extractDasha(data.girl)}

--- GUNA MILAN (Ashtakoota) ---
${extractGunaMilan(data)}

--- CURRENT TRANSITS ---
Boy: ${extractTransits(data.boy.transits)}
Girl: ${extractTransits(data.girl.transits)}

====== ANALYSIS REQUEST ======

Give a COMPREHENSIVE marriage compatibility analysis covering ALL aspects:

1. **💍 Marriage Compatibility** — Guna Milan interpretation, 7th house cross-analysis, Venus/Jupiter placement, Manglik/Nadi/Bhakoot doshas

2. **💰 Wealth & Finance** — Combined financial outlook, who earns more, will marriage improve finances?

3. **💪 Health & Longevity** — Health risks for both, Nadi dosha impact, mental health indicators

4. **👶 Children & Family** — Progeny prospects, timing, any concerns

5. **💼 Career & Growth** — Combined career trajectory, will they support each other professionally?

6. **⏰ Timing** — Best period for marriage, career peaks, financial highs, children timing

For EACH section above, give a clear tier rating:
⭐ Excellent / ✅ Good / ⚠️ Average / ❌ Challenging / 🚫 Serious Concern

7. **⚡ FINAL VERDICT**: 
   Give ONE of these ratings with full justification:
   🟢 BEST MATCH — rare celestial alignment, highly favorable
   🟡 GOOD MATCH — solid foundation, minor issues manageable  
   🟠 AVERAGE — proceed with awareness, some areas need work
   🔴 CHALLENGING — serious remedies needed before proceeding
   ⛔ AVOID — major fundamental incompatibility

   Also tell: "Is this the best this person can find, or should they look further?"
   Be brutally honest.`;
}


function formatLabel(value) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function capitalize(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
