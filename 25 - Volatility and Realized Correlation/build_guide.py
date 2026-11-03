from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Volatility_and_Realized_Correlation_Complete_Simple_Guide.pdf'
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


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    dx = [v - mx for v in xs]
    dy = [v - my for v in ys]
    top = sum(a * b for a, b in zip(dx, dy))
    bot = sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
    return top / bot


RET_X = [0.010, -0.005, 0.008]
RET_Y = [0.012, 0.004, -0.006]
ABS_X = [abs(v) for v in RET_X]
ABS_Y = [abs(v) for v in RET_Y]
RHO_VOL = pearson(ABS_X, ABS_Y)
INTRA_X = [0.004, 0.003, 0.003]
INTRA_Y = [0.005, 0.002, 0.005]
REALIZED_NUM = sum(a * b for a, b in zip(INTRA_X, INTRA_Y))
REALIZED_DEN = sqrt(sum(a * a for a in INTRA_X) * sum(b * b for b in INTRA_Y))
RHO_REALIZED = REALIZED_NUM / REALIZED_DEN
FX_SIMPLE = 1.1110 / 1.1000 - 1
FX_LOG = log(1.1110 / 1.1000)


page('Volatility and realized correlation', 'Method 25 / A complete beginner guide')
p('<b>Two different ways FX co-movement shows up in volatility.</b> Volatility correlation tracks whether absolute moves align. Realized correlation sums intraday return products within a day.')
p('These are <b>two separate calculations</b>. Do not mix daily closing prices into the realized formula when your question needs intraday buckets. Teaching numbers only; experiments not started.')
h('Read it in three parts')
p('<b>First:</b> Definitions and the FX percent example. <b>Next:</b> Formulas and hand work for rho_vol and rho_realized. <b>Last:</b> Hayashi-Yoshida (2005) context, limits, and folder 26 link.')
table([['Pages', 'What you will learn'], ['2', 'Two tools, not one'], ['3', 'FX 1.1000 to 1.1110 percent'], ['4', 'Which series each formula uses'], ['5', 'Hayashi & Yoshida 2005 context'], ['6-9', 'Symbols, formulas, two hand calcs'], ['10-11', 'Why daily closes fail for realized'], ['12-14', 'Limits, software, sources']], [65, 405])
p('Prepared for the folder: 25 - Volatility and Realized Correlation<br/>3 November 2026')

page('Two tools, one folder', '02 / The basic idea')
h('Volatility correlation')
f('rho_vol = Corr( |x_t|, |y_t| )')
p('Apply Pearson (folder 01) to absolute returns (or another volatility proxy) on the same bar clock. It asks whether big moves in X tend to coincide with big moves in Y, ignoring sign.')
h('Realized correlation within day d')
f('rho_realized,d = SUM_k x(d,k)*y(d,k) /\n  sqrt( SUM_k x(d,k)^2 * SUM_k y(d,k)^2 )')
p('Here x(d,k) and y(d,k) are intraday returns in bucket k on day d. The formula is a correlation shape applied to within-day vectors, not to one daily close pair.')
h('Is either score a price percent?')
p('<b>No.</b> Both live on [-1, +1] (when defined). A 1.00% return is input data, not rho_vol or rho_realized.')

page('FX percent math on one move', '03 / Returns in plain numbers')
f('Simple: 1.1110/1.1000 - 1 = 0.01  (1.00%)\nLog: ln(1.1110/1.1000) = about 0.009950')
p('Volatility correlation uses a series of such bar returns, then takes absolute values. Realized correlation splits a day into k buckets (for example 30-minute legs) and uses those bucket returns inside the sums.')
p('Keep one return definition per study. Mixing simple |x| with log y breaks comparability.')

page('Which data for which formula?', '04 / Data rules')
h('rho_vol')
p('Needs aligned bar returns x_t and y_t on the same schedule. Weekly or daily bars are common. You correlate |x_t| with |y_t|, not raw signed returns unless your question says otherwise.')
h('rho_realized,d')
p('Needs intraday returns x(d,k) and y(d,k) for the same day d. Using only two daily closing prices to stand in for SUM_k x(d,k)y(d,k) is the wrong input for this realized definition.')
h('Async quotes')
p('If buckets do not line up in time, see folder 26 (Hayashi-Yoshida covariance) for overlap-aware covariance. Realized correlation here assumes aligned buckets within the day.')

page('Research context', '05 / Hayashi and Yoshida 2005')
h('Hayashi, T., & Yoshida, N. (2005) [1]')
p('Developed covariance and correlation estimators for asynchronously observed processes. Realized FX research often cites this line when closing-time mismatch would bias naive covariances.')
p('This folder separates (a) volatility co-movement rho_vol and (b) within-day realized rho_realized,d. Folder 26 gives the overlap-sum covariance when timestamps differ.')
h('What we claim')
p('Teaching arithmetic only. No invented EURUSD realized paths. When experiments start, log bucket size, timezone, and whether rho_realized is averaged across days.')

page('Meet the symbols', '06 / Dictionary')
table([['Symbol', 'Meaning'], ['x_t, y_t', 'Bar returns (often log) at time t.'], ['|x_t|', 'Absolute return or volatility proxy at t.'], ['rho_vol', 'Pearson correlation of |x| and |y| series.'], ['x(d,k)', 'Intraday return in bucket k on day d.'], ['rho_realized,d', 'Within-day correlation of intraday vectors.']], [125, 345])
p('Some papers average rho_realized,d over d to get a series. State your aggregation rule explicitly in reports.')

page('Volatility correlation formula', '07 / rho_vol')
f('rho_vol = Corr( |x_1|,|y_1| ), ..., ( |x_n|,|y_n| )')
p('Use the Pearson steps from folder 01 on the absolute-value lists. Zero returns contribute zeros to |x|; they are not missing unless you drop the bar.')
h('Interpretation')
p('High rho_vol means volatility shocks tend to arrive together. Signed return correlation can be low while rho_vol is high if both legs often move a lot in opposite directions.')

page('Realized correlation formula', '08 / rho_realized,d')
f('num_d = SUM_k x(d,k) * y(d,k)\nden_d = sqrt( SUM_k x(d,k)^2 * SUM_k y(d,k)^2 )\nrho_realized,d = num_d / den_d')
p('For a single day this is the cosine similarity of the two intraday return vectors. It equals their Pearson correlation when both lists have varying values.')
h('Not the same as rho_vol')
p('rho_vol compares volatility levels across days (or bars). rho_realized,d compares intraday co-movement patterns inside one day. Compute both only when your question needs both.')

page('Hand calc: rho_vol', '09 / Worked example A')
p('Three made-up daily returns (decimals):')
table([['t', 'x_t', 'y_t', '|x_t|', '|y_t|'], ['1', '0.010', '0.012', '0.010', '0.012'], ['2', '-0.005', '0.004', '0.005', '0.004'], ['3', '0.008', '-0.006', '0.008', '0.006']], [40, 70, 70, 70, 70])
f('rho_vol = Pearson(|x|, |y|) = about 0.9226 in this toy list')
p('Opposite signed returns on row 3 still have positive absolute values, so volatility can align even when direction differs.')

page('Hand calc: rho_realized,d', '10 / Worked example B')
p('One teaching day with three intraday buckets:')
table([['k', 'x(d,k)', 'y(d,k)'], ['1', '0.004', '0.005'], ['2', '0.003', '0.002'], ['3', '0.003', '0.005']], [55, 150, 150])
f('num = 0.004*0.005 + 0.003*0.002 + 0.003*0.005 = 0.000041\nsum x^2 = 0.000034, sum y^2 = 0.000054\nden = sqrt(0.000034 * 0.000054)\nrho_realized,d = about 0.9569')
p('If you only had daily closes for that day, you would have one return pair, not this three-bucket vector. That is why daily closes are the wrong input for this realized formula.')

page('Daily closes vs intraday buckets', '11 / Common error')
h('Wrong shortcut')
p('Taking open-to-close once per day and plugging it into SUM_k x(d,k)y(d,k) mislabels a single return as a full intraday sum.')
h('Right habit')
p('Store bucket timestamps, enforce equal bucket rules or document irregular spacing, and compute rho_realized,d per day before any cross-day average.')
p('For volatility correlation, daily closes are fine if x_t and y_t are daily returns and you want rho_vol on daily |x| and |y|.')

page('Limits', '12 / What these scores cannot prove')
h('Not hedge ratios')
p('Correlation of absolute returns does not give a beta for levels or a cointegration hedge (folder 27).')
h('Microstructure noise')
p('Very fine buckets add noise; very coarse buckets hide within-day structure.')
h('Versus folder 26')
p('Hayashi-Yoshida sums overlapping intervals. Realized rho here assumes aligned intraday buckets.')

page('Software sketch', '13 / Reproduce teaching numbers')
f('from math import sqrt\n\ndef pearson(x, y):\n    mx, my = sum(x)/len(x), sum(y)/len(y)\n    dx = [a-mx for a in x]; dy = [b-my for b in y]\n    t = sum(a*b for a,b in zip(dx,dy))\n    b = sqrt(sum(a*a for a in dx)*sum(b*b for b in dy))\n    return t/b\n\nrho_vol = pearson([0.01,0.005,0.008],[0.012,0.004,0.006])\n# Realized: intraday lists in INTRA_X, INTRA_Y')
p('Libraries for realized volatility often provide bucketed returns; map their output to x(d,k) before you apply the formula on page 8.')

page('Sources and further reading', '14 / Research trail')
refs = [
    ('1', 'Hayashi, T., & Yoshida, N. (2005). On covariance estimation of non-synchronously observed diffusion processes. Bernoulli, 11(4), 729-749.', 'https://doi.org/10.3150/b/1125396764', 'Async covariance foundation; related to realized FX practice.'),
    ('2', 'Folder 01 Pearson Correlation guide.', '../01%20-%20Pearson%20Correlation/Pearson_Correlation_Complete_Simple_Guide.pdf', 'Pearson steps used inside rho_vol.'),
    ('3', 'Folder 26 Hayashi-Yoshida Covariance.', '../26%20-%20Hayashi-Yoshida%20Covariance/README.md', 'Overlap covariance when buckets are not aligned.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/>'
        f'<link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Next: experiments/v001 with logged bucket grid and separate CSV columns for rho_vol series and daily rho_realized,d.')

page('Checklist before experiments', '15 / Working method')
h('1. Name which measure you need')
p('Volatility co-movement (rho_vol) versus within-day pattern (rho_realized,d). Do not report one as the other.')
h('2. Build returns consistently')
p('Same quote convention, timezone, and log-or-simple choice. Include the 1.1000 to 1.1110 percent example in notes as a unit check.')
h('3. Validate inputs')
p('For realized work, count buckets per day and flag days with missing intraday data instead of silently reusing closes.')
h('4. Report uncertainty')
p('Toy lists here omit confidence bands. Real studies should state sample length and stability across subsamples.')
p('Experiments not started. No live pair claims belong in this folder until v001 exists with snapshot id.')

def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 25  |  VOLATILITY AND REALIZED CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Volatility and Realized Correlation - Complete Simple Guide',
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
assert abs(RHO_VOL - 0.9226129063148777) < 1e-9
assert abs(RHO_REALIZED - 0.9568580574191401) < 1e-9
print(f'Created and checked {page_count} pages: {OUT}')
