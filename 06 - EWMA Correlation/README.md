# EWMA correlation

**Status:** complete (experiments/v001)

**Formula guide:** section 06 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [EWMA_Correlation_Complete_Simple_Guide.pdf](EWMA_Correlation_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — EWMA rho (lambda = 0.94) on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, returns, EWMA path with Pearson r reference), and [NOTES.md](experiments/v001/NOTES.md).
