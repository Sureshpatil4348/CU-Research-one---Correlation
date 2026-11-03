from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Hayashi_Yoshida_Covariance_Complete_Simple_Guide.pdf'
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


# Teaching intervals: overlap matrix 1 = overlap
# X intervals: I1 [0,1], I2 [1,3]
# Y intervals: J1 [0,2], J2 [2,3]
DX = [0.010, 0.005]
DY = [0.012, 0.008]
OVERLAP = [[1, 0], [1, 1]]


def hy_covariance(dx, dy, overlap):
    total = 0.0
    for i, dxi in enumerate(dx):
        for j, dyj in enumerate(dy):
            if overlap[i][j]:
                total += dxi * dyj
    return total


C_HY = hy_covariance(DX, DY, OVERLAP)
FX_SIMPLE = 1.1110 / 1.1000 - 1
FX_LOG = log(1.1110 / 1.1000)


page('Hayashi-Yoshida covariance', 'Method 26 / A complete beginner guide')
p('<b>How do you estimate covariance when FX quotes arrive at different times?</b> The Hayashi-Yoshida estimator sums products of returns on overlapping intervals only.')
p('The output is a <b>covariance</b>, not a bounded correlation. Daily synced closes are the wrong input when your timestamps are async. Teaching example only; experiments not started.')
h('Read it in three parts')
p('<b>First:</b> Overlaps and FX percent returns. <b>Next:</b> Hayashi and Yoshida (2005) and the main sum. <b>Last:</b> Hand calculation, limits, and link to folder 25.')
table([['Pages', 'What you will learn'], ['2', 'Idea; covariance vs correlation'], ['3', 'FX 1.1000 to 1.1110'], ['4', 'Intervals and overlap indicator'], ['5', 'Hayashi & Yoshida 2005'], ['6-9', 'Formula and hand sum'], ['10-11', 'Why synced daily closes fail'], ['12-14', 'Limits, software, sources']], [65, 405])
p('Prepared for the folder: 26 - Hayashi-Yoshida Covariance<br/>3 November 2026')

page('What does HY covariance do?', '02 / The basic idea')
f('C_HY = SUM_i SUM_j  dX_i * dY_j * 1( I_i overlaps J_j )')
p('dX_i is the return on X over its own observation interval I_i. dY_j is the return on Y over J_j. The indicator is 1 when the time ranges overlap, else 0.')
h('Covariance, not correlation')
p('C_HY is on the scale of return products (for example decimal times decimal). It is <b>not</b> forced into [-1, +1]. To get a correlation shape you must divide by estimated variances with the same overlap logic.')
h('Is C_HY a percent?')
p('<b>No.</b> Returns may be labelled in percent; covariance inherits return units squared in the usual variance scaling story.')

page('FX percent math on one move', '03 / Returns in plain numbers')
f('Simple return on a leg: 1.1110/1.1000 - 1 = 0.01\nLog return: ln(1.1110/1.1000) = about 0.009950')
p('HY uses returns tied to each quote interval, not one artificial daily pair. Build dX_i from the price change between the tick times that define I_i.')
p('Document whether you use log or simple returns before you sum products.')

page('Intervals and overlaps', '04 / Data rules')
h('Record timestamps')
p('Each interval needs start and end in a common clock. Overlap means the ranges intersect with positive length; touching at one instant may be excluded depending on implementation—match your library to [1].')
h('Async is normal in FX')
p('EUR may update on one bank stream while JPY updates on another. HY avoids pretending both moved on a fictional shared close.')
h('Versus folder 25 realized correlation')
p('Realized rho with aligned intraday buckets is a different object. HY is for mismatched interval grids.')

page('Research notes', '05 / Hayashi and Yoshida 2005')
h('Hayashi, T., & Yoshida, N. (2005) [1]')
p('<i>Bernoulli</i>, 11(4), 729-749. Gives the overlap-sum covariance estimator for non-synchronously observed diffusions and studies its properties.')
p('Folder 25 cites the same paper for realized and async context. This folder focuses on the covariance sum itself.')
h('Claims in this guide')
p('Teaching overlap arithmetic only. No invented tick covariance for live pairs until experiments exist.')

page('Meet the symbols', '06 / Dictionary')
table([['Symbol', 'Meaning'], ['I_i', 'Time range for the i-th return on X.'], ['J_j', 'Time range for the j-th return on Y.'], ['dX_i, dY_j', 'Returns on those intervals.'], ['1(overlap)', '1 if I_i and J_j overlap, else 0.'], ['C_HY', 'Hayashi-Yoshida covariance estimate.']], [125, 345])
p('Some codes use half-open intervals [t_start, t_end). State your convention in experiment logs.')

page('The main formula', '07 / What each part does')
f('C_HY = SUM_i SUM_j  dX_i * dY_j * 1( I_i intersects J_j )')
h('Double sum')
p('Every X return pairs with every Y return, but zero weight when intervals do not overlap. Overlapping segments contribute their product once per qualifying pair.')
h('Scaling to correlation (optional)')
p('A HY-type correlation divides C_HY by sqrt(HY variance estimates for X and Y). That extra step is not automatic in the covariance formula above.')

page('Hand setup: intervals', '08 / Worked example part one')
p('Two X intervals and two Y intervals on a unit timeline (hours as labels):')
table([['Leg', 'Interval', 'Return'], ['X', 'I1: [0, 1]', 'dX1 = 0.010'], ['X', 'I2: [1, 3]', 'dX2 = 0.005'], ['Y', 'J1: [0, 2]', 'dY1 = 0.012'], ['Y', 'J2: [2, 3]', 'dY2 = 0.008']], [55, 150, 150])
p('Overlap grid (1 = yes): I1 with J1 yes, I1 with J2 no, I2 with J1 yes, I2 with J2 yes.')

page('Hand finish: the sum', '09 / Worked example part two')
f('Pairs counted:\n  I1-J1: 0.010 * 0.012 = 0.00012\n  I1-J2: skipped (no overlap)\n  I2-J1: 0.005 * 0.012 = 0.00006\n  I2-J2: 0.005 * 0.008 = 0.00004\n\nC_HY = 0.00012 + 0.00006 + 0.00004 = 0.00022')
p('Compare to the naive product of daily totals: you would miss which pieces of time actually shared information.')
h('Sign matters')
p('Negative dX_i or dY_j flip the product sign. Covariance can be negative without being invalid.')

page('Why daily synced closes are wrong', '10 / Input mistake')
h('The error')
p('Taking one close per day for X and one for Y forces a single interval pair. That discards timing inside the day and misstates overlap when quotes are async.')
h('Better habit')
p('Store tick or bar timestamps, build I_i and J_j from actual updates, then apply the indicator sum.')
p('If you only have daily closes, HY is not the right tool unless your question truly is daily and synchronous.')

page('Limits', '11 / What HY cannot tell you')
h('Not a trading rule')
p('Covariance magnitude does not include costs, causality, or stability.')
h('Microstructure noise')
p('Very noisy ticks inflate products; pre-averaging or kernel methods may be needed in production code.')
h('Not bounded')
p('Do not report C_HY as if it were a correlation without explicit normalisation.')

page('Software sketch', '12 / Reproduce the teaching sum')
f('dx = [0.010, 0.005]\ndy = [0.012, 0.008]\noverlap = [[1,0],[1,1]]\nc = 0.0\nfor i, xi in enumerate(dx):\n    for j, yj in enumerate(dy):\n        if overlap[i][j]:\n            c += xi * yj\nprint(c)  # 0.00022')
p('Production HY code builds overlap from timestamps automatically. Verify against one hand grid before scaling up.')

page('Sources and further reading', '13 / Research trail')
refs = [
    ('1', 'Hayashi, T., & Yoshida, N. (2005). On covariance estimation of non-synchronously observed diffusion processes. Bernoulli, 11(4), 729-749.', 'https://doi.org/10.3150/b/1125396764', 'Primary HY covariance reference.'),
    ('2', 'Folder 25 Volatility and Realized Correlation.', '../25%20-%20Volatility%20and%20Realized%20Correlation/README.md', 'Aligned-bucket realized versus async HY.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/>'
        f'<link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))

page('Check your understanding', '14 / Quick questions')
p('<b>Is C_HY a correlation?</b> No, unless you normalise separately. <b>Can I use two daily closes?</b> Not for async HY as taught here. <b>Does overlap matter?</b> Yes; the indicator is the core of the estimator.')
p('When experiments start, save the overlap matrix for one day and reconcile it to the double sum in your HY library.')

page('Workflow before experiments', '15 / Working method')
h('1. State the sampling reality')
p('Async ticks, unequal bar grids, or true daily sync—pick the estimator to match.')
h('2. Unit-check returns')
p('Include the 1.1000 to 1.1110 move as a decimal return sanity row in experiment notes.')
h('3. Log interval rules')
p('Half-open versus closed intervals change edge overlaps. Copy the rule from your package docs.')
h('4. Report covariance with units')
p('Say decimal log returns, sample window, and whether you also publish a HY correlation variant.')
p('Experiments not started. No live pair HY numbers in this folder until v001 with snapshot id.')

def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 26  |  HAYASHI-YOSHIDA COVARIANCE')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Hayashi-Yoshida Covariance - Complete Simple Guide',
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
assert abs(C_HY - 0.00022) < 1e-15
print(f'Created and checked {page_count} pages: {OUT}')
