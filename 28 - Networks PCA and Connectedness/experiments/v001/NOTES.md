# Networks, PCA, and connectedness experiments v001

## Research question

On the eight-major Alpari D1 log-return panel, what are the network distances d_ij, PCA eigenvalues of the correlation matrix, and Diebold-Yilmaz TCI from a BIC-selected VAR with GFEVD horizon H=10?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Panel: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD, EURGBP; n_obs=7127
- Network: d_ij = sqrt(2*(1-rho_ij)) from full-sample Pearson R
- PCA: eigenvalues of R (descending)
- VAR: demeaned returns; lag = BIC among 1..10 (selected p=1); GFEVD H=10
- System TCI: 54.042516
- Outputs: system_metrics.xlsx; 28 pair Word/HTML/Excel reports; system + pair charts under `outputs/figures/`

## System PCA

| component | eigenvalue | variance_share |
| --- | ---: | ---: |
| PC1 | 3.817794 | 0.477224 |
| PC2 | 1.565873 | 0.195734 |
| PC3 | 1.078554 | 0.134819 |
| PC4 | 0.651700 | 0.081463 |
| PC5 | 0.442405 | 0.055301 |
| PC6 | 0.273764 | 0.034221 |
| PC7 | 0.165302 | 0.020663 |
| PC8 | 0.004606 | 0.000576 |

## System connectedness (from/to others, percent)

| symbol | from_others | to_others | net | own_share |
| --- | ---: | ---: | ---: | ---: |
| EURUSD | 67.5488 | 89.2329 | 21.6841 | 32.4512 |
| GBPUSD | 62.0166 | 66.0466 | 4.0301 | 37.9834 |
| AUDUSD | 65.1941 | 71.0563 | 5.8623 | 34.8059 |
| NZDUSD | 64.2971 | 67.8214 | 3.5243 | 35.7029 |
| USDJPY | 24.9767 | 12.9970 | -11.9797 | 75.0233 |
| USDCHF | 59.1792 | 60.8619 | 1.6827 | 40.8208 |
| USDCAD | 56.3555 | 46.2007 | -10.1549 | 43.6445 |
| EURGBP | 32.7722 | 18.1233 | -14.6489 | 67.2278 |

## Pair index

| pair | n | rho | d_ij | theta_L_to_R | theta_R_to_L |
| --- | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.642007 | 0.846160 | 0.133766 | 0.156509 |
| EURUSD-AUDUSD | 7201 | 0.558036 | 0.940174 | 0.101085 | 0.108895 |
| EURUSD-NZDUSD | 7186 | 0.552004 | 0.946568 | 0.098981 | 0.108749 |
| EURUSD-USDJPY | 7200 | -0.299566 | 1.612182 | 0.029125 | 0.066901 |
| EURUSD-USDCHF | 7186 | -0.747345 | 1.869409 | 0.181336 | 0.227509 |
| EURUSD-USDCAD | 7188 | -0.458052 | 1.707660 | 0.068060 | 0.092183 |
| EURUSD-EURGBP | 7183 | 0.439919 | 1.058377 | 0.063135 | 0.131581 |
| GBPUSD-AUDUSD | 7228 | 0.540790 | 0.958342 | 0.111556 | 0.102307 |
| GBPUSD-NZDUSD | 7203 | 0.532783 | 0.966661 | 0.107822 | 0.101356 |
| GBPUSD-USDJPY | 7200 | -0.196287 | 1.546794 | 0.014834 | 0.028163 |
| GBPUSD-USDCHF | 7201 | -0.484413 | 1.723028 | 0.088578 | 0.095088 |
| GBPUSD-USDCAD | 7205 | -0.457478 | 1.707324 | 0.080766 | 0.092304 |
| GBPUSD-EURGBP | 7199 | -0.398603 | 1.672485 | 0.060101 | 0.107482 |
| AUDUSD-NZDUSD | 7202 | 0.828775 | 0.585192 | 0.239713 | 0.245758 |
| AUDUSD-USDJPY | 7199 | -0.086373 | 1.474023 | 0.002879 | 0.007224 |
| AUDUSD-USDCHF | 7200 | -0.381088 | 1.661980 | 0.051004 | 0.059133 |
| AUDUSD-USDCAD | 7204 | -0.648925 | 1.815998 | 0.146632 | 0.184201 |
| AUDUSD-EURGBP | 7198 | 0.036369 | 1.388259 | 0.000510 | 0.001607 |
| NZDUSD-USDJPY | 7185 | -0.133871 | 1.505902 | 0.006441 | 0.014297 |
| NZDUSD-USDCHF | 7185 | -0.394447 | 1.669998 | 0.055576 | 0.063469 |
| NZDUSD-USDCAD | 7190 | -0.589889 | 1.783193 | 0.124608 | 0.152479 |
| NZDUSD-EURGBP | 7183 | 0.035833 | 1.388645 | 0.000482 | 0.001453 |
| USDJPY-USDCHF | 7185 | 0.397789 | 1.097461 | 0.117816 | 0.064386 |
| USDJPY-USDCAD | 7186 | 0.026272 | 1.395513 | 0.002353 | 0.000543 |
| USDJPY-EURGBP | 7181 | -0.129377 | 1.502915 | 0.013012 | 0.011761 |
| USDCHF-USDCAD | 7188 | 0.304864 | 1.179098 | 0.038395 | 0.041663 |
| USDCHF-EURGBP | 7182 | -0.325016 | 1.627892 | 0.043813 | 0.072646 |
| USDCAD-EURGBP | 7185 | -0.014713 | 1.424579 | 0.000181 | 0.001192 |

## Cross-pair conclusion

Reading of the 28-pair network-distance index plus the system TCI. Not a 29th pair analysis and not a trading signal.

System TCI (H=10): 54.0425.
Closest network pair (smallest d_ij): AUDUSD-NZDUSD (d=0.5852, rho=0.8288).
Farthest network pair (largest d_ij): EURUSD-USDCHF (d=1.8694, rho=-0.7473).

This NOTES.md is the system summary plus the pair-distance reading. It is not a trading signal.
