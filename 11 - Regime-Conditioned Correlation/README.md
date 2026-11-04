# Regime-conditioned correlation

**Status:** v001 complete; v002 adds the Forbes-Rigobon adjustment; v003 writes the trailing adjusted-gap feature

**Formula guide:** section 11 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Regime_Conditioned_Correlation_Complete_Simple_Guide.pdf](Regime_Conditioned_Correlation_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — shared look-ahead-free FX turbulence regimes (quiet vs stress) with Pearson rho on each subsample for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, returns with stress shading, regime scatter), and [NOTES.md](experiments/v001/NOTES.md).
