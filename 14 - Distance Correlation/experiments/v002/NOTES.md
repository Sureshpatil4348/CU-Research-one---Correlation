# Distance correlation experiments v002

Done: trailing 252-day biased distance correlation on a daily grid.

## Research question

What is the time-t distance correlation on a trailing window that does not use future returns?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Window: 252. Same biased dCor as v001.
- Timing: 0.0018s per window, about 5.8 minutes for 28 pairs on a daily grid. Grid used: daily.
- Column: m14_dcor. A carried-forward value is the last computed value from an earlier date in the same series, so feature_asof is still the row date and the number was known then.
- v001 files were not edited.

Rows written: 194407.
