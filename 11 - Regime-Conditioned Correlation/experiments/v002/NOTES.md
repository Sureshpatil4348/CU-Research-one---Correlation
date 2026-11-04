# Regime-conditioned correlation experiments v002

Done: quiet/stress table reports Forbes-Rigobon adjusted gaps and a 95% circular block-bootstrap interval for the raw gap (8 of 28 intervals exclude 0).

## Research question

After a Forbes-Rigobon volatility adjustment, which stress-minus-quiet correlation gaps remain large, and which raw gaps does a block bootstrap reject?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Same look-ahead-free turbulence rule as v001: RV is the prior 20 turb days; stress when RV exceeds the 75th percentile of the prior 252 RV values.
- delta is the average of the two legs' (stress variance / quiet variance - 1).
- rho_stress_adj = rho_stress / sqrt(1 + delta * (1 - rho_stress^2)).
- Circular block bootstrap of the raw stress-minus-quiet gap, block=20, draws=500, seed=20261103. Interval is the 2.5 and 97.5 percentiles.
- v001 files were not edited.

## Index

| pair | n_quiet | n_stress | rho_quiet | rho_stress | rho_stress_adj | adj_gap | boot_low | boot_high | raw_gap_excludes_0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EURUSD-GBPUSD | 5092 | 1763 | 0.64087 | 0.651318 | 0.530969 | -0.109901 | -0.0381014 | 0.062201 | False |
| EURUSD-AUDUSD | 5092 | 1763 | 0.575739 | 0.579549 | 0.429902 | -0.145837 | -0.0464694 | 0.0583032 | False |
| EURUSD-NZDUSD | 5092 | 1763 | 0.548709 | 0.591777 | 0.471257 | -0.0774515 | -0.0127437 | 0.0974743 | False |
| EURUSD-USDJPY | 5092 | 1763 | -0.340338 | -0.247157 | -0.188222 | 0.152115 | -0.0555461 | 0.253964 | False |
| EURUSD-USDCHF | 5092 | 1763 | -0.72712 | -0.759347 | -0.671533 | 0.0555861 | -0.20255 | 0.12402 | False |
| EURUSD-USDCAD | 5092 | 1763 | -0.449594 | -0.516888 | -0.400759 | 0.0488351 | -0.137643 | 0.00803487 | False |
| EURUSD-EURGBP | 5092 | 1763 | 0.450304 | 0.39591 | 0.306214 | -0.144091 | -0.156716 | 0.0504631 | False |
| GBPUSD-AUDUSD | 5092 | 1763 | 0.530122 | 0.578127 | 0.420847 | -0.109276 | -0.0169767 | 0.103954 | False |
| GBPUSD-NZDUSD | 5092 | 1763 | 0.513547 | 0.582783 | 0.453223 | -0.0603233 | 0.00365165 | 0.127613 | True |
| GBPUSD-USDJPY | 5092 | 1763 | -0.255955 | -0.110157 | -0.0807163 | 0.175239 | -0.0331389 | 0.325456 | False |
| GBPUSD-USDCHF | 5092 | 1763 | -0.492237 | -0.465397 | -0.368476 | 0.123761 | -0.0873511 | 0.138593 | False |
| GBPUSD-USDCAD | 5092 | 1763 | -0.427452 | -0.526008 | -0.400092 | 0.0273601 | -0.165565 | -0.0436682 | True |
| GBPUSD-EURGBP | 5092 | 1763 | -0.389011 | -0.433512 | -0.329649 | 0.0593617 | -0.157475 | 0.0656789 | False |
| AUDUSD-NZDUSD | 5092 | 1763 | 0.814867 | 0.857862 | 0.737009 | -0.0778575 | 0.0172534 | 0.0663242 | True |
| AUDUSD-USDJPY | 5092 | 1763 | -0.200695 | 0.0659973 | 0.0442747 | 0.24497 | 0.0351123 | 0.461237 | True |
| AUDUSD-USDCHF | 5092 | 1763 | -0.425576 | -0.352667 | -0.250917 | 0.17466 | -0.0367488 | 0.15952 | False |
| AUDUSD-USDCAD | 5092 | 1763 | -0.621582 | -0.693467 | -0.530822 | 0.0907598 | -0.128018 | -0.0202812 | True |
| AUDUSD-EURGBP | 5092 | 1763 | 0.0747761 | -0.00634604 | -0.00422846 | -0.0790046 | -0.171919 | 0.00665102 | False |
| NZDUSD-USDJPY | 5092 | 1763 | -0.215365 | -0.0102839 | -0.00749179 | 0.207873 | 0.00298228 | 0.413899 | True |
| NZDUSD-USDCHF | 5092 | 1763 | -0.419655 | -0.378647 | -0.29384 | 0.125815 | -0.0473719 | 0.141392 | False |
| NZDUSD-USDCAD | 5092 | 1763 | -0.552641 | -0.653986 | -0.519817 | 0.0328243 | -0.155725 | -0.0358396 | True |
| NZDUSD-EURGBP | 5092 | 1763 | 0.0571839 | 0.00194344 | 0.00140642 | -0.0557774 | -0.1365 | 0.0298505 | False |
| USDJPY-USDCHF | 5092 | 1763 | 0.413068 | 0.401194 | 0.322319 | -0.0907486 | -0.109836 | 0.076341 | False |
| USDJPY-USDCAD | 5092 | 1763 | 0.0938364 | -0.0694801 | -0.0504374 | -0.144274 | -0.303705 | -0.0100009 | True |
| USDJPY-EURGBP | 5092 | 1763 | -0.112123 | -0.160373 | -0.120453 | -0.00832973 | -0.131573 | 0.034701 | False |
| USDCHF-USDCAD | 5092 | 1763 | 0.320579 | 0.318276 | 0.243476 | -0.077103 | -0.0881849 | 0.075805 | False |
| USDCHF-EURGBP | 5092 | 1763 | -0.2981 | -0.338639 | -0.267565 | 0.0305343 | -0.15937 | 0.0846212 | False |
| USDCAD-EURGBP | 5092 | 1763 | -0.0428878 | 0.0173293 | 0.0124842 | 0.055372 | -0.0327681 | 0.1434 | False |

## Cross-pair conclusion

AUDUSD-USDJPY raw gap is 0.2667; adjusted gap is 0.2450; bootstrap interval [0.0351, 0.4612].
Raw-gap intervals that exclude 0: 8 of 28.
A larger raw stress correlation can be a volatility effect. The adjusted gap is the bias check.
This is not a trading signal.
