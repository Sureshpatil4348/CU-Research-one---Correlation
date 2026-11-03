# Volatility and realized correlation experiments v001

## Research question

For each unordered pair among the eight majors, what is rho_vol = Corr(|log return|, |log return|) of matched daily closes on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Statistic: rho_vol = Pearson on absolute log returns (headline); signed Pearson r as a side check
- rho_realized: not computed — D1 snapshot has no intraday buckets (formula sheet requires synchronized intraday returns within day d)
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/`

## Index

| pair | n | rho_vol | pearson_r |
| --- | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.456552 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 0.418183 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 0.407411 | 0.549808 |
| EURUSD-USDJPY | 7200 | 0.289809 | -0.300952 |
| EURUSD-USDCHF | 7186 | 0.635604 | -0.749204 |
| EURUSD-USDCAD | 7188 | 0.332217 | -0.456626 |
| EURUSD-EURGBP | 7183 | 0.371437 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 0.406791 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 0.391435 | 0.530079 |
| GBPUSD-USDJPY | 7200 | 0.273595 | -0.198556 |
| GBPUSD-USDCHF | 7201 | 0.299517 | -0.486083 |
| GBPUSD-USDCAD | 7205 | 0.344748 | -0.456462 |
| GBPUSD-EURGBP | 7199 | 0.399715 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 0.727732 | 0.828722 |
| AUDUSD-USDJPY | 7199 | 0.332494 | -0.088151 |
| AUDUSD-USDCHF | 7200 | 0.252302 | -0.380878 |
| AUDUSD-USDCAD | 7204 | 0.524403 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 0.216675 | 0.038173 |
| NZDUSD-USDJPY | 7185 | 0.304709 | -0.133568 |
| NZDUSD-USDCHF | 7185 | 0.270082 | -0.393600 |
| NZDUSD-USDCAD | 7190 | 0.451792 | -0.587831 |
| NZDUSD-EURGBP | 7183 | 0.206626 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.276663 | 0.399461 |
| USDJPY-USDCAD | 7186 | 0.223844 | 0.027603 |
| USDJPY-EURGBP | 7181 | 0.177551 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.214705 | 0.304665 |
| USDCHF-EURGBP | 7182 | 0.240708 | -0.325886 |
| USDCAD-EURGBP | 7185 | 0.191552 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index at pre-specified rho_vol = Corr(|x|,|y|). Not a 29th pair analysis and not a trading signal. rho_realized was not computed on this D1 snapshot.

Strongest rho_vol: AUDUSD-NZDUSD (rho_vol=0.7277).
Nearest-to-zero rho_vol: USDJPY-EURGBP (rho_vol=0.1776); USDCAD-EURGBP (rho_vol=0.1916); NZDUSD-EURGBP (rho_vol=0.2066).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
