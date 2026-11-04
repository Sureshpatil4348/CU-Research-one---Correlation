# Tail dependence experiments v003

Done: trailing 252-day lower-tail excess. Ranks and the Gaussian benchmark use only that window.

## Research question

At each date t, how far is the lower-tail frequency from the Gaussian co-exceedance implied by the window Pearson r?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Window 252, alpha 0.05. Uniforms are rank/(n+1) inside the window.
- L_hat is the average of the two conditioning directions. Excess = L_hat minus the Gaussian benchmark.
- The benchmark is the bivariate-normal co-exceedance, read from a correlation grid with step 0.001.
- Column: m19_excess_lower. No label column.
- v001 and v002 files were not edited.

Rows written: 194407.
