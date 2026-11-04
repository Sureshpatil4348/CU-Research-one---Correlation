# Cointegration and error correction experiments v002

Done: Bonferroni and BH-FDR applied to 28 recomputed Engle-Granger p-values; Bonferroni survivors: none; BH-FDR survivors: none.

## Research question

After a Bonferroni or BH-FDR correction for 28 Engle-Granger tests, which pairs still show cointegration of log closes on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Same design as v001: statsmodels coint(trend='c', autolag='aic'), PY = right on PX = left.
- Bonferroni cut = 0.05 / 28 = 0.00178571.
- BH-FDR at 0.05 via statsmodels multipletests method fdr_bh.
- v001 outputs were read and not edited. Corrected p-values use the recomputed raw p.
- Largest absolute gap between recomputed raw p and v001 coint_p: 0.0116918.

## Index

| pair | n | raw_p | v001_p | bonferroni_p | bh_q | survive_bonferroni | survive_fdr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EURUSD-GBPUSD | 7203 | 0.795116 | 0.796902 | 1 | 0.970082 | no | no |
| EURUSD-AUDUSD | 7202 | 0.0397559 | 0.0495362 | 1 | 0.371055 | no | no |
| EURUSD-NZDUSD | 7187 | 0.150557 | 0.148825 | 1 | 0.873601 | no | no |
| EURUSD-USDJPY | 7201 | 0.896458 | 0.896456 | 1 | 0.970082 | no | no |
| EURUSD-USDCHF | 7187 | 0.970082 | 0.969391 | 1 | 0.970082 | no | no |
| EURUSD-USDCAD | 7189 | 0.0225526 | 0.024499 | 0.631473 | 0.371055 | no | no |
| EURUSD-EURGBP | 7184 | 0.795259 | 0.793656 | 1 | 0.970082 | no | no |
| GBPUSD-AUDUSD | 7229 | 0.61074 | 0.606241 | 1 | 0.970082 | no | no |
| GBPUSD-NZDUSD | 7204 | 0.602723 | 0.597793 | 1 | 0.970082 | no | no |
| GBPUSD-USDJPY | 7201 | 0.866354 | 0.864492 | 1 | 0.970082 | no | no |
| GBPUSD-USDCHF | 7202 | 0.622422 | 0.613178 | 1 | 0.970082 | no | no |
| GBPUSD-USDCAD | 7206 | 0.559352 | 0.561388 | 1 | 0.970082 | no | no |
| GBPUSD-EURGBP | 7200 | 0.671773 | 0.671008 | 1 | 0.970082 | no | no |
| AUDUSD-NZDUSD | 7203 | 0.303358 | 0.304655 | 1 | 0.970082 | no | no |
| AUDUSD-USDJPY | 7200 | 0.682139 | 0.687713 | 1 | 0.970082 | no | no |
| AUDUSD-USDCHF | 7201 | 0.907173 | 0.912955 | 1 | 0.970082 | no | no |
| AUDUSD-USDCAD | 7205 | 0.0373716 | 0.0400587 | 1 | 0.371055 | no | no |
| AUDUSD-EURGBP | 7199 | 0.707049 | 0.706493 | 1 | 0.970082 | no | no |
| NZDUSD-USDJPY | 7186 | 0.82131 | 0.823852 | 1 | 0.970082 | no | no |
| NZDUSD-USDCHF | 7186 | 0.940703 | 0.941179 | 1 | 0.970082 | no | no |
| NZDUSD-USDCAD | 7191 | 0.278917 | 0.273169 | 1 | 0.970082 | no | no |
| NZDUSD-EURGBP | 7184 | 0.655457 | 0.654767 | 1 | 0.970082 | no | no |
| USDJPY-USDCHF | 7186 | 0.830287 | 0.835121 | 1 | 0.970082 | no | no |
| USDJPY-USDCAD | 7187 | 0.356711 | 0.368403 | 1 | 0.970082 | no | no |
| USDJPY-EURGBP | 7182 | 0.776849 | 0.777515 | 1 | 0.970082 | no | no |
| USDCHF-USDCAD | 7189 | 0.873905 | 0.875333 | 1 | 0.970082 | no | no |
| USDCHF-EURGBP | 7183 | 0.156 | 0.156619 | 1 | 0.873601 | no | no |
| USDCAD-EURGBP | 7186 | 0.76053 | 0.760583 | 1 | 0.970082 | no | no |

## Cross-pair conclusion

Bonferroni survivors at 0.05: none.
BH-FDR survivors at 0.05: none.
A raw p below 0.05 is not a robust hit once the 28 tests are counted.
This is not a trading signal.
