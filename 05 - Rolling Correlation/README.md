# Rolling correlation

**Status:** complete (experiments/v001)

**Formula guide:** section 05 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Rolling_Correlation_Complete_Simple_Guide.pdf](Rolling_Correlation_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — rolling Pearson r on daily log returns with windows 20 / 60 / 100 for the short watchlist, secondary tier, and low-value pairs, using Alpari snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. See [NOTES.md](experiments/v001/NOTES.md) and [outputs/WATCHLIST.md](experiments/v001/outputs/WATCHLIST.md).

**Three-cross dig:** [eurgbp-eurchf-nzdusd/](eurgbp-eurchf-nzdusd/) — rolling r_20 / r_60 / r_100 lines for EURGBP–EURCHF, EURGBP–NZDUSD, and EURCHF–NZDUSD (EURCHF built as EURUSD × USDCHF). Page: [index.html](eurgbp-eurchf-nzdusd/index.html).
