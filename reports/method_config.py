"""Config for the 28 one-page method overview PDF. Text aims for ASD-STE100 style."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT = "2026-11-03_majors_alpari_D1"
INPUT_COMMON = (
    "Input: daily log return of close on matched dates from snapshot "
    f"{SNAPSHOT} (eight majors)."
)

METHODS: list[dict] = [
    {
        "num": "01",
        "folder": "01 - Pearson Correlation",
        "name": "Pearson Correlation",
        "index": "index.csv",
        "headline": "r",
        "chart": "heatmap_r",
        "question": "How strong is the linear link between two return series?",
        "what_it_is": (
            "Pearson r measures the linear co-movement of two series. "
            "A value near +1 means the returns rise and fall together on a straight line. "
            "A value near -1 means they move in opposite directions."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: one full-sample Pearson r, two-sided p, and a Fisher 95% band. "
            "Output unit: correlation in [-1, 1]."
        ),
        "you_get": "You get the average linear link over the full history for each unordered pair.",
        "you_do_not_get": "You do not get crash risk, lead-lag, or a trade signal.",
        "formula": "r = SUM((x - x_bar)(y - y_bar))\n    / sqrt( SUM((x - x_bar)^2) * SUM((y - y_bar)^2) )",
        "formula_terms": [
            ("x, y", "Daily log returns of the two FX pairs"),
            ("x_bar, y_bar", "Sample means of those returns"),
            ("r", "Full-sample linear correlation"),
        ],
        "plus": [
            "The formula is simple and fast.",
            "Many desks use this as the base measure.",
            "You can report r with a p-value and a band.",
        ],
        "minus": [
            "It finds only linear links.",
            "Outliers can move r a large amount.",
            "One full-sample r hides regime changes.",
        ],
        "use_for": ["A first screen of pair co-movement.", "A clear baseline for other methods."],
        "not_for": ["Crash risk or non-linear links.", "Lead-lag or who drives whom."],
    },
    {
        "num": "02",
        "folder": "02 - Spearman Rank Correlation",
        "name": "Spearman Rank Correlation",
        "index": "index.csv",
        "headline": "rho",
        "chart": "scatter_vs_pearson",
        "x_col": "pearson_r",
        "y_col": "rho",
        "question": "Do the ranks of the two series move together?",
        "what_it_is": (
            "Spearman correlation applies Pearson r to the ranks of the returns. "
            "It tracks monotone links. It is less sensitive to a few extreme days."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: Spearman rho on ranks, with Pearson r as a side check. "
            "Output unit: rank correlation in [-1, 1]."
        ),
        "you_get": "You get a robust monotone co-movement score for each pair.",
        "you_do_not_get": "You do not get time-varying or directional dependence.",
        "formula": "rho_s = Corr( rank(x), rank(y) )",
        "formula_terms": [
            ("rank(x)", "Order of each return in the sample"),
            ("rho_s", "Pearson correlation of the two rank series"),
        ],
        "plus": [
            "Ranks reduce the effect of extreme returns.",
            "It finds monotone links, not only linear ones.",
            "It stays close to Pearson when the link is linear.",
        ],
        "minus": [
            "It still averages the full sample.",
            "Ties need a clear rank rule.",
            "It does not show time variation.",
        ],
        "use_for": ["A robust check next to Pearson r.", "Cases with heavy tails in returns."],
        "not_for": ["Dynamic regime monitoring alone.", "Directional lead-lag claims."],
    },
    {
        "num": "03",
        "folder": "03 - Kendall Tau-b",
        "name": "Kendall Tau-b",
        "index": "index.xlsx",
        "headline": "tau_b",
        "chart": "scatter_vs_pearson",
        "x_col": "pearson_r",
        "y_col": "tau_b",
        "question": "How often do pair-of-days move in the same order?",
        "what_it_is": (
            "Kendall tau-b counts concordant and discordant day pairs. "
            "It measures rank agreement with a tie correction."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: tau-b with p-value; Pearson r as a side check. "
            "Output unit: tau-b in [-1, 1]."
        ),
        "you_get": "You get a concordance-based rank link for each pair.",
        "you_do_not_get": "You do not get a dynamic path or a crash frequency.",
        "formula": "tau_b = (C - D) / sqrt( (C + D + T_x) * (C + D + T_y) )",
        "formula_terms": [
            ("C", "Concordant day-pairs"),
            ("D", "Discordant day-pairs"),
            ("T_x, T_y", "Tie corrections on each leg"),
        ],
        "plus": [
            "It uses concordant and discordant pairs.",
            "Tau-b handles ties in a standard way.",
            "It is robust to some outliers.",
        ],
        "minus": [
            "The count grows with n squared cost.",
            "The scale differs from Pearson.",
            "It is still a static full-sample score.",
        ],
        "use_for": ["Rank agreement checks beside Spearman.", "Samples where ties appear."],
        "not_for": ["Intraday microstructure alone.", "Crash co-occurrence counts."],
    },
    {
        "num": "04",
        "folder": "04 - Robust Clipped Correlation",
        "name": "Robust Clipped Correlation",
        "index": "index.xlsx",
        "headline": "rho_02",
        "chart": "gap_bars",
        "gap_col": "rho_02_minus_r",
        "question": "What is Pearson r after you clip large returns?",
        "what_it_is": (
            "Clipped correlation caps each return at +/- c, then computes Pearson r. "
            "The cap limits the pull of jump days."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: clipped rho at c in {{0.01, 0.02, 0.03}}; headline uses c=0.02. "
            "Output unit: correlation in [-1, 1]."
        ),
        "you_get": "You get a Pearson-style score that is less driven by a few jumps.",
        "you_do_not_get": "You do not get a measure of the extremes themselves.",
        "formula": "x_tilde = min(c, max(-c, x))\ny_tilde = min(c, max(-c, y))\nrho_clip = Corr(x_tilde, y_tilde)",
        "formula_terms": [
            ("c", "Clip level (0.02 in the headline)"),
            ("x_tilde, y_tilde", "Returns after the cap"),
            ("rho_clip", "Pearson r on clipped returns"),
        ],
        "plus": [
            "Clipping limits the effect of jump days.",
            "You keep a Pearson-style scale.",
            "You can count how often the cap hits.",
        ],
        "minus": [
            "The cap c is a free parameter.",
            "Clipping can hide true crash links.",
            "It remains a static average.",
        ],
        "use_for": ["Sanity check when one day dominates r.", "Compare rho_clip with raw Pearson r."],
        "not_for": ["Tail dependence measurement.", "Cases where extremes are the signal."],
    },
    {
        "num": "05",
        "folder": "05 - Rolling Correlation",
        "name": "Rolling Correlation",
        "index": "index.csv",
        "headline": "latest_r",
        "chart": "rolling_grouped",
        "question": "How does Pearson r change in windows of 20, 60 and 100 days?",
        "what_it_is": (
            "Rolling correlation recomputes Pearson r on the last W days. "
            "It shows how the linear link changes through time."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: latest r for W in {{20, 60, 100}} on a 17-pair watchlist, "
            "plus a full-sample baseline from method 01. "
            "Output unit: correlation in [-1, 1]."
        ),
        "you_get": "You get short-horizon r paths and gaps versus the long baseline.",
        "you_do_not_get": "You do not get a volatility-adjusted or asymmetric path.",
        "formula": "rho_t^(W) = Corr( last W observations of x and y )",
        "formula_terms": [
            ("W", "Window length in trading days"),
            ("rho_t^(W)", "Pearson r on the window that ends at t"),
        ],
        "plus": [
            "It shows short-horizon breaks vs the baseline.",
            "Windows 20 / 60 / 100 are easy to read.",
            "Desks already watch rolling r.",
        ],
        "minus": [
            "Equal weights create a ghost drop at the window edge.",
            "High volatility can inflate rolling r.",
            "Short windows are noisy.",
        ],
        "use_for": ["Watchlist alerts when r_20 moves far from baseline.", "A simple time-varying screen."],
        "not_for": ["Volatility-adjusted dependence alone.", "Formal early-warning claims without tests."],
        "special": "rolling",
    },
    {
        "num": "06",
        "folder": "06 - EWMA Correlation",
        "name": "EWMA Correlation",
        "index": "index.xlsx",
        "headline": "latest_rho",
        "chart": "scatter_vs_pearson",
        "x_col": "pearson_r",
        "y_col": "latest_rho",
        "question": "What is the latest exponentially weighted correlation?",
        "what_it_is": (
            "EWMA correlation gives more weight to recent days. "
            "It updates every day without a hard window edge."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: latest EWMA rho path value; Pearson r as a side check. "
            "Output unit: correlation in [-1, 1]."
        ),
        "you_get": "You get a smooth, recent-weighted linear dependence score.",
        "you_do_not_get": "You do not get GARCH residual standardisation or crash asymmetry.",
        "formula": "c_t = lam*c_{t-1} + (1-lam)*x_t*y_t\nv_x,t = lam*v_x,t-1 + (1-lam)*x_t^2\nrho_t = c_t / sqrt(v_x,t * v_y,t)",
        "formula_terms": [
            ("lam", "Decay factor (near 0.94 in RiskMetrics style)"),
            ("c_t", "EWMA cross-product"),
            ("rho_t", "EWMA correlation at day t"),
        ],
        "plus": [
            "Recent days get more weight than old days.",
            "No hard window edge like rolling W.",
            "It updates every day with one pass.",
        ],
        "minus": [
            "Lambda is a free parameter.",
            "It does not standardise GARCH residuals.",
            "It treats up and down days the same.",
        ],
        "use_for": ["A smooth alternative to rolling Pearson.", "Daily monitoring of latest_rho vs Pearson r."],
        "not_for": ["Crash asymmetry without ADCC.", "Long-run structural levels alone."],
    },
    {
        "num": "07",
        "folder": "07 - Partial and Residual Correlation",
        "name": "Partial and Residual Correlation",
        "index": "index.xlsx",
        "headline": "rho_partial",
        "chart": "scatter_vs_pearson",
        "x_col": "pearson_r",
        "y_col": "rho_partial",
        "question": "What link remains after you remove a USD strength factor?",
        "what_it_is": (
            "Partial correlation removes a common control factor, then correlates the residuals. "
            "In this project the control is a leave-currency-out USD strength factor."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: OLS residual Pearson rho after control z; also R-squared of each leg on z. "
            "Output unit: residual correlation in [-1, 1]."
        ),
        "you_get": "You get the cross-currency link that remains after the dollar factor.",
        "you_do_not_get": "You do not get a dynamic or tail-risk measure.",
        "formula": "x = a + b*z + e_x\ny = c + d*z + e_y\nrho_partial = Corr(e_x, e_y)",
        "formula_terms": [
            ("z", "Leave-currency-out USD strength factor"),
            ("e_x, e_y", "OLS residuals after removing z"),
            ("rho_partial", "Pearson r of the residuals"),
        ],
        "plus": [
            "It strips a shared dollar factor from majors.",
            "Large gaps show fake USD-driven Pearson links.",
            "R-squared on z shows how much USD explains.",
        ],
        "minus": [
            "The control z is a model choice.",
            "Bad controls can create false residuals.",
            "It is still a static residual Pearson.",
        ],
        "use_for": ["Cross-currency links beyond the dollar.", "Checks that EUR and AUD are not only USD moves."],
        "not_for": ["Pairs with no clear common factor.", "Intraday microstructure alone."],
    },
    {
        "num": "08",
        "folder": "08 - Shrinkage Correlation",
        "name": "Shrinkage Correlation",
        "index": "index.xlsx",
        "headline": "rho_LW",
        "chart": "scatter_vs_pearson",
        "x_col": "pearson_r",
        "y_col": "rho_LW",
        "question": "What correlation matrix do you get after Ledoit-Wolf shrinkage?",
        "what_it_is": (
            "Shrinkage blends the sample covariance toward a simple target. "
            "It reduces noise in a correlation matrix used for portfolios or PCA."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: Ledoit-Wolf shrunk pair correlation rho_LW and intensity delta_LW. "
            "Output unit: correlation in [-1, 1]."
        ),
        "you_get": "You get a quieter pair correlation for matrix-based work.",
        "you_do_not_get": "You do not get dynamics, tails, or lead-lag.",
        "formula": "Sigma_tilde = (1 - delta)*S + delta*mu*I\nrho_ij = Sigma_tilde_ij / sqrt(Sigma_ii * Sigma_jj)",
        "formula_terms": [
            ("S", "Sample covariance"),
            ("delta", "Shrinkage intensity (Ledoit-Wolf)"),
            ("rho_ij", "Correlation from the shrunk matrix"),
        ],
        "plus": [
            "Shrinkage reduces noise in large matrices.",
            "Delta has a data-driven Ledoit-Wolf rule.",
            "It helps portfolio and PCA inputs.",
        ],
        "minus": [
            "Pair scores move toward a target.",
            "It can hide true large correlations.",
            "It does not add dynamics.",
        ],
        "use_for": ["Stable inputs to network or PCA work.", "Noise reduction when n is limited vs assets."],
        "not_for": ["Tail event frequency.", "Lead-lag prediction alone."],
    },
    {
        "num": "09",
        "folder": "09 - DCC-GARCH",
        "name": "DCC-GARCH",
        "index": "index.xlsx",
        "headline": "latest_rho",
        "chart": "scatter_vs_pearson",
        "x_col": "pearson_r",
        "y_col": "latest_rho",
        "question": "How does correlation evolve after GARCH standardisation?",
        "what_it_is": (
            "DCC-GARCH first filters each return with GARCH volatility. "
            "It then builds a dynamic correlation path on the standardised residuals."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: latest DCC rho after constant-mean GARCH(1,1) z-scores. "
            "Output unit: dynamic correlation in [-1, 1]."
        ),
        "you_get": "You get a vol-filtered, time-varying linear correlation.",
        "you_do_not_get": "You do not get downside asymmetry (that needs ADCC).",
        "formula": "z_i,t = eps_i,t / sigma_i,t\nq_ij,t = (1-a-b)*q_bar + a*z_i,t-1*z_j,t-1 + b*q_ij,t-1\nrho_ij,t = q_ij,t / sqrt(q_ii,t * q_jj,t)",
        "formula_terms": [
            ("z_i,t", "GARCH-standardised residual"),
            ("a, b", "News and persistence weights"),
            ("rho_ij,t", "Dynamic conditional correlation"),
        ],
        "plus": [
            "It removes volatility clustering before correlation.",
            "Correlation updates every day.",
            "a and b give persistence of the path.",
        ],
        "minus": [
            "Fits can fail or hit bounds.",
            "Symmetric DCC treats crashes and rallies alike.",
            "Needs stable GARCH margins.",
        ],
        "use_for": ["Dynamic correlation after vol filtering.", "Comparison of latest_rho with Pearson r."],
        "not_for": ["Asymmetry in down markets (use ADCC).", "Tiny samples where GARCH fails."],
    },
    {
        "num": "10",
        "folder": "10 - Asymmetric DCC",
        "name": "Asymmetric DCC",
        "index": "index.xlsx",
        "headline": "latest_adcc",
        "chart": "adcc_g",
        "question": "Does correlation rise more after joint negative shocks?",
        "what_it_is": (
            "Asymmetric DCC extends DCC with a crash term g. "
            "Joint negative shocks can raise correlation more than joint positive shocks."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: latest ADCC rho, nested DCC, and parameters a, b, g. "
            "Output unit: dynamic correlation in [-1, 1]; g is an asymmetry weight."
        ),
        "you_get": "You get a dynamic path that can react more to joint sell-offs.",
        "you_do_not_get": "You do not get a valid path when the optimiser fails to converge.",
        "formula": "n_i,t = min(z_i,t, 0)\nq_ij,t = (1-a-b-g)*Qbar + a*z_i*z_j + g*n_i*n_j + b*q_ij\nrho_ij,t = q_ij,t / sqrt(q_ii,t * q_jj,t)",
        "formula_terms": [
            ("n_i,t", "Negative part of the residual (crash side)"),
            ("g", "Asymmetry weight on joint downs"),
            ("rho_ij,t", "Asymmetric DCC correlation"),
        ],
        "plus": [
            "The g term captures crash asymmetry.",
            "It nests symmetric DCC when g = 0.",
            "Useful for carry and safe-haven pairs.",
        ],
        "minus": [
            "More parameters than DCC.",
            "Optimizer bounds can stick (g=0 or bad b).",
            "Needs a likelihood-ratio check for g.",
        ],
        "use_for": ["Stress asymmetry vs calm periods.", "Gaps ADCC minus Pearson and ADCC minus DCC."],
        "not_for": ["Claims without fit diagnostics.", "Price-level mean reversion."],
    },
    {
        "num": "11",
        "folder": "11 - Regime-Conditioned Correlation",
        "name": "Regime-Conditioned Correlation",
        "index": "index.xlsx",
        "headline": "stress_minus_quiet",
        "chart": "regime_gap",
        "question": "How does correlation differ in quiet vs stress states?",
        "what_it_is": (
            "This method splits days into quiet and stress using a shared turbulence rule. "
            "It then computes Pearson r in each state."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: rho_quiet, rho_stress, and stress_minus_quiet from a look-ahead-free FX turbulence rule. "
            "Output unit: correlation in [-1, 1]; gap is a difference of correlations."
        ),
        "you_get": "You get how linear co-movement changes when the market is stressed.",
        "you_do_not_get": "You do not get a volatility-bias-free stress rho without further adjustment.",
        "formula": "rho_quiet = Corr(x,y | state=quiet)\nrho_stress = Corr(x,y | state=stress)",
        "formula_terms": [
            ("state", "Quiet or stress from past turbulence RV"),
            ("rho_quiet", "Pearson r on quiet days"),
            ("rho_stress", "Pearson r on stress days"),
        ],
        "plus": [
            "It splits the sample by a turbulence rule.",
            "stress_minus_quiet flags regime flips.",
            "The state rule uses past data only.",
        ],
        "minus": [
            "High vol can bias raw stress correlation.",
            "State labels depend on the turbulence rule.",
            "Fewer stress days reduce power.",
        ],
        "use_for": ["Quiet vs stress co-movement maps.", "Carry pairs that flip in risk-off."],
        "not_for": ["Unadjusted stress gaps as final truth.", "Exact crash-date prediction."],
    },
    {
        "num": "12",
        "folder": "12 - Lagged Cross-Correlation",
        "name": "Lagged Cross-Correlation",
        "index": "index.xlsx",
        "headline": "rho_L_to_R_k1",
        "chart": "lag_dirs",
        "question": "Does one return series lead the other at lag k?",
        "what_it_is": (
            "Lagged cross-correlation is Pearson r between one series today and the other series k days later. "
            "It is a simple lead-lag screen."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: rho at lag k=1 in both directions; also same-day rho_k0. "
            "Output unit: correlation in [-1, 1]."
        ),
        "you_get": "You get a signed lag-1 linear link in each direction.",
        "you_do_not_get": "You do not get proof of economic causality.",
        "formula": "rho_{X->Y}(k) = Corr( x_t, y_{t+k} )",
        "formula_terms": [
            ("k", "Lag in trading days (headline uses 1)"),
            ("rho_{X->Y}(k)", "Correlation of x today with y after k days"),
        ],
        "plus": [
            "It is a simple lead-lag screen.",
            "You can scan several lags k.",
            "k=0 recovers same-day Pearson.",
        ],
        "minus": [
            "Correlation is not causation.",
            "Many lags raise false positives.",
            "FX majors often show weak lags on D1.",
        ],
        "use_for": ["First look at directed timing.", "Compare with Granger and transfer entropy."],
        "not_for": ["Trading without out-of-sample tests.", "Claims of economic lead without costs."],
    },
    {
        "num": "13",
        "folder": "13 - Granger Predictability",
        "name": "Granger Predictability",
        "index": "index.xlsx",
        "headline": "p_L_to_R_p1",
        "chart": "granger_p",
        "question": "Does past X help forecast Y beyond past Y?",
        "what_it_is": (
            "Granger predictability tests whether past X improves a forecast of Y after you already use past Y. "
            "A small p-value rejects the null of no incremental content."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: lag-1 and lag-5 F-test p-values in both directions. "
            "Output unit: p-value in (0, 1]; smaller means stronger rejection."
        ),
        "you_get": "You get a directed predictability test for each ordered pair.",
        "you_do_not_get": "You do not get true structural causality or a trade rule.",
        "formula": "y_t = c + a*y_{t-1} + b*x_{t-1} + e_t\nH0: b = 0",
        "formula_terms": [
            ("b", "Coefficient on lagged X"),
            ("H0", "Null: past X adds nothing"),
            ("p", "p-value of the test"),
        ],
        "plus": [
            "It tests incremental forecast content.",
            "F-tests and p-values are standard.",
            "You can raise lag order p.",
        ],
        "minus": [
            "Reject H0 is not true causality.",
            "Multiple pairs need multiplicity control.",
            "Linear VAR misses non-linear leads.",
        ],
        "use_for": ["Directed predictability screens.", "Comparison with lagged correlation."],
        "not_for": ["Sole proof of economic causality.", "Non-linear information flow alone."],
        "low_is_strong": True,
        "abs_rank": False,
    },
    {
        "num": "14",
        "folder": "14 - Distance Correlation",
        "name": "Distance Correlation",
        "index": "index.xlsx",
        "headline": "dcor",
        "chart": "gap_bars",
        "gap_col": "dcor_minus_abs_r",
        "question": "Is there any dependence, including non-linear links?",
        "what_it_is": (
            "Distance correlation measures dependence from pairwise distances. "
            "In the population, dCor = 0 only under independence."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: biased sample dCor; also dCor minus |Pearson r|. "
            "Output unit: dCor in [0, 1]."
        ),
        "you_get": "You get a general dependence score and a non-linear excess over |r|.",
        "you_do_not_get": "You do not get a signed hedge ratio or a lead.",
        "formula": "dCor = sqrt( mean(A~ * B~)\n         / sqrt( mean(A~^2) * mean(B~^2) ) )",
        "formula_terms": [
            ("A~, B~", "Double-centered distance matrices"),
            ("dCor", "Distance correlation in [0, 1]"),
        ],
        "plus": [
            "dCor = 0 only under independence.",
            "It finds non-linear co-movement.",
            "Gap dCor - |r| flags extra dependence.",
        ],
        "minus": [
            "Computation uses distance matrices.",
            "Biased sample form needs care for tests.",
            "It does not give a signed direction.",
        ],
        "use_for": ["Pairs where Pearson r is near zero.", "Non-linear spillover checks."],
        "not_for": ["Signed hedge ratios.", "Lead-lag without extra tools."],
    },
    {
        "num": "15",
        "folder": "15 - Mutual Information",
        "name": "Mutual Information",
        "index": "index.xlsx",
        "headline": "nmi",
        "chart": "sorted_bars",
        "bar_col": "nmi",
        "question": "How much shared information do the two series hold?",
        "what_it_is": (
            "Mutual information measures shared information between binned returns. "
            "Normalised MI (NMI) puts the score on a comparable scale."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: discrete MI and normalised MI from equal-frequency bins. "
            "Output unit: NMI typically in [0, 1]."
        ),
        "you_get": "You get an information-theoretic dependence score for each pair.",
        "you_do_not_get": "You do not get a signed correlation for hedge sizing.",
        "formula": "I(X;Y) = SUM p_ab ln( p_ab / (p_a * p_b) )\nNMI = I / sqrt( H(X) H(Y) )",
        "formula_terms": [
            ("p_ab", "Joint bin probability"),
            ("I(X;Y)", "Mutual information in nats"),
            ("NMI", "Normalised mutual information"),
        ],
        "plus": [
            "It captures general dependence.",
            "NMI is easier to compare across pairs.",
            "It does not assume a linear form.",
        ],
        "minus": [
            "Bin count changes the estimate.",
            "Plug-in MI has positive bias.",
            "Scale differs from correlation.",
        ],
        "use_for": ["Information-theoretic dependence screens.", "Complement to distance correlation."],
        "not_for": ["Direct hedge sizing like Pearson r.", "Fine claims without bias correction."],
    },
    {
        "num": "16",
        "folder": "16 - HSIC Kernel Dependence",
        "name": "HSIC Kernel Dependence",
        "index": "index.xlsx",
        "headline": "n_hsic",
        "chart": "sorted_bars",
        "bar_col": "n_hsic",
        "question": "Do kernel embeddings of X and Y show dependence?",
        "what_it_is": (
            "HSIC tests dependence in a reproducing kernel Hilbert space. "
            "A normalised HSIC helps rank pairs."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: HSIC and normalised HSIC with RBF bandwidths ell_x, ell_y. "
            "Output unit: normalised HSIC (dimensionless, larger means more dependence)."
        ),
        "you_get": "You get a flexible kernel dependence score.",
        "you_do_not_get": "You do not get an easy signed hedge ratio.",
        "formula": "K_ij = exp( -(x_i-x_j)^2 / (2 ell^2) )\nHSIC = tr(K H L H) / n^2",
        "formula_terms": [
            ("ell", "RBF bandwidth"),
            ("K, L", "Kernel matrices for X and Y"),
            ("HSIC", "Hilbert-Schmidt independence criterion"),
        ],
        "plus": [
            "Kernels detect flexible non-linear links.",
            "HSIC = 0 under independence (population).",
            "Normalised HSIC helps cross-pair rank.",
        ],
        "minus": [
            "Bandwidth ell is a free choice.",
            "Cost grows with n squared.",
            "Harder to explain than Pearson r.",
        ],
        "use_for": ["Kernel dependence next to dCor and MI.", "Cases with complex scatter shapes."],
        "not_for": ["Simple signed correlation reports.", "Very large n without approx methods."],
    },
    {
        "num": "17",
        "folder": "17 - Transfer Entropy",
        "name": "Transfer Entropy",
        "index": "index.xlsx",
        "headline": "te_L_to_R",
        "chart": "te_bias",
        "question": "Does past X add information about next Y beyond past Y?",
        "what_it_is": (
            "Transfer entropy measures directed information flow. "
            "It asks whether past X helps predict the next state of Y after you use past Y."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: discrete TE in both directions with B=5 bins and lag 1. "
            "Output unit: nats. Plug-in bias under independence is about 0.0056 nats."
        ),
        "you_get": "You get a directed information score in each direction.",
        "you_do_not_get": "You do not get a reliable ranking until bias or shuffle tests pass.",
        "formula": "TE_{X->Y} = I(Y_{t+1}; X_past | Y_past)",
        "formula_terms": [
            ("TE", "Transfer entropy in nats"),
            ("X_past, Y_past", "Lagged binned returns"),
            ("I(...|...)", "Conditional mutual information"),
        ],
        "plus": [
            "Directed information flow in nats.",
            "Allows non-linear predictive content.",
            "Both directions are available.",
        ],
        "minus": [
            "Discrete TE has plug-in bias.",
            "Binning choices change the score.",
            "Many FX TE values sit near bias level.",
        ],
        "use_for": ["Directed screens after bias tests.", "Compare with Granger on the same lags."],
        "not_for": ["Claims without shuffle or surrogate tests.", "Exact crash timing."],
    },
    {
        "num": "18",
        "folder": "18 - Copulas",
        "name": "Copulas",
        "index": "index.xlsx",
        "headline": "gauss_rho",
        "chart": "scatter_vs_pearson",
        "x_col": "pearson_r",
        "y_col": "gauss_rho",
        "question": "What dependence structure links the uniform margins?",
        "what_it_is": (
            "A copula separates each margin from the dependence structure. "
            "Gaussian and Clayton families summarise different joint shapes."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: Gaussian copula rho and Clayton theta on empirical uniforms. "
            "Output unit: Gaussian rho in [-1, 1]; Clayton theta is a family parameter."
        ),
        "you_get": "You get a dependence parameter after transforming returns to uniforms.",
        "you_do_not_get": "You do not get a full crash model unless you also study tails.",
        "formula": "F_XY(x,y) = C( F_X(x), F_Y(y) )\nC_Gauss(u,v; rho) = Phi_2( Phi^{-1}(u), Phi^{-1}(v); rho )",
        "formula_terms": [
            ("u, v", "Uniform transforms of the two returns"),
            ("C", "Copula function"),
            ("rho", "Gaussian copula dependence"),
        ],
        "plus": [
            "Separates margins from dependence.",
            "Clayton and Gauss capture different tails.",
            "Kendall from copula aids comparison.",
        ],
        "minus": [
            "Model choice (Gauss vs Clayton) matters.",
            "Fitting needs careful uniforms u,v.",
            "Misspecified copulas misstate tails.",
        ],
        "use_for": ["Dependence after margin transforms.", "Bridge to tail dependence (method 19)."],
        "not_for": ["Raw return Pearson replacement without care.", "Unsigned crash risk alone."],
    },
    {
        "num": "19",
        "folder": "19 - Tail Dependence",
        "name": "Tail Dependence",
        "index": "index.xlsx",
        "headline": "L_lower_cond_R",
        "chart": "tail_scatter",
        "question": "How often do both legs sit in the extreme lower tail?",
        "what_it_is": (
            "Tail dependence counts how often both series are in an extreme quantile together. "
            "Lower and upper tails can differ."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: empirical L_hat at alpha=0.05 for lower and upper tails, with event counts. "
            "Output unit: conditional frequency in [0, 1]."
        ),
        "you_get": "You get a countable crash (or rally) co-occurrence rate.",
        "you_do_not_get": "You do not get the mathematical limit lambda unless alpha goes to zero.",
        "formula": "L_hat(alpha) = (# u<=alpha AND v<=alpha)\n              / (# v<=alpha)",
        "formula_terms": [
            ("u, v", "Empirical uniforms of the returns"),
            ("alpha", "Tail cutoff (0.05 here)"),
            ("L_hat", "Conditional joint-tail frequency"),
        ],
        "plus": [
            "Direct count of joint crash days.",
            "Lower and upper tails can differ.",
            "Easy to audit with num/den counts.",
        ],
        "minus": [
            "Finite alpha is not the limit lambda.",
            "Benchmark should be Gaussian, not independence.",
            "Rare events give noisy ratios.",
        ],
        "use_for": ["Crash co-movement vs average Pearson r.", "Carry pairs with hidden lower-tail risk."],
        "not_for": ["Daily trading signals alone.", "Claims without a same-r Gaussian benchmark."],
    },
    {
        "num": "20",
        "folder": "20 - Cross-Quantilogram",
        "name": "Cross-Quantilogram",
        "index": "index.xlsx",
        "headline": "rho_L_to_R_t005_k1",
        "chart": "cq_dirs",
        "question": "Do quantile hits of X predict quantile hits of Y at lag k?",
        "what_it_is": (
            "The cross-quantilogram correlates indicator hits of chosen quantiles across time. "
            "It focuses on extreme or moderate quantile dependence with lags."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: rho_tau(k) at tau in {{0.05, 0.20}} and lags 0..10; headline tau=0.05, k=1. "
            "Output unit: quantilogram correlation in [-1, 1]."
        ),
        "you_get": "You get directed extreme-quantile dependence at a chosen lag.",
        "you_do_not_get": "You do not get a center-of-distribution Pearson substitute.",
        "formula": "h_x,t = 1(x_t < q_x) - tau\nrho_tau(k) = SUM h_x,t h_y,t+k\n           / sqrt( SUM h_x^2 * SUM h_y,t+k^2 )",
        "formula_terms": [
            ("tau", "Quantile level (0.05 in the headline)"),
            ("h_x,t", "Centered quantile hit"),
            ("rho_tau(k)", "Cross-quantilogram at lag k"),
        ],
        "plus": [
            "Focuses on chosen quantile tau.",
            "Lag k gives directed extreme dependence.",
            "Useful for left-tail (tau=0.05) risk.",
        ],
        "minus": [
            "Needs expanding quantile estimates.",
            "Many tau and k raise false hits.",
            "Inference needs careful critical values.",
        ],
        "use_for": ["Tail-to-tail predictability screens.", "Complement to static L_hat tails."],
        "not_for": ["Center-of-distribution Pearson only.", "Untested multi-lag fishing."],
    },
    {
        "num": "21",
        "folder": "21 - Spectral Coherence",
        "name": "Spectral Coherence",
        "index": "index.xlsx",
        "headline": "gamma2_p21",
        "chart": "grouped_scales",
        "scale_cols": [("gamma2_p5", "5d"), ("gamma2_p21", "21d"), ("gamma2_p63", "63d")],
        "question": "At which cycle lengths do the series share power?",
        "what_it_is": (
            "Spectral coherence measures shared power at each frequency. "
            "It shows whether co-movement is short-cycle or long-cycle."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: magnitude-squared coherence at periods near 5, 21 and 63 days. "
            "Output unit: gamma^2 in [0, 1]."
        ),
        "you_get": "You get co-movement strength by cycle length.",
        "you_do_not_get": "You do not get a same-day crash count or a signed hedge ratio.",
        "formula": "gamma^2(f) = |S_xy(f)|^2 / ( S_xx(f) * S_yy(f) )",
        "formula_terms": [
            ("f", "Frequency (cycles per day)"),
            ("S_xx, S_yy", "Auto-spectra"),
            ("S_xy", "Cross-spectrum"),
        ],
        "plus": [
            "Splits dependence by frequency.",
            "gamma^2 lies in [0, 1].",
            "Phase shows relative timing at f.",
        ],
        "minus": [
            "Stationarity assumptions matter.",
            "Window choice affects the spectrum.",
            "Hard to map one f to a trade rule.",
        ],
        "use_for": ["Cycle co-movement at 5 / 21 / 63 days.", "Checks whether short and long cycles differ."],
        "not_for": ["Same-day crash counts.", "Signed hedge ratios alone."],
    },
    {
        "num": "22",
        "folder": "22 - Wavelet Correlation and Coherence",
        "name": "Wavelet Correlation and Coherence",
        "index": "index.xlsx",
        "headline": "rho_p21",
        "chart": "grouped_scales",
        "scale_cols": [("rho_p5", "5d"), ("rho_p21", "21d"), ("rho_p63", "63d")],
        "question": "How does correlation change across wavelet time scales?",
        "what_it_is": (
            "Wavelet correlation measures co-movement at chosen time scales. "
            "It localises dependence in both time and horizon."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: Morlet wavelet correlation at periods 5, 21 and 63 days. "
            "Output unit: correlation-like rho in [-1, 1]."
        ),
        "you_get": "You get multi-horizon co-movement for each pair.",
        "you_do_not_get": "You do not get a single desk KPI without picking a scale.",
        "formula": "rho_wavelet(s) = Corr( W_x(s,·), W_y(s,·) )",
        "formula_terms": [
            ("s", "Wavelet scale (maps to day period)"),
            ("W_x, W_y", "Wavelet coefficients at scale s"),
            ("rho_wavelet", "Correlation of those coefficients"),
        ],
        "plus": [
            "Localises dependence in time and scale.",
            "Morlet scales map to day periods.",
            "Mean R^2 shows coherence strength.",
        ],
        "minus": [
            "Edge effects need a cone of influence.",
            "Scale choice is a design decision.",
            "Harder to audit than Pearson r.",
        ],
        "use_for": ["Multi-horizon co-movement maps.", "Compare rho at 5, 21 and 63 days."],
        "not_for": ["Single-number desk headlines alone.", "Ignoring edge masks."],
    },
    {
        "num": "23",
        "folder": "23 - DCCA Detrended Cross-Correlation",
        "name": "DCCA Detrended Cross-Correlation",
        "index": "index.xlsx",
        "headline": "rho_s100",
        "chart": "grouped_scales",
        "scale_cols": [("rho_s20", "s20"), ("rho_s60", "s60"), ("rho_s100", "s100")],
        "question": "After local detrend, how do profiles co-move at scale s?",
        "what_it_is": (
            "DCCA builds cumulative return profiles, removes local trends, then correlates the residuals. "
            "Scale s shows short versus longer memory links."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: rho_DCCA at scales 20, 60 and 100. "
            "Output unit: DCCA correlation in [-1, 1]."
        ),
        "you_get": "You get detrended co-movement at chosen memory scales.",
        "you_do_not_get": "You do not get lead-lag direction from this score alone.",
        "formula": "rho_DCCA(s) = mean(X~ Y~)\n  / sqrt( mean(X~^2) * mean(Y~^2) )",
        "formula_terms": [
            ("X~, Y~", "Detrended profile residuals in windows of length s"),
            ("s", "Window scale in observations"),
            ("rho_DCCA", "Detrended cross-correlation"),
        ],
        "plus": [
            "Removes local trends before correlation.",
            "Scale s shows short vs long memory links.",
            "Useful when trends dominate raw r.",
        ],
        "minus": [
            "Window and poly order are free choices.",
            "Interpretation needs care vs Pearson.",
            "Cost rises with many scales.",
        ],
        "use_for": ["Long-memory co-movement screens.", "Compare rho_s20 vs rho_s100."],
        "not_for": ["Same-day crash frequency.", "Lead-lag direction alone."],
    },
    {
        "num": "24",
        "folder": "24 - Multifractal DCCA",
        "name": "Multifractal DCCA",
        "index": "index.xlsx",
        "headline": "rho_q2_s100",
        "chart": "mf_scatter",
        "question": "How does DCCA correlation change with moment order q?",
        "what_it_is": (
            "Multifractal DCCA weights fluctuation sizes with moment q. "
            "q=2 links to standard DCCA; higher q emphasises large moves."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: rho_q at selected q and scales; headline q=2, s=100. "
            "Output unit: multifractal DCCA correlation in [-1, 1]."
        ),
        "you_get": "You get scale-and-moment dependence for each pair.",
        "you_do_not_get": "You do not get a simple one-number desk KPI without fixed q and s.",
        "formula": "G_xy(q,s) = mean[ sign(c) * |c|^(q/2) ]\nrho_q(s) = G_xy / sqrt( G_xx * G_yy )",
        "formula_terms": [
            ("q", "Moment order"),
            ("c", "Local fluctuation product"),
            ("rho_q(s)", "Multifractal DCCA correlation"),
        ],
        "plus": [
            "q emphasises small or large fluctuations.",
            "q=2 links back to standard DCCA.",
            "Helps multifractal co-movement maps.",
        ],
        "minus": [
            "q and s add many free choices.",
            "Harder for non-specialist readers.",
            "Needs stable long samples.",
        ],
        "use_for": ["Scale and moment dependence together.", "Compare rho_q2 and rho_q4 at s=100."],
        "not_for": ["Simple one-page desk KPIs alone.", "Tiny samples."],
    },
    {
        "num": "25",
        "folder": "25 - Volatility and Realized Correlation",
        "name": "Volatility and Realized Correlation",
        "index": "index.xlsx",
        "headline": "rho_vol",
        "chart": "scatter_vs_pearson",
        "x_col": "pearson_r",
        "y_col": "rho_vol",
        "question": "Do absolute returns (volatility proxies) move together?",
        "what_it_is": (
            "Volatility correlation is Pearson r of absolute returns. "
            "It tracks whether quiet and loud days line up across pairs."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: rho_vol = Corr(|x|, |y|) on daily abs returns. "
            "Output unit: correlation in [-1, 1]."
        ),
        "you_get": "You get a vol-vol linkage score on D1 closes.",
        "you_do_not_get": "You do not get true intraday realised correlation from daily closes alone.",
        "formula": "rho_vol = Corr( |x_t|, |y_t| )",
        "formula_terms": [
            ("|x_t|, |y_t|", "Absolute daily log returns"),
            ("rho_vol", "Correlation of the volatility proxies"),
        ],
        "plus": [
            "Captures vol-vol co-movement.",
            "Simple on daily closes.",
            "Useful when |r| is low but vol clusters.",
        ],
        "minus": [
            "Absolute returns are not signed returns.",
            "True realized corr needs intraday buckets.",
            "D1 proxy is not full realized covariance.",
        ],
        "use_for": ["Volatility linkage screens on D1.", "Risk when vols rise together."],
        "not_for": ["Signed return hedging.", "Calling D1 |r| true intraday realized corr."],
    },
    {
        "num": "26",
        "folder": "26 - Hayashi-Yoshida Covariance",
        "name": "Hayashi-Yoshida Covariance",
        "index": "index.xlsx",
        "headline": "rho_hy",
        "chart": "scatter_vs_pearson",
        "x_col": "pearson_r",
        "y_col": "rho_hy",
        "question": "How do you covary returns when ticks are not synchronous?",
        "what_it_is": (
            "Hayashi-Yoshida covariance sums products of returns whose time intervals overlap. "
            "It targets asynchronous trading."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: HY covariance and a correlation form rho_hy on the aligned D1 panel. "
            "Output unit: correlation-like rho_hy in [-1, 1]."
        ),
        "you_get": "You get an asynchronous-aware covariance summary (limited power on pure D1).",
        "you_do_not_get": "You do not unlock full HY value without true tick intervals.",
        "formula": "C_HY = SUM_i SUM_j dX_i * dY_j * 1(I_i overlaps J_j)",
        "formula_terms": [
            ("dX_i, dY_j", "Returns on intervals I_i and J_j"),
            ("1(overlap)", "Indicator that intervals overlap"),
            ("C_HY", "Hayashi-Yoshida covariance"),
        ],
        "plus": [
            "Handles non-synchronous trading times.",
            "Classic for irregular tick data.",
            "Avoids forced grid refresh bias.",
        ],
        "minus": [
            "Needs true tick intervals for full power.",
            "On D1 closes the gain is limited.",
            "Harder to implement than Pearson.",
        ],
        "use_for": ["Intraday or irregular sampling designs.", "Compare rho_hy with daily Pearson."],
        "not_for": ["Only daily close panels as the main case.", "Lead-lag information flow alone."],
    },
    {
        "num": "27",
        "folder": "27 - Cointegration and Error Correction",
        "name": "Cointegration and Error Correction",
        "index": "index.xlsx",
        "headline": "coint_p",
        "chart": "coint_p",
        "question": "Do log prices share a mean-reverting spread?",
        "what_it_is": (
            "Cointegration asks whether two log price levels stay linked by a stationary spread. "
            "An error-correction term kappa shows how fast the spread pulls back."
        ),
        "how_we_use": (
            "Input: log closes for Engle-Granger; log returns for the ECM side check. "
            f"Snapshot {SNAPSHOT}. "
            "Statistic: cointegration p-value and ECM kappa. "
            "Output unit: p-value; kappa is a speed coefficient."
        ),
        "you_get": "You get a level-link test, which is different from return correlation.",
        "you_do_not_get": "You do not get a proven link from a raw p<0.05 across 28 pairs without multiplicity control.",
        "formula": "e_t = ln(PY_t) - alpha - beta*ln(PX_t)\ndelta ln(PY_t) = c + kappa*e_{t-1} + lags + u_t",
        "formula_terms": [
            ("e_t", "Spread residual of log prices"),
            ("kappa", "Error-correction speed"),
            ("coint_p", "Engle-Granger p-value"),
        ],
        "plus": [
            "Tests level links, not only return corr.",
            "kappa shows error-correction speed.",
            "Key for pairs and mean-reversion ideas.",
        ],
        "minus": [
            "Many pairs raise false positives.",
            "Bonferroni can wipe raw 5% hits.",
            "High return corr does not imply cointegration.",
        ],
        "use_for": ["Price-spread stationarity screens.", "Separate return corr from level tethering."],
        "not_for": ["Treating raw p<0.05 across 28 pairs as proven.", "Crash timing."],
        "low_is_strong": True,
        "abs_rank": False,
    },
    {
        "num": "28",
        "folder": "28 - Networks PCA and Connectedness",
        "name": "Networks PCA and Connectedness",
        "index": "index.xlsx",
        "headline": "d_ij",
        "chart": "network",
        "question": "How close are pairs in a network, and who transmits shocks?",
        "what_it_is": (
            "This method builds network distances from correlations, PCA of the correlation matrix, "
            "and Diebold-Yilmaz connectedness from a VAR forecast-error variance decomposition."
        ),
        "how_we_use": (
            f"{INPUT_COMMON} "
            "Statistic: pair distance d_ij, directional theta, system TCI, and PCA eigenvalues. "
            "Output unit: d_ij >= 0; TCI in percent; variance shares in [0, 1]."
        ),
        "you_get": "You get a system view: closeness, factor share, and shock transmission.",
        "you_do_not_get": "You do not get a pair-trade entry rule from TCI alone.",
        "formula": "d_ij = sqrt( 2*(1 - rho_ij) )\nTCI = 100 * SUM_{i!=j} theta_tilde_ij / N",
        "formula_terms": [
            ("rho_ij", "Pearson correlation of the pair"),
            ("d_ij", "Network distance (smaller = closer)"),
            ("TCI", "System total connectedness index"),
        ],
        "plus": [
            "System view beyond one pair.",
            "PCA shows shared factors.",
            "Diebold-Yilmaz TCI shows spillover intensity.",
        ],
        "minus": [
            "VAR connectedness needs lag choice.",
            "Near-singular panels (EURGBP) distort PCA.",
            "Full-sample TCI is not a forecast.",
        ],
        "use_for": ["Market-wide connectedness maps.", "Net transmitter vs receiver ranks."],
        "not_for": ["Pair trade entries without more filters.", "Ignoring triangular redundancy."],
        "special": "network",
        "abs_rank": False,
        "low_is_strong": True,
    },
]


def method_dir(meta: dict) -> Path:
    return REPO_ROOT / meta["folder"] / "experiments" / "v001" / "outputs"
