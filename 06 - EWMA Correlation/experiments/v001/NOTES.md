# EWMA correlation experiments v001

## Research question

For each unordered pair among the eight majors, what is the EWMA correlation path of matched daily log returns of close on the Alpari D1 history that the broker actually provided, with lambda = 0.94?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Mean adjustment: each leg demeaned by its mean on the matched rows (full-sample description)
- Statistic: RiskMetrics EWMA rho with lambda=0.94, zero seeds, burn-in=60 for path summaries; headline = latest rho; same-sample Pearson r and latest rho minus r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/` (closes, returns, EWMA path with Pearson r reference)

## Index

| pair | n | latest_rho | mean | std | min | max | pearson_r | latest_minus_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.852473 | 0.658094 | 0.166113 | -0.182133 | 0.943938 | 0.641738 | 0.210735 |
| EURUSD-AUDUSD | 7201 | 0.141725 | 0.549880 | 0.214124 | -0.412310 | 0.925362 | 0.556324 | -0.414599 |
| EURUSD-NZDUSD | 7186 | 0.452453 | 0.539542 | 0.201944 | -0.280246 | 0.903521 | 0.549808 | -0.097355 |
| EURUSD-USDJPY | 7200 | -0.372335 | -0.373836 | 0.277228 | -0.868164 | 0.702255 | -0.300952 | -0.071383 |
| EURUSD-USDCHF | 7186 | -0.637363 | -0.829648 | 0.165734 | -0.997239 | 0.514828 | -0.749204 | 0.111840 |
| EURUSD-USDCAD | 7188 | -0.616377 | -0.429907 | 0.241228 | -0.860639 | 0.530718 | -0.456626 | -0.159751 |
| EURUSD-EURGBP | 7183 | 0.186269 | 0.407676 | 0.274828 | -0.645669 | 0.924274 | 0.439899 | -0.253629 |
| GBPUSD-AUDUSD | 7228 | 0.192217 | 0.517038 | 0.219776 | -0.272466 | 0.914120 | 0.539048 | -0.346831 |
| GBPUSD-NZDUSD | 7203 | 0.520720 | 0.507829 | 0.219902 | -0.326118 | 0.913643 | 0.530079 | -0.009359 |
| GBPUSD-USDJPY | 7200 | -0.419698 | -0.279960 | 0.282615 | -0.819667 | 0.777508 | -0.198556 | -0.221143 |
| GBPUSD-USDCHF | 7201 | -0.651428 | -0.562215 | 0.200536 | -0.946074 | 0.259116 | -0.486083 | -0.165345 |
| GBPUSD-USDCAD | 7205 | -0.635453 | -0.410721 | 0.239610 | -0.889292 | 0.503537 | -0.456462 | -0.178990 |
| GBPUSD-EURGBP | 7199 | -0.353983 | -0.355678 | 0.277733 | -0.963861 | 0.519124 | -0.397845 | 0.043863 |
| AUDUSD-NZDUSD | 7202 | 0.367270 | 0.808000 | 0.107003 | 0.190548 | 0.968503 | 0.828722 | -0.461452 |
| AUDUSD-USDJPY | 7199 | -0.278350 | -0.232534 | 0.337956 | -0.851624 | 0.830877 | -0.088151 | -0.190200 |
| AUDUSD-USDCHF | 7200 | 0.135132 | -0.441226 | 0.230293 | -0.880285 | 0.482792 | -0.380878 | 0.516011 |
| AUDUSD-USDCAD | 7204 | -0.390826 | -0.602163 | 0.187852 | -0.937771 | 0.361182 | -0.647362 | 0.256536 |
| AUDUSD-EURGBP | 7198 | -0.104554 | 0.044263 | 0.264445 | -0.812823 | 0.740804 | 0.038173 | -0.142727 |
| NZDUSD-USDJPY | 7185 | -0.239394 | -0.247805 | 0.321541 | -0.827228 | 0.901342 | -0.133568 | -0.105826 |
| NZDUSD-USDCHF | 7185 | -0.224004 | -0.443703 | 0.216486 | -0.869275 | 0.368719 | -0.393600 | 0.169596 |
| NZDUSD-USDCAD | 7190 | -0.270371 | -0.541340 | 0.193494 | -0.925510 | 0.328489 | -0.587831 | 0.317460 |
| NZDUSD-EURGBP | 7183 | -0.162548 | 0.034295 | 0.253645 | -0.777740 | 0.719825 | 0.037186 | -0.199735 |
| USDJPY-USDCHF | 7185 | 0.337960 | 0.471332 | 0.242244 | -0.459612 | 0.883602 | 0.399461 | -0.061501 |
| USDJPY-USDCAD | 7186 | 0.454132 | 0.121293 | 0.297012 | -0.840340 | 0.790839 | 0.027603 | 0.426529 |
| USDJPY-EURGBP | 7181 | 0.124155 | -0.108939 | 0.234409 | -0.778783 | 0.694128 | -0.127992 | 0.252147 |
| USDCHF-USDCAD | 7188 | 0.480567 | 0.338190 | 0.245171 | -0.522730 | 0.852657 | 0.304665 | 0.175902 |
| USDCHF-EURGBP | 7182 | 0.092712 | -0.322479 | 0.269872 | -0.891722 | 0.518322 | -0.325886 | 0.418599 |
| USDCAD-EURGBP | 7185 | 0.093336 | -0.026018 | 0.243948 | -0.672547 | 0.684609 | -0.014622 | 0.107957 |

## Cross-pair conclusion

Reading of the 28-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest positive latest EWMA rho: EURUSD-GBPUSD (latest_rho=0.8525, n=7202).
Strongest negative latest EWMA rho: GBPUSD-USDCHF (latest_rho=-0.6514, n=7201).
Nearest-to-zero latest EWMA rho: USDCHF-EURGBP (latest_rho=0.0927); USDCAD-EURGBP (latest_rho=0.0933); AUDUSD-EURGBP (latest_rho=-0.1046).
Largest |latest rho minus Pearson r| gaps on the same sample: AUDUSD-USDCHF (gap=0.5160, latest_rho=0.1351, r=-0.3809); AUDUSD-NZDUSD (gap=-0.4615, latest_rho=0.3673, r=0.8287); USDJPY-USDCAD (gap=0.4265, latest_rho=0.4541, r=0.0276). A large gap can flag a recent regime shift versus the full-sample mean; inspect that pair's EWMA path before treating either score as settled.

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
