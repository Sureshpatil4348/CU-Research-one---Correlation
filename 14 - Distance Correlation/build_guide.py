from pathlib import Path
from math import sqrt
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Distance_Correlation_Complete_Simple_Guide.pdf'
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


def distance_matrix(x):
    n = len(x)
    return [[abs(x[i] - x[j]) for j in range(n)] for i in range(n)]


def double_center(a):
    n = len(a)
    row_means = [sum(a[i]) / n for i in range(n)]
    col_means = [sum(a[i][j] for i in range(n)) / n for j in range(n)]
    grand = sum(row_means) / n
    return [[a[i][j] - row_means[i] - col_means[j] + grand for j in range(n)] for i in range(n)]


def mean_ab(a, b):
    n = len(a)
    return sum(a[i][j] * b[i][j] for i in range(n) for j in range(n)) / (n * n)


def mean_sq(a):
    n = len(a)
    return sum(a[i][j] ** 2 for i in range(n) for j in range(n)) / (n * n)


def dcor(x, y):
    a = double_center(distance_matrix(x))
    b = double_center(distance_matrix(y))
    num = mean_ab(a, b)
    da, db = mean_sq(a), mean_sq(b)
    if da == 0 or db == 0:
        return 0.0
    return sqrt(num / sqrt(da * db))


TEACH_X = [1, 2, 3, 4, 5]
TEACH_Y = [2, 1, 4, 3, 5]
CURVE_X = [-2, -1, 0, 1, 2]
CURVE_Y = [4, 1, 0, 1, 4]
DCOR_TEACH = dcor(TEACH_X, TEACH_Y)
DCOR_CURVE = dcor(CURVE_X, CURVE_Y)

page('Distance correlation', 'Method 14 / A complete beginner guide')
p('<b>Question this method answers:</b> Do X and Y show any statistical dependence — not only a straight-line tilt?')
p('Distance correlation (dCor) returns a score from 0 to 1. Zero means independence under the population model; larger values mean stronger dependence. It has no sign.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Idea, scale 0–1, vs Pearson'],
    ['3', 'FX return math (majors)'],
    ['4', 'Which series to use'],
    ['5', 'Research notes (Székely et al.)'],
    ['6', 'Symbol dictionary'],
    ['7-9', 'Distance matrix, double center, dCor formula'],
    ['10-11', 'Curve example and daily workflow'],
    ['12', 'Software reproduction'],
    ['13-15', 'Limits, practice, sources'],
], [65, 405])
p('All numeric walkthroughs use made-up teaching arrays. This guide does not report live pair experiment results.')
p('Prepared for: 14 - Distance Correlation. README status: not started.')

page('What is dCor?', '02 / The basic idea')
p('Pearson r looks for a straight-line pattern. Distance correlation compares <i>all pairwise distances</i> in X with those in Y after a centering step. Curved but stable links can score above zero even when r is zero.')
h('Read the score on 0 to 1')
table([
    ['dCor near 0', 'No detectable dependence in this sample (under the test setup).'],
    ['dCor larger', 'Stronger general dependence between X and Y.'],
    ['No minus sign', 'Unlike Pearson, direction is not encoded in dCor itself.'],
], [120, 350])
h('Is this number a percent?')
table([
    ['Mistake', 'Truth'],
    ['"dCor = 0.86 means 86% linked days"', 'No. It is a normalized dependence score, not a day fraction.'],
    ['"dCor = 0.86 equals r = 0.86"', 'No. Scales and definitions differ.'],
], [220, 250])

page('FX percent math (majors)', '03 / Returns before dependence tests')
f('Simple return = P_t / P_{t-1} - 1\nPercent return = 100 * simple return\nLog return = ln(P_t / P_{t-1})')
p('Example quote move: 1.1000 → 1.1110 gives simple return 0.010000 (+1.0000%) and log return about 0.009950. Pick one return type for both legs and keep it fixed in the study.')
p('Align timestamps and quote direction. Missing quotes are not zero returns. Four daily closes give three return rows.')

page('Which series this method uses', '04 / Data choice')
p('Apply dCor to <b>matched numeric series</b> — typically daily log or simple returns on the same calendar for two FX legs. Price levels can trend together and inflate dependence scores that do not describe short-horizon co-movement.')
p('Complete rows only: if either return is missing, drop that day from both lists. Report n after cleaning.')
p('Section 14 in forex-formulas-explained.pdf in this repo states the construction used alongside other correlation methods.')

page('Research notes', '05 / Székely, Rizzo, Bakirov (2007)')
p('<b>Measuring and testing dependence by correlation of distances.</b> Annals of Statistics, 35(6), 2769–2794. DOI: 10.1214/009053607000000505.')
p('The paper defines distance correlation, shows dCor = 0 if and only if independence (for continuous pairs under their framework), and gives asymptotic tests. It motivated a practical check beyond linear Pearson correlation.')
p('FX applications in this project are planned under experiments/v001/; this PDF is method education only, not a back-test report.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['x_i, y_i', 'Observations in row i (e.g. returns).'],
    ['n', 'Number of complete paired rows.'],
    ['a_ij', 'Absolute distance |x_i - x_j| in the X list.'],
    ['A', 'Matrix of a_ij after double centering → Ã.'],
    ['b_ij, B', 'Same for Y → B̃.'],
    ['dCor', 'Distance correlation in [0, 1] from the formula below.'],
    ['mean(·)', 'Average over all n² matrix entries unless noted.'],
], [120, 350])

page('Step 1: pairwise distances', '07 / Build matrix a_ij')
f('a_ij = |x_i - x_j|\n(same pattern for y with b_ij = |y_i - y_j|)')
p('For n = 5 you get a 5×5 matrix. Diagonal entries are zero. The matrix is symmetric: a_ij = a_ji.')
p('Distances use raw numeric gaps, so unit choice matters. Returns in decimal form (0.01 = 1%) keep magnitudes comparable across majors when definitions match.')

page('Step 2: double center', '08 / From A to Ã')
p('Double centering subtracts row means, column means, and adds back the grand mean of the distance matrix. Intuitively, it removes overall level and marginal size effects so the remaining pattern reflects relative geometry among points.')
f('Ã_ij = a_ij - row_mean_i - col_mean_j + grand_mean\n(same for B̃ from b_ij)')
p('Software packages implement this as matrix operations. Hand calculation on n = 5 is tedious — use code for verification, but understand the objects being compared.')

page('Step 3: the dCor formula', '09 / Combine Ã and B̃')
f('dCor(X,Y) = sqrt( mean(Ã * B̃) /\n              sqrt( mean(Ã^2) * mean(B^2) ) )')
p('Products and squares are taken entry-wise on the n×n matrices, then averaged over all n² cells. The outer square root keeps the score non-negative and capped at 1 for sample versions defined this way.')
p(f'Teaching array X = {TEACH_X}, Y = {TEACH_Y} gives dCor ≈ {DCOR_TEACH:.6f} (computed in build_guide.py).')
p('Compare to Pearson r = 0.80 on the same pairs — dCor is high here because the monotone pattern is strong.')

page('When Pearson is zero but dCor is not', '10 / Curved dependence')
p('Let X = -2, -1, 0, 1, 2 and Y = X² (values 4, 1, 0, 1, 4). Pearson r = 0 because upward and downward sides cancel in the linear score.')
f(f'Same curve teaching data: dCor ≈ {DCOR_CURVE:.6f} (> 0)')
p('This shows why dCor is useful as a <i>general</i> dependence screen. It does not replace plotting: a spurious score can still arise from small n or preprocessing choices.')

page('Daily majors workflow', '11 / How to use it in this repo')
h('1. Freeze the return definition')
p('Log or simple returns, same session rules, same snapshot from data/snapshots/ when experiments begin.')
h('2. Compute dCor with reported n')
p('Store dCor beside Pearson and rank methods in NOTES — each answers a slightly different question.')
h('3. Test with care')
p('Asymptotic p-values assume enough data and appropriate null approximations. Very small windows are descriptive only.')
p('No pair panel numbers are claimed here; future experiment folders must cite their own frozen inputs.')

page('Software check', '12 / Reproduce teaching scores')
f('from build_guide import dcor  # or paste the functions\nx = [1, 2, 3, 4, 5]\ny = [2, 1, 4, 3, 5]\nprint(dcor(x, y))  # teaching target in assert')
p('SciPy (recent versions) exposes scipy.stats.distance_correlation for the same idea; confirm API and normalization in your installed version before publishing numbers.')
p('R package energy includes dcor.test — useful cross-check for teaching arrays.')

page('Limits', '13 / What dCor cannot tell you')
p('dCor is not a hedge ratio, not a lead–lag measure, and not proof of trading edge. It summarizes dependence in the window you feed in.')
p('Heavy preprocessing (winsorizing, differing sample lengths) changes geometry. Constant series make denominators degenerate — handle like other correlation methods.')
p('High dCor in a crisis week does not by itself predict the next week; stability checks belong in experiments, not in this guide.')

page('Practice', '14 / Quick checks')
p('<b>Q:</b> Can dCor be negative? <b>A:</b> No on the usual 0–1 sample definition used here.')
p('<b>Q:</b> If X and Y are independent, is dCor exactly 0 in every finite sample? <b>A:</b> Not necessarily — sampling noise can lift a small positive value; use tests and larger n when valid.')
p('<b>Q:</b> Should you run dCor on price levels? <b>A:</b> Usually not for co-movement questions; prefer returns aligned to the research question.')
p('<b>Q:</b> Does dCor replace Pearson? <b>A:</b> No — report both when linear co-movement and general dependence both matter.')

page('Sources', '15 / Research trail')
p('Links checked when this guide was built. Bracket numbers point to references; teaching arithmetic is original to this PDF.')
refs = [
    ('1', 'Székely, G. J., Rizzo, M. L., & Bakirov, N. K. (2007). Measuring and testing dependence by correlation of distances. Annals of Statistics, 35(6), 2769–2794.', 'https://doi.org/10.1214/009053607000000505', 'Primary distance correlation reference.'),
    ('2', 'forex-formulas-explained.pdf — section 14 (this repository).', '../forex-formulas-explained.pdf', 'Project formula sheet for method 14.'),
    ('3', 'SciPy documentation: distance_correlation (if available in your version).', 'https://docs.scipy.org/doc/scipy/reference/stats.html', 'Modern software cross-check.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Rebuild: python build_guide.py from this folder. End of distance correlation beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 14  |  DISTANCE CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Distance Correlation - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert abs(DCOR_TEACH - dcor(TEACH_X, TEACH_Y)) < 1e-12
assert DCOR_CURVE > 0.4
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
