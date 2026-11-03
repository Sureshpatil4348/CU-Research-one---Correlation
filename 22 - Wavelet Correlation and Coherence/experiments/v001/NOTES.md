# Wavelet correlation and coherence experiments v001

## Research question

For each unordered pair among the eight majors, what is the Morlet wavelet correlation of matched daily log returns of close at pre-specified periods {5, 21, 63} trading days on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Wavelet: morl; center freq=0.8125; scale = 0.8125 * period; periods=[5, 21, 63]
- Statistic: rho_wavelet(s) (headline period=21); mean R^2(s,t) with Gaussian time smoothing and edge cone mask; Pearson r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks (matched_rows + scales), charts under `outputs/figures/`

## Index

| pair | n | rho_p5 | mean_r2_p5 | rho_p21 | mean_r2_p21 | rho_p63 | mean_r2_p63 | pearson_r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 0.614073 | 0.536340 | 0.607533 | 0.591301 | 0.624259 | 0.582412 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 0.549154 | 0.490660 | 0.556184 | 0.531061 | 0.611014 | 0.517295 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 0.549130 | 0.486258 | 0.521670 | 0.528227 | 0.639244 | 0.548524 | 0.549808 |
| EURUSD-USDJPY | 7200 | -0.299265 | 0.413804 | -0.324879 | 0.471324 | -0.215574 | 0.465501 | -0.300952 |
| EURUSD-USDCHF | 7186 | -0.709532 | 0.721576 | -0.788368 | 0.758378 | -0.784577 | 0.669525 | -0.749204 |
| EURUSD-USDCAD | 7188 | -0.433917 | 0.424645 | -0.376962 | 0.490490 | -0.486371 | 0.518410 | -0.456626 |
| EURUSD-EURGBP | 7183 | 0.472414 | 0.435597 | 0.467915 | 0.485803 | 0.438741 | 0.417629 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 0.510158 | 0.478304 | 0.565811 | 0.547480 | 0.501278 | 0.509647 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 0.482507 | 0.459869 | 0.536083 | 0.521910 | 0.532490 | 0.515742 | 0.530079 |
| GBPUSD-USDJPY | 7200 | -0.199259 | 0.377461 | -0.169489 | 0.433545 | -0.122670 | 0.458469 | -0.198556 |
| GBPUSD-USDCHF | 7201 | -0.464536 | 0.478198 | -0.485139 | 0.546727 | -0.544498 | 0.505131 | -0.486083 |
| GBPUSD-USDCAD | 7205 | -0.445389 | 0.426110 | -0.420099 | 0.454821 | -0.487197 | 0.457538 | -0.456462 |
| GBPUSD-EURGBP | 7199 | -0.398413 | 0.423423 | -0.413209 | 0.493569 | -0.423773 | 0.496272 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 0.821906 | 0.676228 | 0.836045 | 0.706979 | 0.833487 | 0.644639 | 0.828722 |
| AUDUSD-USDJPY | 7199 | -0.126932 | 0.388521 | -0.137738 | 0.458791 | -0.227028 | 0.477529 | -0.088151 |
| AUDUSD-USDCHF | 7200 | -0.374673 | 0.439173 | -0.419850 | 0.501445 | -0.522739 | 0.463557 | -0.380878 |
| AUDUSD-USDCAD | 7204 | -0.626673 | 0.505820 | -0.669448 | 0.586574 | -0.683812 | 0.604982 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 0.078381 | 0.366476 | -0.001904 | 0.412938 | 0.139580 | 0.415079 | 0.038173 |
| NZDUSD-USDJPY | 7185 | -0.165040 | 0.389804 | -0.194668 | 0.446007 | -0.172648 | 0.473047 | -0.133568 |
| NZDUSD-USDCHF | 7185 | -0.393504 | 0.444227 | -0.389922 | 0.484599 | -0.527391 | 0.493896 | -0.393600 |
| NZDUSD-USDCAD | 7190 | -0.555464 | 0.470632 | -0.625030 | 0.531536 | -0.578707 | 0.564109 | -0.587831 |
| NZDUSD-EURGBP | 7183 | 0.097169 | 0.363399 | -0.013288 | 0.431910 | 0.127077 | 0.368218 | 0.037186 |
| USDJPY-USDCHF | 7185 | 0.377641 | 0.430286 | 0.332917 | 0.474524 | 0.325455 | 0.455409 | 0.399461 |
| USDJPY-USDCAD | 7186 | 0.046669 | 0.361223 | 0.076954 | 0.415268 | 0.095129 | 0.477109 | 0.027603 |
| USDJPY-EURGBP | 7181 | -0.129025 | 0.350084 | -0.180665 | 0.457748 | -0.115098 | 0.415808 | -0.127992 |
| USDCHF-USDCAD | 7188 | 0.309275 | 0.387987 | 0.257108 | 0.449325 | 0.384246 | 0.487039 | 0.304665 |
| USDCHF-EURGBP | 7182 | -0.301573 | 0.400132 | -0.362994 | 0.468947 | -0.277976 | 0.373502 | -0.325886 |
| USDCAD-EURGBP | 7185 | -0.009974 | 0.350941 | 0.039320 | 0.380379 | 0.004889 | 0.415694 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index at pre-specified rho_wavelet for period=21 trading days. Not a 29th pair analysis and not a trading signal.

Strongest positive: AUDUSD-NZDUSD (rho=0.8360).
Strongest negative: EURUSD-USDCHF (rho=-0.7884).
Nearest-to-zero: AUDUSD-EURGBP (rho=-0.0019); NZDUSD-EURGBP (rho=-0.0133); USDCAD-EURGBP (rho=0.0393).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
