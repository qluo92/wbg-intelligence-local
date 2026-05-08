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
PRODUCT_CANDIDATES = [
    PROJECT_ROOT / "outputs" / "notion_product_governance" / "product_capability_publishable_release_verified_2026-05-07-12.csv",
    PROJECT_ROOT / "outputs" / "notion_product_governance" / "product_capability_publishable_release_strict_2026-05-07-11.csv",
    PROJECT_ROOT / "outputs" / "notion_product_governance" / "product_capability_batch13_gated_final_2026-05-07-20_v3.csv",
    PROJECT_ROOT / "outputs" / "notion_product_governance" / "product_capability_batch13_candidate_manifest_manual_2026-05-07-20_v8.csv",
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
        conn.execute("DELETE FROM companies")
        name_to_id = import_companies(conn)
        import_financials(conn)
        product_source = import_products(conn, name_to_id)
        import_governance(conn)
        set_run_state(conn, "current_task", "本地化宽禁带行业数据库：公司主库 + 产品能力 + 财务事实 + 治理风险")
        set_run_state(conn, "seed_company_source", str(COMPANY_CSV.relative_to(PROJECT_ROOT)))
        set_run_state(conn, "seed_finance_source", str(FINANCIAL_CSV.relative_to(PROJECT_ROOT)))
        set_run_state(conn, "seed_product_source", product_source)
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
