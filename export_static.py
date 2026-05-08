from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

from import_seed import DB_PATH, import_all
from server import companies, company_detail, field_dictionary, governance, handoff, judgment_objects, overview, source_registry, term_dictionary


APP_DIR = Path(__file__).resolve().parent
SITE_DIR = APP_DIR / "docs"
STATIC_DIR = APP_DIR / "static"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def all_company_details() -> dict[str, dict]:
    conn = connect()
    try:
        ids = [row[0] for row in conn.execute("SELECT canonical_id FROM companies ORDER BY name").fetchall()]
    finally:
        conn.close()
    details: dict[str, dict] = {}
    for canonical_id in ids:
        status, payload = company_detail(canonical_id)
        if status == 200:
            details[canonical_id] = payload
    return details


def export_static() -> Path:
    if not DB_PATH.exists():
        import_all(rebuild=True)
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    for name in ["index.html", "styles.css", "app.js"]:
        shutil.copy2(STATIC_DIR / name, SITE_DIR / name)
    if (STATIC_DIR / "assets").exists():
        shutil.copytree(STATIC_DIR / "assets", SITE_DIR / "assets", dirs_exist_ok=True)
    payload = {
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
    data_json = json.dumps(payload, ensure_ascii=False, indent=2)
    (SITE_DIR / "data.json").write_text(data_json, encoding="utf-8")
    for locale in ["zh", "en"]:
        locale_dir = SITE_DIR / locale
        locale_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(STATIC_DIR / "index.html", locale_dir / "index.html")
        shutil.copy2(STATIC_DIR / "styles.css", locale_dir / "styles.css")
        shutil.copy2(STATIC_DIR / "app.js", locale_dir / "app.js")
        if (STATIC_DIR / "assets").exists():
            shutil.copytree(STATIC_DIR / "assets", locale_dir / "assets", dirs_exist_ok=True)
        (locale_dir / "data.json").write_text(data_json, encoding="utf-8")
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    return SITE_DIR


def main() -> None:
    site = export_static()
    print(f"Exported static site: {site}")


if __name__ == "__main__":
    main()
