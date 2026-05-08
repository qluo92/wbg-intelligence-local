const state = {
  material: "",
  selected: "",
  withProductsOnly: false,
  staticData: null,
};

const $ = (id) => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function splitValues(value) {
  if (!value) return [];
  return String(value)
    .replaceAll("，", ",")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function tagList(value, className = "") {
  return splitValues(value)
    .slice(0, 6)
    .map((item) => `<span class="tag ${className}">${escapeHtml(item)}</span>`)
    .join("");
}

function sourceLink(url, label = "Source") {
  if (!url) return "";
  return `<a class="source-link" href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`;
}

function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "";
  const number = Number(value);
  if (Number.isNaN(number)) return escapeHtml(value);
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(number);
}

async function loadStaticData() {
  const response = await fetch("data.json", { cache: "no-store" });
  if (!response.ok) throw new Error("Unable to load data.json");
  state.staticData = await response.json();
}

function allCompanies() {
  return state.staticData?.companies || [];
}

function allDetails() {
  return state.staticData?.companyDetails || {};
}

function detailFor(companyId) {
  return allDetails()[companyId] || null;
}

function filteredCompanies() {
  const search = $("search").value.trim().toLowerCase();
  return allCompanies().filter((company) => {
    const blob = `${company.name || ""} ${company.chinese_name || ""} ${company.canonical_id || ""}`.toLowerCase();
    const matchesSearch = !search || blob.includes(search);
    const matchesMaterial = !state.material || String(company.product_categories || "").includes(state.material);
    const detail = detailFor(company.canonical_id);
    const matchesProducts = !state.withProductsOnly || (detail?.products || []).length > 0;
    return matchesSearch && matchesMaterial && matchesProducts;
  });
}

function companyCoverage() {
  const companies = allCompanies();
  const details = allDetails();
  const total = companies.length || 1;
  const withProducts = companies.filter((item) => (details[item.canonical_id]?.products || []).length > 0).length;
  const withFinancials = companies.filter((item) => (details[item.canonical_id]?.financials || []).length > 0).length;
  const locked = companies.filter((item) => item.lock_flag).length;
  const review = companies.filter((item) => item.review_flag).length;
  return [
    ["Product capability coverage", withProducts, total],
    ["Annual financial coverage", withFinancials, total],
    ["Human-confirmed lock coverage", locked, total],
    ["Review queue share", review, total],
  ];
}

function renderOverview() {
  const overview = state.staticData.overview;
  const stats = overview.stats;
  const metrics = [
    ["Company master", stats.companies, "Canonical ID anchored"],
    ["Product capabilities", stats.products, "Source and evidence linked"],
    ["Annual financial rows", stats.financial_rows, "Company-year facts"],
    ["Governance risks", stats.governance_issues, "Schema/manual drift"],
    ["Locked companies", stats.locked_companies, "Human-confirmed rows"],
    ["Review companies", stats.review_companies, "Human decision needed"],
  ];
  $("stats").innerHTML = metrics
    .map(([label, value, note]) => `<div class="metric"><strong>${value}</strong><span>${label}<br>${note}</span></div>`)
    .join("");

  const current = overview.run_state.find((item) => item.key === "current_task");
  $("currentTask").textContent = current?.value || "Tacive WBG Intelligence database";

  $("coverageBars").innerHTML = companyCoverage()
    .map(([label, value, total]) => {
      const pct = Math.round((value / total) * 100);
      return `
        <div class="coverage-row">
          <span>${label}</span>
          <div class="bar"><span style="width:${pct}%"></span></div>
          <strong>${pct}%</strong>
        </div>`;
    })
    .join("");
}

function renderCompanies() {
  const items = filteredCompanies();
  $("resultCount").textContent = items.length;
  $("companyList").innerHTML = items
    .map((company) => {
      const detail = detailFor(company.canonical_id);
      const productCount = detail?.products?.length || 0;
      const financialCount = detail?.financials?.length || 0;
      const selected = state.selected === company.canonical_id ? "selected" : "";
      return `
        <button class="company-card ${selected}" data-id="${escapeHtml(company.canonical_id)}">
          <strong>${escapeHtml(company.name)}</strong>
          <span>${escapeHtml(company.chinese_name || company.canonical_id)}</span>
          <span>${escapeHtml(company.headquarters || "HQ missing")} · ${escapeHtml(company.company_status || "Status missing")}</span>
          <div class="tag-row">
            ${tagList(company.product_categories)}
            ${productCount ? `<span class="tag ok">Products ${productCount}</span>` : ""}
            ${financialCount ? `<span class="tag ok">Financials ${financialCount}</span>` : ""}
            ${company.review_flag ? '<span class="tag danger">Review</span>' : ""}
          </div>
        </button>`;
    })
    .join("");

  document.querySelectorAll(".company-card").forEach((button) => {
    button.addEventListener("click", () => renderCompanyDetail(button.dataset.id));
  });
}

function renderFinancials(rows) {
  if (!rows.length) return '<p class="evidence-text">No annual financial data yet.</p>';
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Fiscal year</th>
            <th>Revenue</th>
            <th>Net income</th>
            <th>EBIT</th>
            <th>FCF</th>
            <th>Currency</th>
            <th>Status</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${escapeHtml(row.fiscal_year || "")}</td>
                  <td>${formatNumber(row.revenue)}</td>
                  <td>${formatNumber(row.net_profit)}</td>
                  <td>${formatNumber(row.ebit)}</td>
                  <td>${formatNumber(row.fcf)}</td>
                  <td>${escapeHtml(row.currency || "")}</td>
                  <td>${escapeHtml(row.collection_status || "")}</td>
                  <td>${sourceLink(row.source_url, row.source_type || "Source")}</td>
                </tr>`,
            )
            .join("")}
        </tbody>
      </table>
    </div>`;
}

function renderProducts(rows) {
  if (!rows.length) return '<p class="evidence-text">No product capability record yet.</p>';
  return `
    <div class="product-list">
      ${rows
        .map(
          (row) => `
            <div class="product-row">
              <strong>${escapeHtml(row.capability_name)}</strong>
              <div class="tag-row">
                ${tagList(row.material_system)}
                ${tagList(row.device_category)}
                ${tagList(row.technology_tags)}
                ${tagList(row.voltage, "ok")}
                ${row.ingest_status ? `<span class="tag ok">${escapeHtml(row.ingest_status)}</span>` : ""}
              </div>
              <p class="evidence-text">${escapeHtml(row.evidence_excerpt || "No evidence excerpt captured yet.")}</p>
              ${sourceLink(row.source_url, `${row.source_type || "Source"} · ${row.last_verified || "No verification date"}`)}
            </div>`,
        )
        .join("")}
    </div>`;
}

function renderCompanyDetail(canonicalId) {
  state.selected = canonicalId;
  const payload = detailFor(canonicalId);
  if (!payload) return;
  const company = payload.company;
  const products = payload.products || [];
  const financials = payload.financials || [];
  const facts = [
    ["Headquarters", company.headquarters],
    ["Founded", company.founded_year],
    ["Employee band", company.employee_band],
    ["Company status", company.company_status],
    ["Company type", company.company_type],
    ["Collection status", company.collection_status],
    ["Last collected", company.last_collected],
    ["Website", company.website ? sourceLink(company.website, "Website") : ""],
  ];

  $("companyDetail").innerHTML = `
    <div class="profile-head">
      <div>
        <p class="eyebrow">Company profile</p>
        <h2>${escapeHtml(company.name)}</h2>
        <p class="canonical">${escapeHtml(company.chinese_name || "")} · ${escapeHtml(company.canonical_id)}</p>
        <p class="profile-note">${escapeHtml(company.positioning || "No positioning statement captured yet.")}</p>
        <div class="tag-row">
          ${tagList(company.product_categories)}
          ${tagList(company.value_chain_roles)}
          ${tagList(company.technology_routes)}
          ${company.lock_flag ? '<span class="tag ok">Human-confirmed lock</span>' : ""}
          ${company.review_flag ? '<span class="tag danger">Needs review</span>' : ""}
        </div>
      </div>
      <div class="profile-score">
        <div class="score-line"><span>Product capabilities</span><strong>${products.length}</strong></div>
        <div class="score-line"><span>Annual financial rows</span><strong>${financials.length}</strong></div>
        <div class="score-line"><span>Source links</span><strong>${products.filter((p) => p.source_url).length + financials.filter((f) => f.source_url).length}</strong></div>
        <div class="score-line"><span>Data posture</span><strong>${company.review_flag ? "Review" : "Usable"}</strong></div>
      </div>
    </div>

    <div class="profile-grid">
      ${facts.map(([label, value]) => `<div class="fact"><span>${label}</span>${value || "Missing"}</div>`).join("")}
    </div>

    <section class="detail-section">
      <h3>Productized capabilities <span>Products, platforms, device capabilities and evidence</span></h3>
      ${renderProducts(products)}
    </section>

    <section class="detail-section">
      <h3>Annual financials <span>Reported facts, source-linked when available</span></h3>
      ${renderFinancials(financials)}
    </section>
  `;
  renderCompanies();
}

function renderGovernance() {
  $("governanceIssues").innerHTML = (state.staticData.governance || [])
    .map(
      (item) => `
        <div class="issue">
          <strong>${escapeHtml(item.scope)} · ${escapeHtml(item.field)}</strong>
          <p>${escapeHtml(item.issue)}</p>
          <p>${escapeHtml(item.recommended_action)}</p>
        </div>`,
    )
    .join("");
}

function bindEvents() {
  $("search").addEventListener("input", () => {
    window.clearTimeout(window.searchTimer);
    window.searchTimer = window.setTimeout(renderCompanies, 120);
  });
  $("withProductsOnly").addEventListener("change", (event) => {
    state.withProductsOnly = event.target.checked;
    renderCompanies();
  });
  document.querySelectorAll("[data-material]").forEach((button) => {
    button.addEventListener("click", () => {
      state.material = button.dataset.material;
      document.querySelectorAll("[data-material]").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      renderCompanies();
    });
  });
}

async function boot() {
  await loadStaticData();
  bindEvents();
  renderOverview();
  renderCompanies();
  renderGovernance();
  const firstCompany = filteredCompanies()[0];
  if (firstCompany) renderCompanyDetail(firstCompany.canonical_id);
}

boot().catch((error) => {
  document.body.innerHTML = `<pre>${escapeHtml(error.stack || error.message)}</pre>`;
});
