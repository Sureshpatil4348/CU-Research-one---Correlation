from pathlib import Path
from math import sqrt
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Cross_Quantilogram_Complete_Simple_Guide.pdf'
EXPECTED_PAGES = 15
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyEasy', fontName='Helvetica', fontSize=11, leading=16, spaceAfter=10))
styles.add(ParagraphStyle(name='HeadEasy', fontName='Helvetica-Bold', fontSize=23, leading=28, textColor=colors.HexColor('#15364A'), spaceAfter=18))
styles.add(ParagraphStyle(name='SubEasy', fontName='Helvetica-Bold', fontSize=13, leading=18, textColor=colors.HexColor('#087F8C'), spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name='FormulaEasy', fontName='Courier', fontSize=10, leading=15, backColor=colors.HexColor('#EDF5F7'), borderPadding=10, spaceBefore=8, spaceAfter=17))
styles.add(ParagraphStyle(name='SmallEasy', fontName='Helvetica', fontSize=9, leading=13, spaceAfter=8))
story = []

TEACH_X = [0.012, -0.008, 0.003, -0.015, 0.006, 0.004, -0.002, 0.001, -0.011, 0.002,
           0.005, -0.004, 0.001, 0.002, -0.006, 0.003, -0.001, 0.004, -0.002, 0.001]
TEACH_Y = [0.010, -0.007, 0.002, -0.013, 0.005, 0.003, -0.001, 0.0005, -0.009, 0.0015,
           0.004, -0.003, 0.0008, 0.0015, -0.005, 0.0025, -0.0008, 0.003, -0.0015, 0.0008]
TAU = 0.20
LAG = 1


def quantile_value(values, tau):
    xs = sorted(values)
    n = len(xs)
    idx = max(0, min(n - 1, int(tau * n) - 1 if int(tau * n) >= 1 else 0))
    return xs[idx]


def cross_quantilogram(x, y, tau, lag):
    n = len(x)
    assert len(y) == n and lag >= 0
    qx = quantile_value(x, tau)
    qy = quantile_value(y, tau)
    hx = [1.0 if v < qx else 0.0 for v in x]
    hx = [h - tau for h in hx]
    hy = [1.0 if v < qy else 0.0 for v in y]
    hy = [h - tau for h in hy]
    hx_use = hx[: n - lag]
    hy_use = hy[lag:]
    num = sum(a * b for a, b in zip(hx_use, hy_use))
    sx = sqrt(sum(a * a for a in hx_use))
    sy = sqrt(sum(b * b for b in hy_use))
    if sx == 0 or sy == 0:
        return 0.0
    return num / (sx * sy)


RHO_TAU_K = cross_quantilogram(TEACH_X, TEACH_Y, TAU, LAG)


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


page('Cross-quantilogram', 'Method 20 / A complete beginner guide')
p('<b>Question this method answers:</b> After an extreme move in FX leg X, does leg Y tend to hit its own chosen quantile k days later?')
p('The cross-quantilogram ρτ(k) compares centered quantile-hit indicators — not ordinary Pearson correlation on all returns.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Quantile hits versus full-sample r'],
    ['3', 'FX percent math (majors)'],
    ['4', 'Building h without future data'],
    ['5', 'Research notes (Han et al. 2016)'],
    ['6', 'Symbol dictionary'],
    ['7-9', 'Formula, lag k, teaching array'],
    ['10-11', 'Workflow and inference notes'],
    ['12', 'Software sketch'],
    ['13-15', 'Limits, practice, sources'],
], [65, 405])
p('Teaching returns only — no snapshot cross-quantilogram panels.')
p('Prepared for: 20 - Cross-Quantilogram. README status: not started.')

page('Hits in part of the distribution', '02 / The basic idea')
p('Bottom-5% days are rare. The cross-quantilogram focuses on whether those hits line up across series and lags. A near-zero Pearson r can still show quantile linkage if tails move together.')
h('Centered indicators')
table([
    ['h_x,t = 1(x_t < q_x) − τ', 'Positive when return is below the τ quantile.'],
    ['ρτ(k)', 'Normalized cross-product of h_x at t and h_y at t+k.'],
    ['Unlike Pearson', 'Targets a chosen quantile region, not all days equally.'],
], [200, 270])

page('FX percent math (majors)', '03 / Returns first')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('1.1000 → 1.1110 is about +1% simple return. Quantiles q_x and q_y are computed from past and current data only — never from future returns you would not have at time t.')
p('Example question from the formula sheet: does a bottom-5% EUR/USD day tend to precede a bottom-5% GBP/USD day one day later? That is a τ ≈ 0.05 setting with k = 1.')

page('Estimate quantiles causally', '04 / No lookahead')
p('At date t, q_x uses information available up to t (expanding window, rolling window, or a model fit on past data). Using the full-sample quantile on the whole history leaks future tail thresholds into early dates.')
p('Serial dependence in daily FX returns means standard i.i.d. confidence bands may be wrong — Han et al. provide bootstrap and HAC tools for ρτ(k).')
p('Section 20 in forex-formulas-explained.pdf states the same ρτ(k) normalization as this guide.')

page('Research notes', '05 / Han, Linton, Oka and Whang (2016)')
p('<b>The cross-quantilogram: measuring quantile dependence and testing directional predictability between time series.</b> Journal of Econometrics, 2016.')
p('Introduces ρτ(k) for directional predictability between series at chosen quantiles, with inference that allows serial dependence. Useful when FX researchers care about crash days rather than average co-movement.')
p('This PDF explains construction; formal p-values belong in experiment code with their bootstrap routines.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['τ (tau)', 'Quantile level for both legs (may differ in extensions).'],
    ['q_x, q_y', 'Sample τ-quantiles of X and Y returns.'],
    ['1(·)', 'Indicator: 1 if condition true, else 0.'],
    ['h_x,t, h_y,t', 'Centered quantile-hit series.'],
    ['k', 'Lead/lag horizon (days for D1 data).'],
    ['ρτ(k)', 'Cross-quantilogram at quantile τ and lag k.'],
], [120, 350])

page('Main formula', '07 / Normalized cross-product')
f('h_x,t = 1(x_t < q_x) - tau\n\nrho_tau(k) = SUM_t h_x,t * h_y,t+k /\n  sqrt( SUM_t h_x,t^2 * SUM_t h_y,t+k^2 )')
p('Build h_y the same way. The denominator scales the sum so ρτ(k) behaves like a correlation among hit indicators.')
p('Use the same τ definition for reporting across pairs. Mixed τ values are not comparable on one chart.')

page('Read the lag k', '08 / Direction and timing')
p('k &gt; 0: today’s X quantile event is paired with Y’s event k days later — a lead from X to Y in calendar time. k = 0: same-day co-hits. Negative k reverses the lead; define the sign convention in NOTES before batch runs.')
p('Plot ρτ(k) over a band of k (for example 0–10) to see where predictability concentrates. One lag alone can mislead if serial correlation is strong.')

page('Teaching calculation', '09 / Twenty return pairs')
f(f'tau = {TAU}, lag k = {LAG}\nn = {len(TEACH_X)} paired days\nrho_tau(k) ≈ {RHO_TAU_K:.4f}')
p('Returns are made-up major-style decimals. q_x and q_y come from the teaching sample only — acceptable for a workbook, not for causal backtests.')
p('Recompute after any change to τ, lag, or quantile rule. The number is not a percent of days; it is a normalized score among hit indicators.')

page('Inference outline', '10 / Serial dependence matters')
p('Han et al. recommend resampling schemes that respect time dependence when testing H0: ρτ(k) = 0. Plain Pearson t-tests on h series are a poor default for daily FX.')
p('Pre-specify the quantile τ, lag grid, and resampling seed in experiments/v001/ before ranking pairs.')
p('When you report a significant ρτ(k), include the effective sample size after lag alignment (n − k) and the count of active hits in the denominator sums. Sparse tails mean wide uncertainty even when the normalized score looks large.')
p('Bootstrap blocks should match the economic calendar — shuffling daily returns destroys weekend gaps and can inflate significance for D1 FX panels.')

page('Daily majors workflow', '11 / Repo usage')
h('1. Freeze return type and quantile rule')
p('Log returns from a named snapshot; document rolling versus expanding q_x.')
h('2. Compute ρτ(k) on aligned panels')
p('Drop unpaired rows; keep holiday gaps explicit.')
h('3. Report τ, k, and the quantile estimation window')
p('Store arrays in experiment outputs — not only peak ρτ.')
p('Do not open MT5 from this folder; read data/snapshots/ only.')

page('Software sketch', '12 / Python structure')
f('hx = (x < q_x).astype(float) - tau\nhy = (y < q_y).astype(float) - tau\n# align hy shifted by k, then normalized sum')
p('NumPy boolean masks implement 1(·). SciPy and statsmodels offer quantile helpers — verify inclusive/exclusive tie handling matches your econometric definition.')
p('Cross-quantilogram code should live under experiments/, not inside shared/mt5_data/.')

page('Limits', '13 / What ρτ(k) cannot tell you')
p('It is not a hedge ratio, not tail copula λ, and not proof of economic mechanism. Quantile thresholds jump when sample size is small.')
p('Multiple lags and quantiles inflate false discoveries unless you correct or pre-register.')
p('ρτ(k) magnitude depends on τ; do not rank pairs at τ = 0.20 against pairs at τ = 0.05 without comment.')

page('Practice', '14 / Quick checks')
p('<b>Q:</b> Is ρτ(k) the same as Pearson r on returns? <b>A:</b> No — it uses centered hit indicators at quantile τ.')
p('<b>Q:</b> Can q_x use tomorrow’s data? <b>A:</b> No — that leaks future information.')
p(f'<b>Check:</b> teaching ρτ({TAU}) at k={LAG} ≈ {RHO_TAU_K:.4f} from build_guide.py.')
p('<b>Q:</b> Does ρτ(k) = 0.3 mean 30% of days? <b>A:</b> No — it is not a daily frequency percent.')

page('Sources', '15 / Research trail')
refs = [
    ('1', 'Han, H., Linton, O., Oka, T., & Whang, Y. J. (2016). The cross-quantilogram. Journal of Econometrics.', 'https://doi.org/10.1016/j.jeconom.2015.09.003', 'Definition and inference for ρτ(k).'),
    ('2', 'forex-formulas-explained.pdf — section 20 (this repository).', '../forex-formulas-explained.pdf', 'Project formula sheet.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Rebuild: python build_guide.py. End of cross-quantilogram beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 20  |  CROSS-QUANTILOGRAM')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Cross-Quantilogram - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert -1.0 <= RHO_TAU_K <= 1.0
assert abs(RHO_TAU_K - cross_quantilogram(TEACH_X, TEACH_Y, TAU, LAG)) < 1e-12
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
