# Transfer entropy

**Status:** v001 complete; v002 ranks transfer entropy after a permutation null and BH-FDR (`experiments/v002/`)

**Formula guide:** section 17 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Transfer_Entropy_Complete_Simple_Guide.pdf](Transfer_Entropy_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — discrete transfer entropy (B=5 equal-frequency bins, lag k=m=1, both directions) on daily log returns for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, returns, TE bars), and [NOTES.md](experiments/v001/NOTES.md).
