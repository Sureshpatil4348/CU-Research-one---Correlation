# EURUSD same-day candle board

## Last complete day

On 2026-11-02 EURUSD closed up. Same day: GBPUSD with, AUDUSD against, NZDUSD against, USDJPY against, USDCHF with, USDCAD against.

## Pack-median side note

JPY is the currency moving out of line versus the pack. It disagreed with the other six on the most days (2175).

Last complete day (2026-11-02) vs pack: EUR, GBP, CHF were out of line.

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- EURGBP left out.
- Anchor: EURUSD close direction that day.
- WITH/AGAINST uses aligned currency-vs-USD signs (USDJPY, USDCHF, USDCAD flipped).
- Candle / board window: last 60 complete days.
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Full history vs EURUSD

| pair | days with | days against | % with | % against |
| --- | ---: | ---: | ---: | ---: |
| GBPUSD | 5232 | 1876 | 73.6% | 26.4% |
| AUDUSD | 4999 | 2095 | 70.5% | 29.5% |
| NZDUSD | 4895 | 2208 | 68.9% | 31.1% |
| USDJPY | 4482 | 2621 | 63.1% | 36.9% |
| USDCHF | 5919 | 1184 | 83.3% | 16.7% |
| USDCAD | 4592 | 2515 | 64.6% | 35.4% |

## Pack-median counts

| currency | days | with pack | out of line | lone dissenter | break days |
| --- | ---: | ---: | ---: | ---: | ---: |
| EUR | 7119 | 6027 | 1092 | 93 | 223 |
| GBP | 7119 | 5736 | 1383 | 273 | 410 |
| AUD | 7119 | 5862 | 1257 | 139 | 339 |
| NZD | 7119 | 5809 | 1310 | 163 | 366 |
| JPY | 7119 | 4944 | 2175 | 720 | 918 |
| CHF | 7119 | 5822 | 1297 | 122 | 347 |
| CAD | 7119 | 5275 | 1844 | 478 | 611 |

This NOTES.md is a same-day co-move record. It is not a crash forecast and not a trading signal.
