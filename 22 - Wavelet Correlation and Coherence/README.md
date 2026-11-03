# Wavelet correlation and coherence

**Status:** complete (experiments/v001)

**Formula guide:** section 22 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Wavelet_Correlation_and_Coherence_Complete_Simple_Guide.pdf](Wavelet_Correlation_and_Coherence_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — Morlet CWT wavelet correlation ρ_wavelet at periods {5, 21, 63} trading days (headline 21) plus mean R² with Gaussian time smoothing and edge cone mask on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks (matched rows + scales), charts (closes, returns, ρ by period), and [NOTES.md](experiments/v001/NOTES.md).
