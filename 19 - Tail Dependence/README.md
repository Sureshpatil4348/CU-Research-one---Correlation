# Tail dependence

**Status:** v001 complete; v002 adds the Gaussian co-exceedance benchmark; v003 writes the trailing lower-tail excess

**Formula guide:** section 19 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Tail_Dependence_Complete_Simple_Guide.pdf](Tail_Dependence_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — empirical lower and upper tail frequencies L_hat at alpha=0.05 (both conditioning directions, with counts) on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, returns, uniforms with alpha lines), and [NOTES.md](experiments/v001/NOTES.md).
