# WBG Intelligence Local App

本目录是宽禁带半导体行业数据库的本地代码化版本。

它不再把 Notion 当执行平台；Notion 导出的 CSV、审计文件和历史沉淀只作为种子数据与参考资料。

## 当前版本

最小可运行版本包含：

- 公司主库：从 `outputs/notion_company_directory_audit/company_directory_snapshot.csv` 导入
- 年度财务事实：从 `outputs/notion_finance_audit/annual_financials_snapshot.csv` 导入
- 产品化能力候选：从 `outputs/notion_product_governance/*candidate_manifest*.csv` 导入
- 治理风险：从 `company_directory_schema_issues.csv` 导入
- 本地 Web 前台：公司搜索、公司详情、财务表、产品能力、治理问题

## 启动

```powershell
python wbg_local_app\import_seed.py --rebuild
python wbg_local_app\server.py
```

打开：

```text
http://127.0.0.1:8765
```

## 设计原则

- 公司主库是中心锚点。
- 子维度事实围绕公司展开。
- 证据、状态、锁、待复核保留为一等字段。
- AI 可以生成候选和审计结果，但不能自动覆盖人工裁决。
- 本地 SQLite 是当前事实仓；后续可以迁移到 PostgreSQL 或其他数据库。
