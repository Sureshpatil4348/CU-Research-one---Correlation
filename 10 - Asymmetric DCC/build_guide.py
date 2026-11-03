from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Asymmetric_DCC_Complete_Simple_Guide.pdf'
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


A_ADCC, B_ADCC, G_ADCC = 0.05, 0.85, 0.05
QBAR, Q_PREV = 0.22, 0.28
Z1_PREV, Z2_PREV = -0.6, -0.4
N1, N2 = min(Z1_PREV, 0), min(Z2_PREV, 0)
FX_SIMPLE = 1.1110 / 1.1000 - 1
FX_LOG = log(1.1110 / 1.1000)

Q12_T = (1 - A_ADCC - B_ADCC - G_ADCC) * QBAR + A_ADCC * Z1_PREV * Z2_PREV + G_ADCC * N1 * N2 + B_ADCC * Q_PREV


page('Asymmetric DCC correlation', 'Method 10 / A complete beginner guide')
p('<b>What if bad news moves FX correlations differently from good news?</b> Asymmetric DCC extends standard DCC with an extra term that reacts to <b>negative</b> standardised shocks.')
p('You will see n_i = min(z_i, 0), the g weight, and why quote inversion changes the meaning of a negative shock. Teaching numbers only; experiments not started.')
h('Read it in three parts')
p('<b>First:</b> Idea, percent returns, data. <b>Next:</b> Cappiello-Engle-Sheppard (2006), symbols, formulas, hand step. <b>Last:</b> FX practice, limits, software.')
table([['Pages', 'What you will learn'], ['2', 'Idea and whether rho is a percent'], ['3', 'FX percent on 1.1000 to 1.1110'], ['4', 'Series choice and quote direction'], ['5', 'Research: CES 2006'], ['6-9', 'Symbols, ADCC formula, hand calc'], ['10-11', 'Effective use and limits'], ['12-14', 'Checks, software, sources']], [65, 405])
p('Prepared for the folder: 10 - Asymmetric DCC<br/>3 November 2026')

page('What does Asymmetric DCC do?', '02 / The basic idea')
p('Standard DCC treats positive and negative z shocks symmetrically in the news term z_i z_j. Asymmetric DCC adds g * n_i * n_j where n_i is zero for good shocks and negative for bad shocks.')
h('The answer is still rho_ij,t')
p('Mapped from Q the same way as DCC: divide off-diagonal q_ij by sqrt(q_ii q_jj). Still on [-1, +1]. <b>Not</b> a percent.')
h('Is this a percent?')
p('<b>No.</b> Returns may be labelled in percent. rho is a correlation. g is a model weight, not a percent readout of co-movement.')

page('FX percent math on one move', '03 / Returns in plain numbers')
f('Simple return = 1.1110 / 1.1000 - 1 = 0.01  (1.00%)\nLog return = ln(1.1110 / 1.1000) = about 0.009950  (~0.995%)')
p('GARCH and ADCC layers use returns. The asymmetric term works on standardised z, not on raw percent labels.')
p('Example: if a daily log return is -0.015 (about -1.5% as a label), z might be -1.8 after dividing by a small sigma. Then n = min(z,0) = -1.8 and the asymmetric news term can activate. A +0.015 return gives n = 0 on that leg.')
p('Keep the same return definition for every series in a panel. Document bar time and quote direction before you interpret negative shocks.')

page('Which series and quote direction?', '04 / Data rules')
h('Same panel as DCC')
p('One GARCH per leg, aligned returns, z = epsilon / sigma. ADCC updates Q on top.')
h('Quote inversion matters for n_i')
p('If you flip EURUSD to USDEUR, the sign of a log return reverses exactly. A negative shock on one quote can look like a positive shock on the inverted quote. Define base and quote before you interpret g * n_i * n_j as bad-news co-movement.')
p('Keep one quote convention per experiment batch. Document it in experiment notes when v001 exists.')

page('Where did ADCC come from?', '05 / Research notes')
h('Cappiello, L., Engle, R. F., &amp; Sheppard, K. (2006) [1]')
p('<i>Journal of Financial Econometrics</i>, 4(4), 537-572. They extend DCC so correlation can rise more on joint negative shocks than on joint positive shocks of the same magnitude.')
p('The paper targets asymmetric effects seen in equity and multivariate FX settings. Constraints generalise to a + b + g/2 &lt; 1 in the standard ADCC specification (verify in the paper for your estimator).')
h('What this guide claims')
p('We teach the n = min(z, 0) news term and the quote-inversion warning. Full likelihood and matrix cases are in the primary source and in your package docs.')

page('Meet the symbols', '06 / Dictionary')
table([['Symbol', 'Meaning'], ['z_i,t', 'Standardised GARCH residual.'], ['n_i,t', 'min(z_i,t, 0); zero if shock is positive.'], ['a, b, g', 'Symmetric news, memory, asymmetric news weights.'], ['q_ij,t, q_bar_ij', 'ADCC quasi-correlation and target.'], ['rho_ij,t', 'Conditional correlation from Q.']], [125, 345])
p('When z_i is positive, n_i = 0 and the asymmetric term does not fire for that leg on that day.')

page('The ADCC update', '07 / Formula')
f('n_i,t = min(z_i,t, 0)\n\nq_ij,t = (1 - a - b - g) * q_bar_ij\n         + a * z_i,t-1 * z_j,t-1\n         + g * n_i,t-1 * n_j,t-1\n         + b * q_ij,t-1\n\nrho_ij,t = q_ij,t / sqrt(q_ii,t * q_jj,t)')
p('Compare to folder 09: the intercept uses (1-a-b-g) and the g term replaces part of the symmetric news when both shocks are negative.')

page('Negative shocks only', '08 / Intuition')
h('When both z are negative')
p('n_i and n_j are negative, so n_i * n_j is positive. The g term adds extra lift to q_ij beyond a * z_i * z_j (which is also positive when both z are negative).')
h('When one or both z are positive')
p('At least one n is zero, so g * n_i * n_j = 0. Positive-good days rely on the symmetric a term only.')
h('Stress interpretation')
p('Researchers often expect correlation to jump when both markets sell off. ADCC is one way to encode that asymmetry. It is still not proof of causation or of stable future stress correlation.')

page('Calculate by hand: one step', '09 / Worked example')
p('Let a = 0.05, b = 0.85, g = 0.05, q_bar = 0.22, q_12,t-1 = 0.28. Yesterday z_1 = -0.6, z_2 = -0.4.')
f('n_1 = min(-0.6, 0) = -0.6\nn_2 = min(-0.4, 0) = -0.4\n\nq_12,t = 0.05*0.22 + 0.05*(-0.6)(-0.4)\n         + 0.05*(-0.6)(-0.4) + 0.85*0.28\n       = 0.011 + 0.012 + 0.012 + 0.238\n       = 0.273')
p('Then update q_11,t and q_22,t with the same recursion (using z^2 on diagonals as in DCC) before forming rho. This step isolates the off-diagonal asymmetric news arithmetic.')

page('Using ADCC on FX majors', '10 / Effective practice')
p('Use when stress co-movement may differ from calm co-movement and you already justify multivariate GARCH. Fit on a long panel with stable cleaning rules.')
h('Report with context')
p('State quote direction, return type, and whether g is statistically meaningful in your fit. Compare to symmetric DCC (folder 09) as a nested check, not as a contest to pick the prettier rho path.')
p('No invented live pair results here. Experiments not started.')

page('Limits and common errors', '11 / Cautions')
h('Not economic causation')
p('ADCC describes conditional correlation dynamics, not which central bank moved first.')
h('More parameters')
p('g adds flexibility and estimation risk. Small samples can yield unstable g.')
h('Quote mix-ups')
p('Mixing EURUSD on one leg and USDJPY inverted on another without harmonising signs can mis-label negative shocks.')
h('Versus regime splits (folder 11)')
p('Regime conditioning splits the sample by a rule. ADCC keeps one recursion with asymmetric terms. They answer different design questions.')

page('Check your understanding', '12 / Quick questions')
p('<b>Is rho a percent?</b> No. It stays on the correlation scale from -1 to +1 even when returns are written with percent labels.')
p('<b>When is the g term zero?</b> When either standardised shock is non-negative, because n_i = min(z_i, 0) becomes zero on that leg.')
p('<b>Does quote inversion matter?</b> Yes. Inverting the pair flips the sign of log returns, so a negative shock on one quote may look positive on the other.')
p('Save fitted (a, b, g) and one stress-week row of z and Q when experiments begin so you can audit asymmetric updates.')

page('Calculate with software', '13 / Reproduce the teaching step')
f('from math import sqrt\na,b,g = 0.05, 0.85, 0.05\nz1,z2 = -0.6, -0.4\nn1,n2 = min(z1,0), min(z2,0)\nq12 = (1-a-b-g)*0.22 + a*z1*z2 + g*n1*n2 + b*0.28\nprint(q12)  # 0.273')
p('See arch / rugarch ADCC modules. Match n = min(z,0) definition to the package.')
p('After estimation, export one date with z, n, Q, and rho for both symmetric DCC and ADCC if you run nested comparisons. Store quote direction in the same CSV.')
p('The build script for this PDF asserts q_12,t = 0.273 and the FX 1.1000 to 1.1110 percent example; reuse those rows as unit tests in experiment code.')

page('Sources and further reading', '14 / Research trail')
p('Links checked on 3 November 2026.')
refs = [
    ('1', 'Cappiello, L., Engle, R. F., & Sheppard, K. (2006). Asymmetric Dynamics in the Correlations of Global Equity and Bond Returns. Journal of Financial Econometrics, 4(4), 537-572.', 'https://doi.org/10.1093/jjfinec/nbl005', 'Primary ADCC reference.'),
    ('2', 'Folder 09 DCC-GARCH guide and Engle (2002).', '../09%20-%20DCC-GARCH/DCC_GARCH_Complete_Simple_Guide.pdf', 'Symmetric DCC baseline in this repo.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/>'
        f'<link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 10  |  ASYMMETRIC DCC')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(str(OUT), pagesize=(595.28, 841.89), rightMargin=55, leftMargin=55, topMargin=43, bottomMargin=59, title='Asymmetric DCC - Complete Simple Guide', author='Research CO-1', pageCompression=1)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
page_count = len(reader.pages)
assert 14 <= page_count <= 16, f'Unexpected page count: {page_count}'
for i, pg in enumerate(reader.pages):
    assert len(pg.extract_text()) > 350, (i + 1, len(pg.extract_text()))
assert abs(FX_SIMPLE - 0.01) < 1e-12
assert abs(FX_LOG - 0.009950330853168092) < 1e-12
assert abs(Q12_T - 0.273) < 1e-12
print(f'Created and checked {page_count} pages: {OUT}')
