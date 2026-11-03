# Granger predictability

**Status:** complete (experiments/v001)

**Formula guide:** section 13 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Granger_Predictability_Complete_Simple_Guide.pdf](Granger_Predictability_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — OLS Granger F tests at pre-specified lag orders p=1 and p=5 in both directions (headline p=5) for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks (matched rows + results), charts (closes, returns, F-stat bars), and [NOTES.md](experiments/v001/NOTES.md).
