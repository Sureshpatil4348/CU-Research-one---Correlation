# Distance correlation experiments v001

## Research question

For each unordered pair among the eight majors, what is the biased sample distance correlation of matched daily log returns of close on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Statistic: biased sample dCor via double-centered absolute-distance matrices (guide formula); Pearson r and dCor minus |r| as side checks
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/` (closes, returns, scatter)

## Index

| pair | n | dcor | pearson_r | dcor_minus_abs_r |
| --- | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.614668 | 0.641738 | -0.027070 |
| EURUSD-AUDUSD | 7201 | 0.524506 | 0.556324 | -0.031818 |
| EURUSD-NZDUSD | 7186 | 0.506095 | 0.549808 | -0.043713 |
| EURUSD-USDJPY | 7200 | 0.336725 | -0.300952 | 0.035773 |
| EURUSD-USDCHF | 7186 | 0.804722 | -0.749204 | 0.055518 |
| EURUSD-USDCAD | 7188 | 0.406722 | -0.456626 | -0.049903 |
| EURUSD-EURGBP | 7183 | 0.417753 | 0.439899 | -0.022146 |
| GBPUSD-AUDUSD | 7228 | 0.494300 | 0.539048 | -0.044748 |
| GBPUSD-NZDUSD | 7203 | 0.479367 | 0.530079 | -0.050712 |
| GBPUSD-USDJPY | 7200 | 0.263987 | -0.198556 | 0.065432 |
| GBPUSD-USDCHF | 7201 | 0.525406 | -0.486083 | 0.039323 |
| GBPUSD-USDCAD | 7205 | 0.392609 | -0.456462 | -0.063853 |
| GBPUSD-EURGBP | 7199 | 0.320074 | -0.397845 | -0.077771 |
| AUDUSD-NZDUSD | 7202 | 0.783257 | 0.828722 | -0.045465 |
| AUDUSD-USDJPY | 7199 | 0.219281 | -0.088151 | 0.131130 |
| AUDUSD-USDCHF | 7200 | 0.421261 | -0.380878 | 0.040383 |
| AUDUSD-USDCAD | 7204 | 0.576700 | -0.647362 | -0.070662 |
| AUDUSD-EURGBP | 7198 | 0.091247 | 0.038173 | 0.053074 |
| NZDUSD-USDJPY | 7185 | 0.223997 | -0.133568 | 0.090429 |
| NZDUSD-USDCHF | 7185 | 0.413145 | -0.393600 | 0.019546 |
| NZDUSD-USDCAD | 7190 | 0.516034 | -0.587831 | -0.071797 |
| NZDUSD-EURGBP | 7183 | 0.080261 | 0.037186 | 0.043075 |
| USDJPY-USDCHF | 7185 | 0.425263 | 0.399461 | 0.025802 |
| USDJPY-USDCAD | 7186 | 0.114711 | 0.027603 | 0.087108 |
| USDJPY-EURGBP | 7181 | 0.113334 | -0.127992 | -0.014659 |
| USDCHF-USDCAD | 7188 | 0.317131 | 0.304665 | 0.012466 |
| USDCHF-EURGBP | 7182 | 0.337208 | -0.325886 | 0.011321 |
| USDCAD-EURGBP | 7185 | 0.073205 | -0.014622 | 0.058583 |

## Cross-pair conclusion

Reading of the 28-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest dCor: EURUSD-USDCHF (dcor=0.8047, n=7186).
Nearest-to-zero dCor: USDCAD-EURGBP (dcor=0.0732); NZDUSD-EURGBP (dcor=0.0803); AUDUSD-EURGBP (dcor=0.0912).
Largest |dCor minus |r|| gaps: AUDUSD-USDJPY (gap=0.1311, dcor=0.2193, r=-0.0882); NZDUSD-USDJPY (gap=0.0904, dcor=0.2240, r=-0.1336); USDJPY-USDCAD (gap=0.0871, dcor=0.1147, r=0.0276). A large gap can flag dependence beyond the linear Pearson link; inspect that pair's scatter before treating either score as settled.

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
