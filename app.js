(() => {
  let state = {
    data: null,
    activeKeyword: "",
  };

  async function loadData() {
    try {
      const resp = await fetch("./data/trends.json", { cache: "no-store" });
      if (resp.ok) {
        return await resp.json();
      }
    } catch (_) {
      // Fallback for local file:// viewing
    }
    if (window.__DWANCHI_TRENDS__) {
      return window.__DWANCHI_TRENDS__;
    }
    throw new Error("Could not load trends.json or fallback data.");
  }

  function escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderHeader(data) {
    document.getElementById("last-updated").textContent = "Updated: " + data.scraped_at;
    document.getElementById("indexed-count").textContent = data.total_items_indexed + " items indexed";
  }

  function renderOpportunities(data) {
    const grid = document.getElementById("opportunities-grid");
    grid.innerHTML = (data.opportunities || []).map((opp) => `
      <div class="opp-card">
        <div class="opp-top">
          <span class="slot-tag">#${opp.rank} • ${escapeHtml(opp.slot)} (${opp.floor} R$)</span>
          <span class="score-tag">Score ${opp.opportunity_score}</span>
        </div>
        <h3>${escapeHtml(opp.title)}</h3>
        <p class="opp-why">${escapeHtml(opp.why_now)}</p>
        <div class="opp-safe">${escapeHtml(opp.copyright_safe_note)}</div>
      </div>
    `).join("");
  }

  function renderHypeRadar(data) {
    const grid = document.getElementById("hype-radar-grid");
    grid.innerHTML = (data.hype_radar || []).map((ev) => {
      const daysText = ev.days_until > 0 ? `${ev.days_until} days left (${ev.event_date})` : `Live Window (${ev.event_date})`;
      const banned = ev.banned_terms && ev.banned_terms.length
        ? `<div class="radar-ban">Blocked IPs: ${escapeHtml(ev.banned_terms.join(", "))}</div>`
        : `<div class="opp-safe">Zero IP restrictions on generic seasonal wave</div>`;
      return `
        <div class="radar-card">
          <div class="radar-meta">
            <span>${escapeHtml(ev.medium)}</span>
            <span>${escapeHtml(daysText)} • Lead ${ev.lead_score}</span>
          </div>
          <h3>${escapeHtml(ev.title)}</h3>
          <p class="opp-why">${escapeHtml(ev.hype_driver)}</p>
          <div class="radar-arch"><strong>Safe Build:</strong> ${escapeHtml(ev.safe_archetype)}</div>
          <div class="muted small">Slots: ${escapeHtml(ev.recommended_slots.join(", "))}</div>
          ${banned}
        </div>
      `;
    }).join("");
  }

  function renderSlotTable(data) {
    const tbody = document.querySelector("#slot-table tbody");
    tbody.innerHTML = (data.slot_summary || []).map((s) => `
      <tr>
        <td><strong>${escapeHtml(s.slot)}</strong></td>
        <td>${s.price_floor} R$</td>
        <td>${s.chart_hits}</td>
        <td><strong>${s.low_fav_breakouts}</strong></td>
        <td>${s.min_favs_in_chart.toLocaleString()}</td>
        <td><span class="tag-break">${s.openness_score}</span></td>
      </tr>
    `).join("");
  }

  function renderKeywords(data) {
    const box = document.getElementById("keyword-chips");
    box.innerHTML = (data.keyword_stats || []).map((k) => `
      <button class="kw-chip ${state.activeKeyword === k.keyword ? "active" : ""}" data-kw="${escapeHtml(k.keyword)}">
        <div class="kw-name">
          <span>#${escapeHtml(k.keyword)}</span>
          <span class="score-tag">${k.low_fav_count} &lt;3k</span>
        </div>
        <div class="kw-sub">Median ${k.median_favs.toLocaleString()} favs</div>
      </button>
    `).join("");

    box.querySelectorAll(".kw-chip").forEach((btn) => {
      btn.addEventListener("click", () => {
        const kw = btn.getAttribute("data-kw");
        state.activeKeyword = state.activeKeyword === kw ? "" : kw;
        renderKeywords(data);
        renderItemsTable();
      });
    });
  }

  function renderItemsTable() {
    const data = state.data;
    if (!data) return;

    const search = document.getElementById("search-input").value.trim().toLowerCase();
    const slot = document.getElementById("slot-filter").value;
    const sortMode = document.getElementById("sort-select").value;
    const lowFavOnly = document.getElementById("low-fav-only").checked;

    let rows = (data.items || []).filter((it) => {
      if (slot !== "ALL" && it.slot !== slot) return false;
      if (lowFavOnly && it.favs >= 5000) return false;
      if (state.activeKeyword && !(it.keywords || []).includes(state.activeKeyword) && !it.name.toLowerCase().includes(state.activeKeyword)) {
        return false;
      }
      if (search) {
        const hay = `${it.name} ${it.creator} ${(it.keywords || []).join(" ")} ${(it.sources || []).join(" ")}`.toLowerCase();
        if (!hay.includes(search)) return false;
      }
      return true;
    });

    rows = rows.slice().sort((a, b) => {
      if (sortMode === "lowest_favs") return a.favs - b.favs;
      if (sortMode === "highest_favs") return b.favs - a.favs;
      if (sortMode === "rank") return a.best_rank - b.best_rank || b.breakout_score - a.breakout_score;
      return b.breakout_score - a.breakout_score || a.favs - b.favs;
    });

    const tbody = document.querySelector("#items-table tbody");
    tbody.innerHTML = rows.slice(0, 120).map((it) => `
      <tr>
        <td><span class="tag-break">${it.breakout_score}</span></td>
        <td>
          <a href="${escapeHtml(it.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(it.name)}</a>
          <div class="muted small">by ${escapeHtml(it.creator)}</div>
        </td>
        <td>${escapeHtml(it.slot)} • <strong>${it.price} R$</strong></td>
        <td>${it.favs.toLocaleString()}</td>
        <td class="muted small">${escapeHtml((it.sources || []).slice(0, 3).join(", "))}</td>
        <td>${it.copyright_clean_title ? '<span class="tag-safe">Clean</span>' : '<span class="tag-warn">IP Risk</span>'}</td>
      </tr>
    `).join("") || `<tr><td colspan="6" class="muted">No catalog items matched current filters.</td></tr>`;
  }

  function renderPortfolio(data) {
    const container = document.getElementById("portfolio-container");
    const drops = (data.dwanchi_portfolio && data.dwanchi_portfolio.drops) || [];
    container.innerHTML = drops.map((d) => `
      <div class="drop-block">
        <div class="drop-title">${escapeHtml(d.name)} (${d.set_price_floor} R$ full set)</div>
        <div class="drop-status">${escapeHtml(d.status)}</div>
        <ul class="drop-list">
          ${d.items.map((it) => `<li><strong>#${it.id} ${escapeHtml(it.slot)} (${it.floor} R$):</strong> ${escapeHtml(it.title)} — <code>${escapeHtml(it.mesh_id)}</code></li>`).join("")}
        </ul>
      </div>
    `).join("");
  }

  function setupShield(data) {
    const input = document.getElementById("shield-input");
    const box = document.getElementById("shield-result");
    const banned = data.banned_words || [];

    input.addEventListener("input", () => {
      const val = input.value.trim();
      if (!val) {
        box.className = "shield-box safe";
        box.textContent = "Type or paste a title above — checks run live as you type.";
        return;
      }
      const hits = [];
      for (const w of banned) {
        const rx = new RegExp(`(^|[^a-z0-9])${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}([^a-z0-9]|$)`, "i");
        if (rx.test(val)) hits.push(w);
      }
      if (hits.length > 0) {
        box.className = "shield-box danger";
        box.innerHTML = `<strong>BLOCKED (${hits.length} copyright triggers):</strong> ${escapeHtml(hits.join(", "))}. Replace with safe terms like <em>Iron Sovereign</em>, <em>Arcane Warlock</em>, <em>Umbral Monarch</em>, or <em>Liquid Platinum</em>.`;
      } else {
        const lenNote = val.length > 50 ? ` (Warning: ${val.length}/50 chars — Roblox Catalog titles cap at 50 chars!)` : ` (${val.length}/50 chars)`;
        box.className = "shield-box safe";
        box.textContent = `PASS — Zero trademark or Roblox IP hits detected${lenNote}.`;
      }
    });
  }

  async function init() {
    try {
      const data = await loadData();
      state.data = data;
      renderHeader(data);
      renderOpportunities(data);
      renderHypeRadar(data);
      renderSlotTable(data);
      renderKeywords(data);
      renderItemsTable();
      renderPortfolio(data);
      setupShield(data);

      ["search-input", "slot-filter", "sort-select", "low-fav-only"].forEach((id) => {
        document.getElementById(id).addEventListener("input", renderItemsTable);
        document.getElementById(id).addEventListener("change", renderItemsTable);
      });
    } catch (err) {
      document.getElementById("last-updated").textContent = "Error: " + err.message;
    }
  }

  init();
})();
