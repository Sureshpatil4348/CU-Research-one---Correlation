from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Partial_and_Residual_Correlation_Complete_Simple_Guide.pdf'
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


Z = [1.0, 2.0, 3.0, 4.0, 5.0]
X = [2.0, 4.0, 5.0, 4.0, 5.0]
Y = [1.0, 3.0, 4.0, 5.0, 6.0]
FX_LOG = log(1.1110 / 1.1000)
FX_SIMPLE = 1.1110 / 1.1000 - 1


def ols_residuals(dep, ctrl):
    n = len(dep)
    mean_c = sum(ctrl) / n
    mean_d = sum(dep) / n
    num = sum((ctrl[i] - mean_c) * (dep[i] - mean_d) for i in range(n))
    den = sum((ctrl[i] - mean_c) ** 2 for i in range(n))
    slope = num / den
    intercept = mean_d - slope * mean_c
    return [dep[i] - (intercept + slope * ctrl[i]) for i in range(n)]


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    top = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    bot = sqrt(sum((a[i] - ma) ** 2 for i in range(n)) * sum((b[i] - mb) ** 2 for i in range(n)))
    return top / bot


EX = ols_residuals(X, Z)
EY = ols_residuals(Y, Z)
RHO_PARTIAL = pearson(EX, EY)


page('Partial and residual correlation', 'Method 07 / A complete beginner guide')
p('<b>How do two FX return series relate after you remove the part explained by a control series?</b> This guide explains residual (partial) correlation in small steps.')
p('You will regress each series on a control factor z, take the leftovers e_x and e_y, and correlate those residuals. That is the idea behind partial correlation in this folder.')
h('Read it in three parts')
p('<b>First:</b> The idea, percent returns, and data rules. <b>Next:</b> Symbols, regression formulas, and a hand calculation. <b>Last:</b> Majors practice, limits, and software checks.')
table([['Pages', 'What you will learn'], ['2', 'The idea and whether rho is a percent'], ['3', 'FX percent math on a worked quote move'], ['4', 'Which series and control factor to use'], ['5', 'Research: Basnarkov et al. 2019'], ['6-8', 'Symbols, formulas, and hand calculation'], ['9-10', 'Majors context and limits'], ['11-12', 'Software reproduction and sources']], [65, 405])
p('Examples are made-up teaching data. Experiments in this folder have not started. No invented live pair results appear here.')
p('Prepared for the folder: 07 - Partial and Residual Correlation<br/>3 November 2026')

page('What is partial / residual correlation?', '02 / The basic idea')
p('Sometimes two FX pairs move together mainly because they share a common driver. Partial correlation asks: <b>after accounting for z, do x and y still move together?</b>')
h('Two regressions, then one correlation')
p('Fit x = a + b*z + e_x. Fit y = c + d*z + e_y. The residuals e_x and e_y are the parts of x and y not explained by z. Partial correlation is Corr(e_x, e_y).')
h('Is this a percent?')
p('<b>No.</b> Returns may be labelled in percent. The partial correlation rho_partial is on the -1 to +1 scale. It describes linear co-movement of residuals, not a percent of variance explained (that would be R-squared language from regression).')
table([['Step', 'Output'], ['Regress x on z', 'Residuals e_x'], ['Regress y on z', 'Residuals e_y'], ['Pearson on e_x, e_y', 'rho_partial']], [120, 350])

page('FX percent math on one move', '03 / Returns in plain numbers')
p('From quote <b>1.1000 to 1.1110</b>:')
f('Simple return = 1.1110 / 1.1000 - 1 = 0.01  (1.00%)\nLog return = ln(1.1110 / 1.1000) = about 0.009950  (~0.995%)')
p('Partial correlation is usually computed on <b>return series</b> (log or simple) aligned in time. The control z_t should be built on the same clock and return definition unless your research note says otherwise.')
h('Control factor examples (conceptual)')
p('z might be a dollar index return, a PCA factor, or another portfolio return. The method does not pick z for you. A bad z choice can leave misleading residual correlation.')

page('Which series does this method use?', '04 / Data and control construction')
h('Returns for x, y, and z')
p('Use matched-period returns for the pair legs and the control. Document demeaning: many workflows use raw returns in regression; others demean first. Stay consistent within an experiment batch.')
h('Why control construction matters')
p('If z is a basket that already contains EUR and GBP, then EURUSD and GBPUSD residuals may look artificially weak or strong because overlap was baked into z. That is <b>mechanical overlap</b>, not causal isolation of a unique shock.')
h('Same currencies in basket vs true factor')
p('A well-designed factor targets shared movement you want to remove (e.g. broad USD). A basket copied from the same underlyings without orthogonalisation can remove too much or the wrong part. Write down the economic story before you interpret rho_partial.')
p('Experiments are not started in this folder. Future v001 should name the control series formula and snapshot id explicitly.')

page('Where does this fit in FX research?', '05 / Research notes')
h('Basnarkov et al. (2019) [1]')
p('<i>Correlation Patterns in Foreign Exchange Markets.</i> The paper studies structure in FX correlation matrices and motivates tools that separate common components from pair-specific co-movement. Partial and residual correlation are standard ways to ask how pairs relate after conditioning on a factor.')
p('This guide uses their work as the FX research anchor for folder 07. It does not reproduce their empirical tables or claim their results for your snapshot.')
h('Statistical lineage')
p('Partial correlation appears in multivariate statistics textbooks as correlation of residuals from linear adjustment. In FX, the hard part is choosing z, not the final Pearson step on e_x and e_y.')

page('Meet the symbols', '06 / A small math dictionary')
table([['Symbol', 'Meaning'], ['x_t, y_t', 'Return series for two pairs (or legs).'], ['z_t', 'Control factor return at the same time t.'], ['a, b, c, d', 'Regression intercepts and slopes.'], ['e_x, e_y', 'Residuals after regressing on z.'], ['rho_partial', 'Pearson correlation of e_x and e_y.'], ['n', 'Number of complete time rows.']], [125, 345])
p('Each t must have complete x, y, and z. Missing bars drop that row or require an explicit imputation rule recorded in experiment notes.')

page('The main formulas', '07 / What each part does')
f('x_t = a + b * z_t + e_x,t\ny_t = c + d * z_t + e_y,t\n\nrho_partial = Corr(e_x, e_y)')
h('Step 1: Regress x on z')
p('Ordinary least squares finds a and b that minimise squared errors. e_x,t is the vertical distance from the fitted line at each t.')
h('Step 2: Regress y on z')
p('Do the same separately for y. Use the same z column and the same row set. Do not mix different samples for the two regressions.')
h('Step 3: Correlate residuals')
p('Apply the Pearson formula from folder 01 to e_x and e_y. Sign and strength now refer to co-movement <b>after</b> linear removal of z.')

page('Regression details (one control)', '08 / How slopes are found')
f('b = SUM((z_t - z_bar)(x_t - x_bar)) / SUM((z_t - z_bar)^2)\na = x_bar - b * z_bar\ne_x,t = x_t - (a + b * z_t)')
p('Repeat with y_t to get c, d, and e_y,t. For multiple controls, matrix regression replaces these scalar formulas; this beginner guide stays with one z_t.')
h('Partial vs raw Pearson')
p('If z explains most of x and y, raw Pearson can be high while rho_partial is near zero. The opposite can also happen when z obscures a opposite co-movement. Always report what z was.')

page('Calculate it by hand: start', '09 / Worked example, part one')
p('Five made-up rows. z could stand for a common factor; numbers are not market data.')
table([['t', 'z', 'x', 'y'], ['1', '1', '2', '1'], ['2', '2', '4', '3'], ['3', '3', '5', '4'], ['4', '4', '4', '5'], ['5', '5', '5', '6']], [50, 80, 80, 80])
h('Regress x on z')
f('z_bar = 3, x_bar = 4\nb = 6 / 10 = 0.6\na = 4 - 0.6*3 = 2.2\nFitted x_hat = 2.2 + 0.6*z')
table([['t', 'x_hat', 'e_x = x - x_hat'], ['1', '2.8', '-0.8'], ['2', '3.4', '0.6'], ['3', '4.0', '1.0'], ['4', '4.6', '-0.6'], ['5', '5.2', '-0.2']], [50, 120, 280])
p('Both e_x and e_y will have spread, so Pearson on the residuals is defined.')

page('Calculate it by hand: finish', '10 / Worked example, part two')
h('Regress y on z')
f('y_bar = 3.8\nb = 6 / 10 = 1.2\nc = 3.8 - 1.2*3 = 0.2\nFitted y_hat = 0.2 + 1.2*z')
table([['t', 'y_hat', 'e_y = y - y_hat'], ['1', '1.4', '-0.4'], ['2', '2.6', '0.4'], ['3', '3.8', '0.2'], ['4', '5.0', '0.0'], ['5', '6.2', '-0.2']], [50, 120, 280])
h('Partial correlation')
f('rho_partial = Corr(e_x, e_y) = about 0.8165')
p('Positive rho_partial means that after removing linear z effects, the leftover x and y pieces still tend to move in the same direction in this tiny sample. Five rows are far too few for market inference.')

page('Using partial correlation on majors', '11 / Effective practice')
h('Typical questions (when experiments exist)')
p('After removing a USD factor, do EURUSD and GBPUSD residuals still correlate? Does a correlation matrix entry reflect EUR-GBP idiosyncrasy or only shared USD beta? Those are design questions, not answers supplied here.')
h('Document z precisely')
p('Write the formula for z_t, its data source, return type, and whether it includes overlapping currencies. Review overlap before calling a residual independence result.')
h('No results in this guide')
p('Folder status is not started. Do not cite pair-specific partial correlations from this PDF. Run v001 with a frozen snapshot and store z construction in NOTES.md.')

page('Limits and common errors', '12 / What partial correlation cannot do')
h('Linear control only')
p('If the true common effect is nonlinear, linear regression leaves structure in residuals. Partial correlation then mixes that leftover structure with genuine pair co-movement.')
h('z is not automatically causal')
p('Removing a statistical factor does not prove counterfactual trading. Overlapping baskets can zero out correlation for mechanical reasons.')
h('Sample size and stability')
p('Many parameters (two regressions plus correlation) on short windows produce unstable rho_partial. Wide confidence intervals are expected unless n is large and the design is stable.')
h('Residual correlation is not partial correlation matrix entry in every package')
p('Some software computes partial correlation via a formula on the full correlation matrix. With one z and OLS residuals, the approaches align for Pearson partial under standard assumptions. Verify your library definition.')

page('Calculate it with software', '13 / Reproduce the teaching example')
h('Python: regress then correlate')
f('from math import sqrt\nz = [1,2,3,4,5]\nx = [2,4,5,4,5]\ny = [1,3,4,5,6]\ndef resid(dep, ctrl):\n    n = len(dep); mc = sum(ctrl)/n; md = sum(dep)/n\n    num = sum((ctrl[i]-mc)*(dep[i]-md) for i in range(n))\n    den = sum((ctrl[i]-mc)**2 for i in range(n))\n    b = num/den; a = md - b*mc\n    return [dep[i]-(a+b*ctrl[i]) for i in range(n)]\ndef pearson(a,b):\n    n=len(a); ma,mb=sum(a)/n,sum(b)/n\n    top=sum((a[i]-ma)*(b[i]-mb) for i in range(n))\n    bot=sqrt(sum((a[i]-ma)**2 for i in range(n))*sum((b[i]-mb)**2 for i in range(n)))\n    return top/bot\nrho = pearson(resid(x,z), resid(y,z))\nprint(rho)  # about 0.8165')
p('statsmodels or sklearn can fit OLS; scipy.stats.pearsonr finishes the last step. Align rows and handle missing data before regression.')

page('Sources and further reading', '14 / Research trail')
p('Links checked on 3 November 2026. Teaching numbers are original. [1] is the FX research anchor for this method folder.')
refs = [
    ('1', 'Basnarkov et al. (2019). Correlation Patterns in Foreign Exchange Markets.', 'https://doi.org/10.1016/j.physa.2018.12.015', 'FX correlation structure; use for research context and citation in experiment reports.'),
    ('2', 'SciPy: scipy.stats.pearsonr for the final residual correlation step.', 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html', 'Same Pearson definition as folder 01, applied to e_x and e_y.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/>'
        f'<link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('When experiments start, add a third reference row pointing to your frozen snapshot README and the exact z_t formula used in v001.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 07  |  PARTIAL / RESIDUAL CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Partial and Residual Correlation - Complete Simple Guide',
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
assert abs(RHO_PARTIAL - 0.8164965809277263) < 1e-9
print(f'Created and checked {page_count} pages: {OUT}')
