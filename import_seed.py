from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
DB_PATH = APP_DIR / "data" / "wbg_intelligence.db"
SCHEMA_PATH = APP_DIR / "schema.sql"

COMPANY_CSV = PROJECT_ROOT / "outputs" / "notion_company_directory_audit" / "company_directory_snapshot.csv"
SCHEMA_ISSUES_CSV = PROJECT_ROOT / "outputs" / "notion_company_directory_audit" / "company_directory_schema_issues.csv"
FINANCIAL_CSV = PROJECT_ROOT / "outputs" / "notion_finance_audit" / "annual_financials_snapshot.csv"
FINANCE_PROFILE_CSV = PROJECT_ROOT / "outputs" / "notion_finance_audit" / "finance_profile_snapshot.csv"
CAPITAL_EVENTS_CSV = PROJECT_ROOT / "outputs" / "notion_finance_audit" / "capital_events_snapshot.csv"
FIELD_DICTIONARY_CSV = PROJECT_ROOT / "outputs" / "notion_finance_audit" / "field_governance_manual_review_snapshot.csv"
PRODUCT_CANDIDATES = [
    PROJECT_ROOT / "outputs" / "notion_product_governance" / "product_capability_publishable_release_verified_2026-05-07-12.csv",
    PROJECT_ROOT / "outputs" / "notion_product_governance" / "product_capability_publishable_release_strict_2026-05-07-11.csv",
    PROJECT_ROOT / "outputs" / "notion_product_governance" / "product_capability_batch13_gated_final_2026-05-07-20_v3.csv",
    PROJECT_ROOT / "outputs" / "notion_product_governance" / "product_capability_batch13_candidate_manifest_manual_2026-05-07-20_v8.csv",
]

SOURCE_REGISTRY = [
    {
        "id": "brand-system-v2",
        "title": "Tacive｜Brand System v2｜Active Source of Truth",
        "source_type": "Notion brand source",
        "notion_url": "https://www.notion.so/34c61c48368c819fa8f3c7af3d85f192",
        "data_source_url": "",
        "priority": "Active",
        "product_role": "Highest brand, narrative, and execution constraint",
        "active_status": "active",
        "notes": "Overrides historical brand documents.",
    },
    {
        "id": "homepage-messaging-v2",
        "title": "Tacive｜Homepage Messaging v2｜判断资产版",
        "source_type": "Notion brand source",
        "notion_url": "https://www.notion.so/34c61c48368c813da0d2e21227c01974",
        "data_source_url": "",
        "priority": "Active",
        "product_role": "Homepage copy and module source",
        "active_status": "active",
        "notes": "No freeform hero copy outside this source.",
    },
    {
        "id": "explorer-spec-v2",
        "title": "Tacive｜Explorer Spec v2｜Judgment Object Database",
        "source_type": "Notion product spec",
        "notion_url": "https://www.notion.so/34c61c48368c81d183a5c350e49f3685",
        "data_source_url": "",
        "priority": "Active",
        "product_role": "Explorer layout and judgment object grammar",
        "active_status": "active",
        "notes": "Explorer must not become a dashboard or news feed.",
    },
    {
        "id": "brand-guidelines-mini-v1",
        "title": "Tacive｜Brand Guidelines Mini v1",
        "source_type": "Notion brand source",
        "notion_url": "https://www.notion.so/34a61c48368c816e8587e3d82c36f798",
        "data_source_url": "",
        "priority": "Active",
        "product_role": "Color, type, density, and visual constraints",
        "active_status": "active",
        "notes": "Dark mode, semantic accents, restrained operational UI.",
    },
    {
        "id": "field-governance-manual",
        "title": "字段治理手册",
        "source_type": "Notion data source",
        "notion_url": "https://www.notion.so/a3b6a654fb0b4a8fa0e1ec73210754b0",
        "data_source_url": "collection://e30ae913-2b66-4288-8af1-40cdc766a7fd",
        "priority": "Active",
        "product_role": "Machine-readable field policy and quality gate source",
        "active_status": "active",
        "notes": "Compiled from local snapshot when live querying is unavailable.",
    },
    {
        "id": "company-directory",
        "title": "产业公司名录",
        "source_type": "Notion data source",
        "notion_url": "https://www.notion.so/11b61c48368c8058af6cf46b5d5bba32",
        "data_source_url": "collection://b3fdb1b6-56a2-47c6-ad24-85c126abb4f7",
        "priority": "Active",
        "product_role": "Company master and Canonical ID anchor",
        "active_status": "active",
        "notes": "Customer-deliverable gate depends on source, confidence, and lock fields.",
    },
    {
        "id": "product-capability-map",
        "title": "宽禁带半导体｜产品化能力图谱",
        "source_type": "Notion data source",
        "notion_url": "https://www.notion.so/96bd43f9627e446cad015d1c2ef0e015",
        "data_source_url": "collection://96936691-e986-4e32-9cd3-4f8e0b671b97",
        "priority": "Active",
        "product_role": "Productized capability and roadmap signal source",
        "active_status": "active",
        "notes": "Formal rows require source URL, evidence excerpt, and Tier 1/2 credibility.",
    },
    {
        "id": "industry-dynamics",
        "title": "产业动态追踪",
        "source_type": "Notion product page",
        "notion_url": "https://www.notion.so/5d09cc1584564d6e8086ff58a8803b50",
        "data_source_url": "",
        "priority": "Active",
        "product_role": "Finance, product, technology, market, customer module index",
        "active_status": "active",
        "notes": "Defines the multidimensional industry database structure.",
    },
]

TERMS = [
    ("term-wbg", "宽禁带半导体", "wide-bandgap semiconductors / WBG semiconductors", "wbg_semiconductors", "industry", "Use WBG after first mention.", ""),
    ("term-sic", "碳化硅", "silicon carbide / SiC", "sic", "material", "Chinese UI may show 碳化硅（SiC）.", ""),
    ("term-gan", "氮化镓", "gallium nitride / GaN", "gan", "material", "Chinese UI may show 氮化镓（GaN）.", ""),
    ("term-ga2o3", "氧化镓", "gallium oxide / Ga2O3", "ga2o3", "material", "Use Ga2O3 in ASCII code paths; render Ga₂O₃ only in display text when safe.", ""),
    ("term-substrate", "衬底", "substrate", "substrate", "value_chain", "", ""),
    ("term-epitaxy", "外延", "epitaxy", "epitaxy", "value_chain", "", ""),
    ("term-foundry", "芯片生产（Foundry）", "wafer fabrication / foundry", "foundry", "value_chain", "Use foundry when the source means contract manufacturing.", ""),
    ("term-packaging", "封装测试", "packaging and testing", "packaging_testing", "value_chain", "", ""),
    ("term-design-in", "Design-in", "design-in", "design_in", "customer", "Keep English in Chinese UI.", "设计导入"),
    ("term-design-win", "Design-win", "design-win", "design_win", "customer", "Keep English in Chinese UI.", "设计赢单"),
    ("term-judgment-object", "判断对象", "Judgment Object", "judgment_object", "tacive", "Core Explorer record grammar.", "insight card"),
    ("term-judgment-asset", "判断资产", "Judgment Asset", "judgment_asset", "tacive", "Use for maintained strategic judgments.", "content asset"),
    ("term-competitor-roadmap", "竞品路线图数据库", "Competitor Roadmap Database", "competitor_roadmap_database", "tacive", "Current commercial wedge.", "dashboard"),
    ("term-evidence", "证据摘录", "evidence excerpt", "evidence_excerpt", "governance", "", ""),
    ("term-confidence", "置信度", "confidence", "confidence", "governance", "", ""),
    ("term-boundary", "边界条件", "boundary condition", "boundary_condition", "governance", "", ""),
    ("term-counter-signal", "反证信号", "counter-signal", "counter_signal", "governance", "", ""),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def first_present(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return ""


def to_bool(value: str) -> int:
    return 1 if str(value).strip().lower() in {"yes", "true", "1", "✓", "__yes__"} else 0


def to_float(value: str) -> float | None:
    value = str(value or "").strip().replace(",", "")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def compact_jsonish(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    try:
        loaded: Any = json.loads(value)
    except json.JSONDecodeError:
        return value
    if isinstance(loaded, list):
        return ", ".join(str(item) for item in loaded)
    return str(loaded)


def initialize_db(db_path: Path, rebuild: bool = False) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if rebuild and db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def import_companies(conn: sqlite3.Connection) -> dict[str, str]:
    rows = read_csv(COMPANY_CSV)
    name_to_id: dict[str, str] = {}
    for row in rows:
        canonical_id = first_present(row, "Canonical ID")
        name = first_present(row, "公司名称")
        if not canonical_id or not name:
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO companies (
              canonical_id, name, chinese_name, website, headquarters, founded_year,
              employee_band, company_type, company_status, product_categories,
              value_chain_roles, technology_routes, global_footprint, positioning,
              collection_status, review_flag, lock_flag, last_collected, source_page_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                canonical_id,
                name,
                first_present(row, "中文名称"),
                first_present(row, "官网"),
                first_present(row, "总部所在地"),
                first_present(row, "成立年份"),
                first_present(row, "员工数量"),
                first_present(row, "公司类型"),
                first_present(row, "公司状态"),
                first_present(row, "产品分类"),
                first_present(row, "产业链环节"),
                first_present(row, "主要技术路线"),
                first_present(row, "全球业务布局"),
                first_present(row, "一句话定位"),
                first_present(row, "采集状态"),
                to_bool(first_present(row, "待审核")),
                to_bool(first_present(row, "人工确认锁")),
                first_present(row, "最后采集时间"),
                first_present(row, "page_id"),
            ),
        )
        name_to_id[name.lower()] = canonical_id
        alias_blob = first_present(row, "别名 Aliases")
        for alias in alias_blob.replace(";", "\n").splitlines():
            alias = alias.strip()
            if alias:
                name_to_id[alias.lower()] = canonical_id
    return name_to_id


def import_financials(conn: sqlite3.Connection) -> None:
    for row in read_csv(FINANCIAL_CSV):
        canonical_id = first_present(row, "_normalized_canonical_id", "公司筛选ID")
        if not canonical_id:
            continue
        conn.execute(
            """
            INSERT INTO financials (
              canonical_id, company_name, fiscal_year, period_type, revenue, net_profit,
              ebit, rd_expense, capex, ocf, fcf, cash, total_debt, currency,
              source_type, source_url, collection_status, review_flag, lock_flag, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                canonical_id,
                first_present(row, "_normalized_company_name"),
                first_present(row, "财年", "title"),
                first_present(row, "期间类型"),
                to_float(first_present(row, "营收（百万）")),
                to_float(first_present(row, "净利润（百万）")),
                to_float(first_present(row, "营业利润/EBIT（百万）")),
                to_float(first_present(row, "研发支出（百万）", "GAAP 研发支出（百万）")),
                to_float(first_present(row, "资本开支 CapEx（百万）")),
                to_float(first_present(row, "经营现金流 OCF（百万）")),
                to_float(first_present(row, "自由现金流 FCF（百万）")),
                to_float(first_present(row, "期末现金及等价物（百万）")),
                to_float(first_present(row, "总债务（百万）")),
                first_present(row, "货币"),
                first_present(row, "来源类型"),
                first_present(row, "来源链接"),
                first_present(row, "采集状态"),
                to_bool(first_present(row, "待审核")),
                to_bool(first_present(row, "人工确认锁")),
                first_present(row, "备注"),
            ),
        )


def product_source_path() -> Path | None:
    for path in PRODUCT_CANDIDATES:
        if path.exists():
            return path
    files = sorted(
        (PROJECT_ROOT / "outputs" / "notion_product_governance").glob("*candidate_manifest*.csv"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def import_products(conn: sqlite3.Connection, name_to_id: dict[str, str]) -> str:
    path = product_source_path()
    if not path:
        return ""
    for row in read_csv(path):
        company_name = first_present(row, "company", "公司文本")
        canonical_id = name_to_id.get(company_name.lower()) or None
        conn.execute(
            """
            INSERT INTO product_capabilities (
              canonical_id, company_name, capability_name, material_system, device_category,
              technology_tags, voltage, target_applications, platform_positioning,
              product_status, commercial_maturity, disclosure_type, source_type, source_url,
              evidence_excerpt, credibility, ingest_status, ready_to_write, decision_reason,
              last_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                canonical_id,
                company_name,
                first_present(row, "product_capability_name", "产品化能力名称"),
                compact_jsonish(first_present(row, "material_system", "材料体系")),
                compact_jsonish(first_present(row, "device_category", "器件/能力类别")),
                compact_jsonish(first_present(row, "tech_tags", "标准技术标签")),
                compact_jsonish(first_present(row, "voltage", "器件电压等级")),
                compact_jsonish(first_present(row, "target_app", "目标应用")),
                compact_jsonish(first_present(row, "platform_positioning", "产品归属类型")),
                first_present(row, "product_status", "产品状态"),
                first_present(row, "commercial_maturity", "商业成熟度"),
                first_present(row, "disclosure_type", "治理验证方式"),
                first_present(row, "source_type", "来源类型"),
                first_present(row, "source_url", "来源链接"),
                first_present(row, "evidence_excerpt", "证据摘录")[:1200],
                first_present(row, "credibility", "可信度"),
                first_present(row, "ingest_status", "入库状态"),
                first_present(row, "ready_to_write", "gated_ready_to_write"),
                first_present(row, "decision_reason", "gated_reason", "治理验证状态"),
                first_present(row, "last_verified", "最后核验时间"),
            ),
        )
    return str(path.relative_to(PROJECT_ROOT))


def import_governance(conn: sqlite3.Connection) -> None:
    for row in read_csv(SCHEMA_ISSUES_CSV):
        conn.execute(
            """
            INSERT INTO governance_issues (
              scope, field, issue, extra_in_schema, missing_in_schema, actual_value,
              manual_value, severity, recommended_action, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "产业公司名录",
                first_present(row, "field"),
                first_present(row, "issue"),
                first_present(row, "extra_in_schema"),
                first_present(row, "missing_in_schema"),
                first_present(row, "actual"),
                first_present(row, "manual"),
                "P1",
                "待人工裁决：决定修手册还是修数据库 schema",
                str(SCHEMA_ISSUES_CSV.relative_to(PROJECT_ROOT)),
            ),
        )


def import_source_registry(conn: sqlite3.Connection) -> None:
    for row in SOURCE_REGISTRY:
        conn.execute(
            """
            INSERT OR REPLACE INTO source_registry (
              id, title, source_type, notion_url, data_source_url, priority,
              product_role, active_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                row["title"],
                row["source_type"],
                row["notion_url"],
                row["data_source_url"],
                row["priority"],
                row["product_role"],
                row["active_status"],
                row["notes"],
            ),
        )


def import_field_dictionary(conn: sqlite3.Connection) -> None:
    for index, row in enumerate(read_csv(FIELD_DICTIONARY_CSV), start=1):
        field_key = first_present(row, "title", "字段键")
        if not field_key:
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO field_dictionary (
              id, field_key, source_database, display_order, field_type,
              agent_permission, required_flag, source_requirement, lock_condition,
              unit_policy, business_definition, governance_note, enum_values, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                first_present(row, "id") or f"field-{index:04d}",
                field_key,
                first_present(row, "db", "所属数据库"),
                to_float(first_present(row, "order", "展示顺序")),
                first_present(row, "type", "字段类型"),
                first_present(row, "perm", "Agent 权限"),
                to_bool(first_present(row, "req", "必填")),
                first_present(row, "source", "来源要求"),
                first_present(row, "lock", "锁条件"),
                first_present(row, "unit", "单位/口径"),
                first_present(row, "def", "业务定义"),
                first_present(row, "note", "治理备注"),
                first_present(row, "enum", "枚举值 / 取值域"),
                str(FIELD_DICTIONARY_CSV.relative_to(PROJECT_ROOT)) if FIELD_DICTIONARY_CSV.exists() else "",
            ),
        )


def import_term_dictionary(conn: sqlite3.Connection) -> None:
    for row in TERMS:
        conn.execute(
            """
            INSERT OR REPLACE INTO term_dictionary (
              id, term_zh, term_en, canonical_value, domain, usage_note, forbidden_translation
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )


def classify_formal_status(source_url: str, confidence: str, status: str) -> str:
    blob = f"{confidence} {status}".lower()
    if not source_url:
        return "Needs Review"
    if "tier 1" in blob or "tier 2" in blob or "已入库" in status or "verified" in blob:
        return "Formal"
    if "推断" in confidence or "tier 3" in blob:
        return "Candidate"
    return "Needs Review"


def import_evidence_items(conn: sqlite3.Connection) -> None:
    products = conn.execute(
        """
        SELECT id, source_url, source_type, evidence_excerpt, credibility, ingest_status, last_verified
        FROM product_capabilities
        WHERE source_url <> '' OR evidence_excerpt <> ''
        """
    ).fetchall()
    for row in products:
        conn.execute(
            """
            INSERT INTO evidence_items (
              object_type, object_id, source_url, source_type, evidence_excerpt,
              confidence, formal_status, last_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "product_capability",
                str(row["id"]),
                row["source_url"],
                row["source_type"],
                row["evidence_excerpt"],
                row["credibility"],
                classify_formal_status(row["source_url"], row["credibility"], row["ingest_status"]),
                row["last_verified"],
            ),
        )
    financials = conn.execute(
        """
        SELECT id, source_url, source_type, collection_status, fiscal_year
        FROM financials
        WHERE source_url <> ''
        """
    ).fetchall()
    for row in financials:
        conn.execute(
            """
            INSERT INTO evidence_items (
              object_type, object_id, source_url, source_type, evidence_excerpt,
              confidence, formal_status, last_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "financial_period",
                str(row["id"]),
                row["source_url"],
                row["source_type"],
                f"Financial period source for {row['fiscal_year']}",
                row["collection_status"],
                classify_formal_status(row["source_url"], row["source_type"], row["collection_status"]),
                "",
            ),
        )


def import_judgment_objects(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT c.canonical_id, c.name, c.product_categories, c.technology_routes, c.value_chain_roles,
               c.positioning, COUNT(p.id) AS product_count,
               SUM(CASE WHEN p.source_url <> '' THEN 1 ELSE 0 END) AS sourced_products,
               MAX(p.last_verified) AS last_verified
        FROM companies c
        LEFT JOIN product_capabilities p
          ON p.canonical_id = c.canonical_id OR lower(p.company_name) = lower(c.name)
        GROUP BY c.canonical_id
        HAVING product_count > 0
        ORDER BY sourced_products DESC, product_count DESC, c.name
        LIMIT 24
        """
    ).fetchall()
    for index, row in enumerate(rows, start=1):
        material = row["product_categories"] or "WBG"
        routes = row["technology_routes"] or "route not normalized"
        value_chain = row["value_chain_roles"] or "value-chain role not normalized"
        confidence = "Medium-high" if row["sourced_products"] and row["sourced_products"] == row["product_count"] else "Medium"
        formal_status = "Formal" if row["sourced_products"] else "Needs Review"
        object_id = f"jo-{row['canonical_id'].lower()}-{index:02d}"
        conn.execute(
            """
            INSERT OR REPLACE INTO judgment_objects (
              id, object_name, company_id, company_name, category, signal,
              current_judgment, evidence_summary, confidence, boundary_condition,
              counter_signal, impact, change_note, owner, updated_at, formal_status,
              source_url, source_page_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                object_id,
                f"{row['name']} productized capability posture",
                row["canonical_id"],
                row["name"],
                "Competitor roadmap",
                f"{row['name']} has {row['product_count']} productized capability records attached to the company profile.",
                f"{row['name']} should be tracked as a {material} competitor object across {value_chain}; current route signal: {routes}.",
                f"{row['sourced_products']} of {row['product_count']} product capability records include source links in the current local release.",
                confidence,
                "This judgment describes public product and roadmap posture captured in the database, not confirmed revenue mix or undisclosed customer adoption.",
                "If source coverage is incomplete or product records lack representative model anchors, the judgment remains provisional.",
                "Affects competitor roadmap tracking, product capability comparison, and company 360 prioritization.",
                "Generated from Notion-derived company and product capability records during the Notion-first implementation pass.",
                "Tacive data system",
                row["last_verified"] or "2026-05-08",
                formal_status,
                "",
                "",
            ),
        )


def import_handoff_state(conn: sqlite3.Connection) -> None:
    records_imported = (
        conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        + conn.execute("SELECT COUNT(*) FROM product_capabilities").fetchone()[0]
        + conn.execute("SELECT COUNT(*) FROM financials").fetchone()[0]
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO ingestion_runs (
          run_id, scope, status, completed_at, sources_checked, records_imported,
          candidates_created, issues_found, notes
        ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
        """,
        (
            "run-2026-05-08-notion-first-implementation",
            "Notion-first local product implementation",
            "completed",
            len(SOURCE_REGISTRY),
            records_imported,
            conn.execute("SELECT COUNT(*) FROM judgment_objects WHERE formal_status <> 'Formal'").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM governance_issues").fetchone()[0],
            "First executable pass: source registry, field dictionary, terms, judgment objects, evidence and handoff state.",
        ),
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO handoff_states (
          id, title, status, summary, next_actions, risk_register
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "handoff-latest",
            "Tacive WBG Intelligence Notion-first implementation",
            "active",
            "Static/SQLite product now carries Notion source registry, field dictionary, term dictionary, judgment objects, evidence items and bilingual Explorer shell.",
            "Next: expand live Notion row syncing for technology, market, customer and capital-event tables; migrate static prototype to Next/Postgres when product shell stabilizes.",
            "Current local source still depends on CSV snapshots for rows; formal paid view must continue filtering out missing-source facts.",
        ),
    )


def set_run_state(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO run_state (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
        """,
        (key, value),
    )


def import_all(rebuild: bool = False) -> Path:
    conn = initialize_db(DB_PATH, rebuild=rebuild)
    with conn:
        conn.execute("DELETE FROM financials")
        conn.execute("DELETE FROM product_capabilities")
        conn.execute("DELETE FROM governance_issues")
        conn.execute("DELETE FROM source_registry")
        conn.execute("DELETE FROM field_dictionary")
        conn.execute("DELETE FROM term_dictionary")
        conn.execute("DELETE FROM judgment_objects")
        conn.execute("DELETE FROM evidence_items")
        conn.execute("DELETE FROM ingestion_runs")
        conn.execute("DELETE FROM handoff_states")
        conn.execute("DELETE FROM companies")
        name_to_id = import_companies(conn)
        import_financials(conn)
        product_source = import_products(conn, name_to_id)
        import_governance(conn)
        import_source_registry(conn)
        import_field_dictionary(conn)
        import_term_dictionary(conn)
        import_evidence_items(conn)
        import_judgment_objects(conn)
        import_handoff_state(conn)
        set_run_state(conn, "current_task", "Tacive WBG Intelligence: Notion-first homepage, Explorer, field policy, evidence and judgment object system")
        set_run_state(conn, "seed_company_source", str(COMPANY_CSV.relative_to(PROJECT_ROOT)))
        set_run_state(conn, "seed_finance_source", str(FINANCIAL_CSV.relative_to(PROJECT_ROOT)))
        set_run_state(conn, "seed_product_source", product_source)
        set_run_state(conn, "seed_field_dictionary_source", str(FIELD_DICTIONARY_CSV.relative_to(PROJECT_ROOT)) if FIELD_DICTIONARY_CSV.exists() else "Notion field governance manual")
        set_run_state(conn, "notion_priority", "Brand System v2 > Homepage Messaging v2 > Explorer Spec v2 > Field Governance Manual > WBG core databases")
    conn.close()
    return DB_PATH


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="recreate the SQLite database")
    args = parser.parse_args()
    db_path = import_all(rebuild=args.rebuild)
    print(f"Seeded local WBG database: {db_path}")


if __name__ == "__main__":
    main()
