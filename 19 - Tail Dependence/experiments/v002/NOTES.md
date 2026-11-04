# Tail dependence experiments v002

Done: each pair has L_hat, a Gaussian co-exceedance benchmark at the same Pearson r, and excess = L_hat - benchmark, for both tails.

## Research question

For each unordered pair, how does the empirical tail frequency at alpha=0.05 compare with the co-exceedance a Gaussian with the same Pearson r would give?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Same uniforms as v001: rank/(n+1), alpha=0.05, both conditioning directions.
- Gaussian benchmark = bivariate-normal CDF at Phi^{-1}(alpha), divided by alpha.
- Upper and lower Gaussian benchmarks are equal by symmetry. Excess uses that one number.
- v001 L_hat was recomputed as a check and v001 files were not edited.

## Index

| pair | n | pearson_r | L_lower_cond_R | gauss_benchmark | excess_lower_cond_R | L_upper_cond_R | excess_upper_cond_R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EURUSD-GBPUSD | 7202 | 0.641738 | 0.325 | 0.342399 | -0.0173987 | 0.394444 | 0.0520457 |
| EURUSD-AUDUSD | 7201 | 0.556324 | 0.330556 | 0.279757 | 0.0507985 | 0.363889 | 0.0841318 |
| EURUSD-NZDUSD | 7186 | 0.549808 | 0.306407 | 0.275397 | 0.0310101 | 0.331476 | 0.0560797 |
| EURUSD-USDJPY | 7200 | -0.300952 | 0.0638889 | 0.00910664 | 0.0547822 | 0.0472222 | 0.0381156 |
| EURUSD-USDCHF | 7186 | -0.749204 | 0.00278552 | 2.03301e-06 | 0.00278348 | 0 | -2.03301e-06 |
| EURUSD-USDCAD | 7188 | -0.456626 | 0.00835655 | 0.00207911 | 0.00627743 | 0.0111421 | 0.00906295 |
| EURUSD-EURGBP | 7183 | 0.439899 | 0.373259 | 0.209368 | 0.163891 | 0.278552 | 0.0691837 |
| GBPUSD-AUDUSD | 7228 | 0.539048 | 0.32964 | 0.268314 | 0.0613263 | 0.33795 | 0.0696365 |
| GBPUSD-NZDUSD | 7203 | 0.530079 | 0.313889 | 0.26252 | 0.0513694 | 0.311111 | 0.0485916 |
| GBPUSD-USDJPY | 7200 | -0.198556 | 0.0805556 | 0.018283 | 0.0622725 | 0.0666667 | 0.0483836 |
| GBPUSD-USDCHF | 7201 | -0.486083 | 0.00277778 | 0.00144131 | 0.00133646 | 0.0138889 | 0.0124476 |
| GBPUSD-USDCAD | 7205 | -0.456462 | 0.0138889 | 0.00208313 | 0.0118058 | 0.0166667 | 0.0145835 |
| GBPUSD-EURGBP | 7199 | -0.397845 | 0.0333333 | 0.00392593 | 0.0294074 | 0.0361111 | 0.0321852 |
| AUDUSD-NZDUSD | 7202 | 0.828722 | 0.583333 | 0.53063 | 0.052703 | 0.602778 | 0.0721475 |
| AUDUSD-USDJPY | 7199 | -0.0881506 | 0.169444 | 0.0334123 | 0.136032 | 0.0972222 | 0.0638099 |
| AUDUSD-USDCHF | 7200 | -0.380878 | 0.0361111 | 0.00462424 | 0.0314869 | 0.0333333 | 0.0287091 |
| AUDUSD-USDCAD | 7204 | -0.647362 | 0 | 7.51667e-05 | -7.51667e-05 | 0.00555556 | 0.00548039 |
| AUDUSD-EURGBP | 7198 | 0.0381733 | 0.142061 | 0.0585461 | 0.0835152 | 0.111421 | 0.0528745 |
| NZDUSD-USDJPY | 7185 | -0.133568 | 0.142061 | 0.0264714 | 0.11559 | 0.097493 | 0.0710216 |
| NZDUSD-USDCHF | 7185 | -0.3936 | 0.0306407 | 0.00409315 | 0.0265475 | 0.0389972 | 0.0349041 |
| NZDUSD-USDCAD | 7190 | -0.587831 | 0.00835655 | 0.000285379 | 0.00807117 | 0.00557103 | 0.00528565 |
| NZDUSD-EURGBP | 7183 | 0.0371864 | 0.139276 | 0.0583143 | 0.0809615 | 0.119777 | 0.0614629 |
| USDJPY-USDCHF | 7185 | 0.399461 | 0.267409 | 0.188274 | 0.0791353 | 0.228412 | 0.0401381 |
| USDJPY-USDCAD | 7186 | 0.027603 | 0.108635 | 0.0560937 | 0.0525414 | 0.0947075 | 0.0386138 |
| USDJPY-EURGBP | 7181 | -0.127992 | 0.0668524 | 0.0272678 | 0.0395846 | 0.0584958 | 0.031228 |
| USDCHF-USDCAD | 7188 | 0.304665 | 0.208914 | 0.144644 | 0.0642698 | 0.214485 | 0.0698409 |
| USDCHF-EURGBP | 7182 | -0.325886 | 0.0167131 | 0.00748158 | 0.00923151 | 0.0194986 | 0.012017 |
| USDCAD-EURGBP | 7185 | -0.0146219 | 0.0529248 | 0.0469506 | 0.00597423 | 0.144847 | 0.0978962 |

## Cross-pair conclusion

AUDUSD-NZDUSD lower L_hat is 0.5833 against a Gaussian benchmark of 0.5306 (excess 0.0527) at r=0.8287.
Independence (benchmark = alpha = 0.05) is the wrong yardstick when r is not zero.
This is not a trading signal.

Check: v001 excess for AUDUSD-NZDUSD is 0.052703; recomputed excess is 0.052703.
