# Data snapshots

## Research question (one paragraph)

Which of the 28 dependence measures in `forex-formulas-explained.pdf` is most useful for a later up, down, or crash read on these eight major FX pairs? This document records the frozen price data used to answer that question later. It does not define a trading signal, backtest, or comparison table.

## Active snapshot (Alpari full history)

| Field | Value |
| --- | --- |
| Path | `data/snapshots/2026-11-03_majors_alpari_D1/` |
| Created (UTC) | 2026-11-03T08:30:13+00:00 |
| Timeframe | D1 |
| Pull mode | Full history (year chunks from today back to 1970; keep only bars returned) |
| Actual range | 1999-01-04 → 2026-11-03 UTC (EURGBP first bar 1999-01-05) |
| Terminal | Alpari-MT5 (login 245089294), MetaTrader 5 build 6296 |
| Max bars in chart | 100,000,000 |
| Broker suffix | `_i` (logical EURUSD → broker `EURUSD_i`) |
| Immutable | Yes — do not edit CSVs or rewrite this folder |

### Resolved symbols and bar counts

| Logical | Resolved | Bars | First bar (UTC) | Last bar (UTC) |
| --- | --- | ---: | --- | --- |
| EURUSD | EURUSD_i | 7206 | 1999-01-04 | 2026-11-03 |
| GBPUSD | GBPUSD_i | 7231 | 1999-01-04 | 2026-11-03 |
| AUDUSD | AUDUSD_i | 7230 | 1999-01-04 | 2026-11-03 |
| NZDUSD | NZDUSD_i | 7207 | 1999-01-04 | 2026-11-03 |
| USDJPY | USDJPY_i | 7204 | 1999-01-04 | 2026-11-03 |
| USDCHF | USDCHF_i | 7206 | 1999-01-04 | 2026-11-03 |
| USDCAD | USDCAD_i | 7210 | 1999-01-04 | 2026-11-03 |
| EURGBP | EURGBP_i | 7203 | 1999-01-05 | 2026-11-03 |

Each CSV has columns: `time`, `open`, `high`, `low`, `close`, `tick_volume`, `spread`, `real_volume`. Full machine-readable metadata is in `manifest.json` inside the snapshot folder.

Pearson experiment `01 - Pearson Correlation/experiments/v001/`, Spearman experiment `02 - Spearman Rank Correlation/experiments/v001/`, Kendall tau-b experiment `03 - Kendall Tau-b/experiments/v001/`, robust clipped correlation experiment `04 - Robust Clipped Correlation/experiments/v001/`, rolling correlation experiment `05 - Rolling Correlation/experiments/v001/`, EWMA correlation experiment `06 - EWMA Correlation/experiments/v001/`, partial / residual correlation experiment `07 - Partial and Residual Correlation/experiments/v001/`, shrinkage correlation experiment `08 - Shrinkage Correlation/experiments/v001/`, DCC-GARCH experiment `09 - DCC-GARCH/experiments/v001/`, asymmetric DCC experiment `10 - Asymmetric DCC/experiments/v001/`, regime-conditioned correlation experiment `11 - Regime-Conditioned Correlation/experiments/v001/`, lagged cross-correlation experiment `12 - Lagged Cross-Correlation/experiments/v001/`, Granger predictability experiment `13 - Granger Predictability/experiments/v001/`, distance correlation experiment `14 - Distance Correlation/experiments/v001/`, mutual information experiment `15 - Mutual Information/experiments/v001/`, HSIC kernel dependence experiment `16 - HSIC Kernel Dependence/experiments/v001/`, transfer entropy experiment `17 - Transfer Entropy/experiments/v001/`, copulas experiment `18 - Copulas/experiments/v001/`, tail dependence experiment `19 - Tail Dependence/experiments/v001/`, cross-quantilogram experiment `20 - Cross-Quantilogram/experiments/v001/`, spectral coherence experiment `21 - Spectral Coherence/experiments/v001/`, wavelet correlation experiment `22 - Wavelet Correlation and Coherence/experiments/v001/`, DCCA experiment `23 - DCCA Detrended Cross-Correlation/experiments/v001/`, multifractal DCCA experiment `24 - Multifractal DCCA/experiments/v001/`, volatility correlation experiment `25 - Volatility and Realized Correlation/experiments/v001/`, Hayashi–Yoshida experiment `26 - Hayashi-Yoshida Covariance/experiments/v001/`, cointegration experiment `27 - Cointegration and Error Correction/experiments/v001/`, and networks / PCA / connectedness experiment `28 - Networks PCA and Connectedness/experiments/v001/` load this snapshot.


## Earlier snapshot (Vantage, five-year window)

Left frozen. Not used by the Pearson v001 reports.

| Field | Value |
| --- | --- |
| Path | `data/snapshots/2026-11-03_majors_D1/` |
| Created (UTC) | 2026-11-03T07:24:17+00:00 |
| Timeframe | D1 |
| Requested range | 5 years ending pull day (2021-11-04 → 2026-11-03 UTC) |
| Terminal | VantageMarkets-Live 8 (login 21894742), MetaTrader 5 build 6296 |
| Bars per major | 1296 (2021-11-05 → 2026-11-03) |
| Immutable | Yes |

## How later experiments use a snapshot

1. Name the snapshot folder in the experiment `NOTES.md`.
2. Load with `shared.mt5_data.load_snapshot(...)`.
3. Derive log returns inside the method experiment when the formula guide requires them.
4. Do not open MT5 from a method folder for analysis. For newer bars, create a new dated snapshot with `python -m shared.mt5_data.cli --full-history --label majors_alpari`.
