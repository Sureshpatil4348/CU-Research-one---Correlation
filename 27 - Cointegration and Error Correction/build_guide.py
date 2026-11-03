from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Cointegration_and_Error_Correction_Complete_Simple_Guide.pdf'
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


ALPHA = 0.050
BETA = 1.100
PX = [1.1000, 1.1110, 1.1050]
PY = [1.2500, 1.2625, 1.2580]
LN_PX = [log(p) for p in PX]
LN_PY = [log(p) for p in PY]
SPREAD = [lpy - ALPHA - BETA * lpx for lpy, lpx in zip(LN_PY, LN_PX)]
# ECM one-lag teaching: delta ln(PY)_2 = c + kappa * e_1
C_ECM = 0.001
KAPPA = -0.35
E1 = SPREAD[0]
D_LN_PY_2 = LN_PY[1] - LN_PY[0]
ECM_PRED = C_ECM + KAPPA * E1
FX_SIMPLE = 1.1110 / 1.1000 - 1
FX_LOG = log(1.1110 / 1.1000)


page('Cointegration and error correction', 'Method 27 / A complete beginner guide')
p('<b>When do two FX log prices share a long-run anchor, and how does the short-run return pull toward it?</b> Cointegration uses log price levels. Error correction adds the lagged spread to a return equation.')
p('This is <b>not</b> return correlation. Correlated returns can still leave a non-mean-reverting spread. Teaching numbers only; experiments not started.')
h('Read it in three parts')
p('<b>First:</b> Spread in log space and FX percent. <b>Next:</b> Engle-Granger (1987) context, ECM with kappa. <b>Last:</b> Hand rows, beta is not lot size, limits.')
table([['Pages', 'What you will learn'], ['2', 'Levels vs return correlation'], ['3', 'FX 1.1000 to 1.1110 in logs'], ['4', 'Spread e and parameters alpha, beta'], ['5', 'Engle & Granger 1987'], ['6-9', 'ECM formula and hand rows'], ['10-11', 'Beta not hedge lots'], ['12-14', 'Limits, checks, sources']], [65, 405])
p('Prepared for the folder: 27 - Cointegration and Error Correction<br/>3 November 2026')

page('What does cointegration ask?', '02 / The basic idea')
f('e_t = ln(PY_t) - alpha - beta * ln(PX_t)')
p('PY and PX are FX prices in consistent units. The spread e_t is a log-price gap. Cointegration means e_t is stationary (mean-reverting) even when each log price trends.')
h('Error correction on returns')
f('delta ln(PY_t) = c + kappa * e_{t-1} + lags + u_t')
p('kappa negative often means last period\'s positive spread pulls today\'s ln(PY) return down, nudging e toward zero. Lags and u_t carry short-run dynamics.')
h('Not Pearson on returns')
p('Folder 01 correlation of returns does not test this level anchor. Two return series can correlate highly while e_t drifts.')

page('FX percent math on one move', '03 / Log prices and returns')
p('From <b>1.1000 to 1.1110</b> on PX:')
f('Simple return = 0.01  (1.00% label)\nln(PX_new) - ln(PX_old) = ln(1.1110/1.1000) = about 0.009950')
p('Cointegration works in log price levels ln(P_t). Returns enter the ECM as changes delta ln(P_t). Use natural logs consistently for both legs.')
p('Percent labels describe returns; spread e_t lives in log-price units, not percent points.')

page('Spread parameters', '04 / Data rules')
h('Estimate alpha and beta')
p('Engle-Granger step one regresses ln(PY) on ln(PX) (or vice versa per your design) to obtain alpha hat and beta hat. Step two tests whether residuals e_t are stationary.')
h('Same clock')
p('Row t must be the same time for both prices. Gaps in quotes need a documented rule before v001 experiments.')
h('FX quotes')
p('State which currency is base and quote for PX and PY. Reversing a quote changes log levels and beta interpretation.')

page('Research notes', '05 / Engle and Granger 1987')
h('Engle, R. F., & Granger, C. W. J. (1987) [1]')
p('<i>Econometrica</i>, 55(2), 251-276. Two-step cointegration and error-correction representation linking long-run equilibrium and short-run adjustments.')
p('Modern systems use Johansen and other multivariate tests; this guide stays with the beginner spread plus ECM form used in many FX pair notes.')
h('Claims here')
p('Teaching spread and one ECM row only. No claim that any major pair is cointegrated until you run tests on snapshot data.')

page('Meet the symbols', '06 / Dictionary')
table([['Symbol', 'Meaning'], ['ln(P)', 'Natural log of price; requires P &gt; 0.'], ['alpha', 'Intercept in log-log relation.'], ['beta', 'Slope on ln(PX); not automatic lot size.'], ['e_t', 'Spread / equilibrium error at t.'], ['kappa', 'Error-correction speed on e_{t-1}.'], ['delta ln(PY)', 'First difference of log price Y.']], [125, 345])
p('Lags of delta ln(PY) and delta ln(PX) absorb short-run dynamics omitted in the tiny hand example.')

page('The main equations', '07 / What each part does')
f('e_t = ln(PY_t) - alpha - beta * ln(PX_t)\n\ndelta ln(PY_t) = c + kappa * e_{t-1}\n                   + lag terms + u_t')
h('Read kappa')
p('If kappa = -0.35, a spread e_{t-1} = +0.10 adds -0.035 to today\'s delta ln(PY) before lags. Sign and magnitude depend on units of e.')
h('Stationarity of e')
p('Cointegration requires statistical evidence that e_t does not behave like a random walk. ADF or similar tests belong in your estimation notebook, not skipped silently.')

page('Hand calc: spread rows', '08 / Worked example part one')
p('Teaching alpha = 0.050, beta = 1.100 (fixed for arithmetic):')
table([['t', 'PX', 'PY', 'ln(PX)', 'ln(PY)', 'e_t'], ['1', '1.1000', '1.2500', f'{LN_PX[0]:.5f}', f'{LN_PY[0]:.5f}', f'{SPREAD[0]:.5f}'], ['2', '1.1110', '1.2625', f'{LN_PX[1]:.5f}', f'{LN_PY[1]:.5f}', f'{SPREAD[1]:.5f}'], ['3', '1.1050', '1.2580', f'{LN_PX[2]:.5f}', f'{LN_PY[2]:.5f}', f'{SPREAD[2]:.5f}']], [35, 65, 65, 75, 75, 75])
p('PX row 2 uses the familiar 1.1000 to 1.1110 move. e_t is not a return percent; compare it only across time with the same alpha and beta.')

page('Hand calc: one ECM row', '09 / Worked example part two')
f('delta ln(PY)_2 = ln(PY_2) - ln(PY_1) = about 0.009950\n(same magnitude as the log return on PY for that step)\n\ne_1 = {e1:.6f}\nECM part: c + kappa * e_1 = {c} + ({k}) * e_1\n         = about {pred:.6f} (teaching c, kappa fixed)'
    .format(e1=E1, c=C_ECM, k=KAPPA, pred=ECM_PRED))
p('Full estimation fits c, kappa, and lags by regression on a long sample. Here we show how one lagged spread enters one return row.')
p('Correlated daily returns could still leave e_t drifting if the level anchor fails.')

page('Beta is not automatic lot size', '10 / Trading caution')
h('Hedge ratio confusion')
p('beta links log levels in a cointegrating regression. It is not automatically the FX lot ratio for PnL hedging without conversion through levels, volatility, and account currency.')
h('Mean reversion is statistical')
p('Even with cointegration, e_t can stay wide for long spans. Risk limits must use spread volatility, not only kappa sign.')
h('Versus folder 01')
p('High return correlation does not imply mean-reverting e_t. Report which object you estimated.')

page('Limits', '11 / What this cannot prove')
h('Not proof of profitability')
p('Stationary spread models ignore costs, jumps, and regime breaks.')
h('Structural breaks')
p('Fixing alpha and beta across crisis periods can fail. Rolling or break tests may be needed in v001.')
h('Multiple currencies')
p('Triangular FX relationships may need multivariate cointegration rather than one pairwise spread.')

page('Software sketch', '12 / Spread and ECM row')
f('from math import log\nalpha, beta = 0.05, 1.1\npx, py = 1.1110, 1.2625\nlnpx, lnpy = log(px), log(py)\ne = lnpy - alpha - beta*lnpx\nkappa = -0.35\nc = 0.001\nprint(c + kappa * e)  # ECM contribution from e at t-1')
p('Use statsmodels.tsa.stattools.coint for Engle-Granger tests and OLS for step one when you move beyond toy rows.')

page('Sources and further reading', '13 / Research trail')
refs = [
    ('1', 'Engle, R. F., & Granger, C. W. J. (1987). Co-integration and error correction: representation, estimation, and testing. Econometrica, 55(2), 251-276.', 'https://doi.org/10.2307/1913236', 'Primary cointegration and ECM reference.'),
    ('2', 'Folder 01 Pearson Correlation.', '../01%20-%20Pearson%20Correlation/README.md', 'Return correlation contrast.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/>'
        f'<link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))

page('Check your understanding', '14 / Quick questions')
p('<b>Do I use log prices or returns for e_t?</b> Log prices inside e_t; returns enter the ECM as deltas. <b>Does high return correlation imply cointegration?</b> No. <b>Is beta my hedge lot?</b> Not automatically.')
p('When experiments start, save alpha hat, beta hat, ADF p-value on e_t, and kappa with standard errors from the same snapshot window.')

page('Workflow before experiments', '15 / Working method')
h('1. Write the economic pair')
p('Name PX and PY with quote directions and why a long-run anchor might exist (policy band, cross-rate identity, etc.).')
h('2. Levels first, returns second')
p('Build ln(P) series, estimate spread, test stationarity, then specify ECM lags.')
h('3. Unit check')
p('Verify 1.1000 to 1.1110 log increment matches your return column for PX.')
h('4. Report all steps')
p('Do not report only kappa without alpha, beta, and test outcomes.')
p('Experiments not started. No live cointegration claims until v001 with frozen snapshot.')

def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 27  |  COINTEGRATION AND ERROR CORRECTION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Cointegration and Error Correction - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
page_count = len(reader.pages)
assert 14 <= page_count <= 16, f'Unexpected page count: {page_count}'
for i, pg in enumerate(reader.pages):
    assert len(pg.extract_text()) > 350, (i + 1, len(pg.extract_text()))
assert abs(FX_SIMPLE - 0.01) < 1e-12
assert abs(FX_LOG - 0.009950330853168092) < 1e-12
assert abs(D_LN_PY_2 - FX_LOG) < 1e-12
assert abs(ECM_PRED - (C_ECM + KAPPA * E1)) < 1e-15
print(f'Created and checked {page_count} pages: {OUT}')
