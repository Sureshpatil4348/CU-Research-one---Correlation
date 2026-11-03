# Copulas experiments v001

## Research question

For each unordered pair among the eight majors, what Gaussian copula rho and Clayton theta describe the empirical-rank dependence of matched daily log returns of close on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Margins: empirical ranks / (n+1)
- Families: Gaussian rho (normal-score correlation) and Clayton theta (MLE); Kendall tau from each; Spearman of (u,v); Pearson r on returns as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/`

## Index

| pair | n | gauss_rho | gauss_kendall | clayton_theta | clayton_kendall | spearman_uv | pearson_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.655256 | 0.454878 | 1.083145 | 0.351312 | 0.642659 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 0.565780 | 0.382849 | 0.865394 | 0.302016 | 0.546799 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 0.548447 | 0.369562 | 0.816675 | 0.289943 | 0.527857 | 0.549808 |
| EURUSD-USDJPY | 7200 | -0.336081 | -0.218203 | 0.000000 | 0.000000 | -0.351179 | -0.300952 |
| EURUSD-USDCHF | 7186 | -0.828593 | -0.621717 | 0.000000 | 0.000000 | -0.823916 | -0.749204 |
| EURUSD-USDCAD | 7188 | -0.448379 | -0.295997 | 0.000000 | 0.000000 | -0.421892 | -0.456626 |
| EURUSD-EURGBP | 7183 | 0.452423 | 0.298880 | 0.691847 | 0.257016 | 0.430454 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 0.538374 | 0.361923 | 0.822780 | 0.291479 | 0.515913 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 0.523542 | 0.350779 | 0.781121 | 0.280866 | 0.500616 | 0.530079 |
| GBPUSD-USDJPY | 7200 | -0.253160 | -0.162940 | 0.000000 | 0.000000 | -0.273964 | -0.198556 |
| GBPUSD-USDCHF | 7201 | -0.553528 | -0.373438 | 0.000000 | 0.000000 | -0.551519 | -0.486083 |
| GBPUSD-USDCAD | 7205 | -0.439996 | -0.290041 | 0.000000 | 0.000000 | -0.404480 | -0.456462 |
| GBPUSD-EURGBP | 7199 | -0.352016 | -0.229007 | 0.000000 | 0.000000 | -0.317786 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 0.825470 | 0.618180 | 2.216754 | 0.525701 | 0.805371 | 0.828722 |
| AUDUSD-USDJPY | 7199 | -0.177324 | -0.113488 | 0.000000 | 0.000000 | -0.214343 | -0.088151 |
| AUDUSD-USDCHF | 7200 | -0.442400 | -0.291745 | 0.000000 | 0.000000 | -0.442076 | -0.380878 |
| AUDUSD-USDCAD | 7204 | -0.630420 | -0.434235 | 0.000000 | 0.000000 | -0.596232 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 0.063018 | 0.040145 | 0.088313 | 0.042289 | 0.064436 | 0.038173 |
| NZDUSD-USDJPY | 7185 | -0.191865 | -0.122907 | 0.000000 | 0.000000 | -0.223115 | -0.133568 |
| NZDUSD-USDCHF | 7185 | -0.434649 | -0.286255 | 0.000000 | 0.000000 | -0.433752 | -0.393600 |
| NZDUSD-USDCAD | 7190 | -0.569020 | -0.385355 | 0.000000 | 0.000000 | -0.535570 | -0.587831 |
| NZDUSD-EURGBP | 7183 | 0.056071 | 0.035715 | 0.081222 | 0.039026 | 0.055201 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.443657 | 0.292638 | 0.668974 | 0.250648 | 0.443335 | 0.399461 |
| USDJPY-USDCAD | 7186 | 0.073263 | 0.046682 | 0.101128 | 0.048130 | 0.100814 | 0.027603 |
| USDJPY-EURGBP | 7181 | -0.118291 | -0.075483 | 0.000000 | 0.000000 | -0.109100 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.336842 | 0.218717 | 0.443956 | 0.181655 | 0.329543 | 0.304665 |
| USDCHF-EURGBP | 7182 | -0.369763 | -0.241122 | 0.000000 | 0.000000 | -0.347712 | -0.325886 |
| USDCAD-EURGBP | 7185 | -0.035833 | -0.022817 | 0.000000 | 0.000000 | -0.045060 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest Gaussian rho: AUDUSD-NZDUSD (rho=0.8255).
Weakest Gaussian rho: EURUSD-USDCHF (rho=-0.8286).
Largest Clayton theta (lower-tail screen): AUDUSD-NZDUSD (theta=2.2168).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
