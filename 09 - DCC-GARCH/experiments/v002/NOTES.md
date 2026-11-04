# DCC-GARCH experiments v002

Done: every pair has a status flag after a refit with b >= 0 removed (ok=28, check=0, fail=0).

## Research question

Do the Engle DCC parameters stay interior when the v001 lower bound b >= 0.5 is removed?

## Snapshot

- Folder: `data/snapshots/2026-11-03_majors_alpari_D1`
- Dropped unfinished last bar dated 2026-11-03 UTC after a tick-volume check against the prior complete day.

## Parameters

- Marginal model: constant-mean GARCH(1,1) via arch, fit on percent returns, z = resid/sigma.
- DCC bounds: a in [0, 0.5], b in [0, 0.999], constraint a+b < 0.999.
- v001 used b >= 0.5. That floor is removed. Starts include b = 0.50, 0.20, and 0.05.
- status ok: optimizer success. status check: a finite point that did not report success. status fail: no finite fit.
- boundary lists a, b, or a+b when the point sits on that edge. interior means none of those.
- v001 files were not edited.

## Index

| pair | n | status | success | a | b | boundary | v001_a | v001_b | nll |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EURUSD-GBPUSD | 7202 | ok | yes | 0.0235817 | 0.974448 | a+b | 0.0235811 | 0.974449 | 4951.27 |
| EURUSD-AUDUSD | 7201 | ok | yes | 0.0312067 | 0.960498 | interior | 0.0312064 | 0.960498 | 5751.65 |
| EURUSD-NZDUSD | 7186 | ok | yes | 0.022676 | 0.972641 | interior | 0.0226759 | 0.972641 | 5825.3 |
| EURUSD-USDJPY | 7200 | ok | yes | 0.0482708 | 0.930831 | interior | 0.0482709 | 0.930831 | 6470.51 |
| EURUSD-USDCHF | 7186 | ok | yes | 0.25211 | 0.00340705 | interior | 0.136115 | 0.5 | 4112.28 |
| EURUSD-USDCAD | 7188 | ok | yes | 0.0203664 | 0.976171 | interior | 0.0203666 | 0.976171 | 6282.35 |
| EURUSD-EURGBP | 7183 | ok | yes | 0.0243986 | 0.970579 | interior | 0.0243986 | 0.970579 | 6263.59 |
| GBPUSD-AUDUSD | 7228 | ok | yes | 0.0171835 | 0.980953 | a+b | 0.0171835 | 0.980953 | 5909.58 |
| GBPUSD-NZDUSD | 7203 | ok | yes | 0.0212264 | 0.977008 | a+b | 0.0212264 | 0.977008 | 5922.42 |
| GBPUSD-USDJPY | 7200 | ok | yes | 0.0262745 | 0.966438 | interior | 0.0262745 | 0.966438 | 6757.16 |
| GBPUSD-USDCHF | 7201 | ok | yes | 0.0073993 | 0.991601 | a+b | 0.00739927 | 0.991601 | 5952.27 |
| GBPUSD-USDCAD | 7205 | ok | yes | 0.0147567 | 0.982838 | interior | 0.0147568 | 0.982838 | 6372.65 |
| GBPUSD-EURGBP | 7199 | ok | yes | 0.0247523 | 0.972137 | interior | 0.0247524 | 0.972137 | 6400.71 |
| AUDUSD-NZDUSD | 7202 | ok | yes | 0.0210762 | 0.975685 | interior | 0.0210761 | 0.975685 | 3095.57 |
| AUDUSD-USDJPY | 7199 | ok | yes | 0.0608989 | 0.916242 | interior | 0.0608989 | 0.916242 | 6728.8 |
| AUDUSD-USDCHF | 7200 | ok | yes | 0.0495707 | 0.924292 | interior | 0.0495703 | 0.924292 | 6445.04 |
| AUDUSD-USDCAD | 7204 | ok | yes | 0.0163448 | 0.981495 | interior | 0.0163452 | 0.981495 | 5352.56 |
| AUDUSD-EURGBP | 7198 | ok | yes | 0.0121698 | 0.98473 | interior | 0.0121698 | 0.98473 | 7093.31 |
| NZDUSD-USDJPY | 7185 | ok | yes | 0.0412742 | 0.941046 | interior | 0.0412742 | 0.941046 | 6741.78 |
| NZDUSD-USDCHF | 7185 | ok | yes | 0.0490861 | 0.92623 | interior | 0.0490861 | 0.926231 | 6428.47 |
| NZDUSD-USDCAD | 7190 | ok | yes | 0.0150372 | 0.983083 | a+b | 0.0150372 | 0.983083 | 5763.27 |
| NZDUSD-EURGBP | 7183 | ok | yes | 0.00935805 | 0.988547 | interior | 0.00935802 | 0.988547 | 7099.54 |
| USDJPY-USDCHF | 7185 | ok | yes | 0.0790123 | 0.88527 | interior | 0.0790123 | 0.885271 | 6242.51 |
| USDJPY-USDCAD | 7186 | ok | yes | 0.0310798 | 0.95704 | interior | 0.0310798 | 0.95704 | 6971.64 |
| USDJPY-EURGBP | 7181 | ok | yes | 0.0130846 | 0.979315 | interior | 0.0130846 | 0.979315 | 7082.27 |
| USDCHF-USDCAD | 7188 | ok | yes | 0.0193038 | 0.979531 | a+b | 0.0202503 | 0.977974 | 6697.61 |
| USDCHF-EURGBP | 7182 | ok | yes | 0.0462356 | 0.926142 | interior | 0.0462356 | 0.926142 | 6751.68 |
| USDCAD-EURGBP | 7185 | ok | yes | 0.00867244 | 0.989217 | interior | 0.00867244 | 0.989217 | 7114.32 |

## Cross-pair conclusion

EURUSD-USDCHF v002 b is 0.003407 (v001 b was 0.500000), boundary=interior, status=ok.
A reported b of 0.5 in v001 was the old box constraint, not evidence of a special correlation law.
This is not a trading signal.
