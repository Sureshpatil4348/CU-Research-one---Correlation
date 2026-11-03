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

Pearson (method 01) v001 through networks / PCA / connectedness (method 28) v001 are complete on the Alpari full-history D1 snapshot — all 28 dependence measures in the formula guide. Rolling covers the short watchlist, secondary tier, and low-value pairs with windows 20 / 60 / 100. See [docs/DATA.md](docs/DATA.md) and [05 - Rolling Correlation/experiments/v001/outputs/WATCHLIST.md](05%20-%20Rolling%20Correlation/experiments/v001/outputs/WATCHLIST.md).



