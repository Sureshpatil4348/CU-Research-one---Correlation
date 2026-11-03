# Rolling correlation experiments v001

## Research question

For the short watchlist, secondary tier, and low-value pairs, how does Pearson correlation of daily log returns move when recomputed on the last 20, 60, and 100 matched days?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Statistic: rolling Pearson r with W in {20, 60, 100}
- Full-sample baseline: copied from Pearson method 01 v001 NOTES
- Outputs: 17 Word reports, HTML tables, CSVs, charts, WATCHLIST.md

## Short watchlist

| pair | baseline_r | r20 | r60 | r100 | std20 | std100 | n_roll_100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AUDUSD-NZDUSD | 0.828722 | 0.263046 | 0.606659 | 0.705993 | 0.125776 | 0.090679 | 7103 |
| EURUSD-USDCHF | -0.749204 | -0.728572 | -0.691696 | -0.755247 | 0.174392 | 0.160609 | 7087 |
| AUDUSD-USDCAD | -0.647362 | -0.302206 | -0.526113 | -0.522737 | 0.221049 | 0.160716 | 7105 |
| EURUSD-GBPUSD | 0.641738 | 0.925234 | 0.875106 | 0.851407 | 0.203389 | 0.130660 | 7103 |
| NZDUSD-USDCAD | -0.587831 | -0.398148 | -0.530855 | -0.564059 | 0.230846 | 0.162925 | 7091 |

## Secondary tier

| pair | baseline_r | r20 | r60 | r100 | std20 | std100 | n_roll_100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-AUDUSD | 0.556324 | -0.003562 | 0.443604 | 0.534255 | 0.252543 | 0.180631 | 7102 |
| EURUSD-NZDUSD | 0.549808 | 0.477766 | 0.685647 | 0.717512 | 0.240765 | 0.164785 | 7087 |
| GBPUSD-AUDUSD | 0.539048 | 0.053272 | 0.443461 | 0.528758 | 0.257180 | 0.187357 | 7129 |
| GBPUSD-NZDUSD | 0.530079 | 0.568543 | 0.724486 | 0.726667 | 0.258716 | 0.186486 | 7104 |
| GBPUSD-USDCHF | -0.486083 | -0.728440 | -0.637713 | -0.702638 | 0.231920 | 0.171379 | 7102 |

## Low-value

| pair | baseline_r | r20 | r60 | r100 | std20 | std100 | n_roll_100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AUDUSD-EURGBP | 0.038173 | -0.141629 | -0.003735 | -0.094151 | 0.308699 | 0.221223 | 7099 |
| NZDUSD-EURGBP | 0.037186 | -0.272686 | -0.091435 | -0.165066 | 0.296263 | 0.206823 | 7084 |
| USDJPY-USDCAD | 0.027603 | 0.487295 | 0.516258 | 0.418713 | 0.339732 | 0.257416 | 7087 |
| USDCAD-EURGBP | -0.014622 | 0.031654 | -0.105504 | 0.007327 | 0.287676 | 0.195219 | 7086 |
| AUDUSD-USDJPY | -0.088151 | 0.030926 | -0.465814 | -0.440955 | 0.380564 | 0.299004 | 7100 |
| NZDUSD-USDJPY | -0.133568 | -0.023279 | -0.401882 | -0.456400 | 0.359165 | 0.286866 | 7086 |
| USDJPY-EURGBP | -0.127992 | 0.245513 | -0.086351 | 0.013357 | 0.282542 | 0.183262 | 7082 |

This NOTES.md is the index only. It is not an 18th analysis.
