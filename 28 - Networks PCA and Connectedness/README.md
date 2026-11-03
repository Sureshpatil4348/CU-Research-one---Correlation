# Networks, PCA, and connectedness

**Status:** complete (experiments/v001)

**Formula guide:** section 28 in [forex-formulas-explained.pdf](../forex-formulas-explained.pdf)

**Local guide:** [Networks_PCA_and_Connectedness_Complete_Simple_Guide.pdf](Networks_PCA_and_Connectedness_Complete_Simple_Guide.pdf) (built by build_guide.py)

**Experiments:** [experiments/v001/](experiments/v001/) — eight-major daily log-return panel: network distances d_ij = √(2(1−ρ)), PCA eigenvalues of the correlation matrix, and Diebold–Yilmaz TCI from a BIC-selected VAR with generalised FEVD (H=10), plus 28 pair reports with d_ij and directed θ̃ shares, using the Alpari full-history D1 snapshot `data/snapshots/2026-11-03_majors_alpari_D1`. Outputs: `system_metrics.xlsx`, 28 Word/HTML/Excel pair reports, system and pair charts, and [NOTES.md](experiments/v001/NOTES.md).
