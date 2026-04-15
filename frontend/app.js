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
