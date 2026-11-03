# Regime-conditioned correlation experiments v001

## Research question

For each unordered pair among the eight majors, how do Pearson correlations of matched daily log returns of close differ in quiet versus stress states defined from a shared look-ahead-free FX turbulence rule on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- State rule: on dates with all eight majors present, turb = equal-weight mean of |log returns|; RV = mean of prior 20 turb days; after 252 past RV values, stress if RV > 75th percentile of those past values, else quiet; unlabeled days dropped from both rhos
- Statistic: Pearson rho_quiet and rho_stress via `scipy.stats.pearsonr` with Fisher 95% intervals; Pearson r on labeled rows as a side check; stress_minus_quiet reported
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/` (closes, returns with stress shading, regime scatter)

## Index

| pair | n_labeled | n_quiet | rho_quiet | p_quiet | n_stress | rho_stress | p_stress | pearson_r_labeled | stress_minus_quiet |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 6855 | 5092 | 0.640870 | 0 | 1763 | 0.651318 | 2.36516e-213 | 0.644539 | 0.010448 |
| EURUSD-AUDUSD | 6855 | 5092 | 0.575739 | 0 | 1763 | 0.579549 | 1.01222e-158 | 0.574238 | 0.003810 |
| EURUSD-NZDUSD | 6855 | 5092 | 0.548709 | 0 | 1763 | 0.591777 | 4.55975e-167 | 0.565376 | 0.043068 |
| EURUSD-USDJPY | 6855 | 5092 | -0.340338 | 2.81841e-138 | 1763 | -0.247157 | 6.01216e-26 | -0.304930 | 0.093180 |
| EURUSD-USDCHF | 6855 | 5092 | -0.727120 | 0 | 1763 | -0.759347 | 0 | -0.738402 | -0.032228 |
| EURUSD-USDCAD | 6855 | 5092 | -0.449594 | 6.39427e-252 | 1763 | -0.516888 | 4.99318e-121 | -0.475909 | -0.067294 |
| EURUSD-EURGBP | 6855 | 5092 | 0.450304 | 8.30987e-253 | 1763 | 0.395910 | 3.07045e-67 | 0.429175 | -0.054395 |
| GBPUSD-AUDUSD | 6855 | 5092 | 0.530122 | 0 | 1763 | 0.578127 | 8.97329e-158 | 0.550184 | 0.048005 |
| GBPUSD-NZDUSD | 6855 | 5092 | 0.513547 | 0 | 1763 | 0.582783 | 6.79767e-161 | 0.542102 | 0.069236 |
| GBPUSD-USDJPY | 6855 | 5092 | -0.255955 | 5.60026e-77 | 1763 | -0.110157 | 3.55012e-06 | -0.198601 | 0.145798 |
| GBPUSD-USDCHF | 6855 | 5092 | -0.492237 | 4.79071e-309 | 1763 | -0.465397 | 1.8436e-95 | -0.481376 | 0.026840 |
| GBPUSD-USDCAD | 6855 | 5092 | -0.427452 | 2.55807e-225 | 1763 | -0.526008 | 4.95995e-126 | -0.468324 | -0.098556 |
| GBPUSD-EURGBP | 6855 | 5092 | -0.389011 | 1.25581e-183 | 1763 | -0.433512 | 1.08785e-81 | -0.407085 | -0.044501 |
| AUDUSD-NZDUSD | 6855 | 5092 | 0.814867 | 0 | 1763 | 0.857862 | 0 | 0.831877 | 0.042995 |
| AUDUSD-USDJPY | 6855 | 5092 | -0.200695 | 2.01235e-47 | 1763 | 0.065997 | 0.0055686 | -0.085624 | 0.266692 |
| AUDUSD-USDCHF | 6855 | 5092 | -0.425576 | 3.72639e-223 | 1763 | -0.352667 | 8.73673e-53 | -0.391944 | 0.072909 |
| AUDUSD-USDCAD | 6855 | 5092 | -0.621582 | 0 | 1763 | -0.693467 | 5.23537e-253 | -0.652448 | -0.071885 |
| AUDUSD-EURGBP | 6855 | 5092 | 0.074776 | 9.18958e-08 | 1763 | -0.006346 | 0.79003 | 0.038666 | -0.081122 |
| NZDUSD-USDJPY | 6855 | 5092 | -0.215365 | 1.66495e-54 | 1763 | -0.010284 | 0.6661 | -0.134486 | 0.205081 |
| NZDUSD-USDCHF | 6855 | 5092 | -0.419655 | 2.0514e-216 | 1763 | -0.378647 | 3.32754e-61 | -0.403505 | 0.041008 |
| NZDUSD-USDCAD | 6855 | 5092 | -0.552641 | 0 | 1763 | -0.653986 | 1.12815e-215 | -0.594593 | -0.101345 |
| NZDUSD-EURGBP | 6855 | 5092 | 0.057184 | 4.44812e-05 | 1763 | 0.001943 | 0.93501 | 0.034497 | -0.055240 |
| USDJPY-USDCHF | 6855 | 5092 | 0.413068 | 4.50145e-209 | 1763 | 0.401194 | 3.68487e-69 | 0.408536 | -0.011873 |
| USDJPY-USDCAD | 6855 | 5092 | 0.093836 | 1.95741e-11 | 1763 | -0.069480 | 0.00351385 | 0.029174 | -0.163317 |
| USDJPY-EURGBP | 6855 | 5092 | -0.112123 | 1.02152e-15 | 1763 | -0.160373 | 1.2626e-11 | -0.130442 | -0.048250 |
| USDCHF-USDCAD | 6855 | 5092 | 0.320579 | 4.7933e-122 | 1763 | 0.318276 | 8.54811e-43 | 0.319192 | -0.002303 |
| USDCHF-EURGBP | 6855 | 5092 | -0.298100 | 5.16909e-105 | 1763 | -0.338639 | 1.48146e-48 | -0.312196 | -0.040540 |
| USDCAD-EURGBP | 6855 | 5092 | -0.042888 | 0.0022056 | 1763 | 0.017329 | 0.467125 | -0.017940 | 0.060217 |

## Cross-pair conclusion

Reading of the 28-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest positive rho_stress: AUDUSD-NZDUSD (rho_stress=0.8579, n_stress=1763).
Strongest negative rho_stress: EURUSD-USDCHF (rho_stress=-0.7593, n_stress=1763).
Nearest-to-zero rho_stress: NZDUSD-EURGBP (rho_stress=0.0019); AUDUSD-EURGBP (rho_stress=-0.0063); NZDUSD-USDJPY (rho_stress=-0.0103).
Largest |rho_stress minus rho_quiet| gaps: AUDUSD-USDJPY (gap=0.2667, rho_stress=0.0660, rho_quiet=-0.2007); NZDUSD-USDJPY (gap=0.2051, rho_stress=-0.0103, rho_quiet=-0.2154); USDJPY-USDCAD (gap=-0.1633, rho_stress=-0.0695, rho_quiet=0.0938). A large gap can flag different co-movement in stress versus quiet; inspect that pair's n_stress and charts before treating either score as settled.

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
