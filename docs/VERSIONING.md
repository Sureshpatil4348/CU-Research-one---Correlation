# Versioning and experiment contract

## Shared vs method code

- Shared code lives only under `shared/mt5_data/`.
- A method folder never opens MetaTrader 5 and never imports another method folder.
- There is no single script or runner that executes all 28 methods.

## Experiment versions

Each method folder stores work under:

```text
NN - Method Name/
  experiments/
    v001/
      NOTES.md
      outputs/
    v002/
      NOTES.md
      outputs/
```

Rules:

1. A finished version folder is immutable. Do not edit its code results, notes, or `outputs/` after it is closed.
2. A new idea is a new version (`v002`, `v003`, …), not an overwrite of an earlier version.
3. Each `NOTES.md` records: the research question, the exact snapshot folder name under `data/snapshots/`, parameters, and a short result summary.
4. Re-running an idea creates a new version. It does not overwrite an older snapshot or an older `outputs/` folder.

## Snapshots

Price data is frozen under `data/snapshots/YYYY-MM-DD_majors_D1/` (or a similar dated name). Each snapshot folder contains CSVs, `manifest.json`, and a README stating that the folder is immutable. Experiments name the snapshot they used. They do not call MT5 for analysis.

## Method status READMEs

Every method folder has a short `README.md` with method name, pointer to the matching section of `forex-formulas-explained.pdf`, and status (`not started`, `in progress`, or `complete`). Pearson’s README also points at its existing PDF guide.
