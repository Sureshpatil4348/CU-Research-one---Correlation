# EURGBP / EURCHF / NZDUSD rolling lines

## Research question

For the three crosses among EURGBP, EURCHF, and NZDUSD, how does Pearson correlation of daily log returns move on windows 20, 60, and 100?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- EURCHF is not in the snapshot. Built as `EURUSD close × USDCHF close` on matched dates (CHF per EUR). Its log return is the sum of the EURUSD and USDCHF log returns.
- Statistic: rolling Pearson r with W in {20, 60, 100}
- Outputs: three rolling charts under `outputs/`

## Charts

- `outputs/EURGBP-EURCHF_Rolling_D1_rolling.png`
- `outputs/EURGBP-NZDUSD_Rolling_D1_rolling.png`
- `outputs/EURCHF-NZDUSD_Rolling_D1_rolling.png`

## Page

- [index.html](index.html) — charts, numbers, how to read the lines, and conclusion

This folder is a named dig into the three crosses. It is not a new experiment version and does not change v001.
