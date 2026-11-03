# Asymmetric DCC experiments v001

## Research question

For each unordered pair among the eight majors, what is the asymmetric DCC correlation path of matched daily log returns of close on the Alpari D1 history after constant-mean GARCH(1,1) standardisation, and how does it differ from nested symmetric DCC?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Marginal model: constant-mean GARCH(1,1) via arch (percent scale for fitting; z = resid/sigma)
- ADCC: Cappiello-Engle-Sheppard form with A=(1-a-b)Q_bar - g N_bar; n=min(z,0); constraints a,b,g>=0 and a+b+g/2<1
- Nested DCC: same z path with g=0
- Burn-in=60; headline = latest ADCC rho; Pearson r and nested DCC as side checks
- Outputs: Word / HTML / Excel per successful pair, charts under `outputs/figures/`

## Index

| pair | n | status | latest_adcc | latest_dcc | a | b | g | mean | std | pearson_r | adcc_minus_r | adcc_minus_dcc |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | ok | 0.838990 | 0.837699 | 0.023020 | 0.974614 | 0.001110 | 0.655551 | 0.124745 | 0.641738 | 0.197252 | 0.001292 |
| EURUSD-AUDUSD | 7201 | ok | 0.392502 | 0.392502 | 0.031206 | 0.960498 | 0.000000 | 0.543084 | 0.157193 | 0.556324 | -0.163822 | -0.000000 |
| EURUSD-NZDUSD | 7186 | ok | 0.616207 | 0.616207 | 0.022676 | 0.972641 | 0.000000 | 0.533408 | 0.142468 | 0.549808 | 0.066399 | -0.000000 |
| EURUSD-USDJPY | 7200 | ok | -0.390918 | -0.373270 | 0.056516 | 0.896400 | 0.035173 | -0.378665 | 0.200483 | -0.300952 | -0.089966 | -0.017649 |
| EURUSD-USDCHF | 7186 | ok | -0.752457 | -0.752457 | 0.136115 | 0.500000 | 0.000000 | -0.760469 | 0.072830 | -0.749204 | -0.003254 | -0.000000 |
| EURUSD-USDCAD | 7188 | ok | -0.628887 | -0.628887 | 0.020367 | 0.976171 | 0.000000 | -0.424951 | 0.177293 | -0.456626 | -0.172262 | -0.000000 |
| EURUSD-EURGBP | 7183 | ok | 0.211551 | 0.211551 | 0.024399 | 0.970579 | 0.000000 | 0.412072 | 0.202772 | 0.439899 | -0.228348 | -0.000000 |
| GBPUSD-AUDUSD | 7228 | ok | 0.504442 | 0.504442 | 0.017183 | 0.980953 | 0.000000 | 0.513203 | 0.165140 | 0.539048 | -0.034606 | 0.000000 |
| GBPUSD-NZDUSD | 7203 | ok | 0.669427 | 0.667040 | 0.018184 | 0.978015 | 0.005602 | 0.501956 | 0.172141 | 0.530079 | 0.139348 | 0.002387 |
| GBPUSD-USDJPY | 7200 | ok | -0.421207 | -0.400230 | 0.029079 | 0.952576 | 0.016831 | -0.281857 | 0.194587 | -0.198556 | -0.222651 | -0.020977 |
| GBPUSD-USDCHF | 7201 | ok | -0.681545 | -0.677422 | 0.007461 | 0.991681 | 0.000020 | -0.538762 | 0.138332 | -0.486083 | -0.195462 | -0.004123 |
| GBPUSD-USDCAD | 7205 | ok | -0.594171 | -0.588185 | 0.014822 | 0.982587 | 0.001036 | -0.409339 | 0.167792 | -0.456462 | -0.137709 | -0.005986 |
| GBPUSD-EURGBP | 7199 | ok | -0.370867 | -0.370867 | 0.024752 | 0.972137 | 0.000000 | -0.358343 | 0.221201 | -0.397845 | 0.026978 | -0.000000 |
| AUDUSD-NZDUSD | 7202 | ok | 0.616753 | 0.616507 | 0.021000 | 0.975711 | 0.000119 | 0.808086 | 0.077844 | 0.828722 | -0.211969 | 0.000245 |
| AUDUSD-USDJPY | 7199 | ok | -0.229616 | -0.151274 | 0.054591 | 0.902108 | 0.042052 | -0.246810 | 0.262406 | -0.088151 | -0.141465 | -0.078342 |
| AUDUSD-USDCHF | 7200 | ok | -0.121292 | -0.121291 | 0.049570 | 0.924292 | 0.000000 | -0.419801 | 0.155770 | -0.380878 | 0.259587 | -0.000000 |
| AUDUSD-USDCAD | 7204 | ok | -0.512381 | -0.512381 | 0.016345 | 0.981495 | 0.000000 | -0.602029 | 0.136283 | -0.647362 | 0.134980 | -0.000000 |
| AUDUSD-EURGBP | 7198 | ok | -0.064510 | -0.064511 | 0.012170 | 0.984730 | 0.000000 | 0.039847 | 0.160489 | 0.038173 | -0.102684 | 0.000000 |
| NZDUSD-USDJPY | 7185 | ok | -0.189283 | -0.194392 | 0.043157 | 0.915926 | 0.037462 | -0.257188 | 0.228991 | -0.133568 | -0.055715 | 0.005109 |
| NZDUSD-USDCHF | 7185 | ok | -0.321299 | -0.321299 | 0.049086 | 0.926231 | 0.000000 | -0.423579 | 0.148824 | -0.393600 | 0.072301 | 0.000000 |
| NZDUSD-USDCAD | 7190 | ok | -0.508162 | -0.508162 | 0.015037 | 0.983083 | 0.000000 | -0.542292 | 0.134957 | -0.587831 | 0.079669 | -0.000000 |
| NZDUSD-EURGBP | 7183 | ok | -0.114065 | -0.114054 | 0.009356 | 0.988547 | 0.000005 | 0.033446 | 0.147222 | 0.037186 | -0.151252 | -0.000011 |
| USDJPY-USDCHF | 7185 | ok | 0.473808 | 0.473808 | 0.079012 | 0.885271 | 0.000000 | 0.451435 | 0.188768 | 0.399461 | 0.074348 | -0.000000 |
| USDJPY-USDCAD | 7186 | ok | 0.325417 | 0.325417 | 0.031080 | 0.957040 | 0.000000 | 0.113741 | 0.203852 | 0.027603 | 0.297814 | -0.000000 |
| USDJPY-EURGBP | 7181 | ok | -0.005926 | -0.005926 | 0.013085 | 0.979315 | 0.000000 | -0.111412 | 0.114948 | -0.127992 | 0.122067 | 0.000000 |
| USDCHF-USDCAD | 7188 | ok | 0.523387 | 0.581011 | 0.007073 | 0.968277 | 0.047300 | 0.343939 | 0.178818 | 0.304665 | 0.218722 | -0.057623 |
| USDCHF-EURGBP | 7182 | ok | -0.061088 | -0.061088 | 0.046236 | 0.926142 | 0.000000 | -0.308574 | 0.172066 | -0.325886 | 0.264798 | -0.000000 |
| USDCAD-EURGBP | 7185 | ok | 0.012785 | 0.016929 | 0.008267 | 0.988966 | 0.003299 | -0.021606 | 0.136313 | -0.014622 | 0.027407 | -0.004144 |

## Cross-pair conclusion

Reading of the successful-pair index only. Not a 29th pair analysis and not a trading signal.

Strongest positive latest ADCC rho: EURUSD-GBPUSD (latest_adcc=0.8390, n=7202).
Strongest negative latest ADCC rho: EURUSD-USDCHF (latest_adcc=-0.7525, n=7186).
Nearest-to-zero latest ADCC rho: USDJPY-EURGBP (latest_adcc=-0.0059); USDCAD-EURGBP (latest_adcc=0.0128); USDCHF-EURGBP (latest_adcc=-0.0611).
Largest |ADCC minus Pearson r| gaps: USDJPY-USDCAD (gap=0.2978, latest_adcc=0.3254, r=0.0276); USDCHF-EURGBP (gap=0.2648, latest_adcc=-0.0611, r=-0.3259); AUDUSD-USDCHF (gap=0.2596, latest_adcc=-0.1213, r=-0.3809).
Largest |ADCC minus nested DCC| gaps: AUDUSD-USDJPY (gap=-0.0783, adcc=-0.2296, dcc=-0.1513, g=0.0421); USDCHF-USDCAD (gap=-0.0576, adcc=0.5234, dcc=0.5810, g=0.0473); GBPUSD-USDJPY (gap=-0.0210, adcc=-0.4212, dcc=-0.4002, g=0.0168). A large ADCC-DCC gap can flag an active asymmetric term; inspect g and the stress periods on that pair's chart before treating either path as settled.

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
