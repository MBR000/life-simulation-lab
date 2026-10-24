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

## P1_abroad

P1_abroad.html compares seek/avoid abroad policies for 1,000 paired seeds in each of five country settings. Includes CNY purchasing-power amounts, N2 path-sensitivity reference, policy coverage and five paired-life logs. The p1_ CSV and Python/template files provide analysis outputs and source. To rerun, restore the original experiments/P1_abroad/scripts layout, full P1 jobs/runs/raw data and sibling N_noise data; remove p1_ prefixes from script/template names. The public repository alone cannot reproduce the full analysis.
