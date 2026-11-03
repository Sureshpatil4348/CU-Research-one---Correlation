from pathlib import Path
from math import log
from collections import Counter
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Transfer_Entropy_Complete_Simple_Guide.pdf'
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


# Tiny discrete teaching: X past helps predict Y future beyond Y past alone.
# Y_{t+1} rows indexed; symbols are bin labels only.
Y_FUT = [1, 0, 1, 0]
Y_PAST = [0, 1, 0, 1]
X_PAST = [0, 0, 1, 1]
# TE = I(Y_future; X_past, Y_past) - I(Y_future; Y_past) on aligned tuples — computed below.


def te_from_bins(y_fut, y_past, x_past):
    triples = list(zip(y_fut, y_past, x_past))
    n = len(triples)
    pyf_yp = Counter((a, b) for a, b, _ in triples)
    pyf_yp_xp = Counter((a, b, c) for a, b, c in triples)
    pyf = Counter(a for a, _, _ in triples)
    # I(Yf; Yp, Xp) - I(Yf; Yp) via H(Yf|Yp) - H(Yf|Yp,Xp)
    def cond_h(joint_xy, marginal_x):
        h = 0.0
        for (yf, rest), c in joint_xy.items():
            p = c / n
            if rest in marginal_x:
                px = marginal_x[rest] / n
                if px > 0:
                    h -= p * log(p / px)
        return h

    joint_yf_yp = Counter((a, b) for a, b, _ in triples)
    marg_yp = Counter(b for _, b, _ in triples)
    h1 = cond_h(joint_yf_yp, marg_yp)

    joint_yf_yp_xp = Counter((a, (b, c)) for a, b, c in triples)
    marg_yp_xp = Counter((b, c) for _, b, c in triples)
    h2 = cond_h(joint_yf_yp_xp, marg_yp_xp)
    return h1 - h2


TE_TEACH = te_from_bins(Y_FUT, Y_PAST, X_PAST)

page('Transfer entropy', 'Method 17 / A complete beginner guide')
p('<b>Question this method answers:</b> Does the past of series X add information about the next value of Y beyond what Y\'s own past already explains?')
p('Transfer entropy TE_{X→Y} is measured in nats (natural log). It is directional: TE_{X→Y} need not equal TE_{Y→X}.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Idea, direction, not causation'],
    ['3', 'FX return math (majors)'],
    ['4', 'Lags and embedding'],
    ['5', 'Research notes (Schreiber 2000)'],
    ['6', 'Symbol dictionary'],
    ['7-9', 'Conditional MI definition and intuition'],
    ['10-11', 'Discrete teaching sketch and workflow'],
    ['12', 'Estimation notes'],
    ['13-15', 'Limits, practice, sources'],
], [65, 405])
p('No reported TE scores from major-pair experiments — only symbolic teaching rows.')
p('Prepared for: 17 - Transfer Entropy. README status: not started.')

page('What is TE_{X→Y}?', '02 / The basic idea')
p('Standard correlation and MI at the same time index are symmetric summaries. Transfer entropy looks one step ahead: it rewards cases where X\'s history helps forecast Y\'s next move after accounting for Y\'s history.')
h('Not structural causation')
table([
    ['TE > 0', 'X past adds predictive information about Y future in this model.'],
    ['TE = 0', 'No added information in the discrete population case assumed.'],
    ['Hidden confounders', 'Common drivers can inflate TE without a direct mechanism.'],
], [140, 330])
p('Schreiber (2000) framed TE as a nonparametric information flow measure — useful for hypothesis generation, not proof of economic causality.')

page('FX percent math (majors)', '03 / Returns and time order')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('Example: 1.1000 → 1.1110 is +1% simple move. TE is built on an ordered return series: define Y_{t+1}, Y past lags, and X past lags on the same clock.')
p('Reverse quote direction flips log-return signs — keep one convention per leg. Gaps shorten usable lag vectors.')

page('Lags and embedding', '04 / Design choices')
p('Choose lag length k for Y past and m for X past before analysis. TE depends on those orders — document k, m, and any binning of returns.')
p('Section 17 in forex-formulas-explained.pdf ties TE to the repo\'s correlation method list.')
p('Align sessions so "next day" means the same thing for both series.')

page('Research notes', '05 / Schreiber (2000)')
p('<b>Measuring information transfer.</b> Physical Review Letters, 85(2), 461–464. DOI: 10.1103/PhysRevLett.85.461.')
p('Introduced transfer entropy to quantify directed information flow using conditional probabilities, linking to Granger-style prediction ideas in an information-theoretic form.')
p('Later papers address bias correction, continuous estimators, and multivariate extensions — pick one pipeline and stay consistent across pairs.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['Y_{t+1}', 'Next value of target series Y.'],
    ['Y_past', 'Vector of past Y values (lags).'],
    ['X_past', 'Vector of past X values (lags).'],
    ['TE_{X→Y}', 'I(Y_{t+1}; X_past, Y_past) - I(Y_{t+1}; Y_past) in nats.'],
    ['I(·;·)', 'Mutual information with natural log.'],
    ['I(·;·|·)', 'Conditional mutual information.'],
], [120, 350])

page('Conditional MI form', '07 / Definition used in papers')
f('TE_{X→Y} = I(Y_{t+1}; X_past | Y_past)\n       = I(Y_{t+1}; X_past, Y_past) - I(Y_{t+1}; Y_past)')
p('The second line is the computation recipe: how much information X past adds when Y past is already known about the next Y.')
p('Swap roles to get TE_{Y→X} — compare directions, do not average blindly.')

page('Intuition with words', '08 / Predictive gain')
p('If Y is a random walk, its own past may already fix next-step uncertainty; X past adds nothing → TE_{X→Y} = 0 in the idealized model.')
p('If X leads Y by one day in a discrete teaching chain, TE_{X→Y} can rise while same-time MI also rises — they answer different timing questions.')

page('Discrete bins on returns', '09 / Estimation path')
p('Bin each return into a small alphabet (e.g., down / flat / up). Build empirical counts for tuples (Y_{t+1}, Y_past bins, X_past bins). Plug into the information formulas with care for sparse cells.')
p('Continuous TE estimators (k-NN, kernel) avoid bins but need more data and tuning — plan those in experiments, not in this beginner PDF.')

page('Teaching tuple sketch', '10 / Four aligned rows')
p('Each row is one time step with binned symbols (0/1) for illustration — not EURUSD prices.')
table([
    ['Row', 'Y_{t+1}', 'Y_past', 'X_past'],
    [1, 1, 0, 0], [2, 0, 1, 0], [3, 1, 0, 1], [4, 0, 1, 1],
], [50, 80, 80, 80])
f(f'TE_X_to_Y (discrete teaching estimator) ~ {TE_TEACH:.6f} nats')
p('Positive value means X_past changed conditional uncertainty about Y_{t+1} in this toy table. Recompute only after changing bins or lag definition.')

page('Daily majors workflow', '11 / Repo usage')
h('1. Fix lag orders and bin edges')
p('Write k, m, and return type in NOTES before scanning pairs.')
h('2. Report both directions')
p('TE_{X→Y} and TE_{Y→X} can differ — especially under asymmetric information flow.')
h('3. Surrogate tests')
p('Shuffle or block-bootstrap X past to build null distributions when n allows — raw TE alone is hard to rank.')
p('Experiments under experiments/v001/ should store TE settings beside static correlation columns.')

page('Estimation notes', '12 / Software')
f('# te_from_bins in build_guide.py for the 4-row teaching table\n# Production: dedicated TE libraries with bias correction')
p('Check whether your package uses natural log nats or bits. Match units across methods 15 and 17 in the same report.')
p('Sparse bins with small n inflate TE — merge bins or widen the return window before trusting three decimal places.')
p('Save random seeds and surrogate counts when experiments add significance bands; this guide does not prescribe a single null recipe.')

page('Limits', '13 / What TE cannot tell you')
p('TE is not VAR Granger causality with linear Gaussian assumptions — related idea, different object. It is not proof that trading X predicts Y profitably after costs.')
p('Microstructure noise, asynchronous quotes, and holiday calendars distort lag alignment. TE can reflect preprocessing as much as economics.')

page('Practice', '14 / Quick checks')
p('<b>Q:</b> If TE_{X→Y} > 0, did X cause Y? <b>A:</b> Not necessarily — confounding and reverse mechanisms remain possible.')
p('<b>Q:</b> Is TE symmetric? <b>A:</b> No — compare both directions explicitly.')
p('<b>Q:</b> Same-time MI vs TE? <b>A:</b> MI ignores ordered prediction; TE uses lags and a future step.')
p('<b>Q:</b> Can you TE price levels? <b>A:</b> Usually prefer returns; levels trend and inflate apparent flow.')

page('Sources', '15 / Research trail')
refs = [
    ('1', 'Schreiber, T. (2000). Measuring information transfer. Physical Review Letters, 85(2), 461–464.', 'https://doi.org/10.1103/PhysRevLett.85.461', 'Original transfer entropy paper.'),
    ('2', 'forex-formulas-explained.pdf — section 17 (this repository).', '../forex-formulas-explained.pdf', 'Project formula sheet.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Rebuild: python build_guide.py. End of transfer entropy beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 17  |  TRANSFER ENTROPY')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Transfer Entropy - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert abs(TE_TEACH - te_from_bins(Y_FUT, Y_PAST, X_PAST)) < 1e-12
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
