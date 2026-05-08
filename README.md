# Tacive WBG Intelligence

Tacive WBG Intelligence is the first productized industry database in the Tacive project.

It turns the existing Notion research assets and local audit outputs into a code-hosted, source-linked wide-bandgap semiconductor intelligence workspace.

## Current release

- Company master data from `outputs/notion_company_directory_audit/company_directory_snapshot.csv`
- Annual financial facts from `outputs/notion_finance_audit/annual_financials_snapshot.csv`
- Verified productized capability records from `outputs/notion_product_governance/product_capability_publishable_release_verified_2026-05-07-12.csv`
- Governance risk records from `company_directory_schema_issues.csv`
- Static GitHub Pages delivery plus local SQLite service mode

## Run locally

```powershell
python import_seed.py --rebuild
python server.py
```

```text
http://127.0.0.1:8765
```

## Product principles

- Company master records are the anchor.
- Product, financial and future market/customer facts attach to companies.
- Evidence links, review flags, locks and governance issues remain visible.
- AI may generate candidates and audits, but it cannot silently overwrite human-confirmed facts.
- SQLite is the current portable fact store; PostgreSQL or a managed backend can replace it later.
