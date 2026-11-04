# Rolling correlation

**Status:** v001 complete; v002 writes rolling Pearson at 20, 60, and 100 for all 28 pairs (`experiments/v002/`)

**Formula guide:** section 05 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Rolling_Correlation_Complete_Simple_Guide.pdf](Rolling_Correlation_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — rolling Pearson r on daily log returns with windows 20 / 60 / 100 for the short watchlist, secondary tier, and low-value pairs, using Alpari snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. See [NOTES.md](experiments/v001/NOTES.md) and [outputs/WATCHLIST.md](experiments/v001/outputs/WATCHLIST.md).
