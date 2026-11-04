# Rolling correlation experiments v002

Done: rolling Pearson at 20, 60, and 100 days for all 28 pairs, with |r_20 - expanding Pearson| using only data through t.

## Research question

What are the causal rolling correlations on every major pair, not only the 17-pair v001 watchlist?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Windows: 20, 60, 100.
- Expanding baseline starts at 252 observations. It is not the full-sample r from v001.
- Columns: m05_r20, m05_r60, m05_r100, m05_abs_gap. No label column.
- v001 files were not edited.

Rows written: 200903.
