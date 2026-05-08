# Tacive WBG Intelligence Handoff

Updated: 2026-05-08

## Current Status

This repository now contains the first Notion-first implementation pass for Tacive WBG Intelligence.

- Product surface: bilingual Tacive homepage plus Explorer and Company 360 workspace.
- Data layer: SQLite database compiled from local Notion snapshots.
- Governance layer: source registry, field dictionary, term dictionary, evidence items, judgment objects, ingestion run, and handoff state.
- Static delivery: `docs/` export supports `/`, `/zh/`, and `/en/`.

## Active Notion Sources

- `Tacive｜Brand System v2｜Active Source of Truth`
- `Tacive｜Homepage Messaging v2｜判断资产版`
- `Tacive｜Explorer Spec v2｜Judgment Object Database`
- `Tacive｜Website + Explorer Brand Application v1`
- `Tacive｜品牌资料版本治理表 v1`
- `Tacive｜Brand Guidelines Mini v1`
- `字段治理手册`
- `产业动态追踪`
- WBG company, product capability, finance, technology, market, and customer/design-in databases

## Current Data Counts

- Companies: 138
- Product capabilities: 70
- Annual financial records: 411
- Field policies: 87
- Term dictionary entries: 17
- Judgment objects: 24
- Evidence items: 481
- Governance issues: 3

## How To Run

```powershell
cd "C:\Users\MK 14\Documents\New project\wbg_local_app"
python import_seed.py --rebuild
python server.py --port 8765
```

Open:

- `http://127.0.0.1:8765/zh/`
- `http://127.0.0.1:8765/en/`

Static export:

```powershell
python export_static.py
```

UI smoke test:

```powershell
npm install
npm run test:ui
```

## Verification Completed

- Python syntax check passed: `python -m py_compile import_seed.py server.py export_static.py`
- Database rebuild passed: `python import_seed.py --rebuild`
- Static export passed: `python export_static.py`
- Browser screenshots captured:
  - `output/playwright/tacive-zh-home-wait.png`
  - `output/playwright/tacive-en-home.png`
- Playwright smoke test passed: 2 tests

## Remaining Product Risks

- Only the already verified product capability release snapshot is in the Formal product view; technology, market, customer/design-in tables still need deeper importers.
- Judgment objects are generated from imported product capability posture first; deeper human-authored judgment grammars should be pulled from future Notion judgment records when available.
- Finance profile and capital events snapshots are registered but not yet fully surfaced in Company 360.
- The current data is suitable as a governed product skeleton, not yet a final paid database without expanded source verification and coverage review.

## Next Actions

1. Import and expose finance profile and capital events as first-class Company 360 sections.
2. Build importers for technology profiles, market data, and customer/design-in records.
3. Add field-dictionary-derived validation failures for enum boundary, read-only write, and lock override.
4. Add source drill-down pages for evidence and Notion provenance.
5. Expand company detail QA to at least five representative companies.
