# Pearson correlation experiments v002

Done: expanding Pearson r for all 28 pairs, using only returns through date t.

## Research question

What is the expanding-window Pearson correlation of daily log returns at each date t?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Minimum history: 252 matched log returns.
- Column: m01_expanding_r. feature_asof equals the row date. No label column.
- v001 files were not edited.

Rows written: 194407.
