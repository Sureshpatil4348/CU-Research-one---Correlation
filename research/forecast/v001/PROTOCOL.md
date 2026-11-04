# Forecast protocol v001

Frozen before any forecast score. `score.py` stores the SHA-256 of this file in `outputs/manifest.json` and stops if the file hash differs from a manifest that already holds scores.

Snapshot: `data/snapshots/2026-11-03_majors_alpari_D1`. Quotes are not inverted. The unfinished last bar is dropped with the same tick-volume rule as the v001 experiments.

v001 folders are immutable. `research/forecast/v001/v001_hashes.txt` is the SHA-256 list of every file under `experiments/v001` at the time this protocol was frozen. The panel build fails if any of those hashes change.

This file does not report results. Cuts below are not revised after scores exist.

## Targets

T1, primary, one label per day. On dates when all eight majors have a log return, `turb_t` is the equal-weight mean of the eight absolute log returns. `RV_fwd(t)` is the mean of `turb` over the next 20 trading days, `t+1` through `t+20`. The threshold at t is the 90th percentile of `RV_fwd(s)` for origins s whose forward window has already ended on or before t. The first eligible t needs 252 such completed windows. Spike = 1 when `RV_fwd(t)` is strictly above that threshold.

T2, secondary, one label per pair and day. `baseline_t` is the expanding Pearson correlation of the two log-return series using only observations through t, after at least 252 observations. Break = 1 when the Pearson correlation of `t+1` through `t+20` differs from `baseline_t` by more than 0.30 in absolute value. The cut 0.30 stays fixed.

## Features

Feature files contain no label column. A row dated t uses returns dated t or earlier. `feature_asof` equals that date. The panel build rejects a row whose `feature_asof` is after `date`.

Pair features:

| Column | Method | Definition at t |
| --- | --- | --- |
| `m01_expanding_r` | 01 v002 | Expanding Pearson after 252 days |
| `m05_r20` | 05 v002 | Pearson on the last 20 days |
| `m05_r60` | 05 v002 | Pearson on the last 60 days |
| `m05_r100` | 05 v002 | Pearson on the last 100 days |
| `m05_abs_gap` | 05 v002 | Absolute gap between `m05_r20` and the expanding Pearson |
| `m07_rho_partial` | 07 v002 | Partial correlation on the last 252 days after the leave-currency-out USD factor estimated inside that window |
| `m10_adcc_minus_r` | 10 v003 | ADCC rho minus expanding Pearson. Parameters are fit on data through each 31 December, first end 2006-12-31, then filtered forward until the next refit. Days before the first refit are missing |
| `m11_adj_gap` | 11 v003 | Forbes-Rigobon adjusted stress correlation minus quiet correlation on the last 252 days. Missing if either state has fewer than 30 days in the window |
| `m19_excess_lower` | 19 v003 | Lower-tail L_hat at alpha 0.05 on the last 252 days, minus the Gaussian co-exceedance at that window's Pearson r. Ranks are inside the window |
| `m14_dcor` | 14 v002 | Biased distance correlation on the last 252 days |
| `m28_d_ij` | 28 v003 | Network distance from the last 252 days of Pearson correlation on the seven majors excluding EURGBP |

System features, from method 28 v003, broadcast onto pair rows:

| Column | Definition at t |
| --- | --- |
| `m28_pc1_share` | PC1 variance share of the seven-asset correlation matrix on the last 252 days |
| `m28_tci` | Diebold-Yilmaz TCI from a BIC VAR and GFEVD horizon 10, refit at each quarter-end on data through that quarter-end, then held flat until the next quarter-end |

The USD factor sign rule matches method 07 v001: minus the log return for EURUSD, GBPUSD, AUDUSD, and NZDUSD; plus the log return for USDJPY, USDCHF, and USDCAD. EURGBP never enters the factor. A constituent is left out when it shares a non-USD currency with either leg.

Distance correlation is the biased sample dCor from method 14 v001. The grid is daily unless a timed chunk, run before the full feature pass and recorded in that experiment's NOTES, shows a multi-hour run. Only in that case is the value computed every 5th trading day and carried forward.

## T1 design matrix

One row per eligible day. Pair columns are the cross-sectional mean of the available pair values that day. `m28_pc1_share` and `m28_tci` are the system values, not pair means.

Primary baseline: `baseline_r20` = mean of `m05_r20`.

Second baseline, reported but not the primary horse race: `baseline_abs_gap` = mean of `m05_abs_gap`.

Competitors, the Benjamini-Hochberg family against `baseline_r20`:

`m01_expanding_r`, `m07_rho_partial`, `m10_adcc_minus_r`, `m11_adj_gap`, `m19_excess_lower`, `m14_dcor`, `m28_d_ij`, `m28_pc1_share`, `m28_tci`.

Diagnostic, not in that family and not eligible to win: `diagnostic_rv20`, the mean of `turb` over the 20 days ending at t, including t.

## T2 design matrix

One row per pair and day. The baseline is that pair's `m05_r20`. The same competitor columns are used. System columns are the broadcast values. A missing cell is dropped only for that feature.

Day-level loss for Diebold-Mariano and the model confidence set is the mean squared error across pairs that have both a prediction and a label that day.

## Estimator

Univariate logistic regression of the binary label on one feature. The feature is standardized with the training mean and standard deviation. The first test date is the first date with 1000 earlier dates that have a label. The model is refit every 21 trading days.

A training row dated s may enter a test block that starts at u only when the label window of s ends strictly before u. That is a 20-trading-day embargo. Without it, `RV_fwd(s)` and the T2 future correlation would contain returns inside the test block.

If the training sample has one class, or the training standard deviation is 0, the prediction is the training base rate.

## Scores

Loss is the Brier score, the mean of `(probability - label)^2` on out-of-sample rows.

AUC is the Mann-Whitney statistic on the pooled out-of-sample probabilities.

Diebold-Mariano compares each competitor with `baseline_r20`. The loss differential is competitor minus baseline, so a negative mean means the competitor has the lower Brier score. The standard error is Newey-West with lag 20. The reported p-value is one-sided for a lower Brier score. Benjamini-Hochberg at 0.05 is applied to those one-sided p-values inside the competitor family, separately for T1 and for T2.

The Hansen model confidence set uses the range statistic and a circular block bootstrap with block length 20, 400 draws, and seed `20261103`. The confidence level is 90 percent (elimination alpha 0.10). The set is computed on T1 for the primary baseline plus the competitors. T2 uses the same rule on day-level losses.

A competitor beats the baseline on T1 only when its Brier score is lower and its BH-adjusted one-sided p-value is below 0.05. If several beat it, the winner is the one with the lowest Brier score. If none do, the draft says so.

## Crisis windows

Shades, used only to count hits and false alarms on the T1 signal:

- GFC: 2008-09-15 through 2009-03-31
- SNB floor: 2011-09-06 through 2015-01-14
- SNB removal: the 20 trading days before 2015-01-15 are the pre-window; the removal day is the shade
- COVID: 2020-02-20 through 2020-03-31
- 2022 risk-off: 2022-02-01 through 2022-10-31

The signal is on when the out-of-sample probability exceeds the 80th percentile of the training in-sample probabilities from the model that was active that day. That cut targets a 20 percent training signal rate and is not chosen from the test sample.

Hit rate: the fraction of the 20 trading days before the shade on which the signal is on. A signal that is on only inside the shade is a miss. In-shade rate is reported separately. False-alarm rate: the fraction of out-of-sample days outside every shade and outside every pre-window on which the signal is on.

## Subperiods

The same walk-forward predictions are sliced by the signal date. No new fit sees later data.

- through 2007: through 2007-12-31
- 2008-2015: 2008-01-01 through 2015-12-31
- 2016-2019: 2016-01-01 through 2019-12-31
- 2020-end: from 2020-01-01

## Overlay

The book is the equal-weight mean of the eight major log returns. The position for the next day is 0 when the T1 signal is on, and 1 otherwise. Cost is 0.0001 times the absolute position change. Net log growth is the sum of position times next-day basket return, minus that cost.

Books: always long; the `baseline_r20` rule; and the T1 winner when one exists.

## What this protocol does not do

It does not add a 29th dependence measure. It does not overwrite v001. It does not retune the 0.30 break cut, the 90th percentile, the crisis dates, or the model set after the scores are written.
