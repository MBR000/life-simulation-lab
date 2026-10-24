# Life Simulation Lab

A collection of interactive life-simulation reports. Open index.html for the report directory.

## Published reports

- A_peers2002.html: 10,000 simulated lives born in 2002, across 160 birth countries. Includes age filters, CNY purchasing-power amounts, and 12 traceable cases.

These are simulator results, not real population observations or personal predictions. CNY values use the game's mainland-China purchasing-power factor of 3.5, not a market exchange rate.

## Included data

The report embeds its charts and case narratives. snaps.csv contains age snapshots; money_cny.csv contains currency summaries; the 12 json.gz files are the selected simulated cases.

analyze.py is included as methodology source. This repository does not include the full original runs.jsonl, jobs.jsonl, engine, or other raw lives, so complete analysis cannot be rerun from this repository alone. Local experiment paths in the report describe the original analysis provenance.

## Hosting

GitHub Pages deploys the main branch root. No build step or external scripts required.
