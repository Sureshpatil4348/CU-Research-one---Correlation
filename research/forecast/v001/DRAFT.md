# Draft: which dependence measure warns before stress?

On this frozen majors panel, no shortlist measure improves next-20-day stress forecasts versus rolling Pearson, out of sample, after Benjamini-Hochberg control.

T1 winner under the frozen rule: none.

The test is the frozen protocol in `PROTOCOL.md`. v001 was not overwritten. The catalogue of the 28 full-sample methods remains [reports/Correlation_Methods_28_Pages.pdf](../../../reports/Correlation_Methods_28_Pages.pdf).

## 1. Did the features use only time-t information?

Yes. Each feature row is dated t and uses returns on or before t. Training labels are embargoed by 20 trading days, so a label whose window runs through t+20 is not used to fit a model that is scored on that window. ADCC parameters are refit at each year-end and are not revised backward. The 90th percentile for the stress label uses only forward windows that have already ended.

## 2. Did any measure beat rolling Pearson?

Primary baseline Brier score on T1: 0.0879 (n=5836). A negative Brier gap means a lower Brier score than `baseline_r20`. `beats_baseline` is true only when that gap is negative and the Benjamini-Hochberg q-value is below 0.05.

### T1 stress

| feature | role | n | brier | auc | brier_minus_baseline | dm_p_one_sided | bh_q | in_mcs | beats_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_r20 | baseline | 5836 | 0.0879 | 0.6701 | 0.0000 | n/a | n/a | yes | False |
| baseline_abs_gap | second_baseline | 5836 | 0.0930 | 0.5988 | 0.0051 | 0.9850 | n/a |  | False |
| m01_expanding_r | competitor | 5836 | 0.0940 | 0.5792 | 0.0061 | 0.9938 | 0.9953 | yes | False |
| m07_rho_partial | competitor | 5836 | 0.0926 | 0.6631 | 0.0047 | 0.8659 | 0.9953 | yes | False |
| m10_adcc_minus_r | competitor | 5080 | 0.0843 | 0.6895 | -0.0013 | 0.3106 | 0.9953 | yes | False |
| m11_adj_gap | competitor | 4287 | 0.1078 | 0.5128 | 0.0085 | 0.9639 | 0.9953 | yes | False |
| m19_excess_lower | competitor | 5836 | 0.0901 | 0.6806 | 0.0022 | 0.7715 | 0.9953 | yes | False |
| m14_dcor | competitor | 5836 | 0.0947 | 0.5119 | 0.0068 | 0.9953 | 0.9953 | yes | False |
| m28_d_ij | competitor | 5836 | 0.0866 | 0.6775 | -0.0013 | 0.3917 | 0.9953 | yes | False |
| m28_pc1_share | competitor | 5836 | 0.0941 | 0.5254 | 0.0062 | 0.9891 | 0.9953 | yes | False |
| m28_tci | competitor | 5836 | 0.0950 | 0.4827 | 0.0071 | 0.9926 | 0.9953 | yes | False |
| diagnostic_rv20 | diagnostic | 5836 | 0.0643 | 0.8646 | -0.0237 | 0.0011 | n/a |  | False |

### T2 correlation break (secondary)

| feature | role | n | brier | auc | brier_minus_baseline | dm_p_one_sided | bh_q | in_mcs | beats_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_r20 | baseline | 5856 | 0.2026 | 0.5125 | 0.0000 | n/a | n/a | no | False |
| baseline_abs_gap | second_baseline | 5856 | 0.1929 | 0.6286 | -0.0097 | 0.0000 | n/a |  | False |
| m01_expanding_r | competitor | 5856 | 0.2030 | 0.4812 | 0.0004 | 1.0000 | 1.0000 | no | False |
| m07_rho_partial | competitor | 5856 | 0.2031 | 0.4867 | 0.0005 | 1.0000 | 1.0000 | no | False |
| m10_adcc_minus_r | competitor | 5079 | 0.2018 | 0.5249 | -0.0003 | 0.1657 | 0.2983 | no | False |
| m11_adj_gap | competitor | 4307 | 0.2046 | 0.5154 | 0.0004 | 0.9661 | 1.0000 | no | False |
| m19_excess_lower | competitor | 5856 | 0.2028 | 0.5136 | 0.0002 | 0.7721 | 1.0000 | no | False |
| m14_dcor | competitor | 5856 | 0.1957 | 0.6239 | -0.0070 | 0.0000 | 0.0000 | yes | True |
| m28_d_ij | competitor | 5856 | 0.1943 | 0.5211 | -0.0083 | 0.0000 | 0.0000 | yes | True |
| m28_pc1_share | competitor | 5856 | 0.1957 | 0.5108 | -0.0069 | 0.0000 | 0.0000 | yes | True |
| m28_tci | competitor | 5856 | 0.1957 | 0.4937 | -0.0069 | 0.0000 | 0.0000 | yes | True |

Secondary T2 features with a lower Brier score and BH q below 0.05: `m14_dcor`, `m28_d_ij`, `m28_pc1_share`, `m28_tci`. That target is not the primary horse race, and it does not name a T1 winner.

The model confidence set is the 90% Hansen set on day-level Brier losses. `diagnostic_rv20` is lagged realised volatility. It is not in the horse race.

## 3. Were the many tests controlled?

Yes for the horse race. There are nine pre-registered competitors. Diebold-Mariano p-values are one-sided for a lower Brier score, with Newey-West lag 20, then Benjamini-Hochberg at 0.05. The confidence set uses a block bootstrap of length 20 and 400 draws. Cointegration, transfer entropy, and the ADCC likelihood-ratio tests in the v002 experiments have their own multiplicity or boundary corrections, and those tables are not re-opened here.

## 4. Did the signal work before 2008 and 2020, or only inside the crash?

Hit rate is the share of the 20 trading days before a shade with the signal on. A signal that appears only inside the shade is not an early warning. In-shade rate is reported separately. False-alarm rate is the share of out-of-sample days outside every shade and every pre-window. The table is the rolling-Pearson T1 signal, because that rule is the one the protocol keeps when no competitor wins.

### T1 signals

| feature | window | n_pre | hit_rate | n_shade | in_shade_rate | false_alarm_rate |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_r20 | GFC | 20 | 0.3500 | 139 | 0.4820 | 0.1287 |
| baseline_r20 | SNB_floor | 20 | 1.0000 | 869 | 0.0483 | 0.1287 |
| baseline_r20 | SNB_removal | 20 | 0.0000 | 1 | 0.0000 | 0.1287 |
| baseline_r20 | COVID | 20 | 0.0000 | 29 | 0.0000 | 0.1287 |
| baseline_r20 | Y2022 | 20 | 0.2000 | 195 | 0.1744 | 0.1287 |

### T1 Brier score through 2007

| feature | n | brier | brier_minus_baseline |
| --- | --- | --- | --- |
| baseline_r20 | 979 | 0.1122 | 0.0000 |
| diagnostic_rv20 | 979 | 0.0870 | -0.0252 |

### T1 Brier score from 2020

| feature | n | brier | brier_minus_baseline |
| --- | --- | --- | --- |
| baseline_r20 | 1755 | 0.0515 | 0.0000 |
| diagnostic_rv20 | 1755 | 0.0487 | -0.0028 |

Subperiod Brier scores for every feature are in `outputs/subperiods.csv`. The through-2007 slice is the out-of-sample predictions whose signal date is on or before 2007-12-31. It does not refit on later data.

## 5. Is there a simple economic use with costs?

The book is the equal-weight mean of the eight major log returns. The position for the next day is flat when the T1 signal is on, and long otherwise. The signal cut is the 80th percentile of training probabilities. Cost is 1 basis point of the absolute position change, and the book starts from flat. Net log growth is the sum of position times the next-day basket return, minus that cost.

| book | net_log_growth | n_days | cost_sum | mean_position |
| --- | --- | --- | --- | --- |
| always_long | -0.0182 | 5836 | 0.0001 | 1.0000 |
| baseline_r20 | -0.0666 | 5836 | 0.0168 | 0.8705 |

## What this draft does not claim

It does not name the day of a crash. It does not add a new dependence formula. Protocol SHA-256 recorded with the scores: `705f48a8f04150ca67ae912302cdabd0bd7630197c7cb0bc5384da6d6796b922`.

