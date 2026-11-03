# Shrinkage correlation experiments v001

## Research question

For each unordered pair among the eight majors, what is the shrinkage correlation pulled from an eight-asset covariance matrix of matched daily log returns of close on the Alpari D1 history, using fixed delta = 0.2 and Ledoit-Wolf?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Panel: common calendar across all eight majors, n=7127
- Fixed shrinkage: delta=0.2, mu=3.9170889e-05 (mean of diag(S)), n-1 sample covariance
- Ledoit-Wolf: sklearn LedoitWolf, estimated delta=0.0042157642
- Outputs: 28 Word reports, 28 HTML tables, 28 Excel workbooks, panel CSVs (return_panel, sample_cov, shrink_02_corr, ledoit_wolf_corr), charts under `outputs/figures/`

## Index

| pair | n | pearson_r | rho_02 | rho_LW | rho_02_minus_r | rho_LW_minus_r | delta_LW |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7127 | 0.642007 | 0.494213 | 0.638772 | -0.147794 | -0.003235 | 0.004216 |
| EURUSD-AUDUSD | 7127 | 0.558036 | 0.453734 | 0.555859 | -0.104302 | -0.002177 | 0.004216 |
| EURUSD-NZDUSD | 7127 | 0.552004 | 0.449617 | 0.549870 | -0.102388 | -0.002135 | 0.004216 |
| EURUSD-USDJPY | 7127 | -0.299566 | -0.235461 | -0.298190 | 0.064105 | 0.001375 | 0.004216 |
| EURUSD-USDCHF | 7127 | -0.747345 | -0.594158 | -0.744091 | 0.153187 | 0.003254 | 0.004216 |
| EURUSD-USDCAD | 7127 | -0.458052 | -0.344465 | -0.455504 | 0.113586 | 0.002548 | 0.004216 |
| EURUSD-EURGBP | 7127 | 0.439919 | 0.325783 | 0.437314 | -0.114135 | -0.002604 | 0.004216 |
| GBPUSD-AUDUSD | 7127 | 0.540790 | 0.437012 | 0.538608 | -0.103778 | -0.002183 | 0.004216 |
| GBPUSD-NZDUSD | 7127 | 0.532783 | 0.431297 | 0.530651 | -0.101486 | -0.002132 | 0.004216 |
| GBPUSD-USDJPY | 7127 | -0.196287 | -0.153336 | -0.195359 | 0.042951 | 0.000928 | 0.004216 |
| GBPUSD-USDCHF | 7127 | -0.484413 | -0.382756 | -0.482238 | 0.101656 | 0.002174 | 0.004216 |
| GBPUSD-USDCAD | 7127 | -0.457478 | -0.341922 | -0.454872 | 0.115556 | 0.002606 | 0.004216 |
| GBPUSD-EURGBP | 7127 | -0.398603 | -0.293375 | -0.396190 | 0.105228 | 0.002413 | 0.004216 |
| AUDUSD-NZDUSD | 7127 | 0.828775 | 0.708642 | 0.826403 | -0.120133 | -0.002372 | 0.004216 |
| AUDUSD-USDJPY | 7127 | -0.086373 | -0.071268 | -0.086063 | 0.015105 | 0.000310 | 0.004216 |
| AUDUSD-USDCHF | 7127 | -0.381088 | -0.318051 | -0.379811 | 0.063037 | 0.001277 | 0.004216 |
| AUDUSD-USDCAD | 7127 | -0.648925 | -0.512290 | -0.645966 | 0.136635 | 0.002959 | 0.004216 |
| AUDUSD-EURGBP | 7127 | 0.036369 | 0.028273 | 0.036190 | -0.008096 | -0.000179 | 0.004216 |
| NZDUSD-USDJPY | 7127 | -0.133871 | -0.110653 | -0.133395 | 0.023218 | 0.000476 | 0.004216 |
| NZDUSD-USDCHF | 7127 | -0.394447 | -0.329777 | -0.393139 | 0.064670 | 0.001308 | 0.004216 |
| NZDUSD-USDCAD | 7127 | -0.589889 | -0.466501 | -0.587220 | 0.123388 | 0.002669 | 0.004216 |
| NZDUSD-EURGBP | 7127 | 0.035833 | 0.027906 | 0.035658 | -0.007927 | -0.000175 | 0.004216 |
| USDJPY-USDCHF | 7127 | 0.397789 | 0.320931 | 0.396182 | -0.076858 | -0.001607 | 0.004216 |
| USDJPY-USDCAD | 7127 | 0.026272 | 0.020050 | 0.026134 | -0.006223 | -0.000138 | 0.004216 |
| USDJPY-EURGBP | 7127 | -0.129377 | -0.097228 | -0.128652 | 0.032149 | 0.000725 | 0.004216 |
| USDCHF-USDCAD | 7127 | 0.304864 | 0.235326 | 0.303336 | -0.069538 | -0.001528 | 0.004216 |
| USDCHF-EURGBP | 7127 | -0.325016 | -0.247055 | -0.323271 | 0.077961 | 0.001745 | 0.004216 |
| USDCAD-EURGBP | 7127 | -0.014713 | -0.010579 | -0.014616 | 0.004134 | 0.000097 | 0.004216 |

## Cross-pair conclusion

Reading of the 28-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest positive fixed-delta shrink link: AUDUSD-NZDUSD (rho_02=0.7086, n=7127).
Strongest negative fixed-delta shrink link: EURUSD-USDCHF (rho_02=-0.5942, n=7127).
Nearest-to-zero fixed-delta shrink links: USDCAD-EURGBP (rho_02=-0.0106); USDJPY-USDCAD (rho_02=0.0200); NZDUSD-EURGBP (rho_02=0.0279).
Largest |rho_02 minus Pearson r| gaps on the same panel: EURUSD-USDCHF (gap=0.1532, rho_02=-0.5942, r=-0.7473); EURUSD-GBPUSD (gap=-0.1478, rho_02=0.4942, r=0.6420); AUDUSD-USDCAD (gap=0.1366, rho_02=-0.5123, r=-0.6489). A large gap means the delta=0.2 blend pulled the off-diagonal harder relative to the raw sample link; inspect that pair's scatter before treating either score as settled.

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
