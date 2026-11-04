# Networks, PCA, and connectedness experiments v003

Done: trailing 252-day d_ij and PC1 share on the seven majors, plus a quarterly TCI held flat until the next quarter-end.

## Research question

What network and connectedness numbers are known at date t without EURGBP and without future returns?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Panel: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD.
- d_ij = sqrt(2*(1-rho)) and PC1 variance share use the last 252 days.
- TCI uses a BIC VAR (max lag 10, or less when the sample is short) and GFEVD horizon 10.
- A quarter-end fit uses data through that date and is held through the day before the next quarter-end.
- Columns: m28_d_ij, m28_pc1_share, m28_tci. No label column. EURGBP pairs are absent.
- v001 and v002 files were not edited.

Rows written: 144837. Quarter-end refits: 109.
