# Asymmetric DCC experiments v002

Done: every pair has a status flag, a boundary flag, and a chi-bar-square likelihood-ratio p-value for g=0 (ok=27, check=1, fail=0; lr_p<0.05 on 5 pairs).

## Research question

After removing the v001 floor b >= 0.5 and allowing g = 0, which pairs have a likelihood-ratio rejection of symmetric DCC?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Marginal model: constant-mean GARCH(1,1) via arch, z = resid/sigma.
- ADCC: a, g in [0, 0.5], b in [0, 0.999], constraint a+b+g/2 < 0.999.
- Nested DCC is the same likelihood at g=0.
- LR = 2 * (nll_dcc - nll_adcc), floored at 0.
- p-value is the chi-bar-square mixture: 0.5 * P(chi^2_1 > LR) when LR > 0, else 1.
- status ok requires both optimizers to report success. check is a finite point without that flag. fail is no finite fit.
- v001 files were not edited.

## Index

| pair | n | status | a | b | g | boundary | lr | lr_p | v001_b | v001_g |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EURUSD-GBPUSD | 7202 | ok | 0.0230202 | 0.974613 | 0.00111009 | stationarity | 0.0468409 | 0.414327 | 0.974614 | 0.00110979 |
| EURUSD-AUDUSD | 7201 | ok | 0.0312067 | 0.960498 | 4.3316e-14 | g | 0 | 1 | 0.960498 | 1e-08 |
| EURUSD-NZDUSD | 7186 | ok | 0.022676 | 0.972641 | 3.35753e-15 | g | 7.63976e-11 | 0.499997 | 0.972641 | 1e-08 |
| EURUSD-USDJPY | 7200 | ok | 0.0565161 | 0.8964 | 0.0351729 | interior | 21.7554 | 1.5486e-06 | 0.8964 | 0.0351725 |
| EURUSD-USDCHF | 7186 | ok | 0.25211 | 0.00340709 | 0 | g | 0 | 1 | 0.5 | 1e-08 |
| EURUSD-USDCAD | 7188 | ok | 0.0203664 | 0.976171 | 0 | g | 3.09228e-11 | 0.499998 | 0.976171 | 1e-08 |
| EURUSD-EURGBP | 7183 | ok | 0.0243986 | 0.970579 | 0 | g | 0 | 1 | 0.970579 | 1e-08 |
| GBPUSD-AUDUSD | 7228 | ok | 0.0171835 | 0.980953 | 6.22435e-19 | g,stationarity | 0 | 1 | 0.980953 | 1e-08 |
| GBPUSD-NZDUSD | 7203 | check | 0.0182009 | 0.978025 | 0.00554924 | stationarity | 1.23296 | 0.133416 | 0.978015 | 0.00560219 |
| GBPUSD-USDJPY | 7200 | ok | 0.0290789 | 0.952576 | 0.0168308 | interior | 8.38789 | 0.00188865 | 0.952576 | 0.0168308 |
| GBPUSD-USDCHF | 7201 | ok | 0.00740959 | 0.991563 | 0 | g,stationarity | 0 | 1 | 0.991681 | 1.95197e-05 |
| GBPUSD-USDCAD | 7205 | ok | 0.0148223 | 0.982587 | 0.00103583 | interior | 0.161623 | 0.343833 | 0.982587 | 0.00103565 |
| GBPUSD-EURGBP | 7199 | ok | 0.0247523 | 0.972137 | 0 | g | 2.18279e-11 | 0.499998 | 0.972137 | 1e-08 |
| AUDUSD-NZDUSD | 7202 | ok | 0.0209996 | 0.975711 | 0.000118787 | interior | 0.000706596 | 0.489397 | 0.975711 | 0.000118756 |
| AUDUSD-USDJPY | 7199 | ok | 0.0545908 | 0.902108 | 0.0420519 | interior | 37.0181 | 5.85184e-10 | 0.902108 | 0.042052 |
| AUDUSD-USDCHF | 7200 | ok | 0.0495707 | 0.924292 | 0 | g | 2.72848e-11 | 0.499998 | 0.924292 | 1e-08 |
| AUDUSD-USDCAD | 7204 | ok | 0.0163448 | 0.981495 | 0 | g | 3.81988e-11 | 0.499998 | 0.981495 | 1e-08 |
| AUDUSD-EURGBP | 7198 | ok | 0.0121698 | 0.98473 | 1.93101e-15 | g | 0 | 1 | 0.98473 | 1e-08 |
| NZDUSD-USDJPY | 7185 | ok | 0.0431568 | 0.915926 | 0.0374617 | interior | 30.4851 | 1.68218e-08 | 0.915926 | 0.0374617 |
| NZDUSD-USDCHF | 7185 | ok | 0.0490861 | 0.92623 | 0 | g | 7.27596e-12 | 0.499999 | 0.926231 | 1e-08 |
| NZDUSD-USDCAD | 7190 | ok | 0.0150372 | 0.983083 | 0 | g,stationarity | 9.64064e-11 | 0.499996 | 0.983083 | 1e-08 |
| NZDUSD-EURGBP | 7183 | ok | 0.00935644 | 0.988547 | 4.87587e-06 | g | 1.70196e-06 | 0.49948 | 0.988547 | 4.83713e-06 |
| USDJPY-USDCHF | 7185 | ok | 0.0790123 | 0.88527 | 0 | g | 1.09139e-11 | 0.499999 | 0.885271 | 1e-08 |
| USDJPY-USDCAD | 7186 | ok | 0.0310798 | 0.95704 | 0 | g | 0 | 1 | 0.95704 | 1e-08 |
| USDJPY-EURGBP | 7181 | ok | 0.0130846 | 0.979315 | 0 | g | 0 | 1 | 0.979315 | 1e-08 |
| USDCHF-USDCAD | 7188 | ok | 0.00707341 | 0.968276 | 0.047301 | stationarity | 43.042 | 2.67892e-11 | 0.968277 | 0.0473002 |
| USDCHF-EURGBP | 7182 | ok | 0.0462356 | 0.926142 | 0 | g | 0 | 1 | 0.926142 | 1e-08 |
| USDCAD-EURGBP | 7185 | ok | 0.00824755 | 0.988969 | 0.00341926 | stationarity | 0.543926 | 0.230405 | 0.988966 | 0.0032987 |

## Cross-pair conclusion

EURUSD-USDCHF v002 b is 0.003407 (v001 b was 0.500000), g=0.000000, boundary=g, lr_p=1, status=ok.
Pairs with chi-bar p below 0.05: 5 of 28. A g of 0 in v001 can be the old lower bound of 1e-8 rounded in the table.
This is not a trading signal.
