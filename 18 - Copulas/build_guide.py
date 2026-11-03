from pathlib import Path
from math import log, sqrt, exp
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Copulas_Complete_Simple_Guide.pdf'
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


def normal_cdf(z):
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def erf(x):
    # Abramowitz-Stegun approximation for teaching asserts
    sign = 1 if x >= 0 else -1
    x = abs(x)
    t = 1.0 / (1.0 + 0.3275911 * x)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * exp(-x * x)
    return sign * y


def rank_uniform(values):
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    for r, i in enumerate(order, start=1):
        ranks[i] = r / (n + 1.0)
    return ranks


TEACH_X = [-0.02, -0.01, 0.0, 0.01, 0.02]
TEACH_Y = [-0.015, -0.005, 0.005, 0.012, 0.018]
U = rank_uniform(TEACH_X)
V = rank_uniform(TEACH_Y)
# Gaussian copula density check: both uniforms near 0.5 for middle row
MID_U, MID_V = U[2], V[2]

page('Copulas', 'Method 18 / A complete beginner guide')
p('<b>Question this method answers:</b> How do two FX return series link in the <i>joint distribution</i>, separate from each leg\'s own volatility shape?')
p('A copula is a model for dependence among uniform ranks u and v. It is not one Pearson-style correlation number — though copula parameters are sometimes loosely called "correlation."')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Idea: margins vs dependence'],
    ['3', 'FX return math (majors)'],
    ['4', 'Ranks u, v from returns'],
    ['5', 'Research notes (Patton 2006)'],
    ['6', 'Symbol dictionary'],
    ['7-9', 'Sklar, Gaussian copula, tail ideas'],
    ['10-11', 'Teaching ranks and workflow'],
    ['12', 'Estimation outline'],
    ['13-15', 'Limits, practice, sources'],
], [65, 405])
p('No fitted copula parameters from live major-pair panels appear here.')
p('Prepared for: 18 - Copulas. README status: not started.')

page('Margins and copula', '02 / The basic idea')
p('Each return series has its own distribution (fat tails, volatility clustering). Copula methods split the problem: model each margin, then model how uniform transforms u and v move together.')
h('Not a single r score')
table([
    ['Pearson r', 'One linear co-movement number on raw or transformed data.'],
    ['Copula C', 'Whole dependence structure on [0,1]² — may allow asymmetric tails.'],
    ['Patton (2006) FX focus', 'Exchange rates often show asymmetric dependence — copulas target that.'],
], [130, 340])

page('FX percent math (majors)', '03 / Returns first')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('1.1000 → 1.1110 ≈ +1% simple. Copula work uses many days of returns, converts each leg to pseudo-observations u_i = F̂_X(x_i), v_i = F̂_Y(y_i) with estimated margins F̂.')
p('Missings drop paired rows. Crisis periods change both margins and copula — report the window honestly.')

page('From returns to u and v', '04 / Pseudo-observations')
f('u_i = F_hat_X(x_i)\nv_i = F_hat_Y(y_i)')
p('F_hat can be empirical ranks / (n+1), a fitted t-distribution CDF, or a GARCH-filtered residual CDF. Different F_hat → different u,v → different copula fit.')
p('Section 18 in forex-formulas-explained.pdf documents the repo placement of copula dependence.')

page('Research notes', '05 / Patton (2006)')
p('<b>Modelling asymmetric exchange rate dependence.</b> International Economic Review, 47(2), 527–556. DOI: 10.1111/j.1468-2354.2006.00387.x.')
p('Shows symmetric Gaussian copulas can miss FX dependence patterns — especially stronger co-movement during joint depreciations vs appreciations. Motivates copula families with tail asymmetry.')
p('This guide explains concepts; parameter estimates belong in future experiment outputs with frozen code versions.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['F_X, F_Y', 'Marginal CDFs of X and Y returns.'],
    ['u, v', 'Uniform transforms in (0,1).'],
    ['C(u,v)', 'Copula — joint CDF on the unit square.'],
    ['c(u,v)', 'Copula density if differentiable.'],
    ['θ (theta)', 'Copula parameter (meaning depends on family).'],
    ['Sklar', 'Theorem linking joint CDF to margins + copula.'],
], [120, 350])

page('Sklar\'s theorem', '07 / Joint CDF factorization')
f('F_XY(x,y) = C( F_X(x), F_Y(y) )')
p('Any bivariate CDF with continuous margins can be written this way. Dependence lives entirely in C; margins describe each leg alone.')
p('For discrete binned returns, copula theory needs adjustments — FX daily work usually stays with continuous or pseudo-continuous u,v.')

page('Gaussian copula (symmetric baseline)', '08 / Quick formulas')
f('C_Gauss(u,v; rho) = Phi_2( Phi^{-1}(u), Phi^{-1}(v); rho )')
p('Phi is a standard normal CDF. rho plays a role like linear correlation in the Gaussian world, but tail behaviour is symmetric — often a poor FX tail match per Patton (2006).')
p('Use Gaussian copula as a teaching baseline, not as the final word on majors.')

page('Tail dependence intuition', '09 / Why FX cares')
p('Lower-tail dependence: do both returns crash together more often than Gaussian predicts? Upper-tail dependence: joint spikes? Asymmetric copulas (clayton, rotated, or time-varying C) encode different tail stories.')
p('One Pearson r cannot separate margin fat tails from tail dependence — copula + margin split is the point.')

page('Teaching ranks', '10 / Five return pairs')
table([
    ['Day', 'x (return)', 'y (return)', 'u rank', 'v rank'],
    [1, TEACH_X[0], TEACH_Y[0], f'{U[0]:.3f}', f'{V[0]:.3f}'],
    [2, TEACH_X[1], TEACH_Y[1], f'{U[1]:.3f}', f'{V[1]:.3f}'],
    [3, TEACH_X[2], TEACH_Y[2], f'{U[2]:.3f}', f'{V[2]:.3f}'],
    [4, TEACH_X[3], TEACH_Y[3], f'{U[3]:.3f}', f'{V[3]:.3f}'],
    [5, TEACH_X[4], TEACH_Y[4], f'{U[4]:.3f}', f'{V[4]:.3f}'],
], [45, 90, 90, 80, 80])
p('Ranks use i/(n+1) on sorted values — a simple empirical uniform for teaching. Monotone co-movement pushes u and v up together across days.')

page('Daily majors workflow', '11 / Repo usage')
h('1. Filter margins first')
p('GARCH or empirical CDF — pick one pipeline and version it in experiments.')
h('2. Choose copula family before seeing pair rankings')
p('Document symmetric vs asymmetric candidates and selection criteria (AIC, tail tests).')
h('3. Report dependence separately from volatility')
p('A day with huge |return| affects margins; copula parameters summarize linkage among u,v after margins absorb scale.')
p('Store outputs in experiments/v001/ when built — not in this PDF.')

page('Estimation outline', '12 / Two-step idea')
f('Step 1: Fit F_hat_X, F_hat_Y on return samples\nStep 2: Set u_i, v_i and maximize copula log-likelihood for theta')
p('Time-varying copulas (Patton and follow-ups) let theta_t evolve — advanced topic for later experiment notes.')
p('Libraries: copulas (Python), rugarch + copula packages in R — verify Sklar conventions in docs.')

page('Limits', '13 / What copulas cannot tell you')
p('A copula fit is only as good as margins and the chosen family. Small n makes tail parameters unstable. Regime shifts break constant-copula models.')
p('Copula dependence is not TE directionality and not a hedge ratio. Trading claims need out-of-sample checks outside this guide.')
p('When margins are mis-specified, u and v can look uniform while still hiding bad tail fit — always check margin residuals before trusting theta.')

page('Practice', '14 / Quick checks')
p('<b>Q:</b> Is copula rho the same as Pearson r? <b>A:</b> Not in general — related under Gaussian specials, different objects otherwise.')
p('<b>Q:</b> Can u and v come from price levels? <b>A:</b> Usually model return margins, not trending prices.')
p('<b>Q:</b> Does asymmetric copula imply causation? <b>A:</b> No — it describes joint tail linkage in the window.')
p(f'<b>Check:</b> middle-row teaching u ≈ {MID_U:.3f}, v ≈ {MID_V:.3f} — both near 0.5 for balanced ranks.')

page('Sources', '15 / Research trail')
refs = [
    ('1', 'Patton, A. J. (2006). Modelling asymmetric exchange rate dependence. International Economic Review, 47(2), 527–556.', 'https://doi.org/10.1111/j.1468-2354.2006.00387.x', 'FX asymmetric dependence motivation.'),
    ('2', 'Sklar, A. (1959). Fonctions de répartition à n dimensions et leurs marges. Publications de l\'Institut de Statistique de l\'Université de Paris, 8, 229–231.', 'https://www.jstor.org/', 'Sklar theorem original.'),
    ('3', 'forex-formulas-explained.pdf — section 18 (this repository).', '../forex-formulas-explained.pdf', 'Project formula sheet.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Rebuild: python build_guide.py. End of copulas beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 18  |  COPULAS')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Copulas - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert abs(U[2] - 3 / 6) < 1e-12
assert len(U) == len(V) == 5
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
