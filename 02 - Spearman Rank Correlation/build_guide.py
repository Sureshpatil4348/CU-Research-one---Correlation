from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Spearman_Rank_Correlation_Complete_Simple_Guide.pdf'
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


def pearson_r(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    dx = [a - mx for a in x]
    dy = [b - my for b in y]
    top = sum(a * b for a, b in zip(dx, dy))
    bot = sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
    return top / bot


def rank_average(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


TEACH_X = [-2, 0, 3]
TEACH_Y = [-1, 1, 9]
assert rank_average(TEACH_X) == [1.0, 2.0, 3.0]
assert rank_average(TEACH_Y) == [1.0, 2.0, 3.0]
assert abs(pearson_r(rank_average(TEACH_X), rank_average(TEACH_Y)) - 1.0) < 1e-12

page('Spearman rank correlation', 'Method 02 / A complete beginner guide')
p('<b>Question this method answers:</b> When X goes up, does Y tend to go up too — even if the link is curved rather than a straight line? Spearman looks at <i>order</i> (ranks), not raw sizes.')
p('This guide walks through the idea, FX return setup, the formula, a tiny hand example, daily-major usage, limits, and a software check. All teaching numbers are made up unless labelled as research notes.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Idea, sign, size, and the percent trap'],
    ['3', 'FX percent and log return math'],
    ['4', 'Which series Spearman uses here'],
    ['5', 'Research notes (section 02)'],
    ['6', 'Symbol dictionary'],
    ['7-8', 'Formula and hand calculation'],
    ['9-10', 'Daily majors workflow and limits'],
    ['11', 'Software reproduction'],
    ['12-15', 'Ties, monotonic vs U-shape, practice, sources'],
], [65, 405])
p('Prepared for the folder: 02 - Spearman Rank Correlation. Status in README: not started — no pair results are claimed here.')

page('What does rho_s mean?', '02 / The basic idea')
p('Pearson correlation cares about straight-line distance. Spearman first replaces each value with its <b>rank</b> (1 = smallest, n = largest), then runs Pearson correlation on those ranks.')
h('Sign and size')
table([
    ['Value', 'Plain meaning'],
    ['rho_s near +1', 'Higher rank in X tends to go with higher rank in Y (monotonic up).'],
    ['rho_s near 0', 'No consistent rank order link.'],
    ['rho_s near -1', 'Higher rank in X tends to go with lower rank in Y (monotonic down).'],
], [90, 380])
h('Is this number a percent?')
table([
    ['Common mistake', 'Correct reading'],
    ['"rho_s = 0.80 means 80% of days moved together"', 'No. It is a rank-order score from -1 to +1, not a day count or win rate.'],
    ['"0.80 means an 80% return link"', 'No. Returns and rho_s live on different scales.'],
], [200, 270])
p('Spearman is <b>not</b> "percent of days". It summarizes how often larger X ranks pair with larger Y ranks across all pairs in the sample.')

page('FX percent math (majors)', '03 / Returns before correlation')
p('For daily major FX work you usually correlate <b>returns</b>, not raw price levels. Use the same return definition on both legs of a pair.')
f('Simple return at t = P_t / P_{t-1} - 1\nPercent return = 100 * simple return\nLog return = ln(P_t / P_{t-1})')
p('Example: price moves 1.1000 to 1.1110. Ratio = 1.01, so simple return = 0.010000 = 1.0000%. Log return = ln(1.01) ≈ 0.009950, about 0.9950% when shown as a percent.')
h('Quote direction and missing data')
p('Reversing the quote (EURUSD vs USDEUR) flips the sign of log returns exactly. Simple returns do not flip by a simple minus sign. Keep both series in the same direction.')
p('A missing quote is not zero. Drop that day or impute with a documented rule — do not silently fill with 0. Four close prices on consecutive days give three returns.')

page('Which series this method uses', '04 / Data choice')
p('In this repo’s FX workflow, Spearman is applied to <b>matched daily returns</b> on two symbols (same calendar dates after alignment), the same pairing idea as Pearson method 01.')
h('Typical choice')
p('Use <b>daily log returns of close</b> unless your research note says otherwise. Rank those return values within the sample window you fix before you look. Spearman on ranks is less driven by one huge crash day than Pearson on raw returns, but huge days still change who is "largest".')
h('One row = one day')
p('Row i must be the same trading day for X and Y. Do not sort X and Y separately. Count only complete pairs.')

page('Research notes (section 02)', '05 / Where the method comes from')
p('Section 02 in forex-formulas-explained.pdf defines Spearman rank correlation as Pearson correlation applied to ranks: rho_s = Corr(rank(x), rank(y)).')
h('Plain-language citation')
p('Modern software follows the standard rank-correlation definition documented for <b>scipy.stats.spearmanr</b> in the SciPy library. That routine ranks both inputs (with average ranks for ties) and returns rho_s plus optional p-values under stated assumptions.')
p('Spearman (1904) introduced rank correlation for monotonic relationships. For FX monitoring, the practical point is: Spearman rewards consistent ordering, not linear fit.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['x_i, y_i', 'Raw values on day i (often a return).'],
    ['rank(x_i)', 'Position of x_i in the sorted list (ties averaged).'],
    ['n', 'Number of complete pairs.'],
    ['rho_s', 'Spearman rank correlation in the sample.'],
    ['Corr(.,.)', 'Pearson correlation on the two lists given.'],
], [120, 350])
p('After ranking, the rank lists behave like any other numbers for the Pearson formula.')

page('The formula, piece by piece', '07 / Main equation')
f('rho_s = Corr( rank(x), rank(y) )')
h('Step 1 — rank each list')
p('Sort each value to its rank from 1 to n. If two values tie, assign the average of the ranks they would have occupied.')
h('Step 2 — Pearson on ranks')
p('Compute deviations from the mean rank, multiply, sum, and scale exactly as Pearson r. The result is rho_s.')
p('Ties matter: average ranks slightly shrink extreme rho_s values compared with breaking ties at random.')

page('Hand calculation (teaching data)', '08 / Worked example')
p('Use the teaching vectors from section 02 of the formula PDF:')
table([['i', 'x', 'y', 'rank(x)', 'rank(y)'], [1, -2, -1, 1, 1], [2, 0, 1, 2, 2], [3, 3, 9, 3, 3]], [40, 70, 70, 90, 90])
f('rank(x) = [1, 2, 3]\nrank(y) = [1, 2, 3]\nPearson on ranks = +1.0000\nrho_s = +1')
p('X is not proportional to Y in raw units (-2 vs 9), but both lists increase step by step, so every pair is concordant in rank. Spearman sees a perfect monotonic match.')

page('Ties and shapes Spearman misses', '09 / Extra behaviour')
h('Average ranks for ties')
p('If x = [1, 1, 3], ranks are [1.5, 1.5, 3]. SciPy and this guide use that rule so results match standard software.')
h('Monotonic yes, U-shape no')
p('If Y rises then falls while X only moves up, rank order can break and rho_s drops. A symmetric U in Y with monotone X can yield rho_s near 0 even when Y is predictable — same lesson as Pearson on a curve.')
p('Spearman does not prove causation, lead-lag, or stability out of sample.')

page('Daily majors: how to use it', '10 / Practical workflow')
h('1. Fix the window and pairs first')
p('Choose dates, both symbols, return type, and timezone rules before viewing rho_s. Write the question: "Over these matched D1 log returns, is the rank link positive or negative?"')
h('2. Align and clean')
p('Inner-join on date, drop incomplete rows, log how many days were lost. Check for stale quotes and splits.')
h('3. Compare with Pearson')
p('If Pearson and Spearman disagree a lot, outliers or non-linearity may be present — inspect plots. This folder has no frozen experiment yet; treat any future pair table as separate from this teaching PDF.')

page('Limits — what Spearman cannot tell you', '11 / Honest boundaries')
p('rho_s is not a hedge ratio, not a forecast, and not percent of co-movement days. It does not tell which symbol leads. It does not auto-adjust for volatility regimes.')
p('With very small n, rho_s can swing wildly. With huge n, tiny rho_s can look "significant" while economically tiny — always pair with context and plots.')

page('Software check', '12 / Reproduce the teaching example')
f('from scipy.stats import spearmanr\nx = [-2, 0, 3]\ny = [-1, 1, 9]\nrho, pval = spearmanr(x, y)\n# rho = 1.0')
p('Manual check: rank both lists, then use Pearson code (same as method 01 guide). Expected rho_s = +1.0000 for this teaching set.')
p('For FX returns, pass two equal-length arrays of daily log returns after your date merge.')

page('Practice and quick checks', '13 / Try it yourself')
p('<b>Q:</b> x = [10, 20, 30], y = [100, 200, 300]. What is rho_s? <b>A:</b> +1 (strict rank match).')
p('<b>Q:</b> Does rho_s = 0.6 mean 60% of days? <b>A:</b> No.')
p('<b>Q:</b> x = [-2, 0, 3], y = [9, 1, -1]. What happens? <b>A:</b> Ranks reverse; rho_s = -1.')
p('<b>Q:</b> Why rank before correlating? <b>A:</b> So one extreme return day cannot pull the score as hard as in Pearson, while still rewarding steady up-together or down-together ordering.')
p('Before you publish a Spearman table for FX, sanity-check: sorted dates, equal n, documented return type, and at least one scatter or rank plot for suspicious pairs.')

page('Sources', '14 / Research trail')
refs = [
    ('1', 'SciPy documentation: scipy.stats.spearmanr.', 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html', 'Definition, tie handling, and return values.'),
    ('2', 'forex-formulas-explained.pdf — section 02 (this repository).', '../forex-formulas-explained.pdf', 'FX-focused formula sheet for method 02.'),
    ('3', 'Spearman, C. (1904). The proof and measurement of association between two things. American Journal of Psychology, 15(1), 72–101.', 'https://doi.org/10.2307/1412159', 'Historical rank-correlation reference.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))

page('Folder checklist', '15 / Before you run real pairs')
p('Confirm: matched dates, same return type, ranks computed on the same n rows you report, ties handled with average ranks, and rho_s reported with n and date range.')
p('When experiments land under experiments/v001/, copy their numbers into NOTES — not into this teaching PDF.')
p('End of Spearman rank correlation beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 02  |  SPEARMAN RANK CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Spearman Rank Correlation - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert abs(pearson_r(rank_average(TEACH_X), rank_average(TEACH_Y)) - 1.0) < 1e-12
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
