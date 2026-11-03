# Cross-quantilogram

**Status:** complete (experiments/v001)

**Formula guide:** section 20 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Cross_Quantilogram_Complete_Simple_Guide.pdf](Cross_Quantilogram_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — expanding-window cross-quantilogram at tau in {0.05, 0.20} and lags k=0..10 (headline tau=0.05, k=1) on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks (matched rows + CQ sheet), charts (closes, returns, CQ bars), and [NOTES.md](experiments/v001/NOTES.md).
