# DCCA detrended cross-correlation

**Status:** complete (experiments/v001)

**Formula guide:** section 23 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [DCCA_Detrended_Cross_Correlation_Complete_Simple_Guide.pdf](DCCA_Detrended_Cross_Correlation_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — non-overlapping linear DCCA ρ_DCCA(s) at s in {20, 60, 100} (headline s=100) on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks (matched rows + scales), charts (closes, returns, ρ versus s), and [NOTES.md](experiments/v001/NOTES.md).
