# Partial and residual correlation experiments v002

Done: trailing 252-day partial correlation. The leave-currency-out USD factor is estimated inside each window.

## Research question

What is the time-t partial correlation after removing a USD factor that uses only the same 252 days?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Window: 252.
- USD strength: minus the log return for EURUSD, GBPUSD, AUDUSD, NZDUSD; plus for USDJPY, USDCHF, USDCAD.
- EURGBP never enters the factor. A constituent that shares a non-USD currency with either leg is left out.
- Column: m07_rho_partial. No label column.
- v001 files were not edited.

Rows written: 192981.
