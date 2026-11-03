# Spectral coherence experiments v001

## Research question

For each unordered pair among the eight majors, what is the Welch magnitude-squared coherence of matched daily log returns of close at pre-specified frequency bins nearest f in {1/5, 1/21, 1/63} on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Welch: fs=1.0, nperseg=256, noverlap=128, window=hann, detrend=constant
- Statistic: gamma^2 at bins nearest 1/5 (headline), 1/21, 1/63; mean gamma^2; phase at 1/5; Pearson r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks (matched_rows + coherence), charts under `outputs/figures/`

## Index

| pair | n | gamma2_p5 | phase_p5 | gamma2_p21 | gamma2_p63 | mean_gamma2 | pearson_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.343395 | 0.152792 | 0.353928 | 0.427611 | 0.426530 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 0.396112 | 0.206291 | 0.360610 | 0.402833 | 0.337457 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 0.446199 | 0.022085 | 0.263873 | 0.463681 | 0.327776 | 0.549808 |
| EURUSD-USDJPY | 7200 | 0.138813 | 2.699202 | 0.156942 | 0.053608 | 0.115687 | -0.300952 |
| EURUSD-USDCHF | 7186 | 0.541320 | 2.940848 | 0.701503 | 0.611767 | 0.569590 | -0.749204 |
| EURUSD-USDCAD | 7188 | 0.169411 | -2.745905 | 0.079752 | 0.235771 | 0.229684 | -0.456626 |
| EURUSD-EURGBP | 7183 | 0.106148 | -0.294591 | 0.274736 | 0.244662 | 0.208524 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 0.313920 | 0.174201 | 0.378064 | 0.294951 | 0.316287 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 0.195704 | -0.059550 | 0.338329 | 0.334047 | 0.302741 | 0.530079 |
| GBPUSD-USDJPY | 7200 | 0.069672 | 2.283568 | 0.028496 | 0.041409 | 0.063201 | -0.198556 |
| GBPUSD-USDCHF | 7201 | 0.251884 | 2.654751 | 0.286589 | 0.351789 | 0.261682 | -0.486083 |
| GBPUSD-USDCAD | 7205 | 0.221322 | -2.954995 | 0.201167 | 0.257345 | 0.237189 | -0.456462 |
| GBPUSD-EURGBP | 7199 | 0.373158 | -2.946494 | 0.130619 | 0.184809 | 0.178790 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 0.672850 | -0.207142 | 0.696488 | 0.698663 | 0.696966 | 0.828722 |
| AUDUSD-USDJPY | 7199 | 0.060073 | 2.040487 | 0.034529 | 0.076238 | 0.037372 | -0.088151 |
| AUDUSD-USDCHF | 7200 | 0.077791 | 2.445277 | 0.278876 | 0.330602 | 0.179845 | -0.380878 |
| AUDUSD-USDCAD | 7204 | 0.371376 | 3.119776 | 0.487028 | 0.460426 | 0.437711 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 0.003754 | -1.310955 | 0.036596 | 0.037033 | 0.034149 | 0.038173 |
| NZDUSD-USDJPY | 7185 | 0.118937 | 2.506322 | 0.066912 | 0.037278 | 0.045845 | -0.133568 |
| NZDUSD-USDCHF | 7185 | 0.176738 | 2.833808 | 0.204246 | 0.323452 | 0.184311 | -0.393600 |
| NZDUSD-USDCAD | 7190 | 0.222825 | -2.935569 | 0.420405 | 0.340483 | 0.353694 | -0.587831 |
| NZDUSD-EURGBP | 7183 | 0.011946 | 0.417536 | 0.002260 | 0.109677 | 0.030789 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.225611 | 0.104061 | 0.141938 | 0.124486 | 0.181330 | 0.399461 |
| USDJPY-USDCAD | 7186 | 0.014205 | 1.787786 | 0.001481 | 0.007337 | 0.027188 | 0.027603 |
| USDJPY-EURGBP | 7181 | 0.019296 | 2.538198 | 0.106748 | 0.038089 | 0.043805 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.115453 | 0.624490 | 0.051186 | 0.161992 | 0.120846 | 0.304665 |
| USDCHF-EURGBP | 7182 | 0.069904 | 2.450367 | 0.189118 | 0.138420 | 0.124637 | -0.325886 |
| USDCAD-EURGBP | 7185 | 0.038620 | 0.598725 | 0.045220 | 0.014078 | 0.032573 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index at pre-specified gamma^2 nearest f=1/5. Not a 29th pair analysis and not a trading signal.

Strongest gamma^2 near 1/5: AUDUSD-NZDUSD (gamma2=0.6729).
Nearest-to-zero gamma^2 near 1/5: AUDUSD-EURGBP (gamma2=0.0038); NZDUSD-EURGBP (gamma2=0.0119); USDJPY-USDCAD (gamma2=0.0142).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
