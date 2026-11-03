# Cointegration and error correction experiments v001

## Research question

For each unordered pair among the eight majors, what is the Engle-Granger cointegration evidence and ECM kappa for log closes (PY = right on PX = left) on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: log close levels for cointegration; log returns for ECM and Pearson side check; quote direction unchanged
- Engle-Granger: OLS with constant; statsmodels coint(trend='c', autolag='aic')
- ECM: one lag of both delta ln legs; headline coint p-value and kappa
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/`

## Index

| pair | n | alpha | beta | coint_t | coint_p | kappa | pearson_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.310961 | 0.600813 | -1.401781 | 0.796902 | -0.000771 | 0.641738 |
| EURUSD-AUDUSD | 7201 | -0.487028 | 1.175892 | -3.339439 | 0.0495362 | -0.003177 | 0.556324 |
| EURUSD-NZDUSD | 7186 | -0.610114 | 1.101393 | -2.854952 | 0.148825 | -0.002364 | 0.549808 |
| EURUSD-USDJPY | 7200 | 4.828032 | -0.678568 | -1.032760 | 0.896456 | -0.000581 | -0.300952 |
| EURUSD-USDCHF | 7186 | 0.187234 | -0.742026 | -0.422872 | 0.969391 | -0.000308 | -0.749204 |
| EURUSD-USDCAD | 7188 | 0.374605 | -0.929008 | -3.600037 | 0.024499 | -0.002654 | -0.456626 |
| EURUSD-EURGBP | 7183 | -0.310483 | 0.397265 | -1.411177 | 0.793656 | -0.000710 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | -0.495926 | 0.479909 | -1.847773 | 0.606241 | -0.000947 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | -0.563759 | 0.314598 | -1.864708 | 0.597793 | -0.000977 | 0.530079 |
| GBPUSD-USDJPY | 7200 | 4.906447 | -0.457698 | -1.174341 | 0.864492 | -0.000592 | -0.198556 |
| GBPUSD-USDCHF | 7201 | -0.161244 | 0.570007 | -1.833772 | 0.613178 | -0.000682 | -0.486083 |
| GBPUSD-USDCAD | 7205 | 0.415302 | -0.462257 | -1.936497 | 0.561388 | -0.000949 | -0.456462 |
| GBPUSD-EURGBP | 7199 | -0.046926 | -0.494893 | -1.712852 | 0.671008 | -0.000812 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | -0.160941 | 0.914132 | -2.443248 | 0.304655 | -0.002031 | 0.828722 |
| AUDUSD-USDJPY | 7199 | 4.534546 | -0.618603 | -1.676138 | 0.687713 | -0.000438 | -0.088151 |
| AUDUSD-USDCHF | 7200 | -0.120401 | -0.633698 | -0.944050 | 0.912955 | -0.000408 | -0.380878 |
| AUDUSD-USDCAD | 7204 | 0.008758 | -0.727258 | -3.421115 | 0.0400587 | -0.002239 | -0.647362 |
| AUDUSD-EURGBP | 7198 | -0.151328 | 0.321120 | -1.633619 | 0.706493 | -0.000729 | 0.038173 |
| NZDUSD-USDJPY | 7185 | 4.520937 | -0.458210 | -1.319250 | 0.823852 | -0.000345 | -0.133568 |
| NZDUSD-USDCHF | 7185 | -0.275443 | -0.792241 | -0.748202 | 0.941179 | -0.000425 | -0.393600 |
| NZDUSD-USDCAD | 7190 | -0.054746 | -0.647638 | -2.513451 | 0.273169 | -0.000898 | -0.587831 |
| NZDUSD-EURGBP | 7183 | -0.077491 | 0.390425 | -1.747686 | 0.654767 | -0.000872 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.280684 | -0.044731 | -1.281934 | 0.835121 | -0.000446 | 0.399461 |
| USDJPY-USDCAD | 7186 | -2.260759 | 0.527080 | -2.310344 | 0.368403 | -0.001522 | 0.027603 |
| USDJPY-EURGBP | 7181 | 0.124492 | -0.078788 | -1.456437 | 0.777515 | -0.000745 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.208485 | 0.270618 | -1.129822 | 0.875333 | -0.000540 | 0.304665 |
| USDCHF-EURGBP | 7182 | -0.210484 | -0.532874 | -2.829042 | 0.156619 | -0.001828 | -0.325886 |
| USDCAD-EURGBP | 7185 | -0.171099 | -0.336354 | -1.501586 | 0.760583 | -0.000780 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index at pre-specified Engle-Granger p-value (PY on PX = right on left). Not a 29th pair analysis and not a trading signal.

Strongest cointegration evidence (lowest p): EURUSD-USDCAD (p=0.0245, t=-3.6000, kappa=-0.0027).
Weakest cointegration evidence (highest p): EURUSD-USDCHF (p=0.9694).
Most negative ECM kappa: EURUSD-AUDUSD (kappa=-0.0032).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
