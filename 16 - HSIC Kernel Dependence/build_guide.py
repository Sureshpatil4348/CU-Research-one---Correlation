from pathlib import Path
from math import exp, sqrt
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'HSIC_Kernel_Dependence_Complete_Simple_Guide.pdf'
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


def hsic_rbf(x, y, ell):
    n = len(x)
    h = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            h[i][j] = (1.0 if i == j else -1.0 / n)

    def kernel(v):
        k = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                d = v[i] - v[j]
                k[i][j] = exp(-(d * d) / (2 * ell * ell))
        return k

    kx = kernel(x)
    ky = kernel(y)

    def matmul(a, b):
        m, p, q = len(a), len(b), len(b[0])
        out = [[0.0] * q for _ in range(m)]
        for i in range(m):
            for j in range(q):
                for k in range(p):
                    out[i][j] += a[i][k] * b[k][j]
        return out

    kh = matmul(kx, h)
    trace = 0.0
    tmp = matmul(kh, ky)
    tmp2 = matmul(tmp, h)
    for i in range(n):
        trace += tmp2[i][i]
    return trace / (n * n)


TEACH_X = [1, 2, 3, 4, 5]
TEACH_Y = [2, 1, 4, 3, 5]
TEACH_ELL = 1.0
HSIC_TEACH = hsic_rbf(TEACH_X, TEACH_Y, TEACH_ELL)

page('HSIC kernel dependence', 'Method 16 / A complete beginner guide')
p('<b>Question this method answers:</b> In a reproducing-kernel view, how strongly do X and Y co-vary beyond independence — with flexibility for nonlinear patterns?')
p('The Hilbert–Schmidt Independence Criterion (HSIC) is a nonnegative score. Larger values suggest stronger dependence; bandwidth choice matters.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Idea, unsigned score, bandwidth'],
    ['3', 'FX return math (majors)'],
    ['4', 'Kernels on return series'],
    ['5', 'Research notes (Gretton et al.)'],
    ['6', 'Symbol dictionary'],
    ['7-9', 'RBF kernel, centering matrix H, HSIC formula'],
    ['10-11', 'Teaching value and workflow'],
    ['12', 'Software notes'],
    ['13-15', 'Limits, practice, sources'],
], [65, 405])
p('Made-up teaching arrays only — no experiment panel HSIC values.')
p('Prepared for: 16 - HSIC Kernel Dependence. README status: not started.')

page('What is HSIC?', '02 / The basic idea')
p('HSIC maps each series into a high-dimensional feature space via a kernel, then measures alignment between the two kernel matrices after centering. Linear Pearson is a very special case; HSIC with a nonlinear kernel can react to broader patterns.')
h('Unsigned and bandwidth-dependent')
table([
    ['No -1 to +1 sign', 'HSIC reports strength, not up/down co-movement.'],
    ['Length scale ℓ', 'Gaussian RBF width — smaller ℓ → local comparisons; larger ℓ → smoother.'],
    ['Not a percent', 'Do not read 0.09 as 9% of days.'],
], [180, 290])

page('FX percent math (majors)', '03 / Returns before kernels')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('1.1000 → 1.1110 is about +1% simple return. HSIC is computed on numeric return arrays; scale ℓ relative to typical |return| gaps (often fractions like 0.005).')
p('If you standardize returns first, ℓ = 1 means something different — document preprocessing.')

page('Kernels on FX data', '04 / Practical choices')
p('Gaussian (RBF) kernel is the usual teaching default. Linear kernel HSIC relates to squared covariance structure; RBF is the nonlinear workhorse in dependence testing literature.')
p('Section 16 in forex-formulas-explained.pdf records the project definition alongside other methods.')
p('Pick ℓ from a prespecified rule (median heuristic, fixed fraction of std) before scanning pairs to avoid implicit tuning.')

page('Research notes', '05 / Gretton et al. (2007)')
p('<b>A kernel statistical test of independence.</b> Journal of Machine Learning Research, 8, 723–773.')
p('Introduces HSIC as an independence test statistic with asymptotic null distribution. Widely cited for nonlinear dependence screening between multivariate samples.')
p('Later work extends HSIC to feature selection and two-sample testing; this guide stays on the pairwise FX return use case.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['K_ij', 'Kernel similarity between x_i and x_j.'],
    ['ℓ (ell)', 'RBF length scale (bandwidth).'],
    ['H', 'Centering matrix I - (1/n) 11′.'],
    ['L', 'Kernel matrix for Y (often G in papers).'],
    ['HSIC', 'tr(K H L H) / n² for sample version used here.'],
    ['n', 'Complete paired row count.'],
], [120, 350])
p('Matrices K and L are n×n and symmetric. H is the same for every pair in a given sample size n.')

page('Gaussian RBF kernel', '07 / Build K')
f('K_ij = exp( -(x_i - x_j)^2 / (2 * ell^2) )')
p('Nearby return values get K_ij near 1; far apart values get K_ij near 0 when ℓ is modest. Build the same for Y as matrix L (or G).')
p('Diagonal entries are 1. The matrix is symmetric.')
p('On daily FX decimals, pairwise gaps are often 0.001–0.02; ℓ must be stated in those units. Rescaling returns rescales effective ℓ.')
p('Alternative kernels (Laplacian, polynomial) change sensitivity; the repo sheet emphasizes RBF for method 16 consistency.')

page('Centering matrix H', '08 / Remove mean structure')
f('H = I - (1/n) * ones(n,n)\n(each entry of ones is 1)')
p('Premultiplying and postmultiplying by H centers kernel features in the Hilbert space sense used in the HSIC definition. Implementation matches matrix trace formula below.')
p('Intuition: without H, a series whose returns are all large would inflate kernel similarities; centering removes that shared level before comparing X and Y geometry.')
p('For n = 5 teaching data, H is a fixed 5×5 matrix — reuse the same H when multiplying K and L for a fair HSIC number.')

page('HSIC formula', '09 / Trace form')
f('HSIC = tr(K H L H) / n^2')
p('tr means trace — sum of diagonal entries of the product matrix. The /n² scaling matches the common sample normalization in Gretton et al.')
f(f'Teaching x,y with ell={TEACH_ELL}: HSIC ≈ {HSIC_TEACH:.6f}')
p('Changing ℓ changes this number even when Pearson r stays fixed — always report ℓ.')

page('Read HSIC beside Pearson', '10 / Same teaching pairs')
p('On X = 1..5, Y = 2,1,4,3,5, Pearson r = 0.80. HSIC is positive but not on the same scale as r — compare HSIC across pairs only with identical ℓ and preprocessing.')
p('HSIC near zero supports an independence hypothesis under the test setup; it is not proof of tradable decorrelation.')

page('Daily majors workflow', '11 / Repo usage')
h('1. Freeze ℓ rule and return type')
p('Log returns from a named snapshot; store ℓ and n in NOTES.')
h('2. Batch compute with fixed settings')
p('When experiments/v001/ exists, append HSIC next to MI and dCor — do not cherry-pick bandwidth after seeing rankings.')
h('3. Use permutation or bootstrap tests when n allows')
p('Raw HSIC magnitude alone is hard to interpret; p-values from the JMLR framework need adequate sample size.')

page('Software notes', '12 / Reproduce teaching HSIC')
f('ell = 1.0\nx = [1, 2, 3, 4, 5]\ny = [2, 1, 4, 3, 5]\n# hsic_rbf in build_guide.py')
p('Libraries: sklearn.metrics.pairwise.rbf_kernel for K; combine with centering per formula. Some packages expose independence tests directly — verify normalization matches tr(KHLH)/n².')
p('Run the teaching arrays first; only then scale to full snapshot panels inside experiments.')

page('Limits', '13 / What HSIC cannot tell you')
p('HSIC is not a hedge ratio, not lead–lag, and not invariant to ℓ choice. It can be sensitive to outliers in returns unless you winsorize or robustify — document if you do.')
p('Very small n makes both HSIC and its p-value unreliable.')
p('Rolling HSIC across windows can track regime change, but each window needs its own ℓ rule — do not reuse a bandwidth tuned on the full sample without noting leakage.')
p('Pair rankings from HSIC alone are fragile when ℓ is free — pre-register the bandwidth heuristic in experiment NOTES.')

page('Practice', '14 / Quick checks')
p('<b>Q:</b> Does HSIC flip sign if Y is multiplied by -1? <b>A:</b> RBF uses squared differences in Y, so HSIC magnitude is unchanged; Pearson sign would flip.')
p('<b>Q:</b> Is larger ℓ always better? <b>A:</b> No — it oversmooths local structure.')
p('<b>Q:</b> Can HSIC replace dCor? <b>A:</b> Both screen nonlinear dependence; definitions differ — report settings, not just rankings.')

page('Sources', '15 / Research trail')
refs = [
    ('1', 'Gretton, A., Fukumizu, K., Teo, C., Song, L., Schölkopf, B., & Smola, A. (2007). A kernel statistical test of independence. JMLR, 8, 723–773.', 'https://www.jmlr.org/papers/v8/gretton07a.html', 'HSIC independence test paper.'),
    ('2', 'forex-formulas-explained.pdf — section 16 (this repository).', '../forex-formulas-explained.pdf', 'Project formula sheet.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Rebuild: python build_guide.py. End of HSIC kernel dependence beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 16  |  HSIC KERNEL DEPENDENCE')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='HSIC Kernel Dependence - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert abs(HSIC_TEACH - hsic_rbf(TEACH_X, TEACH_Y, TEACH_ELL)) < 1e-9
assert HSIC_TEACH > 0
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
