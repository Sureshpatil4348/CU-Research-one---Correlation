from pathlib import Path
from math import log
from collections import Counter
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Mutual_Information_Complete_Simple_Guide.pdf'
EXPECTED_PAGES = 15
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


def mi_discrete(x, y):
    n = len(x)
    joint = Counter(zip(x, y))
    px = Counter(x)
    py = Counter(y)
    total = 0.0
    for (a, b), cab in joint.items():
        pab = cab / n
        pa = px[a] / n
        pb = py[b] / n
        total += pab * log(pab / (pa * pb))
    return total


TEACH_X = [0, 0, 0, 1, 1, 1]
TEACH_Y = [0, 0, 1, 0, 1, 1]
MI_TEACH = mi_discrete(TEACH_X, TEACH_Y)

page('Mutual information', 'Method 15 / A complete beginner guide')
p('<b>Question this method answers:</b> How much knowing X reduces uncertainty about Y (and vice versa), measured in information units?')
p('Mutual information I(X;Y) is zero when X and Y are independent; larger values mean stronger statistical linkage. It is not a percent and not bounded to 1.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Idea, nats vs bits, vs correlation'],
    ['3', 'FX return math (majors)'],
    ['4', 'Continuous data and binning'],
    ['5', 'Research notes (KSG)'],
    ['6', 'Symbol dictionary'],
    ['7-9', 'Joint/marginal probabilities and formula'],
    ['10-11', 'Discrete teaching example and workflow'],
    ['12', 'Software notes'],
    ['13-15', 'Limits, practice, sources'],
], [65, 405])
p('Teaching counts are made up. No live FX pair MI panel appears in this guide.')
p('Prepared for: 15 - Mutual Information. README status: not started.')

page('What is I(X;Y)?', '02 / The basic idea')
p('Imagine X and Y are random quantities. If learning X often tells you something about Y, mutual information is positive. If they are unrelated, I(X;Y) = 0.')
h('Units: nats, not percent')
table([
    ['Natural log (ln)', 'Answer in nats (this guide).'],
    ['log base 2', 'Answer in bits — multiply nats by 1/ln(2) to convert.'],
    ['"I = 0.05 means 5% linked"', 'Wrong — it is information, not a share of days.'],
], [160, 310])
p('Unlike Pearson r, MI can rise for nonlinear patterns and does not flip sign with direction in the same way linear correlation does.')

page('FX percent math (majors)', '03 / Returns before MI')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('Move 1.1000 → 1.1110: simple +1.0000%, log about +0.9950%. MI on returns requires turning continuous numbers into bins or using a k-nearest-neighbor estimator — the bin or bandwidth choice changes the number.')
p('Match calendars; missing ≠ 0. Document every discretization rule before comparing pairs.')

page('Continuous FX returns', '04 / Binning and estimation')
p('Raw daily returns are continuous. Common routes: (1) histogram bins on each leg, then plug counts into the discrete formula; (2) Kraskov–Stögbauer–Grassberger (KSG) k-NN MI without fixed bins.')
p('Finer bins → more spurious spikes with small n; coarse bins → washed-out dependence. There is no universal bin count for all majors — sensitivity analysis belongs in experiments.')
p('Section 15 in forex-formulas-explained.pdf aligns this method with the repo formula sheet.')

page('Research notes', '05 / Kraskov, Stögbauer, Grassberger (2004)')
p('<b>Estimating mutual information.</b> Physical Review E, 69(6), 066138. DOI: 10.1103/PhysRevE.69.066138.')
p('The KSG estimator is widely used for continuous data because it reduces bin-width bias. It still needs enough samples and careful parameter k (neighbors).')
p('Classical discrete MI formulas predate KSG; the 2004 paper matters when you skip manual binning on return series.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['p_a', 'Marginal probability P(X = a).'],
    ['p_b', 'Marginal probability P(Y = b).'],
    ['p_ab', 'Joint probability P(X = a, Y = b).'],
    ['I(X;Y)', 'Mutual information (nats if ln is used).'],
    ['H(X)', 'Entropy of X alone — average surprise in nats.'],
    ['n', 'Number of complete paired observations.'],
], [120, 350])
p('When you discretize returns, each bin label becomes a symbol a or b in the sums above. Keep bin labels consistent across the whole sample window.')

page('Entropy reminder', '07 / Building block')
f('H(X) = - sum_a p_a ln(p_a)\nH(X|Y) = - sum_a sum_b p_ab ln(p_ab / p_b)')
p('Entropy measures average uncertainty. Conditional entropy H(X|Y) is uncertainty in X after seeing Y. MI is how much entropy drops when you link the variables.')
p('If every day is its own unique bin, entropies grow and MI estimates become unstable — another reason bin width must be chosen deliberately on FX returns.')
p('Chain rule link used later in transfer entropy: knowing extra past variables can only reduce conditional uncertainty, never increase it under the same probability model.')

page('The MI formula', '08 / Discrete form')
f('I(X;Y) = sum_a sum_b p_ab ln( p_ab / (p_a * p_b) )')
p('Each term uses joint count divided by n for p_ab, and row/column totals for marginals. The log is natural unless you explicitly choose base 2.')
p('Independence makes every ratio p_ab/(p_a p_b) equal to 1, so ln(1) = 0 and MI is exactly zero in the discrete population case.')

page('Link to correlation', '09 / Different question')
p('Pearson asks about linear co-movement. MI asks about any shared information. Two series can have low r but positive MI if the link is nonlinear — or high noise can drive MI down while r looks moderate.')
p('Do not rank pairs by MI alone without stating bins or the KSG settings used to produce the score.')

page('Hand counts (discrete teaching)', '10 / Six-row example')
table([
    ['Row', 'X bin', 'Y bin'],
    [1, 0, 0], [2, 0, 0], [3, 0, 1],
    [4, 1, 0], [5, 1, 1], [6, 1, 1],
], [50, 100, 100])
p('Think of bins as signed return buckets (down / up) for illustration only.')
f(f'I(X;Y) ≈ {MI_TEACH:.6f} nats (computed from the table counts)')
p('Mixed bins (0 with 1) carry the information; identical bin pairs contribute through the joint distribution shape.')

page('Daily majors workflow', '11 / How to use it here')
h('1. Fix bin edges or KSG k before looking at pairs')
p('Write the rule in NOTES next to n and date range.')
h('2. Report units')
p('State nats (ln) or bits (log2) explicitly.')
h('3. Compare methods side by side')
p('Store MI beside Pearson, dCor, and HSIC when experiments start — each stresses a different facet of dependence.')
p('Future snapshots under data/snapshots/ are the intended data source; MT5 is out of scope for method folders.')

page('Software notes', '12 / Reproduce teaching MI')
f('from collections import Counter\nfrom math import log\n# use mi_discrete in build_guide.py\nx = [0,0,0,1,1,1]\ny = [0,0,1,0,1,1]\nprint(mi_discrete(x,y))')
p('sklearn.feature_selection.mutual_info_regression uses different defaults — not interchangeable without reading the docs. For KSG, see dedicated libraries implementing PhysRevE 69, 066138.')

page('Limits', '13 / What MI cannot tell you')
p('MI is not causal direction (see transfer entropy for lagged information flow). It is not stationary forever: regime shifts change I(X;Y) in new windows.')
p('Binning MI on small samples is unstable. KSG needs enough neighbors — tiny n gives noisy estimates.')
p('High MI during one crisis week is not evidence of a permanent structural link.')

page('Practice', '14 / Quick checks')
p('<b>Q:</b> If X and Y are independent, is sample MI always 0? <b>A:</b> Population MI is 0; finite samples can show small positive noise.')
p('<b>Q:</b> Is MI symmetric? <b>A:</b> Yes: I(X;Y) = I(Y;X).')
p('<b>Q:</b> Can you compare 0.06 nats on EURUSD with 0.06 nats on USDJPY without caveats? <b>A:</b> Only if n, bins, and return definitions match.')
p('<b>Q:</b> Does MI replace correlation matrices? <b>A:</b> No — it complements them when nonlinear dependence matters.')

page('Sources', '15 / Research trail')
refs = [
    ('1', 'Kraskov, A., Stögbauer, H., & Grassberger, P. (2004). Estimating mutual information. Physical Review E, 69(6), 066138.', 'https://doi.org/10.1103/PhysRevE.69.066138', 'KSG continuous estimator reference.'),
    ('2', 'Cover, T. M., & Thomas, J. A. (2006). Elements of Information Theory (2nd ed.). Wiley.', 'https://www.wiley.com/', 'Standard MI and entropy definitions.'),
    ('3', 'forex-formulas-explained.pdf — section 15 (this repository).', '../forex-formulas-explained.pdf', 'Project formula sheet.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Rebuild: python build_guide.py. End of mutual information beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 15  |  MUTUAL INFORMATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Mutual Information - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert abs(MI_TEACH - mi_discrete(TEACH_X, TEACH_Y)) < 1e-12
assert MI_TEACH > 0
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
