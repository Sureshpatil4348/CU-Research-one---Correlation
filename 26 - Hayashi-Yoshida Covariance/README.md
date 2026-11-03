# Hayashi-Yoshida covariance

**Status:** complete (experiments/v001)

**Formula guide:** section 26 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Hayashi_Yoshida_Covariance_Complete_Simple_Guide.pdf](Hayashi_Yoshida_Covariance_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — synced-D1 Hayashi–Yoshida special case (same-day interval overlaps): C_HY = sum r_x r_y and headline ρ_HY = C_HY / sqrt(sum r_x² · sum r_y²) on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Async tick HY is not tested (no tick snapshot). Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, returns, cumulative product path), and [NOTES.md](experiments/v001/NOTES.md).
