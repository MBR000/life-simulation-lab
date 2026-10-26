# Life Simulation Lab

[简体中文](README.md) · [English](README.en.md)

Interactive reports exploring how starting conditions, choices, and randomness shape simulated lives.
Start with 10,000 people born in the same year, then vary birthplace, birth year, life strategy, and a single decision.

**[Read online](https://mbr000.github.io/life-simulation-lab/) · [Stories and essays](https://mbr000.github.io/life-simulation-lab/library.html) (Chinese) · [All 15 reports](https://mbr000.github.io/life-simulation-lab/reports.html)**

This is a **static report and analysis-material repository** based on engine v0.8.30 outputs, with charts, paired cases, summary CSVs, and analysis source.
The simulation engine and complete original experiment data are not included. Results describe the simulator, not real populations or personal predictions.

> All results come from the 1in8b v0.8.30 engine archived on 2026-10-24. The live game has since moved to the v0.8.40 beta, so its rules may differ.

## Stories and essays

The [reading library](library.html) (Chinese) has three essays that connect the main findings and three stories drawn from raw life records: one persona born in nine countries, one decision changed at age 14, and twelve peers born in 2002. Story text only links engine log entries; quoted lines are verbatim.

## Start with the five core reports

Reading order: **A → B → D → C → C2**. Understand the distribution, explore starting conditions, then examine choices.

| Order | Report | Question |
| --- | --- | --- |
| 1 | [A · What happened to 10,000 peers?](A_peers2002.html) | How do 10,000 simulated lives born in 2002 across 160 birth countries diverge? |
| 2 | [B · A different birthplace](B_country.html) | How do outcomes change when the same preset persona is born in different countries? |
| 3 | [D · A different era](D_era.html) | How do lives change across six birth years and four countries? |
| 4 | [C · A different life strategy](C_strategy.html) | How do six complete policy strategies diverge from the same starting conditions? |
| 5 | [C2 · Change one decision](C2_flip.html) | How much does changing a single decision alter the outcome, and in which direction? |

A provides context about default simulated lives; it is not a shared statistical control group for every other experiment.
Each report defines its own sample, comparison conditions, coverage, and methods.

## Explore a specific question

The ten topic reports can be read independently; there is no need to finish them in numerical order.

| Group | Reports |
| --- | --- |
| Choices and accumulation | [P1 Going abroad](P1_abroad.html) · [P3 Learning](P3_study.html) · [P2 Investing](P2_invest.html) · [P7 Marriage and children](P7_family.html) |
| Everyday life and relationships | [H1 Automatic spending](H1_habits.html) · [P4 Ceremony gifts](P4_gift.html) · [H2 Financial support for parents](H2_parents.html) |
| Health spending | [P5 Insurance](P5_ins.html) · [P6 Diet](P6_diet.html) · [H3 Checkups and personal training](H3_checkup.html) |

Report text and site navigation are currently in Chinese. This English README explains the project; it does not translate the reports.

## Read locally

No Node.js, npm, frontend dependencies, or analysis run is required to browse the reports.

```sh
git clone https://github.com/MBR000/life-simulation-lab.git
cd life-simulation-lab
python -m http.server 8000
```

Open [http://localhost:8000](http://localhost:8000) and follow the core reading path or browse the topic index.
On Windows, use `py -m http.server 8000` if `python` is unavailable.
You can also open `index.html` directly; retain the neighboring repository files for styles, report links, and downloads.

## Repository structure

```text
life-simulation-lab/
├── index.html                 # Core reading homepage; generated
├── reports.html               # Complete report index; generated
├── library.html               # Stories and essays index; generated
├── essay-*.html / story-*.html # Three essays and three stories; generated
├── reading.css                # Styles for reading pages
├── A_peers2002.html … H3_checkup.html
│                             # 15 published reports with their text and chart data
├── site.css                   # Homepage and index styles
├── theme.css                  # Shared report theme and navigation styles
├── site/
│   ├── reports.json           # Single source for order, groups, titles, and reading guides
│   ├── index.template.html    # Homepage template
│   ├── reports.template.html  # Complete index template
│   └── overview.fragment.html # Expandable overview charts on the complete index
├── scripts/publish_site.py    # Generates entry pages and report navigation
├── docs/methodology.md        # Method limits, original paths, and detailed P1 definitions
├── *.csv                     # Published summary tables and age snapshots
├── A-*.json.gz               # 12 selected raw simulated lives from report A
└── *.py / *.template.html / p1_*.js / p1_*.section.html
                              # Published copies of original analysis and report-building sources
```

Reports and downloads retain their existing root URLs to preserve links.
For reading-structure changes, mainly work in `site/`, `scripts/publish_site.py`, and the two stylesheets.
Root-level prefixes such as `b_` and `p1_` distinguish experiment exports with shared original filenames; they do not make those scripts directly runnable as a batch.

## Update the homepage, index, and navigation

Edit groups, order, or reading guides in `site/reports.json`; edit the corresponding templates and styles for layout changes.
Then run from the repository root:

```sh
python scripts/publish_site.py
python scripts/publish_site.py --check
```

The publishing script uses only the Python standard library. It generates `index.html` and `reports.html`, and replaces content inside
the `<!--site:bar-->`, `<!--site:guide-->`, and `<!--site:next-->` regions in each report.
It does not regenerate report analysis, embedded data, or interactive scripts.
`--check` checks whether generated output matches its sources without writing files; it does not validate statistical findings.

Do not directly edit generated entry pages or report navigation; the next generation will overwrite those edits.
GitHub Pages can serve the static files from the `main` branch root. Readers do not need to run a build.

## Data definitions and reproducibility

- **Money:** CNY amounts use the game's mainland-China purchasing-power factor of **3.5**, not a market exchange rate. Monthly income is generally game annual income × 3.5 ÷ 12.
- **Age and sample:** Monetary comparisons often use people with a snapshot at that age or paired survivors. Check sample sizes; cross-sectional differences across ages are not individual growth trajectories.
- **Pairing and selection:** The same seed helps fix starting conditions, but policies can alter later paths. Subgroups selected by actual execution or success are not automatically unbiased causal estimates.
- **Era:** D compares births in 1950, 1960, 1978, 1991, 2002, and 2020 across 24,000 simulated lives. Amounts are not adjusted for real prices across eras. Anything after 2026 is simulated future.
- **Scores:** Happiness, health, and relationship metrics are game scores. Topic findings are not real-world investment, medical, or life-planning advice.

| What this repository supports | Scope |
| --- | --- |
| Reading, filtering, and downloading | Embedded chart data and selected cases, published CSVs, and 12 raw A cases |
| Rebuilding site entry points and navigation | `scripts/publish_site.py`, using this repository and Python |
| Inspecting methods | Published analysis scripts, report templates, and each report's methods section |
| Complete reanalysis or new simulation | **Not possible from this repository alone**: full `runs.jsonl`, `jobs.jsonl`, `raw/`, some auxiliary data, and the engine are missing |

Original analysis scripts use the Python standard library and project-local helper modules, but retain the original `experiments/` and `scripts/` path conventions.
Installing Python is not sufficient: restore the required data, filenames, and directory layout before rerunning them.
See [Methods and reproduction notes](docs/methodology.md) for details, including P1 migration paths and success-conditioned comparisons.

## Contributing

1. For reading flow or navigation, edit `site/` and styles, regenerate the pages, and commit both sources and generated outputs.
2. For report or statistical corrections, identify the report, age, country, filters, source tables, and supporting evidence; update related analysis source and the report together.
3. For a new report, prepare its standalone HTML and downloads, then register its group and valid anchors in `site/reports.json`. Follow an existing report to include `theme.css`, add the `site` class to `body`, and prepare the three paired navigation markers above; the publisher only updates existing regions.
4. Before submitting, run `--check` and use a local server to check desktop and mobile reading order, filters, return links, and downloads.

For data changes, document the engine version, sample definitions, scope of reanalysis, and anything that remains unverified.
