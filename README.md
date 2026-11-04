# CU Research One — Correlation

Research project comparing 28 dependence measures on major FX pairs, with the long-term aim of identifying which measure is most useful for a later up, down, or crash read, and of informing a possible custom formula.

## What already exists

- [forex-formulas-explained.pdf](forex-formulas-explained.pdf) — single formula guide for all 28 methods (log returns, 7 September 2026).
- Folders `01` through `28` — one folder per method. Method 01 already has a beginner PDF guide and `build_guide.py`. Do not regenerate or edit that guide unless the method owner asks.
- Frozen MT5 price snapshots live under `data/snapshots/` after the first pull (see [docs/DATA.md](docs/DATA.md)).

## Folder rules

- Shared code lives only under `shared/mt5_data/`. A method folder never opens MT5 itself and never imports another method folder.
- There is no runner that executes all 28 methods.
- Each method stores experiments under `experiments/v001/`, `experiments/v002/`, and so on. See [docs/VERSIONING.md](docs/VERSIONING.md).
- Experiments read a named snapshot from `data/snapshots/`. They do not pull live MT5 data and do not overwrite older snapshots or older experiment outputs.

## Working universe (majors)

EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD, EURGBP.

## Current phase

v001 of methods 01 through 28 is complete on the Alpari full-history D1 snapshot. Gap checks for cointegration, transfer entropy, DCC, asymmetric DCC, regime correlation, tails, and the seven-asset network are in each method's `experiments/v002/`. Time-t features for the shortlist are in v002 for methods 01, 05, 07, and 14, and in v003 for methods 10, 11, 19, and 28. The pre-registered horse race is [research/forecast/v001/DRAFT.md](research/forecast/v001/DRAFT.md). The 28-method catalogue remains [reports/Correlation_Methods_28_Pages.pdf](reports/Correlation_Methods_28_Pages.pdf).



