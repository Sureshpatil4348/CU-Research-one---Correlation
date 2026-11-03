# DCCA detrended cross-correlation experiments v001

## Research question

For each unordered pair among the eight majors, what is rho_DCCA(s) of matched daily log returns of close at pre-specified window lengths s in {20, 60, 100} on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Scales: s in [20, 60, 100]; headline s=100
- Trend degree=1; overlap=none; Pearson r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks (matched_rows + scales), charts under `outputs/figures/`

## Index

| pair | n | rho_s20 | rho_s60 | rho_s100 | n_windows_s100 | pearson_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.653960 | 0.663383 | 0.688235 | 72 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 0.564751 | 0.532412 | 0.622671 | 72 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 0.549493 | 0.559473 | 0.582480 | 71 | 0.549808 |
| EURUSD-USDJPY | 7200 | -0.299049 | -0.303248 | -0.337373 | 72 | -0.300952 |
| EURUSD-USDCHF | 7186 | -0.719339 | -0.776244 | -0.777402 | 71 | -0.749204 |
| EURUSD-USDCAD | 7188 | -0.468409 | -0.443685 | -0.441552 | 71 | -0.456626 |
| EURUSD-EURGBP | 7183 | 0.389567 | 0.447332 | 0.447523 | 71 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 0.593916 | 0.498546 | 0.498838 | 72 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 0.545413 | 0.525431 | 0.574754 | 72 | 0.530079 |
| GBPUSD-USDJPY | 7200 | -0.180270 | -0.183079 | -0.268652 | 72 | -0.198556 |
| GBPUSD-USDCHF | 7201 | -0.500351 | -0.536912 | -0.589491 | 72 | -0.486083 |
| GBPUSD-USDCAD | 7205 | -0.474521 | -0.461186 | -0.507222 | 72 | -0.456462 |
| GBPUSD-EURGBP | 7199 | -0.409455 | -0.403591 | -0.342743 | 71 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 0.827557 | 0.829455 | 0.814656 | 72 | 0.828722 |
| AUDUSD-USDJPY | 7199 | -0.096862 | -0.152061 | -0.195647 | 71 | -0.088151 |
| AUDUSD-USDCHF | 7200 | -0.385781 | -0.431874 | -0.496588 | 72 | -0.380878 |
| AUDUSD-USDCAD | 7204 | -0.657008 | -0.700962 | -0.728533 | 72 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 0.013856 | 0.018640 | 0.098838 | 71 | 0.038173 |
| NZDUSD-USDJPY | 7185 | -0.136652 | -0.157835 | -0.221006 | 71 | -0.133568 |
| NZDUSD-USDCHF | 7185 | -0.381817 | -0.444551 | -0.508021 | 71 | -0.393600 |
| NZDUSD-USDCAD | 7190 | -0.624407 | -0.614061 | -0.559037 | 71 | -0.587831 |
| NZDUSD-EURGBP | 7183 | -0.007831 | 0.049181 | 0.087743 | 71 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.372525 | 0.403395 | 0.420333 | 71 | 0.399461 |
| USDJPY-USDCAD | 7186 | 0.077238 | 0.061214 | 0.081891 | 71 | 0.027603 |
| USDJPY-EURGBP | 7181 | -0.140276 | -0.141083 | -0.217636 | 71 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.322025 | 0.313109 | 0.321234 | 71 | 0.304665 |
| USDCHF-EURGBP | 7182 | -0.320588 | -0.333051 | -0.304846 | 71 | -0.325886 |
| USDCAD-EURGBP | 7185 | 0.062588 | 0.029019 | 0.002012 | 71 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index at pre-specified rho_DCCA(s=100). Not a 29th pair analysis and not a trading signal.

Strongest positive: AUDUSD-NZDUSD (rho=0.8147).
Strongest negative: EURUSD-USDCHF (rho=-0.7774).
Nearest-to-zero: USDCAD-EURGBP (rho=0.0020); USDJPY-USDCAD (rho=0.0819); NZDUSD-EURGBP (rho=0.0877).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
