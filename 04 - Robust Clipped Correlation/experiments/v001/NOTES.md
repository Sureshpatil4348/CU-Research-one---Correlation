# Robust clipped correlation experiments v001

## Research question

For each unordered pair among the eight majors, what is the robust clipped correlation of matched daily log returns of close on the Alpari D1 history that the broker actually provided, after capping each return at ±0.01, ±0.02, and ±0.03?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Statistic: clip each leg at c in {0.01, 0.02, 0.03}, then Pearson rho_clip via `scipy.stats.pearsonr` on the clipped series; same-row raw Pearson r for comparison; two-sided p and approximate 95% Fisher interval on clipped values; cap-hit counts (|log return| > c) per leg
- Headline: rho_clip at c = 0.02
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/` (closes, returns with ±0.02 lines, scatter with ±0.02 clip box)

## Index

| pair | n | r | rho_01 | rho_02 | rho_03 | left_cap_hits_02 | right_cap_hits_02 | rho_02_minus_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.641738 | 0.649871 | 0.648213 | 0.646146 | 41 | 39 | 0.006475 |
| EURUSD-AUDUSD | 7201 | 0.556324 | 0.550664 | 0.563344 | 0.564695 | 41 | 130 | 0.007020 |
| EURUSD-NZDUSD | 7186 | 0.549808 | 0.532662 | 0.545902 | 0.547747 | 41 | 141 | -0.003906 |
| EURUSD-USDJPY | 7200 | -0.300952 | -0.345032 | -0.323102 | -0.308641 | 41 | 75 | -0.022150 |
| EURUSD-USDCHF | 7186 | -0.749204 | -0.829673 | -0.826478 | -0.819077 | 41 | 47 | -0.077274 |
| EURUSD-USDCAD | 7188 | -0.456626 | -0.440091 | -0.453994 | -0.456864 | 41 | 32 | 0.002631 |
| EURUSD-EURGBP | 7183 | 0.439899 | 0.447399 | 0.453903 | 0.447590 | 41 | 18 | 0.014004 |
| GBPUSD-AUDUSD | 7228 | 0.539048 | 0.522500 | 0.538100 | 0.546212 | 40 | 130 | -0.000948 |
| GBPUSD-NZDUSD | 7203 | 0.530079 | 0.505853 | 0.522090 | 0.528934 | 39 | 142 | -0.007989 |
| GBPUSD-USDJPY | 7200 | -0.198556 | -0.262618 | -0.235694 | -0.218333 | 39 | 75 | -0.037139 |
| GBPUSD-USDCHF | 7201 | -0.486083 | -0.552949 | -0.544369 | -0.533800 | 39 | 47 | -0.058287 |
| GBPUSD-USDCAD | 7205 | -0.456462 | -0.431983 | -0.451155 | -0.457010 | 39 | 32 | 0.005308 |
| GBPUSD-EURGBP | 7199 | -0.397845 | -0.339619 | -0.369638 | -0.381804 | 39 | 18 | 0.028207 |
| AUDUSD-NZDUSD | 7202 | 0.828722 | 0.809347 | 0.825658 | 0.830734 | 129 | 142 | -0.003064 |
| AUDUSD-USDJPY | 7199 | -0.088151 | -0.202027 | -0.157789 | -0.130359 | 130 | 75 | -0.069638 |
| AUDUSD-USDCHF | 7200 | -0.380878 | -0.441773 | -0.434357 | -0.424177 | 130 | 47 | -0.053479 |
| AUDUSD-USDCAD | 7204 | -0.647362 | -0.610841 | -0.637235 | -0.647645 | 130 | 32 | 0.010126 |
| AUDUSD-EURGBP | 7198 | 0.038173 | 0.070824 | 0.058939 | 0.046226 | 130 | 18 | 0.020766 |
| NZDUSD-USDJPY | 7185 | -0.133568 | -0.216451 | -0.179453 | -0.155636 | 141 | 75 | -0.045884 |
| NZDUSD-USDCHF | 7185 | -0.393600 | -0.433664 | -0.428478 | -0.419679 | 141 | 47 | -0.034879 |
| NZDUSD-USDCAD | 7190 | -0.587831 | -0.544739 | -0.574013 | -0.584980 | 142 | 32 | 0.013819 |
| NZDUSD-EURGBP | 7183 | 0.037186 | 0.062564 | 0.056179 | 0.045356 | 142 | 18 | 0.018992 |
| USDJPY-USDCHF | 7185 | 0.399461 | 0.445619 | 0.435982 | 0.427938 | 75 | 47 | 0.036522 |
| USDJPY-USDCAD | 7186 | 0.027603 | 0.084508 | 0.049002 | 0.032808 | 75 | 32 | 0.021399 |
| USDJPY-EURGBP | 7181 | -0.127992 | -0.113476 | -0.120719 | -0.123950 | 75 | 18 | 0.007273 |
| USDCHF-USDCAD | 7188 | 0.304665 | 0.337332 | 0.330741 | 0.329220 | 47 | 32 | 0.026076 |
| USDCHF-EURGBP | 7182 | -0.325886 | -0.368458 | -0.371226 | -0.365015 | 47 | 18 | -0.045339 |
| USDCAD-EURGBP | 7185 | -0.014622 | -0.038084 | -0.026659 | -0.019265 | 32 | 17 | -0.012037 |

## Cross-pair conclusion

Reading of the 28-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest positive clipped link at c=0.02: AUDUSD-NZDUSD (rho_clip=0.8257, n=7202).
Strongest negative clipped link at c=0.02: EURUSD-USDCHF (rho_clip=-0.8265, n=7186).
Nearest-to-zero clipped links at c=0.02: USDCAD-EURGBP (rho_clip=-0.0267); USDJPY-USDCAD (rho_clip=0.0490); NZDUSD-EURGBP (rho_clip=0.0562).
Largest |rho_clip minus Pearson r| gaps at c=0.02 on the same sample: EURUSD-USDCHF (gap=-0.0773, rho_clip=-0.8265, r=-0.7492); AUDUSD-USDJPY (gap=-0.0696, rho_clip=-0.1578, r=-0.0882); GBPUSD-USDCHF (gap=-0.0583, rho_clip=-0.5444, r=-0.4861). A large gap can flag outlier or crisis days that clipping caps; inspect that pair's cap hits and charts before treating either score as settled.

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
