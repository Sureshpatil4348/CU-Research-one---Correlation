from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'EWMA_Correlation_Complete_Simple_Guide.pdf'
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


LAM = 0.94
ONE_MINUS = 0.06
XS = [0.02, -0.01, 0.015]
YS = [0.015, -0.008, 0.012]


def ewma_corr(xs, ys, lam=LAM):
    c = vx = vy = 0.0
    for x, y in zip(xs, ys):
        c = lam * c + (1 - lam) * x * y
        vx = lam * vx + (1 - lam) * x * x
        vy = lam * vy + (1 - lam) * y * y
    if vx <= 0 or vy <= 0:
        raise ValueError('No spread in EWMA variances')
    return c / sqrt(vx * vy), c, vx, vy


RHO_TEACH, C_FINAL, VX_FINAL, VY_FINAL = ewma_corr(XS, YS)
FX_LOG = log(1.1110 / 1.1000)
FX_SIMPLE = 1.1110 / 1.1000 - 1

page('EWMA correlation', 'Method 06 / A complete beginner guide')
p('<b>How closely do two return series move together when recent days matter more?</b> This guide explains exponentially weighted moving average (EWMA) correlation in plain steps.')
p('You will see why RiskMetrics-style models use a decay factor, how rho is built from EWMA covariance and variances, and how to read the score on FX returns.')
h('Read it in three parts')
p('<b>First:</b> The idea, percent returns, and which data to use. <b>Next:</b> Symbols, formulas, and a tiny hand calculation. <b>Last:</b> Practical use on majors, limits, and software checks.')
table([['Pages', 'What you will learn'], ['2', 'The idea and whether rho is a percent'], ['3', 'FX percent math on a worked quote move'], ['4', 'Which return series this method uses'], ['5', 'Research: RiskMetrics 1996'], ['6-8', 'Symbols, formulas, and hand calculation'], ['9-10', 'Using EWMA on major FX pairs and limits'], ['11-12', 'Software reproduction and sources']], [65, 405])
p('All numeric examples are made-up teaching data. Experiments in this folder have not started. This guide does not report live pair results.')
p('Prepared for the folder: 06 - EWMA Correlation<br/>3 November 2026')

page('What does EWMA correlation do?', '02 / The basic idea')
p('Pearson correlation treats every day in the window equally. EWMA correlation gives <b>more weight to recent days</b> and less to older days. That fits the idea that market co-movement can change quickly.')
h('The answer is still called rho (here rho_t)')
p('At time t you get one number between -1 and +1, built from EWMA covariance and two EWMA variances. It is <b>not</b> a percent. It has no unit. It describes how two mean-adjusted return lists have moved together recently, with memory.')
table([['Value', 'Plain meaning'], ['rho near +1', 'Recent co-movement looks like a strong upward link.'], ['rho near 0', 'Recent co-movement is weak in a linear sense.'], ['rho near -1', 'When one return is high, the other tends to be low recently.']], [90, 380])
h('Is this a percent?')
p('<b>No.</b> A return can be written as 1.00% or 0.01 as a decimal. EWMA rho is a correlation-style score on the -1 to +1 scale. Do not say rho = 0.85 means 85% co-movement.')
p('Lambda = 0.94 (a common daily FX setting) means about <b>6% weight on today</b> and <b>94% carried from the previous EWMA state</b>. That is a recipe for updating variance and covariance, not a percent label for rho.')

page('FX percent math on one move', '03 / Returns in plain numbers')
p('Take a quote move from <b>1.1000 to 1.1110</b> (same units, one period). The simple return is the fractional change relative to the old price.')
f('Simple return = P_new / P_old - 1\n= 1.1110 / 1.1000 - 1\n= 0.01  (that is 1.00% as a percent label)')
p('The log return uses the natural logarithm ln. For small moves it is close to the simple return.')
f('Log return = ln(P_new / P_old)\n= ln(1.1110 / 1.1000)\n= about 0.009950  (about 0.995% as a percent label)')
p('EWMA correlation is computed on <b>mean-adjusted returns</b> x_t and y_t (often log returns minus their sample mean, or demeaned within your pipeline). Use the same return type for both series and the same time stamps.')
h('Why this page matters')
p('If you mix simple returns on one leg and log returns on the other, or forget demeaning, your EWMA rho will not match the formula in this guide or in RiskMetrics documentation.')

page('Which series does this method use?', '04 / Data choice')
h('Use returns, not raw price levels')
p('Price levels on two FX pairs can trend together even when daily returns are weakly linked. EWMA correlation is defined on <b>returns</b> (typically daily log or simple returns after mean adjustment).')
h('Pairing and timing')
p('Each row is one time index. EURUSD return at 17:00 New York must pair with GBPUSD return at the same bar close, not a shifted bar. Keep quote direction documented (what one unit of base buys).')
h('Mean adjustment')
p('Let r_x,t and r_y,t be raw returns. Often x_t = r_x,t minus the mean of r_x over your estimation window, and similarly for y_t. The EWMA updates then use x_t and y_t. Check your code: some packages demean once; others use raw returns with a different convention.')
h('Today\'s return in today\'s estimate')
p('The RiskMetrics-style update at t uses x_t and y_t on the same day. That estimate is for monitoring and for decisions on <b>later</b> days, not for pretending you knew today\'s return before it happened.')
p('Experiments under this folder are not started. When you run them, load frozen snapshots from data/snapshots/ and document the return type and lambda in the experiment notes.')

page('Where did EWMA come from?', '05 / Research notes')
h('RiskMetrics Technical Document (1996) [1]')
p('J.P. Morgan and Reuters published the RiskMetrics methodology for measuring market risk. It popularised EWMA volatility and covariance updates with a decay factor lambda (often 0.94 for daily FX and 0.97 for monthly data in their tables).')
p('The document explains why equal-weight windows react slowly to regime shifts, and why exponential weighting gives a one-parameter memory. EWMA correlation is the natural ratio of EWMA covariance to the product of EWMA standard deviations.')
h('What this guide claims')
p('We cite RiskMetrics as the standard industry reference for the EWMA variance and covariance recursion shown here. This PDF is a teaching companion for folder 06, not a reproduction of the full RiskMetrics dataset or every variant (e.g. alternative lambdas, intraday scaling).')
p('Check the primary PDF or archive copy of the 1996 technical document when you need exact wording, regulatory lineage, or historical parameter tables.')

page('Meet the symbols', '06 / A small math dictionary')
table([['Symbol', 'Meaning'], ['x_t, y_t', 'Mean-adjusted returns on day t for series X and Y.'], ['lambda', 'Decay factor between 0 and 1; weight on the previous EWMA state.'], ['1 - lambda', 'Weight on today\'s squared return or product.'], ['c_t', 'EWMA covariance of x and y at t.'], ['v_x,t, v_y,t', 'EWMA variances of x and y at t.'], ['rho_t', 'EWMA correlation at t.'], ['sqrt(a)', 'Positive square root.']], [125, 345])
p('With lambda = 0.94, each day keeps 94% of yesterday\'s EWMA variance and adds 6% of today\'s squared return. The covariance update uses the same split with x_t * y_t instead of a square.')
h('Starting values')
p('Real systems need c_0 and v_0. Teaching examples often start at zero and feed a short warm-up path, as in the hand calculation. Production code may seed from a sample window. Always record your seed rule in experiment notes.')

page('The main formulas', '07 / What each part does')
f('c_t = lambda * c_{t-1} + (1 - lambda) * x_t * y_t\nv_x,t = lambda * v_x,t-1 + (1 - lambda) * x_t^2\nv_y,t = lambda * v_y,t-1 + (1 - lambda) * y_t^2\n\nrho_t = c_t / sqrt(v_x,t * v_y,t)')
h('Step 1: Update covariance')
p('Multiply today\'s mean-adjusted returns. Blend that product with yesterday\'s covariance using lambda and 1 - lambda.')
h('Step 2: Update each variance')
p('Square each mean-adjusted return. Blend with yesterday\'s EWMA variance the same way. You need both variances positive before dividing.')
h('Step 3: Form rho')
p('Divide covariance by the geometric mean of the two EWMA standard deviations. The result stays in [-1, 1] when the variances are positive and the recursion is consistent.')
p('If either variance path hits zero (no movement in one series), rho is undefined until there is spread again.')

page('Formula details and lambda', '08 / Memory in one number')
h('What lambda = 0.94 means in words')
p('Roughly, the half-life of weight is ln(0.5)/ln(0.94) days (about 11 days). That is intuition, not a substitute for reading your risk policy. The key beginner fact: <b>6% new information, 94% old EWMA state</b> each step.')
h('Relation to Pearson on a window')
p('If you took a very long window and gave older points exponentially smaller weights, you would approach the same idea. EWMA is the compact online form: one number carried forward instead of storing all past returns.')
h('Same-day use')
p('The update at t includes x_t and y_t observed at t. Use rho_t for reporting and for rules that apply from the <b>next</b> bar onward unless your research design explicitly allows same-bar execution with a documented lag.')

page('Calculate it by hand: start', '09 / Worked example, part one')
p('Use lambda = 0.94 and three made-up mean-adjusted returns. Start c_0 = v_x,0 = v_y,0 = 0.')
table([['Day', 'x_t', 'y_t'], ['1', '0.0200', '0.0150'], ['2', '-0.0100', '-0.0080'], ['3', '0.0150', '0.0120']], [65, 150, 150])
h('Day 1 updates')
f('c_1 = 0.94*0 + 0.06*(0.02*0.015) = 0.000018\nv_x,1 = 0.06*(0.02^2) = 0.000024\nv_y,1 = 0.06*(0.015^2) = 0.0000135')
h('Day 2 updates')
f('c_2 = 0.94*0.000018 + 0.06*((-0.01)*(-0.008))\n    = 0.00002172\nv_x,2 = 0.94*0.000024 + 0.06*(0.01^2) = 0.00002856\nv_y,2 = 0.94*0.0000135 + 0.06*(0.008^2) = 0.00001653')

page('Calculate it by hand: finish', '10 / Worked example, part two')
h('Day 3 updates')
f('c_3 = 0.94*0.00002172 + 0.06*(0.015*0.012)\n    = 0.0000312168\nv_x,3 = 0.94*0.00002856 + 0.06*(0.015^2)\n    = 0.0000403464\nv_y,3 = 0.94*0.00001653 + 0.06*(0.012^2)\n    = 0.0000241782')
h('rho at day 3')
f('rho_3 = c_3 / sqrt(v_x,3 * v_y,3)\n      = about 0.99948')
p('With only three warm-up days and zero seeds, rho stays very high because x and y have the same sign each day in this toy list. A longer path with mixed signs would pull rho toward more moderate values.')
p('This hand path matches the Python check on page 11. Keep full decimals in code; round only for display.')

page('Using EWMA on major FX pairs', '11 / Effective practice')
h('Why majors are a common lab')
p('The eight majors are liquid and share overlapping sessions. EWMA rho between two dollar pairs often moves with shared USD shocks. That is descriptive, not proof of a stable structural link.')
h('Good habits before you run experiments')
p('Pick one lambda policy (e.g. 0.94 daily) and stick to it across pairs in a batch. Align bar times. Demean returns the same way for every pair. Store c_t, v_x,t, and v_y,t if you need to audit rho_t.')
h('What not to claim')
p('Do not rank pairs here: experiments are not started and this guide includes no invented EURUSD-GBPUSD results. When v001 exists, cite its snapshot id and parameters next to any reported rho.')
h('Compare to Pearson in folder 01')
p('Pearson on a fixed window answers a different question (equal weight over the window). EWMA answers a recent-memory question. Both can be valid; they should not be confused in reports.')

page('Limits and common errors', '12 / What EWMA cannot tell you')
h('Not a causal link')
p('High EWMA rho between two pairs can reflect a shared factor (often USD or risk sentiment), not that one pair drives the other.')
h('Lambda is a choice')
p('0.94 is a famous default, not a law of nature. Slower lambda reacts more slowly; faster lambda chases noise. Sensitivity checks belong in experiment notes.')
h('Linear, memory-weighted link only')
p('EWMA rho does not detect nonlinear dependence by itself. One volatile day can move c_t and v_t for many subsequent days through the 94% memory.')
h('Look-ahead and back-test hygiene')
p('If a strategy uses rho_t computed with the same bar\'s returns, your back-test must include the same lag you would have in live trading. Mixing same-bar rho with next-bar returns without documenting the rule is a common error.')

page('Calculate it with software', '13 / Reproduce the teaching example')
h('Python: tiny loop')
f('from math import sqrt\nlam = 0.94\nxs = [0.02, -0.01, 0.015]\nys = [0.015, -0.008, 0.012]\nc = vx = vy = 0.0\nfor x, y in zip(xs, ys):\n    c = lam*c + (1-lam)*x*y\n    vx = lam*vx + (1-lam)*x*x\n    vy = lam*vy + (1-lam)*y*y\nrho = c / sqrt(vx * vy)\nprint(rho)  # about 0.99948')
p('Libraries such as pandas (ewm) can compute weighted variance; you still need a clear plan for cross-series EWMA covariance (custom loop or multivariate RiskMetrics code). Match demeaning and lambda to this folder\'s experiment spec before comparing to any future v001 output.')
h('FX sanity checks')
f('assert abs(1.1110/1.1000 - 1 - 0.01) < 1e-12\nassert abs(log(1.1110/1.1000) - 0.009950330853168092) < 1e-12\nassert abs(rho - 0.999479760740298) < 1e-9')

page('Sources and further reading', '14 / Research trail')
p('Links checked on 3 November 2026. Teaching arithmetic and wording in this guide are original. Bracket numbers point to primary references.')
refs = [
    ('1', 'J.P. Morgan / Reuters (1996). RiskMetrics Technical Document.', 'https://www.morganmarkets.com/riskmetrics/', 'Industry reference for EWMA volatility and covariance; verify the archive copy your desk uses.'),
    ('2', 'SciPy / pandas documentation for exponential weighted moments.', 'https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html', 'Implementation details differ from hand loops; read adjust, min_periods, and bias flags.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/>'
        f'<link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Next step for this repo: run experiments/v001 under 06 - EWMA Correlation with a documented snapshot, lambda, and return definition, then compare software output to a saved hand-check row.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 06  |  EWMA CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='EWMA Correlation - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
page_count = len(reader.pages)
assert 14 <= page_count <= 16, f'Unexpected page count: {page_count}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text()
    assert len(text) > 350, (i + 1, len(text))
assert abs(FX_SIMPLE - 0.01) < 1e-12
assert abs(FX_LOG - 0.009950330853168092) < 1e-12
assert abs(RHO_TEACH - 0.999479760740298) < 1e-9
assert abs(C_FINAL - 0.0000312168) < 1e-10
print(f'Created and checked {page_count} pages: {OUT}')
