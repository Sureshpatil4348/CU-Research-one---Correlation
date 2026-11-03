# Transfer entropy experiments v001

## Research question

For each unordered pair among the eight majors, does the past of one leg's binned daily log returns add information about the next bin of the other beyond own past, on the Alpari D1 history?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Server: Alpari-MT5 (login 245089294)
- maxbars: 100000000
- Broker suffix: `_i`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Series: daily log return of close, quote direction unchanged
- Discretization: B=5 equal-frequency bins per leg; lag k=m=1
- Statistic: discrete TE in nats both directions; Pearson r as a side check
- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel workbooks, charts under `outputs/figures/`

## Index

| pair | n | n_te | te_L_to_R | te_R_to_L | pearson_r |
| --- | ---: | ---: | ---: | ---: | ---: |
| EURUSD-GBPUSD | 7202 | 7201 | 0.007934 | 0.007042 | 0.641738 |
| EURUSD-AUDUSD | 7201 | 7200 | 0.008867 | 0.006338 | 0.556324 |
| EURUSD-NZDUSD | 7186 | 7185 | 0.007482 | 0.006893 | 0.549808 |
| EURUSD-USDJPY | 7200 | 7199 | 0.009399 | 0.006143 | -0.300952 |
| EURUSD-USDCHF | 7186 | 7185 | 0.007769 | 0.006928 | -0.749204 |
| EURUSD-USDCAD | 7188 | 7187 | 0.007747 | 0.004233 | -0.456626 |
| EURUSD-EURGBP | 7183 | 7182 | 0.007266 | 0.006029 | 0.439899 |
| GBPUSD-AUDUSD | 7228 | 7227 | 0.006526 | 0.006059 | 0.539048 |
| GBPUSD-NZDUSD | 7203 | 7202 | 0.005698 | 0.007882 | 0.530079 |
| GBPUSD-USDJPY | 7200 | 7199 | 0.007068 | 0.006258 | -0.198556 |
| GBPUSD-USDCHF | 7201 | 7200 | 0.006730 | 0.005479 | -0.486083 |
| GBPUSD-USDCAD | 7205 | 7204 | 0.005464 | 0.006203 | -0.456462 |
| GBPUSD-EURGBP | 7199 | 7198 | 0.007090 | 0.005638 | -0.397845 |
| AUDUSD-NZDUSD | 7202 | 7201 | 0.006756 | 0.008001 | 0.828722 |
| AUDUSD-USDJPY | 7199 | 7198 | 0.008041 | 0.009107 | -0.088151 |
| AUDUSD-USDCHF | 7200 | 7199 | 0.007871 | 0.007526 | -0.380878 |
| AUDUSD-USDCAD | 7204 | 7203 | 0.006159 | 0.005861 | -0.647362 |
| AUDUSD-EURGBP | 7198 | 7197 | 0.008449 | 0.006674 | 0.038173 |
| NZDUSD-USDJPY | 7185 | 7184 | 0.007224 | 0.009182 | -0.133568 |
| NZDUSD-USDCHF | 7185 | 7184 | 0.007344 | 0.005881 | -0.393600 |
| NZDUSD-USDCAD | 7190 | 7189 | 0.006133 | 0.007361 | -0.587831 |
| NZDUSD-EURGBP | 7183 | 7182 | 0.006837 | 0.006626 | 0.037186 |
| USDJPY-USDCHF | 7185 | 7184 | 0.006426 | 0.008855 | 0.399461 |
| USDJPY-USDCAD | 7186 | 7185 | 0.006938 | 0.004685 | 0.027603 |
| USDJPY-EURGBP | 7181 | 7180 | 0.005544 | 0.006838 | -0.127992 |
| USDCHF-USDCAD | 7188 | 7187 | 0.007190 | 0.007234 | 0.304665 |
| USDCHF-EURGBP | 7182 | 7181 | 0.008062 | 0.007796 | -0.325886 |
| USDCAD-EURGBP | 7185 | 7184 | 0.009121 | 0.008757 | -0.014622 |

## Cross-pair conclusion

Reading of the 28-pair index (56 directed TE scores). Not a 29th pair analysis and not a trading signal.

Strongest directed TE: EURUSD->USDJPY (TE=0.009399 nats).
Nearest-to-zero directed TE: USDCAD->EURUSD (TE=0.004233); USDCAD->USDJPY (TE=0.004685); GBPUSD->USDCAD (TE=0.005464).

This NOTES.md is the index plus the cross-pair reading above. It is not a 29th pair analysis.
