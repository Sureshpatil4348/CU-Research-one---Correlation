# Lagged cross-correlation experiments v001

## Research question

For each unordered pair among the eight majors, what is the lagged cross-correlation of matched daily log returns of close at pre-specified lags k=0..10 in both directions on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Statistic: rho_X->Y(k)=Pearson(x_t, y_{t+k}) for k=0..10 in both directions via `scipy.stats.pearsonr` with Fisher 95% intervals; headline = k=1 both ways; k=0 is same-bar side check; largest |rho| among k=1..10 is descriptive only
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks (matched_rows + ccf sheets), charts under `outputs/figures/` (closes, returns, CCF bars)

## Index

| pair | n | rho_k0 | rho_L_to_R_k1 | p_L_to_R_k1 | rho_R_to_L_k1 | p_R_to_L_k1 | best_abs_L_to_R_k | best_abs_L_to_R_rho | best_abs_R_to_L_k | best_abs_R_to_L_rho |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.641738 | 0.002079 | 0.859964 | -0.019352 | 0.100579 | 8 | 0.032281 | 10 | -0.025691 |
| EURUSD-AUDUSD | 7201 | 0.556324 | -0.042867 | 0.00027429 | -0.009827 | 0.404425 | 4 | 0.044494 | 9 | -0.043022 |
| EURUSD-NZDUSD | 7186 | 0.549808 | -0.001310 | 0.911598 | -0.023382 | 0.0474913 | 2 | 0.030539 | 1 | -0.023382 |
| EURUSD-USDJPY | 7200 | -0.300952 | -0.009482 | 0.42118 | 0.024939 | 0.0343509 | 5 | -0.017787 | 1 | 0.024939 |
| EURUSD-USDCHF | 7186 | -0.749204 | 0.013360 | 0.257522 | 0.035522 | 0.00260051 | 8 | -0.031244 | 1 | 0.035522 |
| EURUSD-USDCAD | 7188 | -0.456626 | 0.040711 | 0.00055613 | -0.004659 | 0.692911 | 1 | 0.040711 | 9 | 0.042495 |
| EURUSD-EURGBP | 7183 | 0.439899 | -0.033320 | 0.00474181 | -0.004064 | 0.730577 | 9 | -0.041662 | 8 | 0.025964 |
| GBPUSD-AUDUSD | 7228 | 0.539048 | -0.029977 | 0.0108187 | 0.019983 | 0.0893783 | 6 | -0.035810 | 8 | 0.039877 |
| GBPUSD-NZDUSD | 7203 | 0.530079 | -0.005367 | 0.648828 | 0.000798 | 0.946031 | 5 | -0.025547 | 8 | 0.029569 |
| GBPUSD-USDJPY | 7200 | -0.198556 | -0.007036 | 0.550564 | 0.037165 | 0.00161137 | 4 | -0.015802 | 1 | 0.037165 |
| GBPUSD-USDCHF | 7201 | -0.486083 | -0.004628 | 0.694613 | 0.012431 | 0.291567 | 9 | 0.030293 | 8 | -0.021538 |
| GBPUSD-USDCAD | 7205 | -0.456462 | 0.028713 | 0.0148038 | -0.040946 | 0.000508514 | 1 | 0.028713 | 8 | -0.048660 |
| GBPUSD-EURGBP | 7199 | -0.397845 | -0.042373 | 0.000323177 | -0.012040 | 0.307085 | 1 | -0.042373 | 8 | 0.037655 |
| AUDUSD-NZDUSD | 7202 | 0.828722 | -0.009668 | 0.412045 | -0.038993 | 0.000934272 | 9 | -0.039392 | 1 | -0.038993 |
| AUDUSD-USDJPY | 7199 | -0.088151 | -0.047506 | 5.52942e-05 | 0.024257 | 0.0395997 | 1 | -0.047506 | 8 | -0.033866 |
| AUDUSD-USDCHF | 7200 | -0.380878 | -0.004580 | 0.697592 | 0.041640 | 0.000409394 | 9 | 0.032025 | 1 | 0.041640 |
| AUDUSD-USDCAD | 7204 | -0.647362 | 0.023202 | 0.0489398 | 0.007845 | 0.505589 | 4 | -0.032732 | 4 | -0.046499 |
| AUDUSD-EURGBP | 7198 | 0.038173 | -0.031475 | 0.00757625 | -0.009732 | 0.409108 | 1 | -0.031475 | 4 | 0.037876 |
| NZDUSD-USDJPY | 7185 | -0.133568 | -0.035402 | 0.00269097 | 0.008795 | 0.456067 | 1 | -0.035402 | 6 | -0.025986 |
| NZDUSD-USDCHF | 7185 | -0.393600 | 0.002509 | 0.831616 | 0.001692 | 0.886007 | 5 | -0.021145 | 2 | -0.031591 |
| NZDUSD-USDCAD | 7190 | -0.587831 | 0.027254 | 0.0208434 | -0.001090 | 0.926349 | 1 | 0.027254 | 9 | 0.043205 |
| NZDUSD-EURGBP | 7183 | 0.037186 | -0.028542 | 0.0155678 | 0.006758 | 0.566926 | 1 | -0.028542 | 6 | 0.030153 |
| USDJPY-USDCHF | 7185 | 0.399461 | -0.030792 | 0.00905356 | -0.012692 | 0.282105 | 1 | -0.030792 | 8 | 0.022396 |
| USDJPY-USDCAD | 7186 | 0.027603 | -0.023971 | 0.0421717 | 0.047782 | 5.08153e-05 | 6 | 0.026325 | 1 | 0.047782 |
| USDJPY-EURGBP | 7181 | -0.127992 | -0.012227 | 0.300247 | -0.006573 | 0.577631 | 10 | -0.021242 | 4 | 0.040141 |
| USDCHF-USDCAD | 7188 | 0.304665 | -0.049411 | 2.78135e-05 | 0.031676 | 0.00724085 | 1 | -0.049411 | 1 | 0.031676 |
| USDCHF-EURGBP | 7182 | -0.325886 | 0.029865 | 0.0113757 | 0.017331 | 0.141968 | 9 | 0.033595 | 4 | -0.026717 |
| USDCAD-EURGBP | 7185 | -0.014622 | 0.039579 | 0.000792479 | 0.015954 | 0.176344 | 1 | 0.039579 | 4 | -0.035444 |

## Cross-pair conclusion

Reading of the 28-pair index at pre-specified k=1 only (56 directed screens). Not a 29th pair analysis and not a trading signal.

Strongest positive k=1 directed rho: USDCAD->USDJPY (rho=0.0478).
Strongest negative k=1 directed rho: USDCHF->USDCAD (rho=-0.0494).
Nearest-to-zero k=1 directed rhos: NZDUSD->GBPUSD (rho=0.0008); USDCAD->NZDUSD (rho=-0.0011); EURUSD->NZDUSD (rho=-0.0013).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
