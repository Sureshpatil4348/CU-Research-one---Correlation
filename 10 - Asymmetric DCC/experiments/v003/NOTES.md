# Asymmetric DCC experiments v003

Done: ADCC rho minus expanding Pearson, with parameters fit only on data through each year-end.

## Research question

What is the time-t gap between ADCC and expanding Pearson when neither the GARCH parameters nor the ADCC parameters use future returns?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- First refit: last common trading day on or before 2006-12-31 (2006-12-29). Then each later 31 December through the year before the sample's last year.
- GARCH(1,1) is fit on each symbol through the year-end. Later days in that vintage use the frozen recursion. The next year-end replaces the parameters; it does not rewrite earlier feature dates.
- ADCC a, b, g and the targeting matrices are fit on the pair's standardized residuals through that year-end. Two starts: (0.05, 0.90, 0.02) and (0.03, 0.40, 0.05).
- Days before the first refit are missing.
- Column: m10_adcc_minus_r. No label column.
- v001 and v002 files were not edited.

Rows written: 143837. Failed pair-year segments: 0.
