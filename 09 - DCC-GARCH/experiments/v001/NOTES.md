# DCC-GARCH experiments v001

## Research question

For each unordered pair among the eight majors, what is the Engle DCC correlation path of matched daily log returns of close on the Alpari D1 history after constant-mean GARCH(1,1) standardisation?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Marginal model: constant-mean GARCH(1,1) via arch (fit on percent returns for numerical stability; z = resid/sigma)
- DCC: correlation targeting, estimate a,b with a>=0, b>=0, a+b<1; burn-in=60; headline = latest rho; Pearson r side check
- Outputs: Word / HTML / Excel per successful pair, charts under `outputs/figures/`

## Index

| pair | n | status | latest_rho | mean | std | min | max | a | b | pearson_r | latest_minus_r |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | ok | 0.837699 | 0.655501 | 0.124782 | 0.161142 | 0.879268 | 0.023581 | 0.974449 | 0.641738 | 0.195961 |
| EURUSD-AUDUSD | 7201 | ok | 0.392502 | 0.543084 | 0.157193 | -0.165636 | 0.825794 | 0.031206 | 0.960498 | 0.556324 | -0.163822 |
| EURUSD-NZDUSD | 7186 | ok | 0.616207 | 0.533408 | 0.142468 | 0.031357 | 0.776057 | 0.022676 | 0.972641 | 0.549808 | 0.066399 |
| EURUSD-USDJPY | 7200 | ok | -0.373270 | -0.366010 | 0.200330 | -0.743699 | 0.483334 | 0.048271 | 0.930831 | -0.300952 | -0.072318 |
| EURUSD-USDCHF | 7186 | ok | -0.752457 | -0.760469 | 0.072830 | -0.945286 | 0.721349 | 0.136115 | 0.500000 | -0.749204 | -0.003254 |
| EURUSD-USDCAD | 7188 | ok | -0.628887 | -0.424951 | 0.177293 | -0.727514 | 0.199969 | 0.020367 | 0.976171 | -0.456626 | -0.172262 |
| EURUSD-EURGBP | 7183 | ok | 0.211551 | 0.412072 | 0.202772 | -0.252552 | 0.802726 | 0.024399 | 0.970579 | 0.439899 | -0.228348 |
| GBPUSD-AUDUSD | 7228 | ok | 0.504442 | 0.513203 | 0.165140 | 0.003502 | 0.787392 | 0.017183 | 0.980953 | 0.539048 | -0.034606 |
| GBPUSD-NZDUSD | 7203 | ok | 0.667040 | 0.502909 | 0.172573 | 0.057612 | 0.806951 | 0.021226 | 0.977008 | 0.530079 | 0.136961 |
| GBPUSD-USDJPY | 7200 | ok | -0.400230 | -0.272957 | 0.197105 | -0.659121 | 0.470469 | 0.026275 | 0.966438 | -0.198556 | -0.201675 |
| GBPUSD-USDCHF | 7201 | ok | -0.677422 | -0.537985 | 0.136128 | -0.822327 | -0.098798 | 0.007399 | 0.991601 | -0.486083 | -0.191339 |
| GBPUSD-USDCAD | 7205 | ok | -0.588185 | -0.409156 | 0.167576 | -0.706443 | 0.124686 | 0.014757 | 0.982838 | -0.456462 | -0.131722 |
| GBPUSD-EURGBP | 7199 | ok | -0.370867 | -0.358343 | 0.221201 | -0.877857 | 0.240613 | 0.024752 | 0.972137 | -0.397845 | 0.026978 |
| AUDUSD-NZDUSD | 7202 | ok | 0.616507 | 0.808094 | 0.077842 | 0.482230 | 0.939268 | 0.021076 | 0.975685 | 0.828722 | -0.212214 |
| AUDUSD-USDJPY | 7199 | ok | -0.151274 | -0.225422 | 0.259844 | -0.748245 | 0.671802 | 0.060899 | 0.916242 | -0.088151 | -0.063123 |
| AUDUSD-USDCHF | 7200 | ok | -0.121291 | -0.419801 | 0.155770 | -0.764877 | 0.296659 | 0.049570 | 0.924292 | -0.380878 | 0.259587 |
| AUDUSD-USDCAD | 7204 | ok | -0.512381 | -0.602029 | 0.136283 | -0.853655 | -0.030701 | 0.016345 | 0.981495 | -0.647362 | 0.134980 |
| AUDUSD-EURGBP | 7198 | ok | -0.064511 | 0.039847 | 0.160489 | -0.354799 | 0.474148 | 0.012170 | 0.984730 | 0.038173 | -0.102684 |
| NZDUSD-USDJPY | 7185 | ok | -0.194392 | -0.239282 | 0.225947 | -0.675299 | 0.678229 | 0.041274 | 0.941046 | -0.133568 | -0.060824 |
| NZDUSD-USDCHF | 7185 | ok | -0.321299 | -0.423579 | 0.148824 | -0.745854 | 0.209908 | 0.049086 | 0.926231 | -0.393600 | 0.072301 |
| NZDUSD-USDCAD | 7190 | ok | -0.508162 | -0.542292 | 0.134957 | -0.815884 | -0.093664 | 0.015037 | 0.983083 | -0.587831 | 0.079669 |
| NZDUSD-EURGBP | 7183 | ok | -0.114054 | 0.033447 | 0.147222 | -0.299880 | 0.413272 | 0.009358 | 0.988547 | 0.037186 | -0.151241 |
| USDJPY-USDCHF | 7185 | ok | 0.473808 | 0.451435 | 0.188768 | -0.423904 | 0.863717 | 0.079012 | 0.885271 | 0.399461 | 0.074348 |
| USDJPY-USDCAD | 7186 | ok | 0.325417 | 0.113741 | 0.203852 | -0.595892 | 0.573547 | 0.031080 | 0.957040 | 0.027603 | 0.297814 |
| USDJPY-EURGBP | 7181 | ok | -0.005926 | -0.111412 | 0.114947 | -0.493168 | 0.302744 | 0.013085 | 0.979315 | -0.127992 | 0.122066 |
| USDCHF-USDCAD | 7188 | ok | 0.581011 | 0.324376 | 0.186387 | -0.295819 | 0.705355 | 0.020250 | 0.977974 | 0.304665 | 0.276345 |
| USDCHF-EURGBP | 7182 | ok | -0.061088 | -0.308574 | 0.172066 | -0.724757 | 0.469067 | 0.046236 | 0.926142 | -0.325886 | 0.264798 |
| USDCAD-EURGBP | 7185 | ok | 0.016929 | -0.022145 | 0.136160 | -0.349655 | 0.296535 | 0.008672 | 0.989217 | -0.014622 | 0.031551 |

## Cross-pair conclusion

Reading of the successful-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest positive latest DCC rho: EURUSD-GBPUSD (latest_rho=0.8377, n=7202).
Strongest negative latest DCC rho: EURUSD-USDCHF (latest_rho=-0.7525, n=7186).
Nearest-to-zero latest DCC rho: USDJPY-EURGBP (latest_rho=-0.0059); USDCAD-EURGBP (latest_rho=0.0169); USDCHF-EURGBP (latest_rho=-0.0611).
Largest |latest rho minus Pearson r| gaps: USDJPY-USDCAD (gap=0.2978, latest_rho=0.3254, r=0.0276); USDCHF-USDCAD (gap=0.2763, latest_rho=0.5810, r=0.3047); USDCHF-EURGBP (gap=0.2648, latest_rho=-0.0611, r=-0.3259). A large gap can flag a recent conditional regime versus the full-sample mean; inspect that pair's DCC path before treating either score as settled.

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
