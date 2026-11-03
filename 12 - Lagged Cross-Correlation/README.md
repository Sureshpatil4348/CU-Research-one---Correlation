# Lagged cross-correlation

**Status:** complete (experiments/v001)

**Formula guide:** section 12 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Lagged_Cross_Correlation_Complete_Simple_Guide.pdf](Lagged_Cross_Correlation_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — lagged Pearson cross-correlation at k=0..10 in both directions (headline k=1) for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks (matched rows + CCF), charts (closes, returns, CCF bars), and [NOTES.md](experiments/v001/NOTES.md).
