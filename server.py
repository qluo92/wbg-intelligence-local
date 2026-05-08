from __future__ import annotations

import argparse
import json
import mimetypes
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from import_seed import DB_PATH, import_all


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def overview() -> dict:
    conn = connect()
    try:
        stats = {}
        for key, sql in {
            "companies": "SELECT COUNT(*) FROM companies",
            "products": "SELECT COUNT(*) FROM product_capabilities",
            "financial_rows": "SELECT COUNT(*) FROM financials",
            "governance_issues": "SELECT COUNT(*) FROM governance_issues",
            "source_registry": "SELECT COUNT(*) FROM source_registry",
            "field_policies": "SELECT COUNT(*) FROM field_dictionary",
            "judgment_objects": "SELECT COUNT(*) FROM judgment_objects",
            "evidence_items": "SELECT COUNT(*) FROM evidence_items",
            "locked_companies": "SELECT COUNT(*) FROM companies WHERE lock_flag=1",
            "review_companies": "SELECT COUNT(*) FROM companies WHERE review_flag=1",
        }.items():
            stats[key] = conn.execute(sql).fetchone()[0]
        tech_routes = rows_to_dicts(
            conn.execute(
                """
                SELECT technology_routes AS label, COUNT(*) AS value
                FROM companies
                WHERE technology_routes <> ''
                GROUP BY technology_routes
                ORDER BY value DESC
                LIMIT 8
                """
            ).fetchall()
        )
        run_state = rows_to_dicts(conn.execute("SELECT key, value, updated_at FROM run_state").fetchall())
        return {"stats": stats, "tech_routes": tech_routes, "run_state": run_state}
    finally:
        conn.close()


def companies(query: dict[str, list[str]]) -> dict:
    search = query.get("search", [""])[0].strip()
    material = query.get("material", [""])[0].strip()
    status = query.get("status", [""])[0].strip()
    clauses = []
    params: list[str] = []
    if search:
        clauses.append("(name LIKE ? OR chinese_name LIKE ? OR canonical_id LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like])
    if material:
        clauses.append("product_categories LIKE ?")
        params.append(f"%{material}%")
    if status:
        clauses.append("company_status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
      SELECT canonical_id, name, chinese_name, headquarters, product_categories,
             value_chain_roles, technology_routes, company_status, collection_status,
             review_flag, lock_flag, positioning
      FROM companies
      {where}
      ORDER BY name
      LIMIT 200
    """
    conn = connect()
    try:
        return {"items": rows_to_dicts(conn.execute(sql, params).fetchall())}
    finally:
        conn.close()


def company_detail(canonical_id: str) -> tuple[int, dict]:
    conn = connect()
    try:
        company = conn.execute("SELECT * FROM companies WHERE canonical_id = ?", (canonical_id,)).fetchone()
        if not company:
            return 404, {"error": "company not found"}
        financials = conn.execute(
            """
            SELECT fiscal_year, period_type, revenue, net_profit, ebit, rd_expense,
                   capex, fcf, currency, source_type, source_url, collection_status
            FROM financials
            WHERE canonical_id = ?
            ORDER BY fiscal_year DESC
            LIMIT 20
            """,
            (canonical_id,),
        ).fetchall()
        products = conn.execute(
            """
            SELECT capability_name, material_system, device_category, technology_tags,
                   voltage, target_applications, source_type, source_url, ingest_status,
                   ready_to_write, last_verified
            FROM product_capabilities
            WHERE canonical_id = ? OR lower(company_name) = lower(?)
            ORDER BY last_verified DESC, capability_name
            LIMIT 30
            """,
            (canonical_id, company["name"]),
        ).fetchall()
        judgments = conn.execute(
            """
            SELECT id, object_name, category, signal, current_judgment, evidence_summary,
                   confidence, boundary_condition, counter_signal, impact, change_note,
                   owner, updated_at, formal_status
            FROM judgment_objects
            WHERE company_id = ?
            ORDER BY updated_at DESC, object_name
            LIMIT 12
            """,
            (canonical_id,),
        ).fetchall()
        evidence = conn.execute(
            """
            SELECT object_type, object_id, source_url, source_type, evidence_excerpt,
                   confidence, formal_status, last_verified
            FROM evidence_items
            WHERE object_type IN ('product_capability', 'financial_period')
              AND object_id IN (
                SELECT CAST(id AS TEXT) FROM product_capabilities
                WHERE canonical_id = ? OR lower(company_name) = lower(?)
                UNION
                SELECT CAST(id AS TEXT) FROM financials WHERE canonical_id = ?
              )
            ORDER BY formal_status, last_verified DESC
            LIMIT 40
            """,
            (canonical_id, company["name"], canonical_id),
        ).fetchall()
        return 200, {
            "company": dict(company),
            "financials": rows_to_dicts(financials),
            "products": rows_to_dicts(products),
            "judgments": rows_to_dicts(judgments),
            "evidence": rows_to_dicts(evidence),
        }
    finally:
        conn.close()


def governance() -> dict:
    conn = connect()
    try:
        issues = conn.execute(
            """
            SELECT scope, field, issue, extra_in_schema, missing_in_schema, severity,
                   recommended_action, source_file
            FROM governance_issues
            ORDER BY severity, field
            """
        ).fetchall()
        return {"items": rows_to_dicts(issues)}
    finally:
        conn.close()


def source_registry() -> dict:
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT id, title, source_type, notion_url, data_source_url, priority,
                   product_role, active_status, notes
            FROM source_registry
            ORDER BY priority, title
            """
        ).fetchall()
        return {"items": rows_to_dicts(rows)}
    finally:
        conn.close()


def field_dictionary(limit: int = 260) -> dict:
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT id, field_key, source_database, display_order, field_type,
                   agent_permission, required_flag, source_requirement, lock_condition,
                   unit_policy, business_definition, governance_note, enum_values, source_file
            FROM field_dictionary
            ORDER BY source_database, display_order, field_key
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return {"items": rows_to_dicts(rows)}
    finally:
        conn.close()


def term_dictionary() -> dict:
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT id, term_zh, term_en, canonical_value, domain, usage_note, forbidden_translation
            FROM term_dictionary
            ORDER BY domain, term_zh
            """
        ).fetchall()
        return {"items": rows_to_dicts(rows)}
    finally:
        conn.close()


def judgment_objects(query: dict[str, list[str]] | None = None) -> dict:
    query = query or {}
    formal = query.get("formal", [""])[0]
    params: list[str] = []
    where = ""
    if formal:
        where = "WHERE formal_status = ?"
        params.append(formal)
    conn = connect()
    try:
        rows = conn.execute(
            f"""
            SELECT id, object_name, company_id, company_name, category, signal,
                   current_judgment, evidence_summary, confidence, boundary_condition,
                   counter_signal, impact, change_note, owner, updated_at, formal_status,
                   source_url
            FROM judgment_objects
            {where}
            ORDER BY updated_at DESC, object_name
            LIMIT 80
            """,
            params,
        ).fetchall()
        return {"items": rows_to_dicts(rows)}
    finally:
        conn.close()


def handoff() -> dict:
    conn = connect()
    try:
        states = conn.execute(
            "SELECT id, title, status, updated_at, summary, next_actions, risk_register FROM handoff_states ORDER BY updated_at DESC"
        ).fetchall()
        runs = conn.execute(
            "SELECT run_id, scope, status, started_at, completed_at, sources_checked, records_imported, candidates_created, issues_found, notes FROM ingestion_runs ORDER BY started_at DESC"
        ).fetchall()
        return {"states": rows_to_dicts(states), "runs": rows_to_dicts(runs)}
    finally:
        conn.close()


def all_company_details() -> dict[str, dict]:
    conn = connect()
    try:
        ids = [row[0] for row in conn.execute("SELECT canonical_id FROM companies ORDER BY name").fetchall()]
    finally:
        conn.close()
    payload: dict[str, dict] = {}
    for canonical_id in ids:
        status, detail = company_detail(canonical_id)
        if status == 200:
            payload[canonical_id] = detail
    return payload


def static_data_payload() -> dict:
    return {
        "overview": overview(),
        "companies": companies({})["items"],
        "companyDetails": all_company_details(),
        "governance": governance()["items"],
        "sources": source_registry()["items"],
        "fields": field_dictionary()["items"],
        "terms": term_dictionary()["items"],
        "judgments": judgment_objects({})["items"],
        "handoff": handoff(),
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        if relative.startswith(("zh/", "en/")):
            locale, remainder = relative.split("/", 1)
            if remainder in {"", "index.html", "styles.css", "app.js"}:
                relative = "index.html" if remainder == "" else remainder
        target = (STATIC_DIR / relative).resolve()
        if STATIC_DIR.resolve() not in target.parents and target != STATIC_DIR.resolve():
            self.send_error(403)
            return
        if not target.exists() or not target.is_file():
            self.send_error(404)
            return
        data = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if target.suffix in {".html", ".css", ".js"}:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/overview":
            self.send_json(overview())
            return
        if parsed.path == "/api/companies":
            self.send_json(companies(parse_qs(parsed.query)))
            return
        if parsed.path.startswith("/api/company/"):
            canonical_id = unquote(parsed.path.removeprefix("/api/company/"))
            status, payload = company_detail(canonical_id)
            self.send_json(payload, status=status)
            return
        if parsed.path == "/api/governance":
            self.send_json(governance())
            return
        if parsed.path == "/api/sources":
            self.send_json(source_registry())
            return
        if parsed.path == "/api/fields":
            self.send_json(field_dictionary())
            return
        if parsed.path == "/api/terms":
            self.send_json(term_dictionary())
            return
        if parsed.path == "/api/judgments":
            self.send_json(judgment_objects(parse_qs(parsed.query)))
            return
        if parsed.path == "/api/handoff":
            self.send_json(handoff())
            return
        if parsed.path in {"/data.json", "/zh/data.json", "/en/data.json"}:
            self.send_json(static_data_payload())
            return
        if parsed.path in {"/zh", "/zh/", "/en", "/en/", "/explorer", "/zh/explorer", "/en/explorer"}:
            self.send_static("/")
            return
        self.send_static(parsed.path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    if args.rebuild or not DB_PATH.exists():
        import_all(rebuild=args.rebuild)
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"WBG Intelligence local app running at http://{args.host}:{args.port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
