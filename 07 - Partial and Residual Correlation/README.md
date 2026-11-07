# Partial and residual correlation

**Status:** complete (experiments/v001)

**Formula guide:** section 07 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Partial_and_Residual_Correlation_Complete_Simple_Guide.pdf](Partial_and_Residual_Correlation_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — partial / residual correlation on daily log returns for all 28 unique pairs among the eight majors after a leave-currency-out USD strength factor, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, returns+z, residual scatter), and [NOTES.md](experiments/v001/NOTES.md).

**Seven USD majors dig:** [seven-usd-majors/](seven-usd-majors/) — full-sample partial vs Pearson and rolling raw vs in-window partial (W = 20 / 60 / 100) for the 21 pairs among EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD (EURGBP excluded). Page: [index.html](seven-usd-majors/index.html).
