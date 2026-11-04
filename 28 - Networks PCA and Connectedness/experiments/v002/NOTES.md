# Networks, PCA, and connectedness experiments v002

Done: system PCA and VAR/GFEVD rerun without EURGBP; smallest eigenvalue 0.165114 versus v001 PC8 0.004606; TCI 56.0193.

## Research question

On the seven majors that remain after dropping EURGBP, what are the PCA eigenvalues and the Diebold-Yilmaz TCI?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Panel: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD. EURGBP is dropped, not orthogonalised.
- n_obs=7127.
- VAR on demeaned returns; lag = BIC among 1..10; GFEVD H=10. Same algebra as v001.
- v001 PC8 eigenvalue, copied from the v001 NOTES and not refit here: 0.004606.
- corr(EURGBP, EURUSD log return - GBPUSD log return) = 0.991220 on the eight-name inner join.
- v001 files were not edited.

## System PCA

| component | eigenvalue | variance_share |
| --- | --- | --- |
| PC1 | 3.80158 | 0.543083 |
| PC2 | 1.26356 | 0.180509 |
| PC3 | 0.65215 | 0.0931643 |
| PC4 | 0.467881 | 0.0668402 |
| PC5 | 0.441348 | 0.0630497 |
| PC6 | 0.208359 | 0.0297656 |
| PC7 | 0.165114 | 0.0235878 |

## System connectedness (percent)

| symbol | from_others | to_others | net | own_share |
| --- | --- | --- | --- | --- |
| EURUSD | 65.3725 | 78.2366 | 12.8642 | 34.6275 |
| GBPUSD | 59.6009 | 56.7042 | -2.89665 | 40.3991 |
| AUDUSD | 65.182 | 72.5882 | 7.40621 | 34.818 |
| NZDUSD | 64.287 | 69.366 | 5.07895 | 35.713 |
| USDJPY | 24.0159 | 12.4229 | -11.5931 | 75.9841 |
| USDCHF | 57.3262 | 55.5745 | -1.75166 | 42.6738 |
| USDCAD | 56.3505 | 47.2426 | -9.10795 | 43.6495 |

System TCI (H=10): 56.019286. BIC lag: 1.

## Cross-pair conclusion

EURGBP is nearly EURUSD minus GBPUSD (correlation 0.9912), which is why v001 PC8 was 0.004606.
Without that leg the smallest eigenvalue is 0.165114.
This is not a trading signal.
