# Spearman experiments v001

## Research question

For each unordered pair among the eight majors, what is the Spearman rank correlation of matched daily log returns of close on the Alpari D1 history that the broker actually provided?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Statistic: Spearman rho via `scipy.stats.spearmanr`, two-sided p, approximate 95% Fisher interval on rho, same-sample Pearson r and rho minus r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 CSVs, charts under `outputs/figures/` (closes, returns, log-return scatter, rank-rank scatter)

## Index

| pair | n | rho | p | ci_low | ci_high | pearson_r | rho_minus_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.642659 | 0 | 0.628898 | 0.656018 | 0.641738 | 0.000921 |
| EURUSD-AUDUSD | 7201 | 0.546799 | 0 | 0.530400 | 0.562789 | 0.556324 | -0.009525 |
| EURUSD-NZDUSD | 7186 | 0.527857 | 0 | 0.510972 | 0.544335 | 0.549808 | -0.021951 |
| EURUSD-USDJPY | 7200 | -0.351179 | 5.02282e-208 | -0.371266 | -0.330763 | -0.300952 | -0.050226 |
| EURUSD-USDCHF | 7186 | -0.823916 | 0 | -0.831203 | -0.816346 | -0.749204 | -0.074713 |
| EURUSD-USDCAD | 7188 | -0.421892 | 3.13545e-308 | -0.440712 | -0.402701 | -0.456626 | 0.034734 |
| EURUSD-EURGBP | 7183 | 0.430454 | 0 | 0.411423 | 0.449110 | 0.439899 | -0.009445 |
| GBPUSD-AUDUSD | 7228 | 0.515913 | 0 | 0.498791 | 0.532632 | 0.539048 | -0.023135 |
| GBPUSD-NZDUSD | 7203 | 0.500616 | 0 | 0.483107 | 0.517724 | 0.530079 | -0.029463 |
| GBPUSD-USDJPY | 7200 | -0.273964 | 3.83282e-124 | -0.295195 | -0.252463 | -0.198556 | -0.075409 |
| GBPUSD-USDCHF | 7201 | -0.551519 | 0 | -0.567389 | -0.535240 | -0.486083 | -0.065437 |
| GBPUSD-USDCAD | 7205 | -0.404480 | 8.55993e-282 | -0.423615 | -0.384985 | -0.456462 | 0.051982 |
| GBPUSD-EURGBP | 7199 | -0.317786 | 1.24764e-168 | -0.338402 | -0.296864 | -0.397845 | 0.080059 |
| AUDUSD-NZDUSD | 7202 | 0.805371 | 0 | 0.797102 | 0.813338 | 0.828722 | -0.023351 |
| AUDUSD-USDJPY | 7199 | -0.214343 | 1.37813e-75 | -0.236274 | -0.192194 | -0.088151 | -0.126192 |
| AUDUSD-USDCHF | 7200 | -0.442076 | 0 | -0.460473 | -0.423299 | -0.380878 | -0.061197 |
| AUDUSD-USDCAD | 7204 | -0.596232 | 0 | -0.610913 | -0.581141 | -0.647362 | 0.051130 |
| AUDUSD-EURGBP | 7198 | 0.064436 | 4.46132e-08 | 0.041395 | 0.087408 | 0.038173 | 0.026263 |
| NZDUSD-USDJPY | 7185 | -0.223115 | 9.52214e-82 | -0.244975 | -0.201029 | -0.133568 | -0.089547 |
| NZDUSD-USDCHF | 7185 | -0.433752 | 0 | -0.452339 | -0.414789 | -0.393600 | -0.040153 |
| NZDUSD-USDCAD | 7190 | -0.535570 | 0 | -0.551853 | -0.518878 | -0.587831 | 0.052261 |
| NZDUSD-EURGBP | 7183 | 0.055201 | 2.85211e-06 | 0.032116 | 0.078228 | 0.037186 | 0.018015 |
| USDJPY-USDCHF | 7185 | 0.443335 | 0 | 0.424564 | 0.461725 | 0.399461 | 0.043874 |
| USDJPY-USDCAD | 7186 | 0.100814 | 1.06775e-17 | 0.077874 | 0.123648 | 0.027603 | 0.073211 |
| USDJPY-EURGBP | 7181 | -0.109100 | 1.83838e-20 | -0.131897 | -0.086188 | -0.127992 | 0.018892 |
| USDCHF-USDCAD | 7188 | 0.329543 | 1.17217e-181 | 0.308777 | 0.349995 | 0.304665 | 0.024878 |
| USDCHF-EURGBP | 7182 | -0.347712 | 3.33824e-203 | -0.367881 | -0.327215 | -0.325886 | -0.021825 |
| USDCAD-EURGBP | 7185 | -0.045060 | 0.000133062 | -0.068112 | -0.021959 | -0.014622 | -0.030438 |

## Cross-pair conclusion

Reading of the 28-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest positive rank link: AUDUSD-NZDUSD (rho=0.8054, n=7202).
Strongest negative rank link: EURUSD-USDCHF (rho=-0.8239, n=7186).
Nearest-to-zero rank links: USDCAD-EURGBP (rho=-0.0451); NZDUSD-EURGBP (rho=0.0552); AUDUSD-EURGBP (rho=0.0644).
Largest |rho minus Pearson r| gaps on the same sample: AUDUSD-USDJPY (gap=-0.1262, rho=-0.2143, r=-0.0882); NZDUSD-USDJPY (gap=-0.0895, rho=-0.2231, r=-0.1336); GBPUSD-EURGBP (gap=0.0801, rho=-0.3178, r=-0.3978). A large gap can flag outliers or a non-straight link; inspect that pair's charts before treating either score as settled.

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
