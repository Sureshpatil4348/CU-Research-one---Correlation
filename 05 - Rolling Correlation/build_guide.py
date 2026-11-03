from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Rolling_Correlation_Complete_Simple_Guide.pdf'
EXPECTED_PAGES = 16
W_WINDOWS = (20, 60, 100)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyEasy', fontName='Helvetica', fontSize=11, leading=16, spaceAfter=10))
styles.add(ParagraphStyle(name='HeadEasy', fontName='Helvetica-Bold', fontSize=23, leading=28, textColor=colors.HexColor('#15364A'), spaceAfter=18))
styles.add(ParagraphStyle(name='SubEasy', fontName='Helvetica-Bold', fontSize=13, leading=18, textColor=colors.HexColor('#087F8C'), spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name='FormulaEasy', fontName='Courier', fontSize=10, leading=15, backColor=colors.HexColor('#EDF5F7'), borderPadding=10, spaceBefore=8, spaceAfter=17))
styles.add(ParagraphStyle(name='SmallEasy', fontName='Helvetica', fontSize=9, leading=13, spaceAfter=8))
story = []


def p(t):
    story.append(Paragraph(t, styles['BodyEasy']))


def h(t):
    story.append(Paragraph(t, styles['SubEasy']))


def f(t):
    story.append(Paragraph(escape(t).replace('\n', '<br/>'), styles['FormulaEasy']))


def page(title, tag):
    if story:
        story.append(PageBreak())
    story.append(Paragraph(tag.upper(), styles['SubEasy']))
    story.append(Paragraph(title, styles['HeadEasy']))


def table(rows, widths=None):
    data = [[Paragraph(escape(str(v)), styles['SmallEasy']) for v in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DBEDF0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#B8CCD2')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))


def pearson_r(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    dx = [a - mx for a in x]
    dy = [b - my for b in y]
    top = sum(a * b for a, b in zip(dx, dy))
    bot = sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
    return top / bot


def rolling_r(x, y, w):
    assert len(x) == len(y) and len(x) >= w
    return pearson_r(x[-w:], y[-w:])


TEACH_X = [0.01, -0.005, 0.002, 0.004, -0.001, 0.003, 0.0, 0.002]
TEACH_Y = [0.008, -0.004, 0.001, 0.003, -0.002, 0.002, 0.001, 0.001]
W_TEACH = 5
RHO_ROLL = rolling_r(TEACH_X, TEACH_Y, W_TEACH)

page('Rolling correlation', 'Method 05 / A complete beginner guide')
p('<b>Question this method answers:</b> Right now, using only the last W matched daily returns, how strongly do X and Y co-move?')
p('W is an observation count (e.g. 20 trading days), not a calendar-month label. Short windows are noisy; longer windows smooth but lag regime shifts.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Idea, sign, size, percent trap'],
    ['3', 'FX return math'],
    ['4', 'Which series rolling r uses'],
    ['5', 'Research notes (section 05)'],
    ['6', 'Symbol dictionary'],
    ['7-8', 'Formula and teaching hand example'],
    ['9', 'Real v001 Alpari snapshot results'],
    ['10-11', 'Daily monitoring workflow and limits'],
    ['12', 'Software reproduction'],
    ['13-16', 'Window choice, practice, sources'],
], [65, 405])
p('Prepared for: 05 - Rolling Correlation. Experiments v001 is complete on snapshot 2026-11-03_majors_alpari_D1.')

page('What is rho_t^(W)?', '02 / The basic idea')
f('rho_t^(W) = Corr( last W observations of x, last W of y )')
p('At each end date t, take the previous W rows of both return series and compute Pearson r. Move t forward one day to get a new value.')
h('Is this number a percent?')
table([
    ['Mistake', 'Truth'],
    ['"r_20 is 20% something"', 'No. 20 is the window length in observations; r is still between -1 and +1.'],
    ['"High r_20 means 20 winning days"', 'No. It describes co-movement of returns inside the window.'],
], [220, 250])

page('FX percent math (majors)', '03 / Returns before rolling')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('v001 used daily log returns of close, quote unchanged. Example: 1.1000→1.1110 → about +1.0000% simple, ~0.9950% log.')
p('Reverse quote flips log sign. Missing ≠ 0. Four prices → three returns.')
p('Rolling correlation is computed on these return series, not on prices. Mixing return types between baseline and rolling breaks comparability with method 01 outputs.')

page('Which series this method uses', '04 / Data choice')
p('Rolling Pearson on <b>matched daily log returns</b> (same as method 01 baseline in this repo). Each window is W consecutive trading days present in both series after merge.')
p('Windows used in v001: W ∈ {20, 60, 100}.')
p('The unfinished last D1 bar was dropped in v001 after a tick-volume check. Your rolling file should use the same complete-bar rule so r_20 lines up with the snapshot metadata.')
p('Pair names like AUDUSD-NZDUSD mean two return columns merged on date — not a cross-rate formula.')

page('Research notes (section 05)', '05 / Literature context')
p('Section 05 in forex-formulas-explained.pdf defines rolling correlation as local Pearson r over a moving window.')
p('Dynamic conditional correlation models (Engle, 2002) popularized time-varying correlation for risk management. Rolling r is a transparent, non-model shortcut — useful for monitoring even when you do not fit full DCC.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['W', 'Window length in observations (not calendar days unless data is daily and complete).'],
    ['rho_t^(W)', 'Rolling correlation at end date t.'],
    ['r_20, r_60, r_100', 'Latest rolling values for each window in v001 outputs.'],
    ['baseline_r', 'Full-sample Pearson r from method 01 v001.'],
], [130, 340])

page('Formula explained', '07 / Window mechanics')
p('For each t, slice x[t-W+1:t] and y[t-W+1:t] (inclusive). Require exactly W valid pairs; gaps in data shrink effective history unless you impute (not done in v001).')
p('Early dates before W rows exist are skipped or marked missing in output CSVs.')
p('Each window recomputes means from scratch inside the slice — a big move ages out only when it leaves the W-day tail. That is why r_20 reacts faster than r_100 on the same pair.')
p('Calendar holidays remove rows from the count; W = 20 means twenty observed returns, not twenty calendar days on a wall calendar.')

page('Teaching hand example (separate from Alpari)', '08 / W = 5')
p('Made-up decimal returns (last five rows drive the score):')
table([
    ['Day', 'x', 'y'],
    [4, 0.004, 0.003],
    [5, -0.001, -0.002],
    [6, 0.003, 0.002],
    [7, 0.0, 0.001],
    [8, 0.002, 0.001],
], [50, 120, 120])
f(f'rho_roll (W=5 on full 8-day teach set uses last 5) = {RHO_ROLL:.6f}')
p('This toy series is only for arithmetic and Python checks. Alpari v001 pair CSVs contain thousands of rolling rows — never mix those filenames with this teaching table.')
p('Recompute Pearson on the last W rows only; including earlier rows would answer a different window question.')

page('Real results — experiments/v001', '09 / Alpari D1 snapshot')
p('Source: experiments/v001/NOTES.md and outputs/WATCHLIST.md (only v001). Series: daily log return of close. Statistic: rolling Pearson r with W = 20, 60, 100.')
h('Short watchlist (latest rolling vs baseline)')
table([
    ['Pair', 'baseline', 'r_20', 'r_60', 'r_100'],
    ['AUDUSD-NZDUSD', '0.829', '0.263', '0.607', '0.706'],
    ['EURUSD-USDCHF', '-0.749', '-0.729', '-0.692', '-0.755'],
    ['AUDUSD-USDCAD', '-0.647', '-0.302', '-0.526', '-0.523'],
    ['EURUSD-GBPUSD', '0.642', '0.925', '0.875', '0.851'],
    ['NZDUSD-USDCAD', '-0.588', '-0.398', '-0.531', '-0.564'],
], [120, 70, 70, 70, 70])
p('WATCHLIST highlights: AUDUSD-NZDUSD baseline 0.829 vs r_20 0.263 (large gap); EURUSD-GBPUSD r_20 0.925 above baseline 0.642. Short windows can diverge sharply from full history.')

page('More v001 tiers (summary)', '10 / Secondary and low-value')
p('Secondary examples: EURUSD-AUDUSD r_20 ≈ -0.004 vs baseline 0.556; GBPUSD-USDCHF r_20 ≈ -0.728 vs baseline -0.486.')
p('Low-value pairs often stay near zero on r_100 (e.g. USDCAD-EURGBP r_100 ≈ 0.007) — WATCHLIST says safe to ignore unless r_20 spikes.')
p('Monitoring order from WATCHLIST: refresh r_20 first each D1 close, confirm with r_60 and r_100, escalate on sign flips or large baseline gaps.')

page('Daily majors workflow', '11 / How to use rolling r')
p('1) Fix snapshot and merge rules. 2) Compute baseline r once. 3) Append rolling r_20/60/100 each day. 4) Compare to baseline — not to arbitrary thresholds from other pairs.')
p('std20 and std100 in NOTES measure rolling-series volatility; high std20 means r_20 is jumping — treat short windows as noisy.')

page('Limits', '12 / What rolling r cannot tell you')
p('Rolling r does not forecast tomorrow, does not pick hedge size, and is not a percent. Changing W changes the answer — always label W.')
p('Independence assumptions for classic p-values fail on daily FX; use rolling r as descriptive monitoring, as in v001.')
p('A single spike in r_20 can be noise — WATCHLIST compares baseline gaps for a reason. Do not trade on one window alone without charts and baseline context.')

page('Software check', '13 / Teaching arrays')
f('W = 5\nx = [0.01, -0.005, 0.002, 0.004, -0.001, 0.003, 0.0, 0.002]\ny = [0.008, -0.004, 0.001, 0.003, -0.002, 0.002, 0.001, 0.001]\nrho = pearsonr(x[-W:], y[-W:])[0]')
p(f'Expected teaching rho (last W={W_TEACH}) = {RHO_ROLL:.6f}. v001 pair numbers come from run_rolling.py outputs, not from this toy list.')

page('Window choice', '14 / 20 vs 60 vs 100')
p('W=20 reacts fast but noisy (see AUDUSD-NZDUSD). W=100 tracks baseline more closely for stable pairs like EURUSD-USDCHF. Use multiple W as a triangulation, not a single alarm.')
p('std20 in v001 NOTES flags pairs whose r_20 series jumps — pair high std20 with charts before calling a regime break.')
p('If r_20, r_60, and r_100 disagree in sign, treat the pair as unstable until you understand the recent window.')

page('Practice', '15 / Quick questions')
p('<b>Q:</b> W=20 on daily data means 20 calendar days? <b>A:</b> Twenty observations — usually trading days if your series has no gaps.')
p('<b>Q:</b> Can r_20 exceed +1? <b>A:</b> No.')
p('<b>Q:</b> baseline_r vs r_100 — should they match? <b>A:</b> Not necessarily; baseline uses full history while r_100 is only the latest 100-day window.')
p('<b>Q:</b> Where do Alpari numbers live? <b>A:</b> experiments/v001/NOTES.md and outputs/WATCHLIST.md — not in the teaching hand example on page 8.')
p('Monitoring habit: note sign of r_20 and whether it agrees with r_60 and r_100 before escalating a pair on the watchlist.')

page('Sources', '16 / Research trail')
refs = [
    ('1', 'Engle, R. (2002). Dynamic Conditional Correlation. Journal of Business & Economic Statistics, 20(3), 339–350.', 'https://doi.org/10.1198/073500102288618487', 'Time-varying correlation context for rolling monitoring.'),
    ('2', 'SciPy documentation: scipy.stats.pearsonr.', 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html', 'Pearson r inside each window.'),
    ('3', 'forex-formulas-explained.pdf — section 05; experiments/v001/NOTES.md; outputs/WATCHLIST.md.', str(ROOT / 'experiments/v001/NOTES.md'), 'Repo formulas and frozen v001 numbers.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 05  |  ROLLING CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Rolling Correlation - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert W_WINDOWS == (20, 60, 100)
assert abs(RHO_ROLL - rolling_r(TEACH_X, TEACH_Y, W_TEACH)) < 1e-12
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
