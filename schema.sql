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

CREATE TABLE IF NOT EXISTS source_registry (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  notion_url TEXT,
  data_source_url TEXT,
  priority TEXT NOT NULL,
  product_role TEXT NOT NULL,
  active_status TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS field_dictionary (
  id TEXT PRIMARY KEY,
  field_key TEXT NOT NULL,
  source_database TEXT,
  display_order REAL,
  field_type TEXT,
  agent_permission TEXT,
  required_flag INTEGER DEFAULT 0,
  source_requirement TEXT,
  lock_condition TEXT,
  unit_policy TEXT,
  business_definition TEXT,
  governance_note TEXT,
  enum_values TEXT,
  source_file TEXT
);

CREATE TABLE IF NOT EXISTS term_dictionary (
  id TEXT PRIMARY KEY,
  term_zh TEXT NOT NULL,
  term_en TEXT NOT NULL,
  canonical_value TEXT NOT NULL,
  domain TEXT NOT NULL,
  usage_note TEXT,
  forbidden_translation TEXT
);

CREATE TABLE IF NOT EXISTS judgment_objects (
  id TEXT PRIMARY KEY,
  object_name TEXT NOT NULL,
  company_id TEXT,
  company_name TEXT,
  category TEXT NOT NULL,
  signal TEXT NOT NULL,
  current_judgment TEXT NOT NULL,
  evidence_summary TEXT NOT NULL,
  confidence TEXT NOT NULL,
  boundary_condition TEXT NOT NULL,
  counter_signal TEXT NOT NULL,
  impact TEXT NOT NULL,
  change_note TEXT NOT NULL,
  owner TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  formal_status TEXT NOT NULL,
  source_url TEXT,
  source_page_id TEXT,
  FOREIGN KEY (company_id) REFERENCES companies(canonical_id)
);

CREATE TABLE IF NOT EXISTS evidence_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  source_url TEXT,
  source_type TEXT,
  evidence_excerpt TEXT,
  confidence TEXT,
  formal_status TEXT NOT NULL,
  last_verified TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
  run_id TEXT PRIMARY KEY,
  scope TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  sources_checked INTEGER DEFAULT 0,
  records_imported INTEGER DEFAULT 0,
  candidates_created INTEGER DEFAULT 0,
  issues_found INTEGER DEFAULT 0,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS handoff_states (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  summary TEXT NOT NULL,
  next_actions TEXT NOT NULL,
  risk_register TEXT
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
CREATE INDEX IF NOT EXISTS idx_field_dictionary_key ON field_dictionary(field_key);
CREATE INDEX IF NOT EXISTS idx_judgment_company ON judgment_objects(company_id);
CREATE INDEX IF NOT EXISTS idx_evidence_object ON evidence_items(object_type, object_id);
