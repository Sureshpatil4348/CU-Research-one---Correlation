from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Shrinkage_Correlation_Complete_Simple_Guide.pdf'
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


DELTA = 0.2
S11, S22, S12 = 0.04, 0.03, 0.032
MU = (S11 + S22) / 2
T11 = (1 - DELTA) * S11 + DELTA * MU
T22 = (1 - DELTA) * S22 + DELTA * MU
T12 = (1 - DELTA) * S12
RHO_SHRINK = T12 / sqrt(T11 * T22)
FX_LOG = log(1.1110 / 1.1000)
FX_SIMPLE = 1.1110 / 1.1000 - 1


page('Shrinkage correlation', 'Method 08 / A complete beginner guide')
p('<b>How do you estimate a stable correlation matrix when you have many pairs but limited history?</b> Shrinkage pulls a sample matrix toward a simple target so estimates are better conditioned.')
p('This guide explains the blend formula, how to read delta, and how to get rho_ij from the shrunk covariance matrix.')
h('Read it in three parts')
p('<b>First:</b> Idea, percent returns, and inputs. <b>Next:</b> Symbols, shrinkage formulas, hand calculation. <b>Last:</b> Majors matrices, limits, Ledoit-Wolf software notes.')
table([['Pages', 'What you will learn'], ['2', 'The idea and whether rho is a percent'], ['3', 'FX percent math on a worked quote move'], ['4', 'Which series feed the sample matrix S'], ['5', 'Research: Ledoit and Wolf 2004'], ['6-9', 'Symbols, formulas, and hand calculation'], ['10-11', 'Majors correlation matrices and limits'], ['12-14', 'Workflow checklist, software, and sources']], [65, 405])
p('Teaching numbers only. Experiments in this folder have not started. No invented pair correlation tables appear here.')
p('Prepared for the folder: 08 - Shrinkage Correlation<br/>3 November 2026')

page('What is shrinkage correlation?', '02 / The basic idea')
p('From daily returns you build a <b>sample covariance matrix S</b>. When the window is short or pairs are many, S can be noisy (extreme correlations, ill-conditioned matrix).')
h('Blend toward a simple target')
p('Shrinkage replaces S with a mix of S and a structured target. A common target is mu times the identity matrix I: equal variances on the diagonal and zero covariances off-diagonal (in the simplest spec).')
h('Is rho_ij a percent?')
p('<b>No.</b> Returns may be quoted in percent. Matrix entry rho_ij is a correlation on [-1, 1] derived from shrunk covariances. Delta = 0.2 is a <b>weight on the target</b>, not a percent co-movement score.')
table([['delta', 'Plain reading (this guide\'s convention)'], ['0.2', '80% sample S, 20% target on the diagonal blend'], ['0.0', 'Use sample S only (no shrinkage in this formula)'], ['1.0', 'Fully target (only in theory; not used in practice)']], [80, 390])

page('FX percent math on one move', '03 / Returns in plain numbers')
f('Quote 1.1000 -> 1.1110\nSimple return = 0.01  (1.00%)\nLog return = ln(1.1110/1.1000) = about 0.009950 (~0.995%)')
p('Shrinkage is applied to the covariance matrix built from return series. Pick log or simple returns for all legs in S, align times, and document demeaning. The shrinkage step itself does not fix bad alignment.')
h('Units in S')
p('If returns are decimals, variances are decimal squared. Correlation rho_ij is unit-free because it divides by standard deviations.')

page('Which series does this method use?', '04 / Building the sample matrix S')
h('Multivariate return panel')
p('Each column is one pair (or factor) return series over the estimation window. Each row is one time point. S is the sample covariance matrix of those columns (usually with n-1 divisor in unbiased sample cov).')
h('From covariance to correlation')
p('After forming the shrunk matrix Sigma_tilde, convert entry (i,j) to rho_ij = Sigma_tilde_ij / sqrt(Sigma_tilde_ii * Sigma_tilde_jj). Diagonal entries are variances, not correlations.')
h('When shrinkage helps in FX majors work')
p('With 28 unique major pairs, a full matrix has many entries. Short windows make raw sample correlations unstable. Shrinkage is a standard way to stabilise before portfolio or risk steps. Experiments here are not started; this page states design intent only.')

page('Where did shrinkage come from?', '05 / Research notes')
h('Ledoit and Wolf (2004) [1]')
p('<i>A well-conditioned estimator for large-dimensional covariance matrices.</i> They propose an optimal (asymptotic) shrinkage intensity toward a structured target, improving mean-squared error versus the raw sample matrix when dimension is large relative to sample size.')
p('Folder 08 cites this paper as the core reference. Ledoit-Wolf software estimates delta from data rather than fixing 0.2 by hand. The hand example here uses delta = 0.2 for transparent arithmetic.')
h('What this guide does not do')
p('It does not implement the full Ledoit-Wolf formula for optimal delta or every target matrix variant. It teaches the blend and correlation conversion used across the repo\'s formula PDF section 08.')

page('Meet the symbols', '06 / A small math dictionary')
table([['Symbol', 'Meaning'], ['S', 'Sample covariance matrix.'], ['delta', 'Shrinkage intensity in [0, 1].'], ['mu', 'Scalar target level for diagonal shrinkage (example: average sample variance).'], ['I', 'Identity matrix.'], ['Sigma_tilde', 'Shrunk covariance matrix.'], ['rho_ij', 'Correlation from Sigma_tilde.']], [125, 345])
p('Ledoit-Wolf allows richer targets (e.g. constant correlation model). This beginner sheet uses the diagonal mu*I target for a 2x2 hand walkthrough.')

page('The main formulas', '07 / What each part does')
f('Sigma_tilde = (1 - delta) * S + delta * mu * I\n\nrho_ij = Sigma_tilde_ij / sqrt(Sigma_tilde_ii * Sigma_tilde_jj)')
h('Off-diagonal covariances')
p('Only the sample off-diagonal entries scale with (1 - delta) in the simple mu*I target: they are not pulled toward zero by the delta*mu*I term because I has zeros off-diagonal. The target pulls variances toward mu while covariances are simply scaled down by (1 - delta).')
h('Interpret delta = 0.2')
p('Keep 80% of the sample covariance entries (on and off diagonal from S part) and add 20% of mu on each diagonal position. This matches the teaching split used in the next pages.')

page('Two-by-two hand matrix setup', '08 / Sample S and target')
p('Suppose two return series give sample variances 0.04 and 0.03 and sample covariance 0.032 (made-up teaching numbers).')
table([['', 'Series 1', 'Series 2'], ['Series 1', '0.0400', '0.0320'], ['Series 2', '0.0320', '0.0300']], [90, 150, 150])
f('mu = (0.04 + 0.03) / 2 = 0.035\ndelta = 0.2')
p('Raw sample correlation would be 0.032 / sqrt(0.04*0.03) = about 0.919. Shrinkage will pull that toward zero by dampening covariance and adjusting variances.')

page('Calculate shrinkage by hand', '09 / Worked example')
h('Diagonal of Sigma_tilde')
f('Sigma_tilde_11 = 0.8*0.04 + 0.2*0.035 = 0.039\nSigma_tilde_22 = 0.8*0.03 + 0.2*0.035 = 0.031')
h('Off-diagonal')
f('Sigma_tilde_12 = 0.8*0.032 = 0.0256\n(Symmetric: Sigma_tilde_21 = 0.0256)')
h('Correlation rho_12')
f('rho_12 = 0.0256 / sqrt(0.039 * 0.031)\n     = about 0.7363')
p('Compared with the raw 0.919, shrinkage lowers the correlation because the off-diagonal covariance is scaled by 0.8 while variances move toward the common mu.')

page('Using shrinkage on major FX pairs', '10 / Effective practice')
h('Many pairs, one matrix')
p('A 28-pair major study produces a 28-by-28 correlation matrix after shrinkage. Report delta (fixed or Ledoit-Wolf estimated), the return window, and whether S used log returns.')
h('Ledoit-Wolf in software')
p('Packages such as sklearn.covariance.LedoitWolf estimate delta automatically. Compare hand delta = 0.2 to the library intensity when you validate v001.')
h('No empirical matrix here')
p('Experiments are not started. Do not treat the 2x2 numbers as EURUSD-GBPUSD results. They exist only to show arithmetic.')
h('Positive semi-definite matrices')
p('Extreme sample correlations can produce non-PSD matrices in small samples. Shrinkage toward a valid target often improves numerical stability for downstream use.')

page('Limits and common errors', '11 / What shrinkage cannot do')
h('Not a forecast of future correlation')
p('Shrinkage improves estimation under a stated loss function. It does not guarantee stable correlations out of sample when regimes change.')
h('Target choice matters')
p('mu*I is a teaching target. Ledoit-Wolf and others use different targets; delta and the formula for mu change with the spec.')
h('Confusing delta with correlation')
p('delta = 0.2 means 20% weight on the target in the covariance blend defined here, not that correlation is 20%.')
h('Look-ahead in back-tests')
p('Estimate S on a rolling past window only. Do not include future returns in the window that your trading rule would not have seen.')

page('A short workflow checklist', '12 / Before you report a matrix')
h('1. Fix the return panel')
p('Same dates, same return type, same quote direction rules for every column in S. List how many rows were dropped for missing data.')
h('2. Build S, then shrink')
p('Record whether S is sample cov with n or n-1 divisor. Apply Sigma_tilde = (1-delta)*S + delta*mu*I or call LedoitWolf for data-driven delta.')
h('3. Convert to correlations')
p('Compute rho_ij from Sigma_tilde, not from S, if the report label says shrunk correlation. Keep a copy of both matrices for audit.')
h('4. Store parameters')
p('Window length, delta, mu rule, snapshot id, and pair list belong in experiment NOTES.md. This folder has no v001 yet; the checklist is for future runs only.')

page('Calculate it with software', '13 / Reproduce the teaching example')
h('Python: fixed delta 0.2')
f('from math import sqrt\nd = 0.2\nS11, S22, S12 = 0.04, 0.03, 0.032\nmu = (S11 + S22) / 2\nT11 = (1-d)*S11 + d*mu\nT22 = (1-d)*S22 + d*mu\nT12 = (1-d)*S12\nrho = T12 / sqrt(T11 * T22)\nprint(rho)  # about 0.7363')
h('Ledoit-Wolf (when experiments run)')
f('# from sklearn.covariance import LedoitWolf\n# lw = LedoitWolf().fit(returns_matrix)\n# lw.covariance_  then convert to correlation')
p('Match return scaling (decimal vs percent) before comparing to textbook variances.')

page('Sources and further reading', '14 / Research trail')
p('Links checked on 3 November 2026. Hand matrix is original teaching material. [1] is the primary citation for this method folder.')
refs = [
    ('1', 'Ledoit, O., and Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices.', 'https://doi.org/10.1016/j.jmultana.2003.07.002', 'Defines shrinkage toward structured targets and optimal intensity theory.'),
    ('2', 'sklearn.covariance.LedoitWolf documentation.', 'https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html', 'Practical estimator for experiment code in this repo.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/>'
        f'<link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Add experiment snapshot and estimated delta to this list when v001 completes under 08 - Shrinkage Correlation.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 08  |  SHRINKAGE CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Shrinkage Correlation - Complete Simple Guide',
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
assert abs(T11 - 0.039) < 1e-12
assert abs(RHO_SHRINK - 0.7362525549351051) < 1e-9
print(f'Created and checked {page_count} pages: {OUT}')
