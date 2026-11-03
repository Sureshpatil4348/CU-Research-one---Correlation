# Hayashi-Yoshida covariance experiments v001

## Research question

For each unordered pair among the eight majors, what is the synced-D1 Hayashi-Yoshida covariance and normalized rho_HY of matched daily log returns of close on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Intervals: consecutive daily close-to-close; overlap = same day (synchronized special case of HY)
- Statistic: C_HY = sum r_x r_y; rho_HY = C_HY / sqrt(sum r_x^2 * sum r_y^2) as headline; Pearson r as a side check
- Async tick HY: not tested (no tick snapshot in this project yet)
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/`

## Index

| pair | n | c_hy | rho_hy | pearson_r |
| --- | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.15134349 | 0.641737 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 0.17533869 | 0.556316 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 0.17499687 | 0.549806 | 0.549808 |
| EURUSD-USDJPY | 7200 | -0.07796961 | -0.300956 | -0.300952 |
| EURUSD-USDCHF | 7186 | -0.20601824 | -0.749157 | -0.749204 |
| EURUSD-USDCAD | 7188 | -0.09791500 | -0.456619 | -0.456626 |
| EURUSD-EURGBP | 7183 | 0.08928788 | 0.439889 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 0.16595773 | 0.539028 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 0.16467566 | 0.530071 | 0.530079 |
| GBPUSD-USDJPY | 7200 | -0.05008173 | -0.198580 | -0.198556 |
| GBPUSD-USDCHF | 7201 | -0.13025357 | -0.486006 | -0.486083 |
| GBPUSD-USDCAD | 7205 | -0.09539873 | -0.456448 | -0.456462 |
| GBPUSD-EURGBP | 7199 | -0.07872098 | -0.397860 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 0.34418289 | 0.828720 | 0.828722 |
| AUDUSD-USDJPY | 7199 | -0.02969765 | -0.088119 | -0.088151 |
| AUDUSD-USDCHF | 7200 | -0.13644377 | -0.380894 | -0.380878 |
| AUDUSD-USDCAD | 7204 | -0.18097643 | -0.647364 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 0.01010595 | 0.038185 | 0.038173 |
| NZDUSD-USDJPY | 7185 | -0.04548080 | -0.133551 | -0.133568 |
| NZDUSD-USDCHF | 7185 | -0.14233368 | -0.393604 | -0.393600 |
| NZDUSD-USDCAD | 7190 | -0.16616872 | -0.587832 | -0.587831 |
| NZDUSD-EURGBP | 7183 | 0.00994884 | 0.037193 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.11741676 | 0.399345 | 0.399461 |
| USDJPY-USDCAD | 7186 | 0.00632613 | 0.027577 | 0.027603 |
| USDJPY-EURGBP | 7181 | -0.02779584 | -0.127953 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.07429085 | 0.304679 | 0.304665 |
| USDCHF-EURGBP | 7182 | -0.07518405 | -0.325919 | -0.325886 |
| USDCAD-EURGBP | 7185 | -0.00263182 | -0.014628 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index at pre-specified rho_HY (synced D1 special case). Not a 29th pair analysis and not a trading signal.

Strongest positive: AUDUSD-NZDUSD (rho_HY=0.8287).
Strongest negative: EURUSD-USDCHF (rho_HY=-0.7492).
Nearest-to-zero: USDCAD-EURGBP (rho_HY=-0.0146); USDJPY-USDCAD (rho_HY=0.0276); NZDUSD-EURGBP (rho_HY=0.0372).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
