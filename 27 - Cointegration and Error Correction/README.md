# Cointegration and error correction

**Status:** complete (experiments/v001)

**Formula guide:** section 27 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Cointegration_and_Error_Correction_Complete_Simple_Guide.pdf](Cointegration_and_Error_Correction_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — Engle-Granger cointegration of log closes (PY = right on PX = left) plus one-lag ECM κ on daily data for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, spread e_t, returns), and [NOTES.md](experiments/v001/NOTES.md).
