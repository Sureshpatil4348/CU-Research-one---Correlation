# Volatility and realized correlation

**Status:** complete (experiments/v001)

**Formula guide:** section 25 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Volatility_and_Realized_Correlation_Complete_Simple_Guide.pdf](Volatility_and_Realized_Correlation_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — volatility correlation ρ_vol = Corr(|log return|, |log return|) on daily closes for all 28 unique pairs among the eight majors, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Within-day realized correlation ρ_realized is not computed (D1 snapshot has no intraday buckets). Outputs: 28 Word reports, 28 HTML data tables, 28 Excel workbooks, charts (closes, returns, absolute-return scatter), and [NOTES.md](experiments/v001/NOTES.md).
