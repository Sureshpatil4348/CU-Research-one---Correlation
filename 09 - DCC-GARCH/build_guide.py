from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'DCC_GARCH_Complete_Simple_Guide.pdf'
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


A_DCC, B_DCC = 0.05, 0.90
QBAR_OFF, QBAR_II, QBAR_JJ = 0.25, 0.40, 0.36
Q11_PREV, Q22_PREV, Q12_PREV = 0.40, 0.36, 0.30
Z1_PREV, Z2_PREV = 1.0, 0.5
FX_SIMPLE = 1.1110 / 1.1000 - 1
FX_LOG = log(1.1110 / 1.1000)

ONE_MINUS = 1 - A_DCC - B_DCC
Q12_T = ONE_MINUS * QBAR_OFF + A_DCC * Z1_PREV * Z2_PREV + B_DCC * Q12_PREV
Q11_T = ONE_MINUS * QBAR_II + A_DCC * Z1_PREV ** 2 + B_DCC * Q11_PREV
Q22_T = ONE_MINUS * QBAR_JJ + A_DCC * Z2_PREV ** 2 + B_DCC * Q22_PREV
RHO_T = Q12_T / sqrt(Q11_T * Q22_T)


def dcc_q_update(qbar, q_prev, z1, z2, a=A_DCC, b=B_DCC):
    return (1 - a - b) * qbar + a * z1 * z2 + b * q_prev


page('DCC-GARCH correlation', 'Method 09 / A complete beginner guide')
p('<b>How do two FX return series co-move when volatility changes day by day?</b> Dynamic Conditional Correlation (DCC) sits on top of GARCH-style variance models and updates a correlation matrix each period.')
p('This guide explains the standardised shocks z, the Q recursion, and how rho is read from Q. All examples are teaching numbers. Experiments in this folder have not started.')
h('Read it in three parts')
p('<b>First:</b> Idea, percent returns, and data choice. <b>Next:</b> Engle (2002) context, symbols, formulas, and a hand step. <b>Last:</b> Practice on majors, limits, and software checks.')
table([['Pages', 'What you will learn'], ['2', 'The idea and whether rho is a percent'], ['3', 'FX percent math on a worked quote move'], ['4', 'Which series and the GARCH layer'], ['5', 'Research: Engle 2002 DCC'], ['6-9', 'Symbols, DCC formulas, and hand calculation'], ['10-11', 'Using DCC on FX pairs and limits'], ['12-14', 'Checks, software, and sources']], [65, 405])
p('Prepared for the folder: 09 - DCC-GARCH<br/>3 November 2026')

page('What does DCC-GARCH do?', '02 / The basic idea')
p('Each asset has a GARCH model for its own volatility. The raw shock epsilon_t is divided by its conditional standard deviation sigma_t to form a <b>standardised residual</b> z_t. DCC then tracks how z values co-move over time.')
h('The answer is rho_ij,t')
p('For pair (i, j), rho_ij,t is between -1 and +1. It comes from the off-diagonal Q entry divided by the square roots of the diagonal Q entries. It is <b>not</b> a percent.')
table([['Piece', 'Plain meaning'], ['GARCH layer', 'Updates sigma_i,t from past squared shocks.'], ['z_t = eps / sigma', 'Puts shocks on a comparable scale.'], ['Q recursion', 'Remembers co-movement of past z values.'], ['rho from Q', 'Turns Q into a proper correlation number.']], [90, 380])
h('Is this a percent?')
p('<b>No.</b> Daily returns may be written as 1.00% or 0.01. DCC rho is a correlation on [-1, +1]. Parameters a and b are weights, not percent labels for rho.')

page('FX percent math on one move', '03 / Returns in plain numbers')
p('Take a quote move from <b>1.1000 to 1.1110</b> in one period (same units).')
f('Simple return = P_new / P_old - 1\n= 1.1110 / 1.1000 - 1\n= 0.01  (1.00% as a percent label)')
f('Log return = ln(P_new / P_old)\n= ln(1.1110 / 1.1000)\n= about 0.009950  (about 0.995% as a percent label)')
p('DCC is fitted on return series (often log returns). GARCH models those returns; DCC models the correlation of the standardised residuals. Use the same return definition for every leg in a batch.')

page('Which series does this method use?', '04 / Data and the two layers')
h('Returns first, not price levels')
p('Feed GARCH with per-asset return series aligned in time. Price levels can trend together while short-horizon correlation of returns is modest. Document bar close, time zone, and quote direction.')
h('One GARCH per series')
p('Each currency leg (or portfolio return) gets its own variance model. DCC links the z vectors across legs. You need enough history to estimate GARCH and DCC parameters jointly or in a staged workflow.')
h('Pairing')
p('Row t means the same clock time for every series. Missing bars break the panel; do not silently fill with zero returns without a rule in experiment notes.')
p('When experiments start under experiments/v001/, cite the snapshot id, return type, and estimation window. This guide reports no live pair results.')

page('Where did DCC come from?', '05 / Research notes')
h('Engle, R. (2002). Dynamic Conditional Correlation [1]')
p('<i>Journal of Business &amp; Economic Statistics</i>, 20(3), 339-350. Engle separates univariate GARCH variances from a correlation update that is designed to stay positive definite when mapped to rho.')
p('The DCC model became a standard way to build multivariate GARCH with a manageable parameter count: two scalars a and b (plus targets q_bar) drive the whole correlation matrix update in the basic specification.')
h('What this guide claims')
p('We summarise the teaching form of the Q recursion and rho mapping used in textbooks and in the arch / rugarch family of implementations. Full maximum likelihood theory and constraint handling belong in the paper and in your estimation code notes.')
p('Check the journal record or DOI 10.1198/073500102288618487 when you need exact notation.')

page('Meet the symbols', '06 / A small math dictionary')
table([['Symbol', 'Meaning'], ['epsilon_i,t', 'Raw return shock after mean model (often GARCH residual).'], ['sigma_i,t', 'Conditional std dev from univariate GARCH.'], ['z_i,t', 'Standardised shock: epsilon_i,t / sigma_i,t.'], ['q_ij,t', 'DCC quasi-correlation entry for pair (i, j).'], ['q_bar_ij', 'Unconditional target for q_ij (estimated).'], ['a, b', 'DCC news and persistence weights; a,b >= 0 and a+b < 1.'], ['rho_ij,t', 'Conditional correlation at t.']], [125, 345])
p('Diagonal entries q_ii,t follow the same recursion with z_i,t-1 squared instead of a cross product. Off-diagonal entries use z_i,t-1 * z_j,t-1.')

page('The main DCC formulas', '07 / What each part does')
f('z_i,t = epsilon_i,t / sigma_i,t\n\nq_ij,t = (1 - a - b) * q_bar_ij\n         + a * z_i,t-1 * z_j,t-1\n         + b * q_ij,t-1\n\nrho_ij,t = q_ij,t / sqrt(q_ii,t * q_jj,t)')
h('Parameter constraints')
p('Require a >= 0, b >= 0, and a + b &lt; 1 so the Q process is stable and weights sum to less than one on the lagged Q term together with the intercept mass (1-a-b).')
h('Why lag z at t-1')
p('The conditional correlation at t is written with information up through t-1 in the standard DCC timing used in estimation packages. Match your software manual when you map to trading lags.')

page('From z to rho: intuition', '08 / Reading the recursion')
h('News term a * z_i * z_j')
p('If both series had large positive standardised shocks yesterday, the news term is positive and pushes q_ij up before scaling to rho. Opposite signs pull it down.')
h('Memory term b * q_ij,t-1')
p('High b means correlation structure changes slowly. The intercept (1-a-b)*q_bar pulls Q toward a long-run level.')
h('Scaling to rho')
p('Dividing by sqrt(q_ii * q_jj) keeps rho in [-1, 1] when Q is valid. If estimation breaks positive definiteness, fix the optimizer or reduce model complexity; do not silently clip rho without logging.')

page('Calculate it by hand: one step', '09 / Worked example')
p('Use teaching parameters a = 0.05, b = 0.90. Suppose at t-1: z_1 = 1.0, z_2 = 0.5, q_11 = 0.40, q_22 = 0.36, q_12 = 0.30. Targets q_bar_12 = 0.25, q_bar_11 = 0.40, q_bar_22 = 0.36.')
h('Update q_12,t')
f('(1 - a - b) = 0.05\nq_12,t = 0.05*0.25 + 0.05*(1.0*0.5) + 0.90*0.30\n       = 0.0125 + 0.025 + 0.27 = 0.3075')
h('Update diagonals and rho')
f('q_11,t = 0.05*0.40 + 0.05*1.0^2 + 0.90*0.40 = 0.43\nq_22,t = 0.05*0.36 + 0.05*0.5^2 + 0.90*0.36 = 0.3545\n\nrho_12,t = 0.3075 / sqrt(0.43 * 0.3545)\n         = about 0.7876')
p('This is one step only. Real DCC also re-estimates GARCH volatilities and (a, b, q_bar) from data. The arithmetic above checks that you understand the Q-to-rho map.')

page('Using DCC on major FX pairs', '10 / Effective practice')
h('When DCC helps')
p('You want a time-varying correlation matrix for risk or hedging when volatilities are unequal and changing. Dollar blocks often move together in stress; DCC describes that co-movement with a standard recipe.')
h('Good habits')
p('Keep one return type, one bar time, and one estimation window policy across pairs. Save sigma_t, z_t, Q_t, and rho_t if you must audit risk reports. Compare to rolling Pearson (folder 05) only with a clear question in mind.')
h('What not to claim yet')
p('Experiments are not started. Do not invent EURUSD-GBPUSD DCC paths in reports. When v001 exists, tie numbers to snapshot id and fitted parameters.')

page('Limits and common errors', '11 / What DCC cannot tell you')
h('Not causation')
p('High conditional correlation can reflect shared factors (USD, rates, risk appetite), not that one pair drives another.')
h('Model risk')
p('GARCH mis-specification flows into z_t and then into DCC. Wrong lag structure or fat tails can bias rho paths.')
h('Look-ahead')
p('Fitted rho_t uses data through t under your package timing. Back-tests must respect the same information set you would have had live.')
h('Versus EWMA (folder 06)')
p('EWMA is a lighter exponential update. DCC is a full likelihood-based multivariate framework with separate variance and correlation blocks.')

page('Check your understanding', '12 / Quick questions')
h('A. Is rho a percent?')
p('<b>No.</b> It is a correlation on [-1, +1]. Returns can be percent-labelled; rho cannot.')
h('B. What feeds DCC?')
p('Standardised residuals z from GARCH, not raw price levels.')
h('C. Why a + b &lt; 1?')
p('So the Q recursion is stable and the intercept weight (1-a-b) is positive.')
h('D. One-step vs full fit')
p('The hand example updates Q for given z and parameters. Full DCC also estimates GARCH and (a, b) by likelihood on a long sample.')
p('When experiments start, save one row of z_t, Q_t, and rho_t from software and compare to a spreadsheet copy of the formulas on page 9.')

page('Calculate it with software', '13 / Reproduce the teaching step')
h('Python: one DCC q update and rho')
f('from math import sqrt\na, b = 0.05, 0.90\nq12 = (1-a-b)*0.25 + a*1.0*0.5 + b*0.30\nq11 = (1-a-b)*0.40 + a*1.0**2 + b*0.40\nq22 = (1-a-b)*0.36 + a*0.5**2 + b*0.36\nrho = q12 / sqrt(q11 * q22)\nprint(rho)  # about 0.7876')
p('Packages such as arch (Python) implement DCC estimation. Read their standardisation and mean-model defaults before comparing to this hand row.')
h('Sanity asserts used in build_guide.py')
f('assert a >= 0 and b >= 0 and a + b < 1\nassert abs(1.1110/1.1000 - 1 - 0.01) < 1e-12\nassert abs(rho - 0.7854...) < 1e-3')

page('Sources and further reading', '14 / Research trail')
p('Links checked on 3 November 2026. Teaching arithmetic in this guide is original. Bracket numbers point to primary references.')
refs = [
    ('1', 'Engle, R. (2002). Dynamic Conditional Correlation. Journal of Business & Economic Statistics, 20(3), 339-350.', 'https://doi.org/10.1198/073500102288618487', 'Primary DCC reference; notation and constraints.'),
    ('2', 'arch library documentation: multivariate volatility models.', 'https://arch.readthedocs.io/', 'Implementation details for DCC in Python; verify version and API.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/>'
        f'<link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Next step: run experiments/v001 with a frozen snapshot, documented returns, and saved GARCH-DCC fit output compared to one hand-check row.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 09  |  DCC-GARCH')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='DCC-GARCH - Complete Simple Guide',
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
assert abs(dcc_q_update(QBAR_OFF, Q12_PREV, Z1_PREV, Z2_PREV) - Q12_T) < 1e-12
assert abs(RHO_T - 0.7875946775225997) < 1e-9
print(f'Created and checked {page_count} pages: {OUT}')
