from pathlib import Path
from math import sqrt
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'DCCA_Detrended_Cross_Correlation_Complete_Simple_Guide.pdf'
EXPECTED_PAGES = 15
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyEasy', fontName='Helvetica', fontSize=11, leading=16, spaceAfter=10))
styles.add(ParagraphStyle(name='HeadEasy', fontName='Helvetica-Bold', fontSize=23, leading=28, textColor=colors.HexColor('#15364A'), spaceAfter=18))
styles.add(ParagraphStyle(name='SubEasy', fontName='Helvetica-Bold', fontSize=13, leading=18, textColor=colors.HexColor('#087F8C'), spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name='FormulaEasy', fontName='Courier', fontSize=10, leading=15, backColor=colors.HexColor('#EDF5F7'), borderPadding=10, spaceBefore=8, spaceAfter=17))
styles.add(ParagraphStyle(name='SmallEasy', fontName='Helvetica', fontSize=9, leading=13, spaceAfter=8))
story = []

TEACH_X = [0.01, -0.005, 0.002, -0.008, 0.003, 0.004, -0.002, 0.001, -0.006, 0.002,
           0.005, -0.003, 0.001, 0.002, -0.004, 0.003, -0.001, 0.004, -0.002, 0.001]
TEACH_Y = [0.008, -0.004, 0.0015, -0.006, 0.0025, 0.003, -0.0015, 0.0008, -0.005, 0.0015,
           0.004, -0.0025, 0.0008, 0.0015, -0.003, 0.0025, -0.0008, 0.003, -0.0015, 0.0008]
WINDOW_S = 5


def dcca_rho(x, y, window):
    n = len(x)
    assert len(y) == n and window >= 4
    mx = sum(x) / n
    my = sum(y) / n
    prof_x = []
    prof_y = []
    cx = cy = 0.0
    for i in range(n):
        cx += x[i] - mx
        cy += y[i] - my
        prof_x.append(cx)
        prof_y.append(cy)
    nbox = n // window
    xt, yt = [], []
    for b in range(nbox):
        segx = prof_x[b * window:(b + 1) * window]
        segy = prof_y[b * window:(b + 1) * window]
        t = list(range(window))
        sx = sum(segx) / window
        sy = sum(segy) / window
        tx = sum(t) / window
        ty = tx
        b_x = sum((t[i] - tx) * (segx[i] - sx) for i in range(window))
        b_y = sum((t[i] - tx) * (segy[i] - sy) for i in range(window))
        denom_x = sum((t[i] - tx) ** 2 for i in range(window))
        denom_y = denom_x
        a_x = sx - b_x * tx
        a_y = sy - b_y * tx
        for i in range(window):
            fit_x = a_x + b_x * t[i]
            fit_y = a_y + b_y * t[i]
            xt.append(segx[i] - fit_x)
            yt.append(segy[i] - fit_y)
    if not xt:
        return 0.0
    mean_xy = sum(a * b for a, b in zip(xt, yt)) / len(xt)
    mean_xx = sum(a * a for a in xt) / len(xt)
    mean_yy = sum(b * b for b in yt) / len(yt)
    den = sqrt(mean_xx * mean_yy)
    if den == 0:
        return 0.0
    return mean_xy / den


RHO_DCCA = dcca_rho(TEACH_X, TEACH_Y, WINDOW_S)
PEARSON_RAW = 0.0
mx = sum(TEACH_X) / len(TEACH_X)
my = sum(TEACH_Y) / len(TEACH_Y)
dx = [v - mx for v in TEACH_X]
dy = [v - my for v in TEACH_Y]
num = sum(a * b for a, b in zip(dx, dy))
den = sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
if den:
    PEARSON_RAW = num / den


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


page('DCCA detrended cross-correlation', 'Method 23 / A complete beginner guide')
p('<b>Question this method answers:</b> After building cumulative return profiles and removing local trends, how strongly do two FX series co-move at window scale s?')
p('ρ_DCCA(s) differs from raw-return Pearson r — detrending inside each block targets long-memory co-fluctuations.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Profiles versus raw returns'],
    ['3', 'FX percent math (majors)'],
    ['4', 'Cumulative profile X_k'],
    ['5', 'Research notes (Zebende; Kwapień et al.)'],
    ['6', 'Symbol dictionary'],
    ['7-9', 'Detrending and ρ_DCCA(s)'],
    ['10-11', 'Scales s and workflow'],
    ['12', 'Software sketch'],
    ['13-15', 'Limits, practice, sources'],
], [65, 405])
p('Teaching returns only — no snapshot DCCA scaling plots.')
p('Prepared for: 23 - DCCA Detrended Cross-Correlation. README status: not started.')

page('Long-memory co-movement', '02 / The basic idea')
p('Pearson r on daily returns treats each day independently in the formula. DCCA integrates returns into profiles, removes polynomial trends in sliding windows, then correlates residual profiles — emphasizing slow co-movement across scales s.')
h('Different object')
table([
    ['Pearson on returns', 'One-step linear linkage.'],
    ['ρ_DCCA(s)', 'Detrended profile correlation at window length s.'],
    ['Scale sweep', 'Compare s = 20 versus s = 100 observations (formula sheet).'],
], [160, 310])

page('FX percent math (majors)', '03 / Returns integrated')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('1.1000 → 1.1110 is about +1% simple return. DCCA starts from demeaned returns x_t − x̄, then cumulates. Tiny daily percents stack into profile shapes over weeks.')
p('Use the same return type for both legs; mixing simple and log breaks comparability.')

page('Build the profile', '04 / Cumulative sum')
f('X_k = sum_{t=1..k} ( x_t - x_bar )\nY_k = sum_{t=1..k} ( y_t - y_bar )')
p('Profiles look like rough random walks built from returns. Local linear (or polynomial) trends inside each window of size s are fitted and subtracted to obtain X̃ and Ỹ segments.')
p('Section 23 in forex-formulas-explained.pdf uses the same mean-of-products normalization shown on the next pages.')

page('Research notes', '05 / Zebende (2011); Kwapień et al. (2015)')
p('<b>Zebende (2011):</b> Detrended cross-correlation analysis of two nonstationary time series. Physica A, 390, 2480–2490 — introduces ρ_DCCA scaling across window sizes.')
p('<b>Kwapień, Oświęcimka, Drożdż (2015):</b> Detrended fluctuation analysis made flexible — extends DFA/DCCA family including q-dependent variants (method 24 in this repo).')
p('FX applications must specify trend order, overlap, and averaging — defaults from physics papers may not suit daily FX without review.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['x_t, y_t', 'Demeaned daily returns.'],
    ['X_k, Y_k', 'Cumulative profiles.'],
    ['s', 'Detrending window length (observations).'],
    ['X̃, Ỹ', 'Profile residuals after local detrend.'],
    ['ρ_DCCA(s)', 'Detrended cross-correlation at scale s.'],
    ['Overlap', 'How windows slide (non-overlap versus 50%).'],
], [120, 350])

page('Detrend inside each window', '07 / Local linear fit')
p('Split the profile into consecutive (or overlapping) segments of length s. In each segment, fit a line (or low-order polynomial) to X and separately to Y. Subtract the fit to get residuals for that segment.')
p('Concatenate residual segments (or average overlapping estimates) before the correlation step. Document overlap — ρ_DCCA changes with it.')

page('ρ_DCCA formula', '08 / Normalize covariation')
f('rho_DCCA(s) = mean(X_tilde * Y_tilde) /\n  sqrt( mean(X_tilde^2) * mean(Y_tilde^2) )')
p('Means are taken over all residual points contributed at scale s. The score behaves like a correlation on detrended profile fluctuations — not on raw returns.')
f(f'Teaching window s = {WINDOW_S}: rho_DCCA ≈ {RHO_DCCA:.4f}\nRaw Pearson on returns ≈ {PEARSON_RAW:.4f}')
p('The two numbers need not match — that gap is expected when slow profile co-movement differs from one-day linear linkage.')

page('Compare scales', '09 / 20 versus 100 observations')
p('Repeat ρ_DCCA(s) for several s values and plot log(s) versus ρ or related fluctuation functions. FX crisis periods may show stronger detrended linkage at medium s than calm periods.')
p('Method 24 (multifractal DCCA) generalizes with exponent q — stay with q = 2 / standard DCCA here unless you read method 24.')

page('Daily majors workflow', '10 / Repo usage')
h('1. Long aligned return panels')
p('DCCA needs enough length for multiple windows — short snapshots give noisy scales.')
h('2. Freeze detrend degree and overlap')
p('Log choices in experiments/v001/ NOTES.')
h('3. Report ρ_DCCA(s) curves')
p('Do not reduce to a single s tuned after seeing pair rankings.')

page('Versus Pearson and rolling r', '11 / When to use DCCA')
p('Rolling Pearson (method 05) tracks time-varying linear correlation on returns. DCCA emphasizes detrended profile structure across scales — closer to long-memory diagnostics.')
p('Neither replaces tail counts (19) or wavelet maps (22).')
p('If ρ_DCCA(s) rises while rolling r falls, slow profile co-movement may persist after short-horizon decorrelation — but verify with stable window counts and overlapping rules before interpreting.')
p('Document whether profiles were built from log or simple returns; integration makes small differences in x̄ matter over long panels.')

page('Software sketch', '12 / Python loops')
f('# profile = cumsum(x - mean(x))\n# for each window: polyfit trend, subtract\n# correlate flattened residuals')
p('Libraries: nolds, MFDFA implementations, or custom code — verify mean normalization matches Zebende (2011) before comparing to literature.')
p('Keep DCCA code inside method experiments; shared/mt5_data stays I/O only.')

page('Limits', '13 / What DCCA cannot tell you')
p('Nonstationary FX regimes break fixed-scale interpretations. Polynomial detrend order can absorb real co-movement if set too high.')
p('ρ_DCCA(s) is not a trading signal, not TE, and not a copula tail measure.')
p('Very small samples yield too few windows at large s — drop unreliable scales instead of extrapolating.')

page('Practice', '14 / Quick checks')
p('<b>Q:</b> Is ρ_DCCA(s) equal to Pearson r? <b>A:</b> Not in general — different objects (see teaching numbers on page 8).')
p('<b>Q:</b> Can s = 5 on 20 days support s = 100 analysis? <b>A:</b> No — you need enough profile length.')
p(f'<b>Check:</b> teaching ρ_DCCA({WINDOW_S}) ≈ {RHO_DCCA:.4f}.')
p('<b>Q:</b> Do profiles use price levels? <b>A:</b> No — integrate demeaned returns.')

page('Sources', '15 / Research trail')
refs = [
    ('1', 'Zebende, G. F. (2011). Detrended cross-correlation analysis of two nonstationary time series. Physica A, 390, 2480–2490.', 'https://doi.org/10.1016/j.physa.2011.02.029', 'ρ_DCCA definition.'),
    ('2', 'Kwapień, J., Oświęcimka, P., & Drożdż, S. (2015). Detrended fluctuation analysis made flexible. Physica A, 427, 1–8.', 'https://doi.org/10.1016/j.physa.2015.02.028', 'Flexible DFA/DCCA framework.'),
    ('3', 'forex-formulas-explained.pdf — section 23 (this repository).', '../forex-formulas-explained.pdf', 'Project formula sheet.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Rebuild: python build_guide.py. End of DCCA detrended cross-correlation beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 23  |  DCCA DETRENDED CROSS-CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='DCCA Detrended Cross-Correlation - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert -1.0 <= RHO_DCCA <= 1.0
assert abs(RHO_DCCA - dcca_rho(TEACH_X, TEACH_Y, WINDOW_S)) < 1e-12
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
