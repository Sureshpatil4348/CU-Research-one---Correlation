# Multifractal DCCA experiments v001

## Research question

For each unordered pair among the eight majors, what is rho_q(s) of matched daily log returns of close at pre-specified q in {2, 4} and s in {20, 60, 100} on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Scales: s in [20, 60, 100]; q in [2.0, 4.0]; headline q=2, s=100
- Trend degree=1; overlap=none; positive q only; Pearson r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks (matched_rows + scales), charts under `outputs/figures/`

## Index

| pair | n | rho_q2_s20 | rho_q2_s60 | rho_q2_s100 | rho_q4_s100 | pearson_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.653960 | 0.663383 | 0.688235 | 0.510161 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 0.564751 | 0.532412 | 0.622671 | 0.598056 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 0.549493 | 0.559473 | 0.582480 | 0.435962 | 0.549808 |
| EURUSD-USDJPY | 7200 | -0.299049 | -0.303248 | -0.337373 | -0.173688 | -0.300952 |
| EURUSD-USDCHF | 7186 | -0.719339 | -0.776244 | -0.777402 | -0.508231 | -0.749204 |
| EURUSD-USDCAD | 7188 | -0.468409 | -0.443685 | -0.441552 | -0.277254 | -0.456626 |
| EURUSD-EURGBP | 7183 | 0.389567 | 0.447332 | 0.447523 | 0.346823 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 0.593916 | 0.498546 | 0.498838 | 0.282096 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 0.545413 | 0.525431 | 0.574754 | 0.488386 | 0.530079 |
| GBPUSD-USDJPY | 7200 | -0.180270 | -0.183079 | -0.268652 | -0.234507 | -0.198556 |
| GBPUSD-USDCHF | 7201 | -0.500351 | -0.536912 | -0.589491 | -0.344597 | -0.486083 |
| GBPUSD-USDCAD | 7205 | -0.474521 | -0.461186 | -0.507222 | -0.391686 | -0.456462 |
| GBPUSD-EURGBP | 7199 | -0.409455 | -0.403591 | -0.342743 | -0.224556 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 0.827557 | 0.829455 | 0.814656 | 0.687025 | 0.828722 |
| AUDUSD-USDJPY | 7199 | -0.096862 | -0.152061 | -0.195647 | -0.090621 | -0.088151 |
| AUDUSD-USDCHF | 7200 | -0.385781 | -0.431874 | -0.496588 | -0.300681 | -0.380878 |
| AUDUSD-USDCAD | 7204 | -0.657008 | -0.700962 | -0.728533 | -0.740440 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 0.013856 | 0.018640 | 0.098838 | 0.094941 | 0.038173 |
| NZDUSD-USDJPY | 7185 | -0.136652 | -0.157835 | -0.221006 | -0.140021 | -0.133568 |
| NZDUSD-USDCHF | 7185 | -0.381817 | -0.444551 | -0.508021 | -0.296786 | -0.393600 |
| NZDUSD-USDCAD | 7190 | -0.624407 | -0.614061 | -0.559037 | -0.430894 | -0.587831 |
| NZDUSD-EURGBP | 7183 | -0.007831 | 0.049181 | 0.087743 | 0.046793 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.372525 | 0.403395 | 0.420333 | 0.209127 | 0.399461 |
| USDJPY-USDCAD | 7186 | 0.077238 | 0.061214 | 0.081891 | 0.021383 | 0.027603 |
| USDJPY-EURGBP | 7181 | -0.140276 | -0.141083 | -0.217636 | -0.232765 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.322025 | 0.313109 | 0.321234 | 0.131032 | 0.304665 |
| USDCHF-EURGBP | 7182 | -0.320588 | -0.333051 | -0.304846 | -0.139197 | -0.325886 |
| USDCAD-EURGBP | 7185 | 0.062588 | 0.029019 | 0.002012 | 0.013755 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index at pre-specified rho_q(q=2,s=100). Not a 29th pair analysis and not a trading signal.

Strongest positive: AUDUSD-NZDUSD (rho=0.8147).
Strongest negative: EURUSD-USDCHF (rho=-0.7774).
Nearest-to-zero: USDCAD-EURGBP (rho=0.0020); USDJPY-USDCAD (rho=0.0819); NZDUSD-EURGBP (rho=0.0877).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
