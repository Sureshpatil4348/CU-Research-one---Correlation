# Regime-conditioned correlation experiments v003

Done: trailing 252-day Forbes-Rigobon adjusted stress-minus-quiet gap. The state at t uses only RV history before t.

## Research question

What is the time-t adjusted correlation gap between quiet and stress days inside the last 252 days?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- State rule matches v001: turb is the eight-major mean absolute log return; RV is the prior 20 turb days; stress when RV exceeds the 75th percentile of the prior 252 RV values.
- Feature window: 252 days. Missing if either state has fewer than 30 days in the window.
- Adjustment matches v002: rho_stress / sqrt(1 + delta * (1 - rho_stress^2)) - rho_quiet, with delta the average variance ratio minus one.
- Column: m11_adj_gap. No label column.
- v001 and v002 files were not edited.

Rows written: 141932.
