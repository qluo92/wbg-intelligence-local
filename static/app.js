const state = {
  material: "",
  selected: "",
  staticData: null,
};

const el = (id) => document.getElementById(id);

async function getJson(url) {
  if (state.staticData) {
    if (url === "/api/overview") return state.staticData.overview;
    if (url === "/api/governance") return { items: state.staticData.governance };
    if (url.startsWith("/api/companies")) return filterStaticCompanies(url);
    if (url.startsWith("/api/company/")) {
      const id = decodeURIComponent(url.replace("/api/company/", ""));
      return state.staticData.companyDetails[id];
    }
  }
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed: ${url}`);
  return response.json();
}

function filterStaticCompanies(url) {
  const parsed = new URL(url, window.location.origin);
  const search = (parsed.searchParams.get("search") || "").toLowerCase();
  const material = parsed.searchParams.get("material") || "";
  const items = state.staticData.companies.filter((item) => {
    const matchesSearch =
      !search ||
      `${item.name || ""} ${item.chinese_name || ""} ${item.canonical_id || ""}`.toLowerCase().includes(search);
    const matchesMaterial = !material || String(item.product_categories || "").includes(material);
    return matchesSearch && matchesMaterial;
  });
  return { items };
}

function tagList(value) {
  if (!value) return "";
  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 5)
    .map((item) => `<span class="tag">${item}</span>`)
    .join("");
}

function yesNoTag(value, label) {
  return value ? `<span class="tag red">${label}</span>` : "";
}

async function loadOverview() {
  const data = await getJson("/api/overview");
  const labels = {
    companies: "公司",
    products: "产品化能力",
    financial_rows: "财务行",
    governance_issues: "治理风险",
    locked_companies: "锁定公司",
    review_companies: "待审核公司",
  };
  el("stats").innerHTML = Object.entries(labels)
    .map(([key, label]) => `<div class="stat"><strong>${data.stats[key] ?? 0}</strong><span>${label}</span></div>`)
    .join("");
  const current = data.run_state.find((item) => item.key === "current_task");
  el("currentTask").textContent = current ? current.value : "本地行业数据库";
}

async function loadCompanies() {
  const search = encodeURIComponent(el("search").value.trim());
  const material = encodeURIComponent(state.material);
  const data = await getJson(`/api/companies?search=${search}&material=${material}`);
  el("companyList").innerHTML = data.items
    .map(
      (item) => `
      <button class="company-card" data-id="${item.canonical_id}">
        <strong>${item.name}</strong>
        <span>${item.chinese_name || item.canonical_id}</span>
        <span>${item.headquarters || "总部未填"} · ${item.company_status || "状态未填"}</span>
        <div class="tags">
          ${tagList(item.product_categories)}
          ${yesNoTag(item.review_flag, "待审核")}
          ${item.lock_flag ? '<span class="tag green">锁定</span>' : ""}
        </div>
      </button>
    `,
    )
    .join("");
  document.querySelectorAll(".company-card").forEach((button) => {
    button.addEventListener("click", () => loadCompany(button.dataset.id));
  });
}

function renderFinancials(rows) {
  if (!rows.length) return '<p class="muted">暂无财务行。</p>';
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>财年</th><th>营收</th><th>净利润</th><th>EBIT</th><th>FCF</th><th>货币</th><th>状态</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
              <tr>
                <td>${row.fiscal_year || ""}</td>
                <td>${row.revenue ?? ""}</td>
                <td>${row.net_profit ?? ""}</td>
                <td>${row.ebit ?? ""}</td>
                <td>${row.fcf ?? ""}</td>
                <td>${row.currency || ""}</td>
                <td>${row.collection_status || ""}</td>
              </tr>
            `,
            )
            .join("")}
        </tbody>
      </table>
    </div>`;
}

function renderProducts(rows) {
  if (!rows.length) return '<p class="muted">暂无产品化能力。</p>';
  return rows
    .map(
      (row) => `
      <div class="fact">
        <strong>${row.capability_name}</strong>
        <div class="tags">
          ${tagList(row.material_system)}
          ${tagList(row.device_category)}
          ${tagList(row.voltage)}
          ${row.ingest_status ? `<span class="tag green">${row.ingest_status}</span>` : ""}
        </div>
        <p class="muted">${row.source_type || ""}${row.last_verified ? ` · ${row.last_verified}` : ""}</p>
      </div>
    `,
    )
    .join("");
}

async function loadCompany(canonicalId) {
  state.selected = canonicalId;
  const data = await getJson(`/api/company/${encodeURIComponent(canonicalId)}`);
  const company = data.company;
  el("companyDetail").innerHTML = `
    <h2>${company.name}</h2>
    <p class="muted">${company.chinese_name || company.canonical_id}</p>
    <div class="tags">
      ${tagList(company.product_categories)}
      ${tagList(company.value_chain_roles)}
      ${yesNoTag(company.review_flag, "待审核")}
      ${company.lock_flag ? '<span class="tag green">人工确认锁</span>' : ""}
    </div>
    <div class="grid-two" style="margin-top: 14px;">
      <div class="fact"><span>总部</span>${company.headquarters || ""}</div>
      <div class="fact"><span>成立年份</span>${company.founded_year || ""}</div>
      <div class="fact"><span>公司状态</span>${company.company_status || ""}</div>
      <div class="fact"><span>采集状态</span>${company.collection_status || ""}</div>
    </div>
    <div class="fact" style="margin-top: 12px;">
      <span>一句话定位</span>
      ${company.positioning || "未填"}
    </div>
    <h3 style="margin-top: 18px;">产品化能力</h3>
    ${renderProducts(data.products)}
    <h3 style="margin-top: 18px;">年度财务</h3>
    ${renderFinancials(data.financials)}
  `;
}

async function loadGovernance() {
  const data = await getJson("/api/governance");
  el("governanceIssues").innerHTML = data.items
    .map(
      (item) => `
      <div class="issue">
        <strong>${item.scope} · ${item.field}</strong>
        <p>${item.issue}</p>
        <p class="muted">${item.recommended_action}</p>
      </div>
    `,
    )
    .join("");
}

function bindEvents() {
  el("search").addEventListener("input", () => {
    window.clearTimeout(window.__searchTimer);
    window.__searchTimer = window.setTimeout(loadCompanies, 160);
  });
  document.querySelectorAll("[data-material]").forEach((button) => {
    button.addEventListener("click", () => {
      state.material = button.dataset.material;
      document.querySelectorAll("[data-material]").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      loadCompanies();
    });
  });
}

async function boot() {
  try {
    const staticResponse = await fetch("/data.json", { cache: "no-store" });
    if (staticResponse.ok) {
      state.staticData = await staticResponse.json();
    }
  } catch (_) {
    state.staticData = null;
  }
  bindEvents();
  await loadOverview();
  await loadCompanies();
  await loadGovernance();
}

boot().catch((error) => {
  document.body.innerHTML = `<pre>${error.stack}</pre>`;
});
