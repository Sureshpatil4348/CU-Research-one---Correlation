# Kendall tau-b experiments v001

## Research question

For each unordered pair among the eight majors, what is the Kendall tau-b of matched daily log returns of close on the Alpari D1 history that the broker actually provided?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Statistic: Kendall tau-b via `scipy.stats.kendalltau` (variant="b"), two-sided p, approximate 95% Bonett-Wright interval on tau-b, same-sample Pearson r and tau-b minus r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/` (closes, returns, log-return scatter)

## Index

| pair | n | tau_b | p | ci_low | ci_high | pearson_r | tau_minus_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.468025 | 0 | 0.456014 | 0.479866 | 0.641738 | -0.173713 |
| EURUSD-AUDUSD | 7201 | 0.393179 | 0 | 0.380190 | 0.406012 | 0.556324 | -0.163145 |
| EURUSD-NZDUSD | 7186 | 0.376957 | 0 | 0.363766 | 0.389997 | 0.549808 | -0.172851 |
| EURUSD-USDJPY | 7200 | -0.247249 | 2.90677e-217 | -0.261534 | -0.232856 | -0.300952 | 0.053703 |
| EURUSD-USDCHF | 7186 | -0.656699 | 0 | -0.665307 | -0.647916 | -0.749204 | 0.092504 |
| EURUSD-USDCAD | 7188 | -0.295698 | 2.55914e-309 | -0.309584 | -0.281686 | -0.456626 | 0.160927 |
| EURUSD-EURGBP | 7183 | 0.303853 | 0 | 0.289909 | 0.317668 | 0.439899 | -0.136046 |
| GBPUSD-AUDUSD | 7228 | 0.366609 | 0 | 0.353340 | 0.379729 | 0.539048 | -0.172439 |
| GBPUSD-NZDUSD | 7203 | 0.354894 | 0 | 0.341475 | 0.368168 | 0.530079 | -0.175185 |
| GBPUSD-USDJPY | 7200 | -0.191777 | 1.58699e-131 | -0.206445 | -0.177023 | -0.198556 | 0.006778 |
| GBPUSD-USDCHF | 7201 | -0.395036 | 0 | -0.407847 | -0.382070 | -0.486083 | 0.091046 |
| GBPUSD-USDCAD | 7205 | -0.281899 | 5.57399e-282 | -0.295892 | -0.267784 | -0.456462 | 0.174564 |
| GBPUSD-EURGBP | 7199 | -0.222580 | 1.95066e-176 | -0.237048 | -0.208014 | -0.397845 | 0.175265 |
| AUDUSD-NZDUSD | 7202 | 0.622652 | 0 | 0.613212 | 0.631914 | 0.828722 | -0.206070 |
| AUDUSD-USDJPY | 7199 | -0.151980 | 2.59778e-83 | -0.166866 | -0.137024 | -0.088151 | -0.063829 |
| AUDUSD-USDCHF | 7200 | -0.313011 | 0 | -0.326722 | -0.299169 | -0.380878 | 0.067867 |
| AUDUSD-USDCAD | 7204 | -0.430496 | 0 | -0.442854 | -0.417975 | -0.647362 | 0.216865 |
| AUDUSD-EURGBP | 7198 | 0.044038 | 2.10948e-08 | 0.028783 | 0.059273 | 0.038173 | 0.005865 |
| NZDUSD-USDJPY | 7185 | -0.157597 | 2.85439e-89 | -0.172470 | -0.142652 | -0.133568 | -0.024028 |
| NZDUSD-USDCHF | 7185 | -0.306188 | 0 | -0.319978 | -0.292267 | -0.393600 | 0.087412 |
| NZDUSD-USDCAD | 7190 | -0.381717 | 0 | -0.394698 | -0.368584 | -0.587831 | 0.206114 |
| NZDUSD-EURGBP | 7183 | 0.037706 | 1.64991e-06 | 0.022428 | 0.052966 | 0.037186 | 0.000519 |
| USDJPY-USDCHF | 7185 | 0.314473 | 0 | 0.300630 | 0.328184 | 0.399461 | -0.084988 |
| USDJPY-USDCAD | 7186 | 0.070007 | 5.60971e-19 | 0.054778 | 0.085203 | 0.027603 | 0.042404 |
| USDJPY-EURGBP | 7181 | -0.074232 | 3.98249e-21 | -0.089423 | -0.059006 | -0.127992 | 0.053761 |
| USDCHF-USDCAD | 7188 | 0.229614 | 2.35858e-187 | 0.215084 | 0.244043 | 0.304665 | -0.075051 |
| USDCHF-EURGBP | 7182 | -0.241190 | 2.51176e-206 | -0.255539 | -0.226734 | -0.325886 | 0.084697 |
| USDCAD-EURGBP | 7185 | -0.031204 | 7.29777e-05 | -0.046470 | -0.015923 | -0.014622 | -0.016582 |

## Cross-pair conclusion

Reading of the 28-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest positive concordance link: AUDUSD-NZDUSD (tau_b=0.6227, n=7202).
Strongest negative concordance link: EURUSD-USDCHF (tau_b=-0.6567, n=7186).
Nearest-to-zero concordance links: USDCAD-EURGBP (tau_b=-0.0312); NZDUSD-EURGBP (tau_b=0.0377); AUDUSD-EURGBP (tau_b=0.0440).
Largest |tau-b minus Pearson r| gaps on the same sample: AUDUSD-USDCAD (gap=0.2169, tau_b=-0.4305, r=-0.6474); NZDUSD-USDCAD (gap=0.2061, tau_b=-0.3817, r=-0.5878); AUDUSD-NZDUSD (gap=-0.2061, tau_b=0.6227, r=0.8287). A large gap can flag outliers or a non-straight link; inspect that pair's charts before treating either score as settled.

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
