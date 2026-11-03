# Spectral coherence

**Status:** complete (experiments/v001)

**Formula guide:** section 21 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Spectral_Coherence_Complete_Simple_Guide.pdf](Spectral_Coherence_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — Welch magnitude-squared coherence (fs=1, nperseg=256, noverlap=128, hann, detrend=constant) with headline γ² nearest f=1/5 (also 1/21, 1/63, mean γ², phase at 1/5) on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks (matched rows + coherence curve), charts (closes, returns, γ²(f)), and [NOTES.md](experiments/v001/NOTES.md).
