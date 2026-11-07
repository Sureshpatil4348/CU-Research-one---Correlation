# Seven USD majors — partial correlation vs pace

## Research question

For the 21 unordered pairs among EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, and USDCAD (EURGBP excluded), how does full-sample partial correlation after a leave-currency-out USD factor compare with rolling Pearson, and does the residual series respect the pace of raw rolling correlation on windows 20 / 60 / 100?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Snapshot name: 2026-11-03_majors_alpari_D1
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- EURGBP is not a studied leg and never enters the USD factor
- Control z: equal-weight mean of USD-strength returns from the seven majors that do not share a non-USD currency with either leg; USD-strength is -log return for EURUSD/GBPUSD/AUDUSD/NZDUSD and +log return for USDJPY/USDCHF/USDCAD
- Full-sample: OLS residuals of each leg on z (with intercept), then Pearson rho_partial; same-sample raw Pearson r as side check
- Rolling: for W in {20, 60, 100}, raw rolling Pearson r_xy and in-window partial `(r_xy - r_xz r_yz) / sqrt((1-r_xz^2)(1-r_yz^2))`
- Pace metrics per window: path agreement (corr of raw vs partial paths), pace agreement (corr of first differences), sign agreement, mean gap and mean absolute gap
- Headline window for the conclusion: W=60
- Named dig only. Does not change experiments/v001.

## Index (headline W=60)

| pair | n | rho_partial | pearson_r | gap | path_60 | pace_60 | sign_60 | mean_abs_gap_60 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7148 | 0.3441 | 0.6420 | -0.2978 | 0.5576 | 0.6576 | 0.9561 | 0.2873 |
| EURUSD-AUDUSD | 7148 | -0.0159 | 0.5572 | -0.5731 | 0.5620 | 0.5477 | 0.3977 | 0.6116 |
| EURUSD-NZDUSD | 7148 | -0.0359 | 0.5510 | -0.5869 | 0.5040 | 0.5504 | 0.3875 | 0.5948 |
| EURUSD-USDJPY | 7148 | -0.2147 | -0.3004 | 0.0857 | 0.3734 | 0.5858 | 0.7867 | 0.2693 |
| EURUSD-USDCHF | 7148 | -0.6198 | -0.7481 | 0.1283 | 0.8959 | 0.8608 | 0.9989 | 0.1161 |
| EURUSD-USDCAD | 7148 | -0.0223 | -0.4571 | 0.4347 | 0.6563 | 0.6137 | 0.5645 | 0.4153 |
| GBPUSD-AUDUSD | 7148 | 0.1567 | 0.5407 | -0.3840 | 0.6271 | 0.6416 | 0.6698 | 0.4282 |
| GBPUSD-NZDUSD | 7148 | 0.1368 | 0.5323 | -0.3954 | 0.6969 | 0.6380 | 0.6997 | 0.4036 |
| GBPUSD-USDJPY | 7148 | -0.0561 | -0.1966 | 0.1405 | 0.5697 | 0.7081 | 0.6930 | 0.2517 |
| GBPUSD-USDCHF | 7148 | -0.1658 | -0.4847 | 0.3189 | 0.6853 | 0.6963 | 0.8458 | 0.3150 |
| GBPUSD-USDCAD | 7148 | -0.1457 | -0.4567 | 0.3110 | 0.6641 | 0.6961 | 0.7373 | 0.3210 |
| AUDUSD-NZDUSD | 7148 | 0.7351 | 0.8287 | -0.0936 | 0.7639 | 0.7508 | 1.0000 | 0.1176 |
| AUDUSD-USDJPY | 7148 | 0.1981 | -0.0867 | 0.2848 | 0.7451 | 0.6606 | 0.6042 | 0.3166 |
| AUDUSD-USDCHF | 7148 | 0.2191 | -0.3803 | 0.5994 | 0.5977 | 0.5680 | 0.1608 | 0.6628 |
| AUDUSD-USDCAD | 7148 | -0.4848 | -0.6479 | 0.1631 | 0.7290 | 0.7110 | 0.9874 | 0.1862 |
| NZDUSD-USDJPY | 7148 | 0.0930 | -0.1339 | 0.2269 | 0.7152 | 0.6699 | 0.6576 | 0.2863 |
| NZDUSD-USDCHF | 7148 | 0.1737 | -0.3935 | 0.5672 | 0.5716 | 0.5813 | 0.1868 | 0.6158 |
| NZDUSD-USDCAD | 7148 | -0.3718 | -0.5883 | 0.2166 | 0.6204 | 0.6939 | 0.9361 | 0.2413 |
| USDJPY-USDCHF | 7148 | 0.3659 | 0.3985 | -0.0325 | 0.5669 | 0.6830 | 0.9189 | 0.1887 |
| USDJPY-USDCAD | 7148 | -0.1827 | 0.0262 | -0.2090 | 0.6992 | 0.7019 | 0.5850 | 0.2706 |
| USDCHF-USDCAD | 7148 | -0.1190 | 0.3042 | -0.4232 | 0.7226 | 0.6627 | 0.4226 | 0.4166 |

## Cross-pair reading

Reading of the 21-pair index only. Not a 22nd pair analysis and not a trading signal.

Removing the USD factor changes more than the level. On W=60, path and pace agreement with raw rolling Pearson are often weak, so the residual tempo can diverge from the raw correlation path.

Mean W=60 path agreement: 0.6440. Mean W=60 pace agreement: 0.6609. Median |full-sample gap|: 0.2978. Pairs with pace agreement ≥ 0.85: 1. Pairs with pace agreement < 0.70: 16.
Highest W=60 pace agreement: EURUSD-USDCHF (0.8608).
Lowest W=60 pace agreement: EURUSD-AUDUSD (0.5477).
Largest |rho_partial minus Pearson r| gaps: AUDUSD-USDCHF (gap=0.5994, rho_partial=0.2191, r=-0.3803); EURUSD-NZDUSD (gap=-0.5869, rho_partial=-0.0359, r=0.5510); EURUSD-AUDUSD (gap=-0.5731, rho_partial=-0.0159, r=0.5572).

Page: [index.html](index.html).

This folder is a named dig into the seven USD majors. It is not a new experiment version and does not change v001.
