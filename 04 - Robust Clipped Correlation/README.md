# Robust clipped correlation

**Status:** complete (experiments/v001)

**Formula guide:** section 04 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Robust_Clipped_Correlation_Complete_Simple_Guide.pdf](Robust_Clipped_Correlation_Complete_Simple_Guide.pdf) (built by build_guide.py; leave this guide and generator unchanged unless the method owner asks)

**Experiments:** [experiments/v001/](experiments/v001/) — robust clipped correlation on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Clip grid c = 0.01 / 0.02 / 0.03 with headline at 0.02. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, returns with ±0.02 lines, scatter with ±0.02 clip box), and [NOTES.md](experiments/v001/NOTES.md).
