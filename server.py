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
        return 200, {
            "company": dict(company),
            "financials": rows_to_dicts(financials),
            "products": rows_to_dicts(products),
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
