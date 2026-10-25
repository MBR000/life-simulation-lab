# 方法与复算说明 / Methods and reproduction notes

[中文 README](../README.md) · [English README](../README.en.md)

## 中文

### 这里保存了什么

报告保存了已生成的统计结果、图表与选定案例。`snaps.csv` 是 A 的年龄快照，`money_cny.csv` 是金额汇总；12 个 `A-*.json.gz` 是选出的模拟人生个案。
带实验前缀的 CSV 是相应实验的汇总或审计材料，并非完整原始人生记录。
各报告的方法章节还保留数据指纹、样本说明及原分析来源路径。

公开仓库缺少完整 `runs.jsonl`、`jobs.jsonl`、`raw/`、部分辅助文件及模拟引擎。
因此可以浏览发布结果、检查已公开表格与代码，也可以重新生成站点导航；不能仅用此仓库完整重做统计或生成新的模拟人生。
脚本中的原始校验断言说明了当时的处理要求，不表示本仓库已重新执行那些校验。

### 原分析源码的路径约定

当前分析和报告构建源码使用 Python 标准库，以及 `analyze_policy_reports` 等项目内模块；没有需要安装的第三方 Python 分析包。
这些源码是发布副本，保留了原始目录依赖：

| 来源 | 原始约定 |
| --- | --- |
| A、P1、P4 的实验内脚本 | 位于 `experiments/<实验名>/scripts/`，通过脚本父目录读取该实验的 `runs.jsonl`、`jobs.jsonl`、`raw/`、`tables/` 等 |
| B、C、C2、D 及多数 P/H 报告脚本 | 位于原项目根目录的 `scripts/`，读取 `experiments/<实验名>/`；部分还导入同目录辅助模块 |
| 原报告构建器 | 多数将发布文件写入原项目的 `work/github-pages-peers2002/`，并添加 `b_`、`p1_` 等下载文件前缀 |
| 当前站点发布器 | 本仓库的 `scripts/publish_site.py`，读取 `site/`，只更新入口页面与报告导航 |

复算前应按目标脚本及报告方法章节恢复其原始文件名、目录、辅助模块和完整输入。
不要把所有带前缀的源码去掉前缀后放进同一目录：不同实验的同名文件可能相互覆盖。
A 分析还读取 `tables/codes.json`；噪声比较依赖兄弟实验 `N_noise`；C2 还读取原项目 `work/data-run/c2-selection.json` 等输入。
这些要求不能由运行站点发布器代替。

### P1 出国实验的详细口径

P1 在五个国家设置中分别使用 1,000 对相同 seed，比较 `seek`（寻求出国）与 `avoid`（倾向留下），合计 10,000 次模拟人生。
报告提供人民币购买力金额、N2 随机路径敏感性参照、方针覆盖率，以及五组配对人生记录。

默认主比较只包含**成年后首次通过工作或留学出国**的人。工作与留学分别与各自的同 seed 对照比较，不能直接用两组金额判断哪条路径更好。
跨国收养、战争避难、随配偶外派、数字游牧后定居、晚年与子女团聚、原因未能确认，以及未成年工作或留学出国，均单列为描述性类别。

迁移下钻包括居住路径、首次与最终目的地、事件摘录。
成功条件比较按选定年龄筛选：对照截至该年龄没有观察到国外居住，且双方都有该年龄快照；`current` 口径还要求出国方当时仍住在国外。
`ever` 包含曾出国后已回国者。空配对人群不显示金额，不能当成零金额。

**成功筛选后的比较是描述性的。** 迁移成功与存活都会选择样本，配对不能消除这些选择偏差。
原始完整策略比较保留作参照；报告的随机路径参照章节不跟随成功路径筛选器变化。
年度快照可能漏掉年内迁移；只按明确事件证据分类，无法确认的原因保留为未知。

原发布说明记录了对全部 **770 种人群定义**的分区一致性检查：5 个国家 × 7 个年龄口径 × 2 种成功口径 × 11 种范围。
这是原发布时的校验记录；修改报告导航不会重新执行该统计校验。

### P1 的原始复算顺序

只有补齐原始数据后，以下步骤才适用：

1. 恢复原项目中的 `experiments/P1_abroad/scripts/` 和 `tables/`，补齐 P1 的任务、运行摘要、错误记录与全部 `raw/`。
2. 补齐兄弟目录 `experiments/N_noise/` 中所需的 N2 数据，以及 `experiments/A_peers2002/tables/birth_country.csv` 国家名称映射。
3. 将本仓库的 `p1_` 源码和模板恢复到上述 `scripts/` 并去掉 `p1_` 前缀。包括 `analyze.py`、`analyze_migration.py`、`analyze_success.py`、`build_report.py`、`report.template.html`、`migration.js`、`migration.section.html`、`success.js`、`success.section.html`。
4. 在恢复后的 `experiments/P1_abroad/` 目录，依次执行：

```sh
python scripts/analyze.py
python scripts/analyze_migration.py
python scripts/analyze_success.py
python scripts/build_report.py
```

基础分析先生成 `tables/analysis.json`；迁移分析生成 `migration.json` 与路径表；成功分析生成 `success.json` 与配对表；构建器再读取这些结果及模板。
同时须准备构建器使用的原项目发布目录 `work/github-pages-peers2002/`。
公开仓库中的 `p1_` CSV、Python、JS 和模板可用于核查方法，但不足以替代这些缺失输入。

## English

### What is included

Reports contain generated statistics, charts, and selected cases. `snaps.csv` contains A's age snapshots and `money_cny.csv` its monetary summaries; the 12 `A-*.json.gz` files are selected raw simulated lives.
Experiment-prefixed CSVs are published summaries or audit materials, not the complete original life records.
Report methods sections preserve data fingerprints, sample definitions, and original analysis paths.

The full `runs.jsonl`, `jobs.jsonl`, `raw/`, some auxiliary files, and the engine are absent.
You can read the published results, inspect public tables and code, and regenerate site navigation, but cannot fully rerun the analyses or create new simulated lives from this repository alone.
Assertions in the source document original validation requirements; their presence does not mean those validations have been rerun here.

### Original source layout

The current analysis and report-building sources use the Python standard library and local modules such as `analyze_policy_reports`; no third-party Python analysis packages are required.
The published copies retain their original path dependencies:

| Source | Original convention |
| --- | --- |
| Experiment-local scripts for A, P1, and P4 | Located in `experiments/<experiment>/scripts/`; read that experiment's `runs.jsonl`, `jobs.jsonl`, `raw/`, `tables/`, and related inputs through their parent directory |
| B, C, C2, D, and most P/H report scripts | Located in the original project-root `scripts/`; read `experiments/<experiment>/`, sometimes importing neighboring helper modules |
| Original report builders | Most publish to the original project's `work/github-pages-peers2002/`, adding download prefixes such as `b_` or `p1_` |
| Current site publisher | This repository's `scripts/publish_site.py`; reads `site/` and updates only entry pages and report navigation |

Restore filenames, directories, helper modules, and complete inputs according to the target source and its report's methods section before reanalysis.
Do not remove every prefix and place all sources in one folder: experiment-specific files with the same name may overwrite each other.
A also reads `tables/codes.json`; noise comparisons depend on the sibling `N_noise` experiment; C2 also reads inputs such as the original project's `work/data-run/c2-selection.json`.
Running the site publisher does not satisfy these dependencies.

### P1 migration definitions

P1 compares `seek` and `avoid` abroad policies for 1,000 same-seed pairs in each of five country settings, totaling 10,000 simulated lives.
It includes CNY purchasing-power amounts, N2 path-sensitivity references, policy coverage, and five paired-life logs.

The default primary comparison includes only **adult first departures for work or study**. Work and study are compared separately against their own same-seed controls; comparing their amounts directly does not establish which route is better.
Adoption, refugee flight, spouse postings, nomadic settlement, later-life family reunification, unknown routes, and minor work/study departures remain separate descriptive categories.

Residence-path drilldowns include first and final destinations and event excerpts.
Success-conditioned comparisons require no observed foreign residence in the control by the selected age and snapshots in both arms at that age. The `current` definition additionally requires the seek arm to still reside abroad.
The `ever` definition includes returnees. Empty matched cohorts display no amount, not zero.

**Success-conditioned comparisons are descriptive.** Both migration success and survival select the sample; pairing does not remove those selection biases.
The original full-policy comparison remains as a reference, and the path-sensitivity reference section does not change with the success/path filters.
Annual snapshots can miss within-year moves. Routes are classified only from explicit event evidence; ambiguous routes remain unknown.

The original publication notes report partition-consistency checks for all **770 cohort definitions**: 5 countries × 7 age definitions × 2 success modes × 11 scopes.
This records the original publication's validation, not a statistical check rerun by changing site navigation.

### Original P1 reproduction sequence

These steps apply only after obtaining the missing original data:

1. Restore `experiments/P1_abroad/scripts/` and `tables/` in the original project, plus P1's jobs, run summaries, error records, and complete `raw/` data.
2. Restore the required N2 data in sibling `experiments/N_noise/`, plus the country-name mapping in `experiments/A_peers2002/tables/birth_country.csv`.
3. Restore this repository's P1 sources and templates into that `scripts/` directory, removing their `p1_` prefixes: `analyze.py`, `analyze_migration.py`, `analyze_success.py`, `build_report.py`, `report.template.html`, `migration.js`, `migration.section.html`, `success.js`, and `success.section.html`.
4. From the restored `experiments/P1_abroad/` directory, run:

```sh
python scripts/analyze.py
python scripts/analyze_migration.py
python scripts/analyze_success.py
python scripts/build_report.py
```

Base analysis produces `tables/analysis.json`; migration analysis produces `migration.json` and route tables; success analysis produces `success.json` and paired tables; the builder reads those results and its templates.
Also prepare the original project's publishing directory, `work/github-pages-peers2002/`, expected by the builder.
The published `p1_` CSVs, Python, JS, and templates help inspect the methods, but cannot replace the missing inputs.
