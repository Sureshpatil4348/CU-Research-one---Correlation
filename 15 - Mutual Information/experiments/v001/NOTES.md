# Mutual information experiments v001

## Research question

For each unordered pair among the eight majors, what is the discrete mutual information of matched daily log returns of close after a fixed B=10 equal-frequency binning on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Discretization: B=10 equal-frequency bins per leg on the matched sample (fixed before ranking)
- Statistic: discrete MI in nats; H_x, H_y; normalized MI = I/sqrt(H_x H_y); Pearson r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/` (closes, returns, joint heatmap)

## Index

| pair | n | n_bins | mi | h_x | h_y | nmi | pearson_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 10 | 0.283933 | 2.302574 | 2.302585 | 0.123311 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 10 | 0.196609 | 2.302576 | 2.302585 | 0.085387 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 10 | 0.184995 | 2.302574 | 2.302585 | 0.080343 | 0.549808 |
| EURUSD-USDJPY | 7200 | 10 | 0.091193 | 2.302573 | 2.302585 | 0.039605 | -0.300952 |
| EURUSD-USDCHF | 7186 | 10 | 0.621780 | 2.302581 | 2.302585 | 0.270036 | -0.749204 |
| EURUSD-USDCAD | 7188 | 10 | 0.115953 | 2.302579 | 2.302585 | 0.050358 | -0.456626 |
| EURUSD-EURGBP | 7183 | 10 | 0.126818 | 2.302582 | 2.302585 | 0.055076 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 10 | 0.171961 | 2.302585 | 2.302585 | 0.074682 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 10 | 0.160248 | 2.302585 | 2.302585 | 0.069595 | 0.530079 |
| GBPUSD-USDJPY | 7200 | 10 | 0.061098 | 2.302585 | 2.302585 | 0.026534 | -0.198556 |
| GBPUSD-USDCHF | 7201 | 10 | 0.200400 | 2.302585 | 2.302585 | 0.087033 | -0.486083 |
| GBPUSD-USDCAD | 7205 | 10 | 0.105697 | 2.302585 | 2.302585 | 0.045904 | -0.456462 |
| GBPUSD-EURGBP | 7199 | 10 | 0.079366 | 2.302585 | 2.302585 | 0.034468 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 10 | 0.526019 | 2.302585 | 2.302585 | 0.228447 | 0.828722 |
| AUDUSD-USDJPY | 7199 | 10 | 0.056921 | 2.302585 | 2.302585 | 0.024720 | -0.088151 |
| AUDUSD-USDCHF | 7200 | 10 | 0.132365 | 2.302585 | 2.302585 | 0.057485 | -0.380878 |
| AUDUSD-USDCAD | 7204 | 10 | 0.235407 | 2.302585 | 2.302585 | 0.102236 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 10 | 0.017924 | 2.302585 | 2.302585 | 0.007784 | 0.038173 |
| NZDUSD-USDJPY | 7185 | 10 | 0.054972 | 2.302585 | 2.302585 | 0.023874 | -0.133568 |
| NZDUSD-USDCHF | 7185 | 10 | 0.130128 | 2.302585 | 2.302585 | 0.056514 | -0.393600 |
| NZDUSD-USDCAD | 7190 | 10 | 0.182906 | 2.302585 | 2.302585 | 0.079435 | -0.587831 |
| NZDUSD-EURGBP | 7183 | 10 | 0.016446 | 2.302585 | 2.302585 | 0.007142 | 0.037186 |
| USDJPY-USDCHF | 7185 | 10 | 0.136359 | 2.302585 | 2.302585 | 0.059220 | 0.399461 |
| USDJPY-USDCAD | 7186 | 10 | 0.022200 | 2.302585 | 2.302585 | 0.009642 | 0.027603 |
| USDJPY-EURGBP | 7181 | 10 | 0.015156 | 2.302585 | 2.302585 | 0.006582 | -0.127992 |
| USDCHF-USDCAD | 7188 | 10 | 0.076884 | 2.302585 | 2.302585 | 0.033390 | 0.304665 |
| USDCHF-EURGBP | 7182 | 10 | 0.082707 | 2.302585 | 2.302585 | 0.035919 | -0.325886 |
| USDCAD-EURGBP | 7185 | 10 | 0.013951 | 2.302585 | 2.302585 | 0.006059 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index using normalized MI under the fixed B=10 equal-frequency rule. Not a 29th pair analysis and not a trading signal. Raw I and normalized MI share the same bins.

Strongest normalized MI: EURUSD-USDCHF (nmi=0.2700, I=0.621780 nats, n=7186).
Nearest-to-zero normalized MI: USDCAD-EURGBP (nmi=0.0061, I=0.013951); USDJPY-EURGBP (nmi=0.0066, I=0.015156); NZDUSD-EURGBP (nmi=0.0071, I=0.016446).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
