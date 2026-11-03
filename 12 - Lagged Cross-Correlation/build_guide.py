from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Lagged_Cross_Correlation_Complete_Simple_Guide.pdf'
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


X_SER = [0.010, 0.020, 0.030, 0.040, 0.050]
Y_SER = [0.015, 0.040, 0.050, 0.070, 0.090]
K = 1
RHO_X_TO_Y = pearson(X_SER[:-K], Y_SER[K:])
FX_SIMPLE = 1.1110 / 1.1000 - 1
FX_LOG = log(1.1110 / 1.1000)


page('Lagged cross-correlation', 'Method 12 / A complete beginner guide')
p('<b>Does today\'s move in series X line up with tomorrow\'s move in series Y?</b> Lagged cross-correlation measures Pearson correlation between x_t and y_{t+k} for chosen lag k.')
p('It is a <b>screening</b> tool, not proof that X forecasts Y profitably. Teaching examples only; experiments not started.')
h('Read it in three parts')
p('<b>First:</b> Idea, percents, series. <b>Next:</b> Notation, formula, hand calc. <b>Last:</b> FX use, limits, statsmodels CCF check.')
table([['Pages', 'What you will learn'], ['2', 'Idea; is rho a percent?'], ['3', 'FX percent example'], ['4', 'Which series and lag sign'], ['5', 'Role in time-series screening'], ['6-9', 'Symbols, formula, hand calc'], ['10-11', 'Majors practice and limits'], ['12-14', 'Software and sources']], [65, 405])
p('Prepared for the folder: 12 - Lagged Cross-Correlation<br/>3 November 2026')

page('What does lagged cross-correlation do?', '02 / The basic idea')
p('Same-period correlation asks about x_t and y_t together. Lagged cross-correlation shifts one series forward by k periods and asks whether earlier X moves align with later Y moves.')
f('rho_{X->Y}(k) = Corr( x_t, y_{t+k} )')
h('Is this a percent?')
p('<b>No.</b> x_t and y_t are returns (often decimal form). rho is on [-1, +1]. A lag k is an integer count of bars, not a percent.')

page('FX percent math on one move', '03 / Returns in plain numbers')
f('Simple: 1.1110/1.1000 - 1 = 0.01 (1.00%)\nLog: ln(1.1110/1.1000) = about 0.009950 (~0.995%)')
p('Build return series first. Then align x_t with y_{t+k}. Mixing quote conventions can flip signs; keep one convention per study.')
p('Lagged cross-correlation uses the same return units as same-day correlation. A rho of 0.40 is not 40% return and not 40% forecast accuracy.')
p('After you compute returns, apply the lag before any optional standardisation step so the time index stays transparent in experiment logs.')

page('Which series and which lag?', '04 / Data rules')
h('Returns, equal spacing')
p('Use log or simple returns consistently. Each lag k drops k rows at the end of the alignment.')
h('Direction label X to Y')
p('rho_{X->Y}(k) uses X at t and Y at t+k. rho_{Y->X}(k) swaps roles. They need not match.')
h('Not a trading back-test')
p('A high lagged rho can be spurious with many lags tried or with overlapping macro shocks.')

page('Research and screening role', '05 / Context')
p('Cross-correlation at lags is classical time-series diagnostics (Box-Jenkins tradition). In FX research it often appears as a first pass before Granger tests (folder 13) or VAR models.')
h('What we claim')
p('This guide teaches definition and honest limits. We do not cite invented EURUSD lead-lag results. Experiments not started.')

page('Meet the symbols', '06 / Dictionary')
table([['Symbol', 'Meaning'], ['k', 'Lag in bars (k=1 is one bar ahead for Y).'], ['x_t, y_t', 'Return at time t.'], ['rho_{X->Y}(k)', 'Lagged cross-correlation at lag k.'], ['n_k', 'Number of paired rows after alignment (n - k).']], [125, 345])
p('Positive k means Y is shifted forward relative to X in the pairing described on page 7. If your software uses the opposite sign convention, flip the label when you report results.')
p('n_k shrinks as k grows because the first k rows of Y (or last k rows of X) have no partner. Record n_k beside every rho you publish.')

page('The main formula', '07 / Alignment')
f('For k >= 1:\n  pairs: (x_1, y_{1+k}), (x_2, y_{2+k}), ...\n  rho_{X->Y}(k) = Pearson correlation of those pairs')
p('Apply the usual Pearson steps from folder 01 on the aligned subsample. k = 0 is same-bar correlation (different question).')
p('Write the lag explicitly in the report title, for example EURUSD leads GBPUSD by one daily bar, so readers know which direction you tested.')
p('If you reverse direction, you must rebuild the pairs; swapping labels without re-aligning rows is a common spreadsheet error.')

page('Sign of lag', '08 / Lead and lag language')
p('If rho_{X->Y}(1) is large and positive, x today tends to move with y tomorrow in a linear sense. That is not proof X causes Y economically.')
p('Negative k or reverse ordering defines the opposite direction. Plot the cross-correlation function (CCF) across k to see several lags at once.')

page('Calculate by hand: k = 1', '09 / Worked example')
p('Five made-up daily returns (decimals):')
table([['t', 'x_t', 'y_t'], ['1', '0.010', '0.015'], ['2', '0.020', '0.040'], ['3', '0.030', '0.050'], ['4', '0.040', '0.070'], ['5', '0.050', '0.090']], [55, 150, 150])
p('For k = 1, pair x at t = 1..4 with y at t = 2..5.')
f('Aligned x: [0.010, 0.020, 0.030, 0.040]\nAligned y: [0.040, 0.050, 0.070, 0.090]\nrho_{X->Y}(1) = about 0.9898 in this toy list')
p('This teaching list is almost perfectly aligned at lag 1. Real FX series rarely look this clean; treat high rho as a prompt for deeper validation, not as proof of edge.')

page('Screen several lags', '10 / CCF habit')
p('Compute rho(k) for k = 0, 1, ..., K_max. Pre-specify K_max before you look. Trying many lags and reporting only the best is data mining.')
h('FX majors note')
p('Shared session opens can create microstructure lag patterns that differ from daily bars. Match bar size to the question you wrote down first.')

page('Limits', '11 / What this cannot prove')
h('Not forecast proof')
p('Correlation at a lag does not include costs, stability, or out-of-sample validation.')
h('Autocorrelation contamination')
p('If each series is highly autocorrelated, lagged cross-correlation can partly reflect own-lag structure. Consider pre-whitening or VAR/Granger paths for deeper tests.')
h('Versus Granger (folder 13)')
p('Granger tests predictability in a regression with multiple lags. Lagged cross-correlation is a lighter single-lag Pearson screen.')

page('Software check', '12 / statsmodels CCF')
f('import numpy as np\nfrom statsmodels.tsa.stattools import ccf\nx = np.array([...])\ny = np.array([...])\n# ccf(x, y, adjusted=False) gives cross-correlations\n# Read docs for normalization and lag order')
p('Confirm whether the function returns corr(x_t, y_{t-k}) or corr(x_t, y_{t+k}). Package conventions differ; map explicitly to rho_{X->Y}(k) in this guide.')

page('Check your understanding', '13 / Quick questions')
p('<b>Is rho_{X->Y}(k) a percent?</b> No. <b>Does k=1 prove X forecasts Y?</b> No, it is a linear screen at one lag. <b>Should I try many k values?</b> Pre-set K_max and note multiple-test risk.')
p('Plot the CCF for context, but do not cherry-pick the lag with the largest absolute value without a pre-registration rule.')

page('Sources and further reading', '14 / Research trail')
p('<b>Is rho a percent?</b> No. <b>Does high rho at k=1 prove tradeable lead?</b> No. <b>Should I scan many lags?</b> Only with a pre-set max and multiple-test caution.')
refs = [
    ('1', 'statsmodels.tsa.stattools.ccf documentation.', 'https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.ccf.html', 'CCF implementation and lag convention.'),
    ('2', 'Folder 01 Pearson Correlation guide.', '../01%20-%20Pearson%20Correlation/Pearson_Correlation_Complete_Simple_Guide.pdf', 'Pearson on aligned pairs.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>', styles['SmallEasy']))
    story.append(Spacer(1, 8))


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 12  |  LAGGED CROSS-CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(str(OUT), pagesize=(595.28, 841.89), rightMargin=55, leftMargin=55, topMargin=43, bottomMargin=59, title='Lagged Cross-Correlation - Complete Simple Guide', author='Research CO-1', pageCompression=1)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
page_count = len(reader.pages)
assert 14 <= page_count <= 16, f'Unexpected page count: {page_count}'
for i, pg in enumerate(reader.pages):
    assert len(pg.extract_text()) > 350, (i + 1, len(pg.extract_text()))
assert abs(FX_SIMPLE - 0.01) < 1e-12
assert abs(FX_LOG - 0.009950330853168092) < 1e-12
assert abs(RHO_X_TO_Y - 0.9897782665572893) < 1e-9
print(f'Created and checked {page_count} pages: {OUT}')
