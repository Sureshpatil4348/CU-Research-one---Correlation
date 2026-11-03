# Which data do I need to look after?

Read this after the rolling v001 run. Numbers are the **latest** rolling Pearson scores on daily log returns.

## Look at these first (short watchlist)

- **AUDUSD-NZDUSD**: baseline 0.829; latest r_20=0.263, r_60=0.607, r_100=0.706
- **EURUSD-USDCHF**: baseline -0.749; latest r_20=-0.729, r_60=-0.692, r_100=-0.755
- **AUDUSD-USDCAD**: baseline -0.647; latest r_20=-0.302, r_60=-0.526, r_100=-0.523
- **EURUSD-GBPUSD**: baseline 0.642; latest r_20=0.925, r_60=0.875, r_100=0.851
- **NZDUSD-USDCAD**: baseline -0.588; latest r_20=-0.398, r_60=-0.531, r_100=-0.564

## Also keep on a secondary board

- **EURUSD-AUDUSD**: baseline 0.556; latest r_20=-0.004, r_60=0.444, r_100=0.534
- **EURUSD-NZDUSD**: baseline 0.550; latest r_20=0.478, r_60=0.686, r_100=0.718
- **GBPUSD-AUDUSD**: baseline 0.539; latest r_20=0.053, r_60=0.443, r_100=0.529
- **GBPUSD-NZDUSD**: baseline 0.530; latest r_20=0.569, r_60=0.724, r_100=0.727
- **GBPUSD-USDCHF**: baseline -0.486; latest r_20=-0.728, r_60=-0.638, r_100=-0.703

## Short window vs baseline (possible breaks)

- **AUDUSD-NZDUSD** (Short watchlist): baseline 0.829 vs r_20=0.263 (gap 0.566)
- **EURUSD-AUDUSD** (Secondary tier): baseline 0.556 vs r_20=-0.004 (gap 0.560)
- **GBPUSD-AUDUSD** (Secondary tier): baseline 0.539 vs r_20=0.053 (gap 0.486)
- **USDJPY-USDCAD** (Low-value): baseline 0.028 vs r_20=0.487 (gap 0.460)
- **USDJPY-EURGBP** (Low-value): baseline -0.128 vs r_20=0.246 (gap 0.374)
- **AUDUSD-USDCAD** (Short watchlist): baseline -0.647 vs r_20=-0.302 (gap 0.345)
- **NZDUSD-EURGBP** (Low-value): baseline 0.037 vs r_20=-0.273 (gap 0.310)
- **EURUSD-GBPUSD** (Short watchlist): baseline 0.642 vs r_20=0.925 (gap 0.283)

## Still near zero (safe to ignore for now)

- **AUDUSD-EURGBP**: r_20=-0.142, r_60=-0.004, r_100=-0.094
- **USDCAD-EURGBP**: r_20=0.032, r_60=-0.106, r_100=0.007
- **USDJPY-EURGBP**: r_20=0.246, r_60=-0.086, r_100=0.013

## Practical monitoring order

1. Open the five short-watchlist Word files (or their last-15-row tables).
2. Each new D1 close, refresh attention on **r_20** first, then confirm with **r_60** and **r_100**.
3. Escalate only when r_20 moves far from the baseline or flips sign.
4. Leave the still-near-zero low-value pairs alone unless a short window spikes.
