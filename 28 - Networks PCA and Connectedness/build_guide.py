from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Networks_PCA_and_Connectedness_Complete_Simple_Guide.pdf'
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


RHO12 = 0.60
N_ASSETS = 3
D12 = sqrt(2 * (1 - RHO12))
# Teaching spillover shares theta_tilde (rows from i, cols to j); diagonals own share
THETA = [
    [0.60, 0.25, 0.15],
    [0.20, 0.55, 0.25],
    [0.18, 0.22, 0.60],
]
OFF_SUM = sum(THETA[i][j] for i in range(N_ASSETS) for j in range(N_ASSETS) if i != j)
TCI = 100 * OFF_SUM / N_ASSETS
# Correlation matrix for 3 FX legs (teaching)
CORR = [
    [1.0, 0.6, 0.4],
    [0.6, 1.0, 0.5],
    [0.4, 0.5, 1.0],
]
FX_SIMPLE = 1.1110 / 1.1000 - 1
FX_LOG = log(1.1110 / 1.1000)


page('Networks, PCA, and connectedness', 'Method 28 / A complete beginner guide')
p('<b>Three tools for how FX return correlations fit together:</b> network distance from rho, PCA eigenvalues Rv = lambda_v, and Diebold-Yilmaz total connectedness TCI.')
p('An edge or high TCI is <b>not</b> a trade signal. TCI is already scaled by 100 and reads as percent of forecast-error variance shares, not FX price percent. Teaching numbers only; experiments not started.')
h('Read it in three parts')
p('<b>First:</b> Three tools overview and FX percent. <b>Next:</b> Formulas and hand rows for d_ij, Rv, TCI. <b>Last:</b> Diebold-Yilmaz (2012), Basnarkov (2019), limits.')
table([['Pages', 'What you will learn'], ['2', 'Three tools, not one headline'], ['3', 'FX 1.1000 to 1.1110 returns'], ['4', 'Network distance from correlation'], ['5', 'PCA eigenvalues Rv'], ['6-8', 'TCI formula and hand table'], ['9-11', 'Diebold-Yilmaz and Basnarkov context'], ['12-14', 'Edges not trades, sources']], [65, 405])
p('Prepared for the folder: 28 - Networks PCA and Connectedness<br/>3 November 2026')

page('Three tools in one folder', '02 / The basic idea')
h('1. Network distance')
f('d_ij = sqrt( 2 * (1 - rho_ij) )')
p('Turns correlation into a distance for layout or clustering. rho_ij near +1 gives d_ij near 0.')
h('2. PCA on correlation matrix')
f('R v = lambda_v v   (eigenvalues Rv = lambda_v)')
p('Eigenvalues show how much variance a correlation matrix concentrates in leading components. R1 is the largest lambda.')
h('3. Total connectedness TCI')
f('TCI = 100 * SUM_{i not equal j} theta_tilde_ij / N')
p('theta_tilde_ij are normalised forecast-error variance shares from a VAR setup [2]. TCI aggregates off-diagonal spillovers across N assets.')
h('Is TCI a price percent?')
p('<b>No.</b> TCI is percent of forecast-error share totals, already multiplied by 100 in the usual formula. FX 1.00% returns are separate input data.')

page('FX percent math on one move', '03 / Returns in plain numbers')
f('Simple return = 1.1110/1.1000 - 1 = 0.01\nLog return = ln(1.1110/1.1000) = about 0.009950')
p('Build a return panel for N FX legs, estimate correlations or a VAR, then apply network, PCA, or connectedness tools. Use one return definition across legs.')
p('Quote direction must be consistent so rho_ij matches economic pairing.')

page('Network distance', '04 / From rho to d_ij')
p('For teaching rho_12 = 0.60 between leg 1 and leg 2:')
f('d_12 = sqrt(2 * (1 - 0.60)) = sqrt(0.80) = about 0.8944')
p('Use the same rho_ij you would report in folder 01. Negative rho gives d_ij &gt; sqrt(2) in this metric.')
h('Edge drawing')
p('Thick edges often mean small distance (high rho). That is descriptive geometry, not a buy/sell rule.')

page('PCA on correlation matrix', '05 / Eigenvalues Rv')
p('Given a symmetric correlation matrix of N FX returns, solve for eigenvalues lambda_1 &gt;= lambda_2 &gt;= ... &gt;= lambda_N.')
f('Rv = lambda_v   (v = 1..N)')
p('Large lambda_1 relative to others means co-movement loads mainly on one factor (often a global risk or USD factor in FX panels).')
p('This guide does not hand-solve a 3x3 eigen system; software returns Rv. Interpret Rv with the same correlation window used to build R.')

page('Connectedness shares', '06 / theta_tilde and TCI')
p('Diebold-Yilmaz generalised variance decomposition produces shares theta_tilde_ij: fraction of h-step forecast-error variance in variable j attributed to shocks in i.')
f('TCI = 100 * (1/N) * SUM_{i=1..N} SUM_{j=1..N, j not equal i} theta_tilde_ij')
p('The leading 100 converts the share sum into a percent-style index. It is <b>not</b> the percent move of a rate.')
h('Hand table (teaching shares)')
table([['i\\j', '1', '2', '3'], ['1', '0.60', '0.25', '0.15'], ['2', '0.20', '0.55', '0.25'], ['3', '0.18', '0.22', '0.60']], [55, 90, 90, 90])

page('Hand calc: TCI', '07 / Worked example')
f('Off-diagonal sum = 0.25+0.15+0.20+0.25+0.18+0.22 = 1.25\nN = 3\nTCI = 100 * 1.25 / 3 = about 41.6667')
p('Rows should sum to one in a full decomposition table; here the teaching matrix illustrates the TCI aggregator only.')
p('Compare TCI across windows only when VAR lag order, horizon, and orthonormalisation choices match.')

page('Research context', '08 / Diebold-Yilmaz and Basnarkov')
h('Diebold, F. X., & Yilmaz, K. (2012) [2]')
p('Framework for variance-decomposition connectedness and the TCI measure widely used in financial spillover dashboards.')
h('Basnarkov et al. (2019) [3]')
p('Discusses network perspectives on correlation structure among financial time series; useful when linking PCA/network views to empirical FX panels.')
p('We do not invent live TCI paths for majors. Experiments not started.')

page('How the three tools relate', '09 / One panel, three views')
p('Start from the same estimated correlation or VAR object. Network distances summarise pairwise rho_ij. PCA compresses the correlation matrix spectrum. TCI summarises directional spillover shares.')
h('Do not merge blindly')
p('High rho_ij can coexist with moderate TCI if shock transmission asymmetry differs. Report which tool answers your question.')

page('Edges are not trade signals', '10 / Limits')
h('Descriptive only')
p('Network plots highlight structure; they do not include costs, causality tests, or out-of-sample stability.')
h('VAR specification risk')
p('TCI moves with lag length, ordering in Cholesky identification, and sample window.')
h('PCA factors are not labels')
p('Leading eigenvectors need economic interpretation; they are not guaranteed USD or carry factors without further analysis.')

page('Versus folder 01 Pearson', '11 / Correlation alone')
p('Pearson rho_ij is one input to d_ij. It does not produce TCI or Rv without the extra machinery on pages 5-7.')
p('Rolling correlation (folder 05) can feed time-varying networks; document whether d_ij is static or time-varying.')
p('A single high rho between two majors does not, by itself, justify a pairs trade: network tools describe dependence structure in the window you chose, not forward PnL.')
p('When you publish a network figure, attach the correlation window dates and the list of legs so readers can reproduce rho_ij before they interpret edge length.')

page('Software sketch', '12 / Distance and TCI row')
f('from math import sqrt\nrho12 = 0.60\nd12 = sqrt(2*(1-rho12))\noff = 1.25\nN = 3\ntci = 100 * off / N\nprint(d12, tci)  # about 0.8944, 41.666...')
p('Packages such as ConnectednessApproach (R) or Python ports implement VAR-based theta_tilde_ij. Match horizon and identification to [2].')

page('Sources and further reading', '13 / Research trail')
refs = [
    ('1', 'Folder 01 Pearson Correlation.', '../01%20-%20Pearson%20Correlation/README.md', 'Source of rho_ij for distances.'),
    ('2', 'Diebold, F. X., & Yilmaz, K. (2012). Better to give than to receive: Predictive directional measurement of volatility spillovers. International Journal of Forecasting, 28(1), 57-66.', 'https://doi.org/10.1016/j.ijforecast.2011.02.006', 'Connectedness and TCI framework.'),
    ('3', 'Basnarkov, L., et al. (2019). Network analysis of multivariate financial time series. (See journal record for full author list and title.)', 'https://doi.org/10.1016/j.physa.2019.122607', 'Network view of correlation structure; check record for exact citation.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/>'
        f'<link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))

page('Check your understanding', '14 / Quick questions')
p('<b>Is TCI a FX price percent?</b> No—it scales forecast-error share sums. <b>Does a short edge mean buy?</b> No. <b>Does high rho always mean high TCI?</b> Not necessarily; TCI needs VAR shares.')
p('When experiments start, save VAR lag p, horizon H, and the full theta_tilde matrix with TCI for the snapshot window.')

page('Workflow before experiments', '15 / Working method')
h('1. Fix the panel')
p('Same bar time, return type, and list of N FX legs from one snapshot.')
h('2. Pick the tool to match the question')
p('Pairwise geometry (d_ij), factor compression (Rv), or spillover index (TCI).')
h('3. Unit-check returns')
p('Verify 1.1000 to 1.1110 maps to 0.01 simple and about 0.009950 log on a leg used in the panel.')
h('4. Report specification')
p('VAR lags, identification scheme, and window length beside every network or TCI chart.')
p('Experiments not started. No invented connectedness dashboards until v001 exists.')

def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 28  |  NETWORKS PCA AND CONNECTEDNESS')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Networks PCA and Connectedness - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
page_count = len(reader.pages)
assert 14 <= page_count <= 16, f'Unexpected page count: {page_count}'
for i, pg in enumerate(reader.pages):
    assert len(pg.extract_text()) > 350, (i + 1, len(pg.extract_text()))
assert abs(FX_SIMPLE - 0.01) < 1e-12
assert abs(FX_LOG - 0.009950330853168092) < 1e-12
assert abs(D12 - sqrt(0.8)) < 1e-12
assert abs(TCI - 125 / 3) < 1e-12
print(f'Created and checked {page_count} pages: {OUT}')
