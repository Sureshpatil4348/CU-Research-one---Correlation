from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Regime_Conditioned_Correlation_Complete_Simple_Guide.pdf'
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


QUIET_X = [0.010, 0.020, 0.015, 0.012]
QUIET_Y = [0.008, 0.018, 0.014, 0.011]
STRESS_X = [-0.050, 0.040, -0.030, 0.035]
STRESS_Y = [-0.030, -0.020, 0.025, -0.015]
RHO_QUIET = pearson(QUIET_X, QUIET_Y)
RHO_STRESS = pearson(STRESS_X, STRESS_Y)
FX_SIMPLE = 1.1110 / 1.1000 - 1
FX_LOG = log(1.1110 / 1.1000)


page('Regime-conditioned correlation', 'Method 11 / A complete beginner guide')
p('<b>Does correlation look different in calm weeks versus stress weeks?</b> Regime-conditioned correlation computes Pearson-style correlation separately within states you define in advance.')
p('You will see rho_quiet and rho_stress, why you must not average correlations, and how Benediktsdottir and Scotti (2009) motivate state-dependent FX co-movement. Teaching data only.')
h('Read it in three parts')
p('<b>First:</b> Idea, percents, data. <b>Next:</b> Research, symbols, formulas, hand calc. <b>Last:</b> Practice, limits, software.')
table([['Pages', 'What you will learn'], ['2', 'Idea; is rho a percent?'], ['3', 'FX percent example'], ['4', 'Which series and defining states'], ['5', 'Benediktsdottir & Scotti 2009'], ['6-9', 'Symbols, formulas, hand calc'], ['10-11', 'Use on majors and limits'], ['12-14', 'Checks, software, sources']], [65, 405])
p('Prepared for the folder: 11 - Regime-Conditioned Correlation<br/>3 November 2026')

page('What does regime correlation do?', '02 / The basic idea')
p('Split your sample into non-overlapping states (quiet, stress, or custom labels). Within each state, compute correlation of return series x and y on rows that belong to that state only.')
h('Two scores, not one blended guess')
f('rho_quiet = Corr(x, y | state = quiet)\nrho_stress = Corr(x, y | state = stress)')
h('Is this a percent?')
p('<b>No.</b> Returns inside each state may be written as percents. rho_quiet and rho_stress are correlations on [-1, +1].')

page('FX percent math on one move', '03 / Returns in plain numbers')
f('Simple: 1.1110/1.1000 - 1 = 0.01 (1.00%)\nLog: ln(1.1110/1.1000) = about 0.009950 (~0.995%)')
p('Regime correlation uses return series. States are usually defined from vol indices, policy dates, or rules known without peeking at future pair-specific outcomes.')

page('Which series and how to define states?', '04 / Data rules')
h('Returns, aligned times')
p('Same bar close for both legs. One row per time index before you tag regimes.')
h('Define states with known information')
p('Examples: VIX above a threshold, realised vol quintile computed from past data only, or calendar windows around labelled events. Write the rule before you compute rho_stress.')
h('Do not average correlations')
p('The mean of rho_quiet and rho_stress is generally <b>not</b> equal to the full-sample correlation. Report each regime separately with its sample size n.')

page('Research notes', '05 / Benediktsdottir and Scotti 2009')
h('Benediktsdottir, J., &amp; Scotti, C. (2009) [1]')
p('Working paper / IMF context on time-varying and state-dependent exchange rate correlations. They argue that pooling calm and crisis data hides economically different co-movement.')
p('This folder uses their lesson at a simple level: conditional correlation by regime, not a full copy of their econometric model.')
h('What we do not claim')
p('We do not reproduce their full empirical tables here. Experiments in this folder have not started.')

page('Meet the symbols', '06 / Dictionary')
table([['Symbol', 'Meaning'], ['S_t', 'Regime label at time t (quiet, stress, ...).'], ['1{...}', 'Indicator: 1 if condition true, else 0.'], ['rho_quiet', 'Correlation using rows with S_t = quiet only.'], ['n_quiet', 'Count of paired returns in quiet regime.'], ['x_t, y_t', 'Return series (same definition both legs).']], [125, 345])
p('The same symbols apply when you have more than two regimes; add rho and n for each label you use.')

page('The main formulas', '07 / Conditional correlation')
f('rho_quiet = Corr( {x_t, y_t} for t with S_t = quiet )\nrho_stress = Corr( {x_t, y_t} for t with S_t = stress )')
p('Corr here is the usual Pearson formula on the subsample. Spearman or robust variants are different methods (see folders 02 and 04).')
h('Full sample vs regimes')
f('Corr(x, y) on all rows != (rho_quiet + rho_stress) / 2 in general')
p('Pool correlation weights every day once. Regime correlations answer different questions.')

page('Choosing regimes carefully', '08 / Design notes')
h('Overlap and gaps')
p('If a day fits no state, drop it or add an other bucket. Document the rule.')
h('Small n per regime')
p('With few stress days, rho_stress is noisy. Report n and consider confidence intervals (folder 01 optional pages).')
h('Look-ahead bias')
p('Do not label stress using future knowledge of the pair correlation you are measuring.')

page('Calculate by hand: quiet subsample', '09 / Worked example, part one')
p('Quiet regime (four made-up daily returns, decimals not percent labels):')
table([['Day', 'x', 'y'], ['1', '0.010', '0.008'], ['2', '0.020', '0.018'], ['3', '0.015', '0.014'], ['4', '0.012', '0.011']], [65, 150, 150])
f('Means: x_bar = 0.01425, y_bar = 0.01275\nPearson steps give rho_quiet = about 0.9912')
p('All pairs move up together in this toy quiet window, so r is very high. Real quiet weeks need not look this clean.')

page('Calculate by hand: stress subsample', '10 / Worked example, part two')
p('Stress regime (four made-up returns):')
table([['Day', 'x', 'y'], ['1', '-0.050', '-0.030'], ['2', '0.040', '-0.020'], ['3', '-0.030', '0.025'], ['4', '0.035', '-0.015']], [65, 150, 150])
f('rho_stress = about -0.1895 in this toy list')
p('Stress rho can differ sharply from quiet rho. That is the point. Do not merge the eight rows and pretend one number tells both stories.')

page('Using regimes on FX majors', '11 / Effective practice')
p('Compare dollar-block pairs in quiet vs high-vol weeks when your state rule is fixed and auditable. Store the state series alongside returns.')
h('What not to do')
p('Do not tune the stress threshold until rho_stress looks exciting. Do not average regime rhos for a headline.')
p('Experiments not started; no live pair claims in this PDF.')

page('Limits and software', '12 / Cautions and checks')
h('Limits')
p('Regimes are discrete; boundary days flip labels. Correlation within a thin stress slice is unstable. State rules are not causal models.')
h('Python sketch')
f('import numpy as np\n# mask quiet rows, then np.corrcoef(x[mask], y[mask])[0,1]')
p('Match Pearson definition to folder 01. Save n_quiet and n_stress in outputs.')

page('Check your understanding', '13 / Quick questions')
h('Is rho_quiet a percent?')
p('<b>No.</b> It is a correlation on the quiet subsample only.')
h('Can I average rho_quiet and rho_stress?')
p('<b>Generally no</b> as a substitute for the full-sample correlation or a properly pooled estimator.')
h('Must states be defined in advance?')
p('<b>Yes</b> for honest research. Do not pick stress days after seeing the pair correlation you want.')
p('When experiments start, save the state indicator series next to returns so reviewers can reproduce each rho.')

page('Sources and further reading', '14 / Research trail')
p('<b>Is rho a percent?</b> No. <b>Can I average regime rhos?</b> Not as a substitute for full-sample or pooled estimators. <b>Can I use future data to tag stress?</b> Not if you want an honest research rule.')
p('Links checked 3 November 2026.')
refs = [
    ('1', 'Benediktsdottir, J., & Scotti, C. (2009). Exchange Rate Correlations in Quiet and Turbulent Times.', 'https://www.imf.org/', 'IMF working paper series; verify exact title and number on IMF site.'),
    ('2', 'Folder 01 Pearson Correlation guide.', '../01%20-%20Pearson%20Correlation/Pearson_Correlation_Complete_Simple_Guide.pdf', 'Pearson steps used inside each regime.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>', styles['SmallEasy']))
    story.append(Spacer(1, 8))


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 11  |  REGIME-CONDITIONED CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(str(OUT), pagesize=(595.28, 841.89), rightMargin=55, leftMargin=55, topMargin=43, bottomMargin=59, title='Regime-Conditioned Correlation - Complete Simple Guide', author='Research CO-1', pageCompression=1)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
page_count = len(reader.pages)
assert 14 <= page_count <= 16, f'Unexpected page count: {page_count}'
for i, pg in enumerate(reader.pages):
    assert len(pg.extract_text()) > 350, (i + 1, len(pg.extract_text()))
assert abs(FX_SIMPLE - 0.01) < 1e-12
assert abs(FX_LOG - 0.009950330853168092) < 1e-12
assert abs(RHO_QUIET - 0.9911908577446502) < 1e-9
assert abs(RHO_STRESS - (-0.18945647121890377)) < 1e-9
print(f'Created and checked {page_count} pages: {OUT}')
