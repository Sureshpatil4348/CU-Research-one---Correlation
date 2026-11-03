# Pearson experiments v001

## Research question

For each unordered pair among the eight majors, what is the Pearson correlation of matched daily log returns of close on the Alpari D1 history that the broker actually provided?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Statistic: Pearson r, two-sided p, approximate 95% Fisher interval via `scipy.stats.pearsonr`
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 CSVs, charts under `outputs/figures/`

## Index

| pair | n | r | p | ci_low | ci_high |
| --- | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.641738 | 0 | 0.627949 | 0.655124 |
| EURUSD-AUDUSD | 7201 | 0.556324 | 0 | 0.540167 | 0.572070 |
| EURUSD-NZDUSD | 7186 | 0.549808 | 0 | 0.533468 | 0.565738 |
| EURUSD-USDJPY | 7200 | -0.300952 | 1.26181e-150 | -0.321814 | -0.279798 |
| EURUSD-USDCHF | 7186 | -0.749204 | 0 | -0.759174 | -0.738881 |
| EURUSD-USDCAD | 7188 | -0.456626 | 0 | -0.474732 | -0.438132 |
| EURUSD-EURGBP | 7183 | 0.439899 | 0 | 0.421056 | 0.458362 |
| GBPUSD-AUDUSD | 7228 | 0.539048 | 0 | 0.522487 | 0.555203 |
| GBPUSD-NZDUSD | 7203 | 0.530079 | 0 | 0.513268 | 0.546483 |
| GBPUSD-USDJPY | 7200 | -0.198556 | 6.38567e-65 | -0.220643 | -0.176265 |
| GBPUSD-USDCHF | 7201 | -0.486083 | 0 | -0.503527 | -0.468242 |
| GBPUSD-USDCAD | 7205 | -0.456462 | 0 | -0.474552 | -0.437988 |
| GBPUSD-EURGBP | 7199 | -0.397845 | 1.22348e-271 | -0.417112 | -0.378221 |
| AUDUSD-NZDUSD | 7202 | 0.828722 | 0 | 0.821347 | 0.835820 |
| AUDUSD-USDJPY | 7199 | -0.088151 | 6.75242e-14 | -0.111025 | -0.065183 |
| AUDUSD-USDCHF | 7200 | -0.380878 | 2.58908e-247 | -0.400454 | -0.360955 |
| AUDUSD-USDCAD | 7204 | -0.647362 | 0 | -0.660579 | -0.633743 |
| AUDUSD-EURGBP | 7198 | 0.038173 | 0.00119832 | 0.015084 | 0.061222 |
| NZDUSD-USDJPY | 7185 | -0.133568 | 5.84098e-30 | -0.156209 | -0.110787 |
| NZDUSD-USDCHF | 7185 | -0.393600 | 6.77239e-265 | -0.412964 | -0.373879 |
| NZDUSD-USDCAD | 7190 | -0.587831 | 0 | -0.602756 | -0.572495 |
| NZDUSD-EURGBP | 7183 | 0.037186 | 0.00162054 | 0.014072 | 0.060261 |
| USDJPY-USDCHF | 7185 | 0.399461 | 1.66405e-273 | 0.379846 | 0.418716 |
| USDJPY-USDCAD | 7186 | 0.027603 | 0.0192861 | 0.004484 | 0.050692 |
| USDJPY-EURGBP | 7181 | -0.127992 | 1.29933e-27 | -0.150676 | -0.105174 |
| USDCHF-USDCAD | 7188 | 0.304665 | 3.02232e-154 | 0.283544 | 0.325491 |
| USDCHF-EURGBP | 7182 | -0.325886 | 2.5686e-177 | -0.346404 | -0.305058 |
| USDCAD-EURGBP | 7185 | -0.014622 | 0.215247 | -0.037732 | 0.008504 |

This NOTES.md is the index only. It is not a 29th analysis.
