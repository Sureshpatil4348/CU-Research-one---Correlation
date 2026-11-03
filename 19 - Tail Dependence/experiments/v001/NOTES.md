# Tail dependence experiments v001

## Research question

For each unordered pair among the eight majors, how often do matched daily log returns of close co-occur in the lower and upper empirical uniform tails at alpha=0.05 on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Uniforms: ranks/(n+1); alpha=0.05
- Statistic: lower and upper L_hat conditioning on each leg with numerator and denominator counts; Pearson r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/`

## Index

| pair | n | L_lower_cond_R | num/den_R | L_lower_cond_L | num/den_L | L_upper_cond_R | L_upper_cond_L | pearson_r |
| --- | ---: | ---: | --- | ---: | --- | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.325000 | 117/360 | 0.325000 | 117/360 | 0.394444 | 0.394444 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 0.330556 | 119/360 | 0.330556 | 119/360 | 0.363889 | 0.363889 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 0.306407 | 110/359 | 0.306407 | 110/359 | 0.331476 | 0.331476 | 0.549808 |
| EURUSD-USDJPY | 7200 | 0.063889 | 23/360 | 0.063889 | 23/360 | 0.047222 | 0.047222 | -0.300952 |
| EURUSD-USDCHF | 7186 | 0.002786 | 1/359 | 0.002786 | 1/359 | 0.000000 | 0.000000 | -0.749204 |
| EURUSD-USDCAD | 7188 | 0.008357 | 3/359 | 0.008357 | 3/359 | 0.011142 | 0.011142 | -0.456626 |
| EURUSD-EURGBP | 7183 | 0.373259 | 134/359 | 0.373259 | 134/359 | 0.278552 | 0.278552 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 0.329640 | 119/361 | 0.329640 | 119/361 | 0.337950 | 0.337950 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 0.313889 | 113/360 | 0.313889 | 113/360 | 0.311111 | 0.311111 | 0.530079 |
| GBPUSD-USDJPY | 7200 | 0.080556 | 29/360 | 0.080556 | 29/360 | 0.066667 | 0.066667 | -0.198556 |
| GBPUSD-USDCHF | 7201 | 0.002778 | 1/360 | 0.002778 | 1/360 | 0.013889 | 0.013889 | -0.486083 |
| GBPUSD-USDCAD | 7205 | 0.013889 | 5/360 | 0.013889 | 5/360 | 0.016667 | 0.016667 | -0.456462 |
| GBPUSD-EURGBP | 7199 | 0.033333 | 12/360 | 0.033333 | 12/360 | 0.036111 | 0.036111 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 0.583333 | 210/360 | 0.583333 | 210/360 | 0.602778 | 0.602778 | 0.828722 |
| AUDUSD-USDJPY | 7199 | 0.169444 | 61/360 | 0.169444 | 61/360 | 0.097222 | 0.097222 | -0.088151 |
| AUDUSD-USDCHF | 7200 | 0.036111 | 13/360 | 0.036111 | 13/360 | 0.033333 | 0.033333 | -0.380878 |
| AUDUSD-USDCAD | 7204 | 0.000000 | 0/360 | 0.000000 | 0/360 | 0.005556 | 0.005556 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 0.142061 | 51/359 | 0.142061 | 51/359 | 0.111421 | 0.111421 | 0.038173 |
| NZDUSD-USDJPY | 7185 | 0.142061 | 51/359 | 0.142061 | 51/359 | 0.097493 | 0.097493 | -0.133568 |
| NZDUSD-USDCHF | 7185 | 0.030641 | 11/359 | 0.030641 | 11/359 | 0.038997 | 0.038997 | -0.393600 |
| NZDUSD-USDCAD | 7190 | 0.008357 | 3/359 | 0.008357 | 3/359 | 0.005571 | 0.005571 | -0.587831 |
| NZDUSD-EURGBP | 7183 | 0.139276 | 50/359 | 0.139276 | 50/359 | 0.119777 | 0.119777 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.267409 | 96/359 | 0.267409 | 96/359 | 0.228412 | 0.228412 | 0.399461 |
| USDJPY-USDCAD | 7186 | 0.108635 | 39/359 | 0.108635 | 39/359 | 0.094708 | 0.094708 | 0.027603 |
| USDJPY-EURGBP | 7181 | 0.066852 | 24/359 | 0.066852 | 24/359 | 0.058496 | 0.058496 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.208914 | 75/359 | 0.208914 | 75/359 | 0.214485 | 0.214485 | 0.304665 |
| USDCHF-EURGBP | 7182 | 0.016713 | 6/359 | 0.016713 | 6/359 | 0.019499 | 0.019499 | -0.325886 |
| USDCAD-EURGBP | 7185 | 0.052925 | 19/359 | 0.052925 | 19/359 | 0.144847 | 0.144847 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index at alpha=0.05. Not a 29th pair analysis and not a trading signal.

Strongest lower-tail L_hat: AUDUSD-NZDUSD (cond NZDUSD) (L_hat=0.5833).
Strongest upper-tail L_hat: AUDUSD-NZDUSD (cond NZDUSD) (L_hat=0.6028).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
