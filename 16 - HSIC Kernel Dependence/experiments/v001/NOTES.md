# HSIC kernel dependence experiments v001

## Research question

For each unordered pair among the eight majors, what is the normalized HSIC of matched daily log returns of close under a fixed z-score + median-heuristic RBF rule on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Preprocessing: z-score each leg on the matched sample
- Bandwidth: median pairwise |z_i-z_j| per leg (subsample at most 2000 stratified points for the median only); full-sample RBF HSIC = tr(KHLH)/n^2
- Statistic: raw HSIC, normalized HSIC = HSIC_xy / sqrt(HSIC_xx * HSIC_yy) as headline; Pearson r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/` (closes, returns, scatter)

## Index

| pair | n | ell_x | ell_y | hsic | n_hsic | pearson_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.885067 | 0.850875 | 0.01881318 | 0.276691 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 0.869133 | 0.804408 | 0.01340966 | 0.195585 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 0.864740 | 0.866386 | 0.01228972 | 0.178270 | 0.549808 |
| EURUSD-USDJPY | 7200 | 0.884600 | 0.833509 | 0.00601546 | 0.090444 | -0.300952 |
| EURUSD-USDCHF | 7186 | 0.869853 | 0.810778 | 0.03868780 | 0.574721 | -0.749204 |
| EURUSD-USDCAD | 7188 | 0.859468 | 0.846686 | 0.00707716 | 0.104586 | -0.456626 |
| EURUSD-EURGBP | 7183 | 0.861514 | 0.823416 | 0.00794233 | 0.115365 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 0.846773 | 0.811143 | 0.01154221 | 0.166983 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 0.844037 | 0.858117 | 0.01101636 | 0.157257 | 0.530079 |
| GBPUSD-USDJPY | 7200 | 0.850458 | 0.839399 | 0.00405751 | 0.060052 | -0.198556 |
| GBPUSD-USDCHF | 7201 | 0.866250 | 0.805110 | 0.01380949 | 0.204121 | -0.486083 |
| GBPUSD-USDCAD | 7205 | 0.838018 | 0.826580 | 0.00617800 | 0.089082 | -0.456462 |
| GBPUSD-EURGBP | 7199 | 0.837298 | 0.834469 | 0.00475614 | 0.068560 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 0.804894 | 0.850081 | 0.03542786 | 0.505642 | 0.828722 |
| AUDUSD-USDJPY | 7199 | 0.830831 | 0.848847 | 0.00340105 | 0.051560 | -0.088151 |
| AUDUSD-USDCHF | 7200 | 0.813103 | 0.796119 | 0.00898430 | 0.131683 | -0.380878 |
| AUDUSD-USDCAD | 7204 | 0.819141 | 0.832945 | 0.01534121 | 0.226168 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 0.816085 | 0.819647 | 0.00059063 | 0.008581 | 0.038173 |
| NZDUSD-USDJPY | 7185 | 0.880463 | 0.820501 | 0.00343588 | 0.050625 | -0.133568 |
| NZDUSD-USDCHF | 7185 | 0.880253 | 0.794673 | 0.00861939 | 0.126207 | -0.393600 |
| NZDUSD-USDCAD | 7190 | 0.845631 | 0.819330 | 0.01215573 | 0.173528 | -0.587831 |
| NZDUSD-EURGBP | 7183 | 0.846324 | 0.825563 | 0.00049861 | 0.007115 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.822839 | 0.806989 | 0.00885462 | 0.131945 | 0.399461 |
| USDJPY-USDCAD | 7186 | 0.832608 | 0.826548 | 0.00100621 | 0.014945 | 0.027603 |
| USDJPY-EURGBP | 7181 | 0.841580 | 0.849460 | 0.00055640 | 0.008388 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.802669 | 0.846991 | 0.00474175 | 0.070735 | 0.304665 |
| USDCHF-EURGBP | 7182 | 0.810233 | 0.851191 | 0.00467533 | 0.069925 | -0.325886 |
| USDCAD-EURGBP | 7185 | 0.839305 | 0.850896 | 0.00045402 | 0.006766 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index using normalized HSIC under the fixed z-score + median-heuristic RBF rule. Not a 29th pair analysis and not a trading signal.

Strongest normalized HSIC: EURUSD-USDCHF (n_hsic=0.574721, hsic=0.03868780, n=7186).
Nearest-to-zero normalized HSIC: USDCAD-EURGBP (n_hsic=0.006766); NZDUSD-EURGBP (n_hsic=0.007115); USDJPY-EURGBP (n_hsic=0.008388).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
