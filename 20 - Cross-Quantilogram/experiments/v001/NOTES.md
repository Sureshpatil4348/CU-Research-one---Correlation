# Cross-quantilogram experiments v001

## Research question

For each unordered pair among the eight majors, what is the cross-quantilogram of matched daily log returns of close at pre-specified tau in {0.05, 0.20} and lags k=0..10 on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Quantiles: expanding window through t; min history 252
- Statistic: rho_tau(k) for tau in [0.05, 0.2], k=0..10, both directions; headline tau=0.05, k=1; Pearson r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks (matched_rows + cq), charts under `outputs/figures/`

## Index

| pair | n | rho_L_to_R_t005_k1 | rho_R_to_L_t005_k1 | rho_L_to_R_t020_k1 | rho_R_to_L_t020_k1 | pearson_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.058094 | 0.025467 | 0.036617 | 0.011694 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 0.066796 | 0.055425 | 0.051730 | 0.020591 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 0.078794 | 0.063295 | 0.067389 | 0.020071 | 0.549808 |
| EURUSD-USDJPY | 7200 | 0.030735 | 0.034665 | 0.038308 | 0.040339 | -0.300952 |
| EURUSD-USDCHF | 7186 | 0.001043 | 0.036562 | 0.003178 | 0.033769 | -0.749204 |
| EURUSD-USDCAD | 7188 | 0.063895 | 0.038452 | 0.032822 | 0.023892 | -0.456626 |
| EURUSD-EURGBP | 7183 | 0.050666 | 0.038286 | 0.029998 | 0.045387 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 0.063020 | 0.069201 | 0.032078 | 0.030268 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 0.072951 | 0.057146 | 0.035845 | 0.017482 | 0.530079 |
| GBPUSD-USDJPY | 7200 | 0.030509 | 0.043328 | 0.031565 | 0.030617 | -0.198556 |
| GBPUSD-USDCHF | 7201 | -0.000099 | 0.017990 | -0.001722 | 0.045271 | -0.486083 |
| GBPUSD-USDCAD | 7205 | 0.074110 | 0.033153 | 0.038880 | 0.001731 | -0.456462 |
| GBPUSD-EURGBP | 7199 | 0.034405 | 0.031021 | 0.015345 | 0.021070 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 0.081830 | 0.052044 | 0.031190 | 0.018117 | 0.828722 |
| AUDUSD-USDJPY | 7199 | 0.024054 | 0.057615 | 0.015656 | 0.025272 | -0.088151 |
| AUDUSD-USDCHF | 7200 | 0.006336 | 0.044276 | 0.006389 | 0.035114 | -0.380878 |
| AUDUSD-USDCAD | 7204 | 0.061431 | 0.033828 | 0.040262 | 0.014383 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 0.041625 | 0.031011 | 0.020810 | 0.019840 | 0.038173 |
| NZDUSD-USDJPY | 7185 | 0.020598 | 0.058472 | 0.040655 | 0.013171 | -0.133568 |
| NZDUSD-USDCHF | 7185 | 0.016576 | 0.020447 | 0.017039 | 0.010503 | -0.393600 |
| NZDUSD-USDCAD | 7190 | 0.062409 | 0.021526 | 0.056200 | 0.015341 | -0.587831 |
| NZDUSD-EURGBP | 7183 | 0.035004 | 0.042276 | 0.030863 | 0.029881 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.011798 | 0.039488 | 0.022387 | 0.029553 | 0.399461 |
| USDJPY-USDCAD | 7186 | 0.019852 | 0.032386 | 0.015863 | 0.015864 | 0.027603 |
| USDJPY-EURGBP | 7181 | 0.004529 | 0.015643 | 0.027358 | 0.017211 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.006263 | 0.045615 | -0.014930 | 0.032987 | 0.304665 |
| USDCHF-EURGBP | 7182 | 0.039404 | 0.031086 | 0.036463 | 0.014220 | -0.325886 |
| USDCAD-EURGBP | 7185 | 0.056515 | 0.036370 | 0.037333 | 0.029619 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index at pre-specified tau=0.05, k=1 (56 directed screens). Not a 29th pair analysis and not a trading signal.

Strongest positive: AUDUSD->NZDUSD (rho=0.0818).
Strongest negative: GBPUSD->USDCHF (rho=-0.0001).
Nearest-to-zero: GBPUSD->USDCHF (rho=-0.0001); EURUSD->USDCHF (rho=0.0010); USDJPY->EURGBP (rho=0.0045).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
