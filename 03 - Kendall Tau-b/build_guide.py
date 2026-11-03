from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Kendall_Tau_b_Complete_Simple_Guide.pdf'
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


C_EX = 8
D_EX = 2
TAU_EX = (C_EX - D_EX) / sqrt((C_EX + D_EX) * (C_EX + D_EX))
assert abs(TAU_EX - 0.6) < 1e-12

page('Kendall tau-b', 'Method 03 / A complete beginner guide')
p('<b>Question this method answers:</b> Among all day pairs in your sample, how often do X and Y move in the same direction versus opposite directions — with a tie-aware correction?')
p('Kendall tau-b returns a score from -1 to +1. This guide covers FX returns setup, the tau-b formula, a numeric example (C=8, D=2), daily-major usage, limits, and software checks.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Idea, sign, size, percent trap'],
    ['3', 'FX return math for majors'],
    ['4', 'Which series Kendall uses here'],
    ['5', 'Research notes (section 03)'],
    ['6', 'Symbol dictionary'],
    ['7-8', 'Formula and concordant pairs'],
    ['9-10', 'Daily majors workflow and limits'],
    ['11', 'Software reproduction'],
    ['12-15', 'tau vs Pearson, practice, sources'],
], [65, 405])
p('Prepared for: 03 - Kendall Tau-b. README status: not started — no pair experiment numbers here.')

page('What does tau-b measure?', '02 / The basic idea')
p('Look at every unordered pair of days (i, j). Count concordant pairs (both X and Y move the same way) versus discordant pairs (opposite ways). Ties get tracked separately in tau-b.')
h('Sign and size')
table([
    ['tau_b near +1', 'Almost all usable pairs are concordant.'],
    ['tau_b near 0', 'Concordant and discordant counts balance.'],
    ['tau_b near -1', 'Discordant pairs dominate.'],
], [120, 350])
h('Is this number a percent?')
table([
    ['Mistake', 'Truth'],
    ['"tau_b = 0.6 means 60% concordant pairs"', 'Not exactly — tau-b divides (C-D) by a tie-adjusted denominator, not by pair count alone.'],
    ['"tau_b = 0.6 equals Pearson r = 0.6"', 'No. Same numeric label, different methods. Compare like with like.'],
], [220, 250])
p('Remember: <b>tau 0.6 is not Pearson 0.6</b> even when both are positive.')

page('FX percent math (majors)', '03 / Returns before correlation')
f('Simple return = P_t / P_{t-1} - 1\nPercent = 100 * simple return\nLog return = ln(P_t / P_{t-1})')
p('Example: 1.1000 → 1.1110 gives simple 1.0000% and log about 0.9950%. Use one definition for both FX legs.')
p('Quote reversal flips log-return sign. Missing quotes are not zeros. Four prices → three returns.')

page('Which series this method uses', '04 / Data choice')
p('Apply tau-b to <b>matched daily returns</b> (typically daily log returns of close) on aligned FX dates, same pairing discipline as methods 01 and 02.')
p('Kendall uses pairwise comparisons across days, so duplicate or mis-ordered dates distort C and D counts.')
p('Do not feed price levels unless your question is explicitly about levels — trending prices inflate concordance for the wrong reason. Flat or repeated returns create ties; note that in the report.')

page('Research notes (section 03)', '05 / Where the method comes from')
p('Section 03 in forex-formulas-explained.pdf gives Kendall tau-b with tie corrections:')
f('tau_b = (C - D) / sqrt( (C + D + T_x) * (C + D + T_y) )')
p('C = concordant pairs, D = discordant pairs, T_x and T_y count tie involvement on each variable. SciPy implements this as <b>scipy.stats.kendalltau</b> with method tau-b for standard tie handling.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['C', 'Concordant unordered pairs.'],
    ['D', 'Discordant unordered pairs.'],
    ['T_x, T_y', 'Tie corrections for X and Y.'],
    ['n', 'Number of days (pairs of days = n(n-1)/2).'],
    ['tau_b', 'Kendall tau-b statistic.'],
    ['x_i, y_i', 'Return (or other value) on matched day i.'],
    ['p-value', 'Optional; depends on independence assumptions — fragile for daily FX.'],
], [100, 370])
p('Concordant means (x_i - x_j) and (y_i - y_j) have the same strict sign. Discordant means opposite signs. Ties add to T terms instead of C or D.')

page('Formula explained', '07 / Piece by piece')
f('tau_b = (C - D) / sqrt( (C + D + T_x) * (C + D + T_y) )')
h('Numerator')
p('C - D is the net excess of same-direction moves over opposite-direction moves among counted pairs.')
h('Denominator')
p('The square root term shrinks the score when many ties exist, so tau-b stays comparable across samples with different tie rates.')

page('Hand numeric example (no ties)', '08 / C=8, D=2')
p('When there are no ties, T_x = T_y = 0 and C + D equals all unordered pairs compared.')
f('C = 8\nD = 2\nC + D = 10\ntau_b = (8 - 2) / sqrt(10 * 10) = 6 / 10 = 0.6')
p('This matches the worked line in section 03 of the formula PDF. It is a teaching arithmetic check, not a claim about any currency pair.')
p('With n = 5 days there are 10 unordered day pairs, so C + D = 10 is consistent with a tie-free comparison of five points.')

page('Daily majors: how to use tau-b', '09 / Practical workflow')
p('Fix your date window and return type. Merge AUDUSD and NZDUSD (for example) on date. Compute tau-b on the two return columns.')
p('Use tau-b when you want a robust count-based view that is less sensitive to one giant return than Pearson, but still need tie-aware software for repeated returns.')

page('Limits', '10 / What tau-b cannot tell you')
p('tau-b does not measure linear fit, hedge size, or lead-lag. It is not a percent of days. Small samples yield few unordered pairs — uncertainty is large.')
p('Heavy ties (many flat days) inflate T_x and T_y and pull tau_b toward 0 even if raw moves look linked.')
p('A large |tau_b| in a long FX history still does not prove the link will hold next month. Structural breaks and policy shocks can reorder returns without warning.')

page('Software check', '11 / Reproduce standard output')
f('from scipy.stats import kendalltau\n# On your merged return columns:\n# tau, pval = kendalltau(x, y, method="asymptotic")')
p('For the PDF arithmetic drill, assert (8-2)/sqrt(100) = 0.6 without needing live FX data.')
p('Always report n and date span alongside tau_b.')
p('SciPy may return a p-value; treat it as optional for FX daily panels where independence fails. The tau_b point estimate is still useful descriptively.')

page('Compare methods carefully', '12 / tau_b vs Pearson vs Spearman')
p('Three scores can rank pairs differently. Report which method answers your question. Do not mix baselines across methods in one alert rule without relabelling.')
p('Pearson reacts to magnitude; Spearman to rank order; Kendall to pairwise direction counts with tie correction. For crisis weeks, Kendall and Spearman often move less than Pearson — but none remove the need to inspect plots.')
p('When method 03 experiments start, store tau_b next to method 01 r on the same date merge for apples-to-apples tables.')

page('Practice', '13 / Quick questions')
p('<b>Q:</b> C=10, D=0, no ties — tau_b? <b>A:</b> +1.')
p('<b>Q:</b> C=D — tau_b? <b>A:</b> 0.')
p('<b>Q:</b> Is 0.6 here the same as Pearson 0.6? <b>A:</b> No.')
p('<b>Q:</b> With n=5 days, how many unordered pairs? <b>A:</b> 10.')
p('<b>Q:</b> Does tau_b use ranks like Spearman? <b>A:</b> No — it counts concordant/discordant pairs on raw values (ties handled via T terms).')
p('Work habit: write C, D, and n on scratch paper before trusting software output for a new pair.')

page('Sources', '14 / Research trail')
refs = [
    ('1', 'SciPy documentation: scipy.stats.kendalltau.', 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kendalltau.html', 'tau-b implementation and tie options.'),
    ('2', 'forex-formulas-explained.pdf — section 03 (this repository).', '../forex-formulas-explained.pdf', 'Repo formula sheet for method 03.'),
    ('3', 'Kendall, M. G. (1938). A new measure of rank correlation. Biometrika, 30(1/2), 81–93.', 'https://doi.org/10.2307/2332226', 'Original tau family.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))

page('Folder checklist', '15 / Before experiments')
p('Document merge rules, tie counts if unusual, and keep tau_b alongside Pearson for context when experiments begin under experiments/v001/.')
p('Save snapshot id, return definition, and software versions in NOTES when you freeze a run. Rebuild this PDF after formula changes with python build_guide.py.')
p('End of Kendall tau-b beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 03  |  KENDALL TAU-B')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Kendall Tau-b - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert abs((C_EX - D_EX) / sqrt((C_EX + D_EX) ** 2) - 0.6) < 1e-12
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
