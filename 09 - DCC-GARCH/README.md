# DCC-GARCH

**Status:** v001 complete; v002 refits DCC without the b >= 0.5 floor (`experiments/v002/`)

**Formula guide:** section 09 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [DCC_GARCH_Complete_Simple_Guide.pdf](DCC_GARCH_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — constant-mean GARCH(1,1) + Engle DCC on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, returns, DCC path with Pearson r reference), and [NOTES.md](experiments/v001/NOTES.md).
