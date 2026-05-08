const state = {
  locale: location.pathname.startsWith("/en") ? "en" : "zh",
  material: "",
  selectedCompany: "",
  selectedJudgment: "",
  formalOnly: false,
  withProductsOnly: false,
  data: null,
};

const copy = {
  zh: {
    brandProduct: "WBG Intelligence",
    navHome: "首页",
    navExplorer: "Explorer",
    navCompany: "公司 360",
    navGovernance: "治理",
    heroTitle: "我们不提供更多信息，我们提供更好的判断。",
    heroSubtitle: "Tacive 把分散的半导体产业信号，沉淀为持续更新的竞品路线图数据库，帮助战略团队更快判断竞品方向、市场窗口与路线图变化。",
    primaryCta: "Explore the database",
    secondaryCta: "See how judgments are maintained",
    whyTitle: "信息已经过剩，稀缺的是可靠判断。",
    whyBody: "半导体公司每天面对大量 PR、财报、产品发布、供应链新闻、会议材料与行业传闻。真正的问题不是看不见信息，而是不知道哪些信号会改变判断，哪些只是噪音。",
    whatTitle: "一个持续更新的竞品路线图数据库。",
    whatBody: "Tacive 不是一次性报告，也不是资讯 dashboard。每条记录都围绕一个判断对象维护：对象、信号、判断、证据、置信度、边界条件、反证信号、影响对象和更新时间。",
    changeTitle: "从碎片信号，到判断资产。",
    changeBody: "持续跟踪竞品路线变化，把每个判断连接到证据与边界条件，并保存变化记录，让团队看见判断如何演化。",
    objectListTitle: "被维护的判断对象",
    companyUniverse: "公司宇宙",
    governanceTitle: "字段、证据、来源与交接状态",
    fieldPolicyTitle: "字段治理手册编译结果",
    termTitle: "中英文术语系统",
    riskTitle: "已知治理风险",
    handoffTitle: "运行交接状态",
    searchJudgment: "搜索判断对象",
    searchCompany: "搜索公司",
    formalOnly: "只看 Formal / 可核验对象",
    withProductsOnly: "只看已有产品能力记录的公司",
    stats: {
      companies: "公司主档",
      products: "产品能力",
      financial_rows: "财务记录",
      judgment_objects: "判断对象",
      evidence_items: "证据项",
      field_policies: "字段规则",
    },
  },
  en: {
    brandProduct: "WBG Intelligence",
    navHome: "Home",
    navExplorer: "Explorer",
    navCompany: "Company 360",
    navGovernance: "Governance",
    heroTitle: "Not more information. Better judgment.",
    heroSubtitle: "Tacive turns fragmented semiconductor signals into a continuously maintained competitor roadmap database, helping strategy teams track rival moves, market windows, and roadmap shifts with better judgment.",
    primaryCta: "Explore the database",
    secondaryCta: "See how judgments are maintained",
    whyTitle: "Information is abundant. Reliable judgment is scarce.",
    whyBody: "Semiconductor teams face PR, filings, product launches, supply-chain news, conference material and industry rumors every day. The problem is not seeing information. It is knowing which signals should change judgment and which are noise.",
    whatTitle: "A maintained competitor roadmap database.",
    whatBody: "Tacive is not a one-off report or an information dashboard. Each record is maintained around a judgment object: object, signal, judgment, evidence, confidence, boundary, counter-signal, impact and update time.",
    changeTitle: "From fragmented signals to judgment assets.",
    changeBody: "Track competitor roadmap shifts continuously, link each judgment to evidence and boundary conditions, and preserve change history so teams can see how judgment evolves.",
    objectListTitle: "Maintained judgment objects",
    companyUniverse: "Company universe",
    governanceTitle: "Fields, evidence, sources and handoff state",
    fieldPolicyTitle: "Compiled field governance manual",
    termTitle: "Bilingual terminology system",
    riskTitle: "Known governance risks",
    handoffTitle: "Run handoff state",
    searchJudgment: "Search judgment objects",
    searchCompany: "Search companies",
    formalOnly: "Formal / verifiable only",
    withProductsOnly: "Companies with product capability records only",
    stats: {
      companies: "Company master",
      products: "Product capabilities",
      financial_rows: "Financial rows",
      judgment_objects: "Judgment objects",
      evidence_items: "Evidence items",
      field_policies: "Field policies",
    },
  },
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

async function loadData() {
  const response = await fetch("data.json", { cache: "no-store" });
  if (!response.ok) throw new Error("Unable to load data.json");
  state.data = await response.json();
}

function t(key) {
  return copy[state.locale][key] || key;
}

function applyLocale() {
  document.documentElement.lang = state.locale === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  $("localeToggle").textContent = state.locale === "zh" ? "EN" : "中文";
}

function companies() {
  return state.data?.companies || [];
}

function details() {
  return state.data?.companyDetails || {};
}

function judgments() {
  return state.data?.judgments || [];
}

function detailFor(id) {
  return details()[id] || null;
}

function filteredCompanies() {
  const search = $("companySearch").value.trim().toLowerCase();
  return companies().filter((company) => {
    const blob = `${company.name || ""} ${company.chinese_name || ""} ${company.canonical_id || ""}`.toLowerCase();
    const matchesSearch = !search || blob.includes(search);
    const matchesMaterial = !state.material || String(company.product_categories || "").includes(state.material);
    const detail = detailFor(company.canonical_id);
    const matchesProducts = !state.withProductsOnly || (detail?.products || []).length > 0;
    return matchesSearch && matchesMaterial && matchesProducts;
  });
}

function filteredJudgments() {
  const search = $("judgmentSearch").value.trim().toLowerCase();
  return judgments().filter((item) => {
    const blob = `${item.object_name} ${item.company_name} ${item.signal} ${item.current_judgment}`.toLowerCase();
    const matchesSearch = !search || blob.includes(search);
    const matchesFormal = !state.formalOnly || item.formal_status === "Formal";
    return matchesSearch && matchesFormal;
  });
}

function renderMetrics() {
  const stats = state.data.overview.stats;
  const keys = ["companies", "products", "financial_rows", "judgment_objects", "evidence_items", "field_policies"];
  $("stats").innerHTML = keys
    .map((key) => {
      const label = copy[state.locale].stats[key];
      return `<div class="metric"><strong>${formatNumber(stats[key])}</strong><span>${escapeHtml(label)}</span></div>`;
    })
    .join("");
  const current = state.data.overview.run_state.find((item) => item.key === "current_task");
  $("runState").textContent = current?.value || "Notion-first product state";
}

function renderHeroPreview() {
  const first = judgments()[0];
  if (!first) return;
  $("heroObject").textContent = first.object_name;
  $("heroSignal").textContent = first.signal;
  $("heroEvidence").textContent = first.formal_status;
  $("heroConfidence").textContent = first.confidence;
  $("heroBoundary").textContent = "Public posture";
  $("heroChange").textContent = first.updated_at || "Maintained";
}

function renderSources() {
  $("sourceList").innerHTML = (state.data.sources || [])
    .slice(0, 8)
    .map(
      (source) => `
        <a class="source-item" href="${escapeHtml(source.notion_url || source.data_source_url || "#")}" target="_blank" rel="noreferrer">
          <strong>${escapeHtml(source.title)}</strong>
          <span>${escapeHtml(source.product_role)}</span>
        </a>`,
    )
    .join("");
}

function renderJudgmentList() {
  const items = filteredJudgments();
  $("judgmentCount").textContent = items.length;
  $("judgmentList").innerHTML = items
    .map((item) => {
      const selected = state.selectedJudgment === item.id ? "selected" : "";
      return `
        <button class="judgment-card ${selected}" data-id="${escapeHtml(item.id)}">
          <span>${escapeHtml(item.category)} / ${escapeHtml(item.company_name || "Industry")}</span>
          <strong>${escapeHtml(item.object_name)}</strong>
          <p>${escapeHtml(item.current_judgment)}</p>
          <div class="tag-row">
            <span class="tag ${item.formal_status === "Formal" ? "ok" : "risk"}">${escapeHtml(item.formal_status)}</span>
            <span class="tag">${escapeHtml(item.confidence)}</span>
            <span class="tag">${escapeHtml(item.updated_at)}</span>
          </div>
        </button>`;
    })
    .join("");
  document.querySelectorAll(".judgment-card").forEach((button) => {
    button.addEventListener("click", () => renderJudgmentDetail(button.dataset.id));
  });
}

function renderJudgmentDetail(id) {
  const item = judgments().find((entry) => entry.id === id) || judgments()[0];
  if (!item) return;
  state.selectedJudgment = item.id;
  $("detailTitle").textContent = item.object_name;
  $("detailStatus").textContent = item.formal_status;
  $("detailStatus").className = `status-pill ${item.formal_status === "Formal" ? "ok" : "risk"}`;
  const rows = [
    ["Current Judgment", item.current_judgment],
    ["Signal", item.signal],
    ["Evidence", item.evidence_summary],
    ["Confidence", item.confidence],
    ["Boundary", item.boundary_condition],
    ["Counter-signal", item.counter_signal],
    ["Impact", item.impact],
    ["Change", item.change_note],
    ["Owner", item.owner],
    ["Updated", item.updated_at],
  ];
  $("judgmentDetail").innerHTML = rows
    .map(
      ([label, value]) => `
        <div class="detail-field">
          <span>${escapeHtml(label)}</span>
          <p>${escapeHtml(value || "Missing")}</p>
        </div>`,
    )
    .join("");
  renderJudgmentList();
}

function renderCompanies() {
  const items = filteredCompanies();
  $("companyCount").textContent = items.length;
  $("companyList").innerHTML = items
    .map((company) => {
      const payload = detailFor(company.canonical_id);
      const productCount = payload?.products?.length || 0;
      const financialCount = payload?.financials?.length || 0;
      const judgmentCount = payload?.judgments?.length || 0;
      const selected = state.selectedCompany === company.canonical_id ? "selected" : "";
      return `
        <button class="company-card ${selected}" data-id="${escapeHtml(company.canonical_id)}">
          <strong>${escapeHtml(company.name)}</strong>
          <span>${escapeHtml(company.chinese_name || company.canonical_id)}</span>
          <div class="tag-row">
            ${tagList(company.product_categories)}
            ${productCount ? `<span class="tag ok">Products ${productCount}</span>` : ""}
            ${financialCount ? `<span class="tag ok">Financials ${financialCount}</span>` : ""}
            ${judgmentCount ? `<span class="tag">Judgments ${judgmentCount}</span>` : ""}
            ${company.review_flag ? '<span class="tag danger">Review</span>' : ""}
          </div>
        </button>`;
    })
    .join("");
  document.querySelectorAll(".company-card").forEach((button) => {
    button.addEventListener("click", () => renderCompanyDetail(button.dataset.id));
  });
}

function renderProducts(rows) {
  if (!rows.length) return '<p class="muted-copy">No product capability record yet.</p>';
  return rows
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
          <p>${escapeHtml(row.evidence_excerpt || "No evidence excerpt captured yet.")}</p>
          ${sourceLink(row.source_url, `${row.source_type || "Source"} / ${row.last_verified || "No verification date"}`)}
        </div>`,
    )
    .join("");
}

function renderFinancials(rows) {
  if (!rows.length) return '<p class="muted-copy">No annual financial data yet.</p>';
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>FY</th><th>Revenue</th><th>Net income</th><th>EBIT</th><th>FCF</th><th>Currency</th><th>Source</th>
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
                  <td>${sourceLink(row.source_url, row.source_type || "Source")}</td>
                </tr>`,
            )
            .join("")}
        </tbody>
      </table>
    </div>`;
}

function renderCompanyDetail(id) {
  const payload = detailFor(id) || Object.values(details())[0];
  if (!payload) return;
  const company = payload.company;
  state.selectedCompany = company.canonical_id;
  const facts = [
    ["Canonical ID", company.canonical_id],
    ["Headquarters", company.headquarters],
    ["Founded", company.founded_year],
    ["Employee band", company.employee_band],
    ["Company type", company.company_type],
    ["Company status", company.company_status],
    ["Collection status", company.collection_status],
    ["Website", company.website ? sourceLink(company.website, "Website") : "Missing"],
  ];
  $("companyDetail").innerHTML = `
    <div class="profile-head">
      <div>
        <p class="eyebrow">Company 360</p>
        <h2>${escapeHtml(company.name)}</h2>
        <p class="canonical">${escapeHtml(company.chinese_name || "")}</p>
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
        <div><span>Product capabilities</span><strong>${payload.products.length}</strong></div>
        <div><span>Annual financial rows</span><strong>${payload.financials.length}</strong></div>
        <div><span>Judgment objects</span><strong>${payload.judgments.length}</strong></div>
        <div><span>Evidence items</span><strong>${payload.evidence.length}</strong></div>
      </div>
    </div>
    <div class="fact-grid">${facts.map(([label, value]) => `<div><span>${label}</span><strong>${value || "Missing"}</strong></div>`).join("")}</div>
    <section class="detail-section">
      <h3>Judgment Objects</h3>
      ${(payload.judgments || []).map((item) => `<div class="mini-object"><strong>${escapeHtml(item.object_name)}</strong><p>${escapeHtml(item.current_judgment)}</p></div>`).join("") || '<p class="muted-copy">No judgment object yet.</p>'}
    </section>
    <section class="detail-section">
      <h3>Productized Capabilities</h3>
      ${renderProducts(payload.products)}
    </section>
    <section class="detail-section">
      <h3>Annual Financials</h3>
      ${renderFinancials(payload.financials)}
    </section>
  `;
  renderCompanies();
}

function renderGovernance() {
  $("fieldPolicyList").innerHTML = (state.data.fields || [])
    .slice(0, 24)
    .map(
      (item) => `
        <div class="policy-row">
          <strong>${escapeHtml(item.field_key)}</strong>
          <span>${escapeHtml(item.source_database || "")} / ${escapeHtml(item.field_type || "")} / ${escapeHtml(item.agent_permission || "")}</span>
        </div>`,
    )
    .join("");
  $("termList").innerHTML = (state.data.terms || [])
    .map(
      (item) => `
        <div class="policy-row">
          <strong>${escapeHtml(item.term_zh)} / ${escapeHtml(item.term_en)}</strong>
          <span>${escapeHtml(item.domain)} / ${escapeHtml(item.usage_note || "")}</span>
        </div>`,
    )
    .join("");
  $("governanceIssues").innerHTML = (state.data.governance || [])
    .map(
      (item) => `
        <div class="policy-row risk">
          <strong>${escapeHtml(item.scope)} / ${escapeHtml(item.field)}</strong>
          <span>${escapeHtml(item.issue)} / ${escapeHtml(item.recommended_action)}</span>
        </div>`,
    )
    .join("");
  const handoff = state.data.handoff?.states?.[0];
  const run = state.data.handoff?.runs?.[0];
  $("handoffState").innerHTML = `
    <div class="policy-row">
      <strong>${escapeHtml(handoff?.title || "No handoff")}</strong>
      <span>${escapeHtml(handoff?.summary || "")}</span>
    </div>
    <div class="policy-row">
      <strong>${escapeHtml(run?.run_id || "No run")}</strong>
      <span>records=${escapeHtml(run?.records_imported || 0)} / issues=${escapeHtml(run?.issues_found || 0)} / sources=${escapeHtml(run?.sources_checked || 0)}</span>
    </div>`;
}

function bindEvents() {
  $("localeToggle").addEventListener("click", () => {
    state.locale = state.locale === "zh" ? "en" : "zh";
    applyLocale();
    renderMetrics();
  });
  $("judgmentSearch").addEventListener("input", renderJudgmentList);
  $("companySearch").addEventListener("input", () => {
    renderCompanies();
    const first = filteredCompanies()[0];
    if (first && !state.selectedCompany) renderCompanyDetail(first.canonical_id);
  });
  $("formalOnly").addEventListener("change", (event) => {
    state.formalOnly = event.target.checked;
    renderJudgmentList();
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
  await loadData();
  applyLocale();
  bindEvents();
  renderMetrics();
  renderHeroPreview();
  renderSources();
  renderJudgmentList();
  renderJudgmentDetail(judgments()[0]?.id);
  renderCompanies();
  renderCompanyDetail(companies()[0]?.canonical_id);
  renderGovernance();
}

boot().catch((error) => {
  document.body.innerHTML = `<pre>${escapeHtml(error.stack || error.message)}</pre>`;
});
