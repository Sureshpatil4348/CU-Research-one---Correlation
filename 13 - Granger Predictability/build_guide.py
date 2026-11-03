from pathlib import Path
from math import sqrt, log
import numpy as np
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Granger_Predictability_Complete_Simple_Guide.pdf'
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


Y = [0.020, 0.030, 0.050, 0.040, 0.060]
X = [0.010, 0.020, 0.010, 0.030, 0.020]
Y_T = np.array(Y[1:])
Y_L1 = np.array(Y[:-1])
X_L1 = np.array(X[:-1])
B_HAT = np.linalg.lstsq(np.column_stack([np.ones(len(Y_T)), Y_L1, X_L1]), Y_T, rcond=None)[0][2]
FX_SIMPLE = 1.1110 / 1.1000 - 1
FX_LOG = log(1.1110 / 1.1000)


page('Granger predictability', 'Method 13 / A complete beginner guide')
p('<b>Does past X help predict Y beyond past Y alone?</b> Granger predictability tests whether lagged X adds explanatory power in a time-series regression. It is <b>not</b> economic causation.')
p('Teaching regression arithmetic only. Experiments in this folder have not started.')
h('Read it in three parts')
p('<b>First:</b> Idea, percents, data. <b>Next:</b> Granger (1969), model, null b=0, hand fit. <b>Last:</b> FX use, multiple lags, limits, software.')
table([['Pages', 'What you will learn'], ['2', 'Idea; is this a percent?'], ['3', 'FX percent example'], ['4', 'Return series and lag order'], ['5', 'Granger 1969 context'], ['6-9', 'Model, null, hand calc'], ['10-11', 'Practice and limits'], ['12-14', 'Software and sources']], [65, 405])
p('Prepared for the folder: 13 - Granger Predictability<br/>3 November 2026')

page('What does Granger predictability test?', '02 / The basic idea')
p('Estimate a regression for y_t with lags of y and lags of x. If lagged x coefficients are jointly zero, x does not Granger-cause y in this statistical sense.')
f('y_t = c + a * y_{t-1} + b * x_{t-1} + e_t\nNull for one lag: H0: b = 0')
h('Is b a percent?')
p('<b>Not necessarily.</b> If y_t is a decimal return, b is a slope in return units. The test p-value is a probability, not a percent return. Do not call a significant b proof that X makes Y move economically.')

page('FX percent math on one move', '03 / Returns in plain numbers')
f('Simple: 1.1110/1.1000 - 1 = 0.01 (1.00%)\nLog: ln(1.1110/1.1000) = about 0.009950 (~0.995%)')
p('Granger tests are applied to stationary return (or change) series, not to raw trending price levels.')
p('Regression coefficients b_j scale how past decimal returns of x relate to y_t. They are not the same object as a correlation percent or a hit rate.')
p('Write returns as decimals or percent labels in tables, but keep the regression inputs consistent with the column headers you publish.')

page('Which series and how many lags?', '04 / Data rules')
h('Aligned returns')
p('Same timestamps for x_t and y_t. Build lags from the same cleaned panel.')
h('Lag order p')
p('With multiple lags, test the joint null that all b coefficients on x lags are zero. Choosing p after seeing results inflates false positives.')
h('Stationarity caution')
p('Non-stationary levels can spuriously suggest predictability. Returns are the usual FX starting point.')

page('Granger (1969)', '05 / Research notes')
h('Granger, C. W. J. (1969) [1]')
p('"Investigating Causal Relations by Econometric Models and Cross-spectral Methods." Econometrica, 37(3), 424-438. Introduced Granger causality as predictability in mean (conditional on lags), not philosophical cause.')
p('Modern work stresses limitations: common factors, structural breaks, and reverse causality can violate interpretation even when b is significant.')

page('Meet the symbols', '06 / Dictionary')
table([['Symbol', 'Meaning'], ['y_t, x_t', 'Return series at t.'], ['c', 'Intercept.'], ['a', 'Coefficient on y_{t-1}.'], ['b', 'Coefficient on x_{t-1} (one-lag case).'], ['e_t', 'Regression residual.'], ['H0', 'Null: b = 0 (one lag) or all x-lag b\'s = 0.']], [125, 345])
p('In the multiple-lag case write a_i for y lags and b_j for x lags. The joint null is that every b_j equals zero, not that any single b_1 is zero alone.')
p('The error e_t is what y_t minus the fitted value. Large autocorrelation in e_t means your lag order p may be too small.')

page('One-lag regression', '07 / Formula')
f('y_t = c + a * y_{t-1} + b * x_{t-1} + e_t\n\nRestricted model (null): drop x_{t-1}\nCompare fit with an F-test or t-test on b (equivalent in single-lag linear Gaussian case with same sample).')
p('Multiple lags: include y_{t-1},...,y_{t-p} and x_{t-1},...,x_{t-p}. Joint test all x-lag coefficients.')

page('What Granger is not', '08 / Interpretation')
p('Statistical predictability can come from a shared macro factor that moves both series. It can disappear out of sample. It does not identify policy transmission by itself.')
p('Combine with economic design, stability checks, and (when needed) VAR/VECM frameworks beyond this beginner sheet.')

page('Hand fit: four usable rows', '09 / Worked example')
p('Made-up decimal returns (n=5 gives four regression rows after lagging):')
table([['t', 'x_t', 'y_t'], ['1', '0.010', '0.020'], ['2', '0.020', '0.030'], ['3', '0.010', '0.050'], ['4', '0.030', '0.040'], ['5', '0.020', '0.060']], [55, 150, 150])
p('Regress y_t on y_{t-1} and x_{t-1} for t = 2..5. Software OLS gives b_hat about 1.222 on x_{t-1} (slope in return units, not a percent label).')
f('Null H0: b = 0 is tested with standard regression output.\nDo not treat one tiny sample p-value as trading edge.')
p('Recompute with statsmodels or numpy on page 12 to match digits.')

page('Multiple lags', '10 / Joint test reminder')
f('y_t = c + SUM_{i=1..p} a_i y_{t-i} + SUM_{j=1..p} b_j x_{t-j} + e_t\nH0: b_1 = ... = b_p = 0 jointly')
p('Use a joint F-test or Wald test from your package. Reporting only the single lag with smallest p-value is misleading.')
p('Choose p before estimation when possible. If you must select p by an information criterion, report the criterion path and the final joint test together.')
p('Granger from x to y and Granger from y to x are two separate regressions; symmetry is not assumed and should not be expected in FX.')

page('FX majors and limits', '11 / Practice')
p('Granger tests between majors often react to USD factors and session effects. Pre-specify pairs, lags, sample, and return type.')
h('Limits')
p('In-sample fit only unless you add true out-of-sample steps. Microstructure and holiday gaps matter at high frequency.')
p('Experiments not started; no invented significant pair results here.')

page('Software check', '12 / statsmodels Granger')
f('from statsmodels.tsa.stattools import grangercausalitytests\n# Data matrix [y, x] column order per docs\n# grangercausalitytests(series, maxlag=p)')
p('Also verify with manual OLS: y_t on constant, y lag, x lag. Match b_hat to this guide\'s toy example.')
f('import numpy as np\ny = np.array([0.020,0.030,0.050,0.040,0.060])\nx = np.array([0.010,0.020,0.010,0.030,0.020])\nY=y[1:]; Y1=y[:-1]; X1=x[:-1]\nXmat = np.column_stack([np.ones(4), Y1, X1])\nb = np.linalg.lstsq(Xmat, Y, rcond=None)[0]\nprint(b[2])  # about 1.222')

page('Check your understanding', '13 / Quick questions')
p('<b>Does rejecting H0: b=0 prove economic cause?</b> No. <b>Is b a percent?</b> It is a regression slope in return units. <b>One lag enough?</b> Often use a joint test when p is greater than 1.')
p('Report the unrestricted and restricted model sample sizes and lag order p in experiment notes when v001 begins.')

page('Sources and further reading', '14 / Research trail')
p('<b>Does Granger mean cause?</b> No. <b>One lag enough?</b> Often no; use joint tests when p&gt;1. <b>Is b a percent?</b> It scales returns, not a correlation percent.')
refs = [
    ('1', 'Granger, C. W. J. (1969). Investigating Causal Relations by Econometric Models and Cross-spectral Methods. Econometrica, 37(3), 424-438.', 'https://doi.org/10.2307/1912791', 'Original Granger causality framework.'),
    ('2', 'statsmodels.tsa.stattools.grangercausalitytests.', 'https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.grangercausalitytests.html', 'Lag tests and column order.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>', styles['SmallEasy']))
    story.append(Spacer(1, 8))


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 13  |  GRANGER PREDICTABILITY')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(str(OUT), pagesize=(595.28, 841.89), rightMargin=55, leftMargin=55, topMargin=43, bottomMargin=59, title='Granger Predictability - Complete Simple Guide', author='Research CO-1', pageCompression=1)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
page_count = len(reader.pages)
assert 14 <= page_count <= 16, f'Unexpected page count: {page_count}'
for i, pg in enumerate(reader.pages):
    assert len(pg.extract_text()) > 350, (i + 1, len(pg.extract_text()))
assert abs(FX_SIMPLE - 0.01) < 1e-12
assert abs(FX_LOG - 0.009950330853168092) < 1e-12
assert abs(B_HAT - 1.222222222222222) < 1e-9
print(f'Created and checked {page_count} pages: {OUT}')
