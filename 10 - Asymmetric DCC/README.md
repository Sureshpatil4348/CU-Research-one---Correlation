# Asymmetric DCC

**Status:** v001 complete; v002 refits ADCC with g = 0 allowed; v003 writes the causal ADCC feature

**Formula guide:** section 10 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Asymmetric_DCC_Complete_Simple_Guide.pdf](Asymmetric_DCC_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — constant-mean GARCH(1,1) + Cappiello–Engle–Sheppard asymmetric DCC (with nested symmetric DCC) on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, returns, ADCC path with nested DCC and Pearson r), and [NOTES.md](experiments/v001/NOTES.md).
