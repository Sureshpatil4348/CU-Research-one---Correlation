# Partial and residual correlation experiments v001

## Research question

For each unordered pair among the eight majors, what is the partial correlation of matched daily log returns of close after removing a leave-currency-out USD strength factor, on the Alpari D1 history that the broker actually provided?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Control z: equal-weight mean of USD-strength returns from majors that do not share a non-USD currency with either leg; USD-strength is -log return for EURUSD/GBPUSD/AUDUSD/NZDUSD and +log return for USDJPY/USDCHF/USDCAD; EURGBP never enters z
- Statistic: OLS residuals of each leg on z (with intercept), then Pearson rho_partial via `scipy.stats.pearsonr` with Fisher 95% interval; same-sample raw Pearson r and rho_partial minus r as a side check; R-squared of each leg on z
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/` (closes, returns+z, residual scatter)

## Index

| pair | n | n_controls | rho_partial | p | ci_low | ci_high | pearson_r | partial_minus_r | r2_x | r2_y |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7148 | 5 | 0.344146 | 6.74005e-198 | 0.323545 | 0.364422 | 0.641959 | -0.297813 | 0.541881 | 0.390732 |
| EURUSD-AUDUSD | 7148 | 5 | -0.015950 | 0.177553 | -0.039118 | 0.007236 | 0.557184 | -0.573134 | 0.607662 | 0.523623 |
| EURUSD-NZDUSD | 7148 | 5 | -0.035903 | 0.00239826 | -0.059037 | -0.012731 | 0.550953 | -0.586856 | 0.611976 | 0.524181 |
| EURUSD-USDJPY | 7148 | 5 | -0.214654 | 2.7816e-75 | -0.236659 | -0.192428 | -0.300364 | 0.085710 | 0.563932 | 0.046510 |
| EURUSD-USDCHF | 7148 | 5 | -0.619787 | 0 | -0.633862 | -0.605301 | -0.748079 | 0.128292 | 0.472531 | 0.286276 |
| EURUSD-USDCAD | 7148 | 5 | -0.022343 | 0.0588979 | -0.045503 | 0.000840 | -0.457067 | 0.434723 | 0.593663 | 0.334233 |
| EURUSD-EURGBP | 7127 | 5 | 0.492957 | 0 | 0.475178 | 0.510333 | 0.439919 | 0.053038 | 0.542081 | 0.022356 |
| GBPUSD-AUDUSD | 7148 | 5 | 0.156705 | 1.57247e-40 | 0.134009 | 0.179237 | 0.540669 | -0.383964 | 0.416297 | 0.499404 |
| GBPUSD-NZDUSD | 7148 | 5 | 0.136841 | 3.18358e-31 | 0.114020 | 0.159518 | 0.532284 | -0.395442 | 0.420200 | 0.500620 |
| GBPUSD-USDJPY | 7148 | 5 | -0.056112 | 2.06514e-06 | -0.079192 | -0.032972 | -0.196585 | 0.140473 | 0.438778 | 0.055269 |
| GBPUSD-USDCHF | 7148 | 5 | -0.165833 | 3.03249e-45 | -0.188292 | -0.143200 | -0.484723 | 0.318890 | 0.414537 | 0.353272 |
| GBPUSD-USDCAD | 7148 | 5 | -0.145742 | 3.11555e-35 | -0.168356 | -0.122974 | -0.456720 | 0.310978 | 0.418438 | 0.318308 |
| GBPUSD-EURGBP | 7129 | 5 | -0.637625 | 0 | -0.651200 | -0.623643 | -0.398542 | -0.239083 | 0.390756 | 0.022395 |
| AUDUSD-NZDUSD | 7148 | 5 | 0.735123 | 0 | 0.724283 | 0.745599 | 0.828711 | -0.093588 | 0.353597 | 0.353059 |
| AUDUSD-USDJPY | 7148 | 5 | 0.198113 | 3.50864e-64 | 0.175738 | 0.220285 | -0.086668 | 0.284782 | 0.583085 | 0.075396 |
| AUDUSD-USDCHF | 7148 | 5 | 0.219052 | 2.13614e-78 | 0.196868 | 0.241011 | -0.380331 | 0.599382 | 0.571656 | 0.419290 |
| AUDUSD-USDCAD | 7148 | 5 | -0.484843 | 0 | -0.502379 | -0.466908 | -0.647895 | 0.163052 | 0.440931 | 0.254272 |
| AUDUSD-EURGBP | 7129 | 4 | -0.136336 | 6.32352e-31 | -0.159046 | -0.113481 | 0.036509 | -0.172845 | 0.504849 | 0.033891 |
| NZDUSD-USDJPY | 7148 | 5 | 0.092999 | 3.31662e-15 | 0.069967 | 0.115932 | -0.133922 | 0.226921 | 0.558374 | 0.067135 |
| NZDUSD-USDCHF | 7148 | 5 | 0.173657 | 1.65232e-49 | 0.151082 | 0.196050 | -0.393516 | 0.567173 | 0.561807 | 0.412845 |
| NZDUSD-USDCAD | 7148 | 5 | -0.371754 | 4.07705e-233 | -0.391562 | -0.351601 | -0.588329 | 0.216575 | 0.459697 | 0.275219 |
| NZDUSD-EURGBP | 7129 | 4 | -0.140236 | 1.22198e-32 | -0.162919 | -0.117404 | 0.036015 | -0.176251 | 0.510954 | 0.034301 |
| USDJPY-USDCHF | 7148 | 5 | 0.365948 | 2.04095e-225 | 0.345698 | 0.385857 | 0.398472 | -0.032524 | 0.031763 | 0.307703 |
| USDJPY-USDCAD | 7148 | 5 | -0.182712 | 1.05709e-54 | -0.205027 | -0.160208 | 0.026249 | -0.208961 | 0.070889 | 0.382431 |
| USDJPY-EURGBP | 7129 | 4 | -0.106744 | 1.61041e-19 | -0.129636 | -0.083737 | -0.129471 | 0.022727 | 0.041367 | 0.016094 |
| USDCHF-USDCAD | 7148 | 5 | -0.118976 | 5.93024e-24 | -0.141768 | -0.096058 | 0.304212 | -0.423188 | 0.394707 | 0.362254 |
| USDCHF-EURGBP | 7129 | 4 | -0.334660 | 4.21218e-186 | -0.355115 | -0.313885 | -0.325087 | -0.009573 | 0.249613 | 0.005174 |
| USDCAD-EURGBP | 7129 | 4 | 0.099152 | 4.82302e-17 | 0.076113 | 0.122085 | -0.014688 | 0.113840 | 0.316280 | 0.028826 |

## Cross-pair conclusion

Reading of the 28-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest positive residual link: AUDUSD-NZDUSD (rho_partial=0.7351, n=7148).
Strongest negative residual link: GBPUSD-EURGBP (rho_partial=-0.6376, n=7129).
Nearest-to-zero residual links: EURUSD-AUDUSD (rho_partial=-0.0159); EURUSD-USDCAD (rho_partial=-0.0223); EURUSD-NZDUSD (rho_partial=-0.0359).
Largest |rho_partial minus Pearson r| gaps on the same sample: AUDUSD-USDCHF (gap=0.5994, rho_partial=0.2191, r=-0.3803); EURUSD-NZDUSD (gap=-0.5869, rho_partial=-0.0359, r=0.5510); EURUSD-AUDUSD (gap=-0.5731, rho_partial=-0.0159, r=0.5572). A large gap can mean the USD factor explained much of the raw link, or that residual co-movement runs against the raw sign; inspect that pair's R-squared values and residual scatter before treating either score as settled.

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
