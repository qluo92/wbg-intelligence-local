PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS companies (
  canonical_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  chinese_name TEXT,
  website TEXT,
  headquarters TEXT,
  founded_year TEXT,
  employee_band TEXT,
  company_type TEXT,
  company_status TEXT,
  product_categories TEXT,
  value_chain_roles TEXT,
  technology_routes TEXT,
  global_footprint TEXT,
  positioning TEXT,
  collection_status TEXT,
  review_flag INTEGER DEFAULT 0,
  lock_flag INTEGER DEFAULT 0,
  last_collected TEXT,
  source_page_id TEXT
);

CREATE TABLE IF NOT EXISTS financials (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  canonical_id TEXT,
  company_name TEXT,
  fiscal_year TEXT,
  period_type TEXT,
  revenue REAL,
  net_profit REAL,
  ebit REAL,
  rd_expense REAL,
  capex REAL,
  ocf REAL,
  fcf REAL,
  cash REAL,
  total_debt REAL,
  currency TEXT,
  source_type TEXT,
  source_url TEXT,
  collection_status TEXT,
  review_flag INTEGER DEFAULT 0,
  lock_flag INTEGER DEFAULT 0,
  note TEXT,
  FOREIGN KEY (canonical_id) REFERENCES companies(canonical_id)
);

CREATE TABLE IF NOT EXISTS product_capabilities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  canonical_id TEXT,
  company_name TEXT NOT NULL,
  capability_name TEXT NOT NULL,
  material_system TEXT,
  device_category TEXT,
  technology_tags TEXT,
  voltage TEXT,
  target_applications TEXT,
  platform_positioning TEXT,
  product_status TEXT,
  commercial_maturity TEXT,
  disclosure_type TEXT,
  source_type TEXT,
  source_url TEXT,
  evidence_excerpt TEXT,
  credibility TEXT,
  ingest_status TEXT,
  ready_to_write TEXT,
  decision_reason TEXT,
  last_verified TEXT,
  FOREIGN KEY (canonical_id) REFERENCES companies(canonical_id)
);

CREATE TABLE IF NOT EXISTS governance_issues (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scope TEXT NOT NULL,
  field TEXT NOT NULL,
  issue TEXT NOT NULL,
  extra_in_schema TEXT,
  missing_in_schema TEXT,
  actual_value TEXT,
  manual_value TEXT,
  severity TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  source_file TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_financials_company ON financials(canonical_id);
CREATE INDEX IF NOT EXISTS idx_products_company ON product_capabilities(canonical_id);
CREATE INDEX IF NOT EXISTS idx_products_company_name ON product_capabilities(company_name);
CREATE INDEX IF NOT EXISTS idx_governance_scope ON governance_issues(scope);
