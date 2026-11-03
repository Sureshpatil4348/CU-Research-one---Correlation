from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Robust_Clipped_Correlation_Complete_Simple_Guide.pdf'
EXPECTED_PAGES = 15
CLIP_C = 0.02
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


def clip(v, c):
    return min(c, max(-c, v))


def pearson_r(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    dx = [a - mx for a in x]
    dy = [b - my for b in y]
    top = sum(a * b for a, b in zip(dx, dy))
    bot = sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
    return top / bot


TEACH_X = [0.01, -0.05, 0.003, 0.02]
TEACH_Y = [0.008, -0.04, 0.001, 0.015]
XT = [clip(v, CLIP_C) for v in TEACH_X]
YT = [clip(v, CLIP_C) for v in TEACH_Y]
RHO_CLIP = pearson_r(XT, YT)


page('Robust clipped correlation', 'Method 04 / A complete beginner guide')
p('<b>Question this method answers:</b> How closely do two return series move together if we cap each day\'s return at ±c before correlating — so one crash day cannot dominate?')
p('You still keep raw Pearson r for comparison. Clipping is a sensitivity check, not a replacement for viewing the full data.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Idea, sign, size, percent trap'],
    ['3', 'FX return math (c in decimal units)'],
    ['4', 'Which series clipped correlation uses'],
    ['5', 'Research notes (section 04)'],
    ['6', 'Symbol dictionary'],
    ['7-8', 'Clip formula and hand example'],
    ['9-10', 'Daily majors workflow and limits'],
    ['11', 'Software reproduction'],
    ['12-15', 'Sensitivity, practice, sources'],
], [65, 405])
p('Prepared for: 04 - Robust Clipped Correlation. README status: not started.')

page('What is rho_clip?', '02 / The basic idea')
p('Winsorize (clip) each return to a band, then compute Pearson correlation on the clipped series. Outliers remain in the sample but their <i>magnitude</i> is capped.')
h('Sign and size')
p('rho_clip uses the same -1 to +1 scale as Pearson. Sign still means direction of co-movement among clipped values.')
h('Is this number a percent?')
table([
    ['Mistake', 'Truth'],
    ['"c = 0.02 means clip at 2% returns"', 'Yes in decimal return units: ±0.02 ≈ ±2% simple move size.'],
    ['"rho_clip = 0.5 means half the days"', 'No. It is still a correlation, not a day fraction.'],
], [220, 250])

page('FX percent math (majors)', '03 / Returns and clip units')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('Clip c is applied in the same units as the return series you feed in. If returns are decimals, c=0.02 caps at about ±2%. Example price move 1.1000→1.1110 is +1% — inside the band.')
p('Quote reversal flips log signs. Missing ≠ 0. Four closes → three returns.')

page('Which series this method uses', '04 / Data choice')
p('Use <b>matched daily returns</b> (log or simple — pick one and document it). Clip each leg separately: x_tilde and y_tilde, then correlate.')
p('Always report raw Pearson r on unclipped returns alongside rho_clip so readers see what the cap changed.')
p('If you clip log returns, interpret c on the log scale (not identical to simple-percent caps). Stay consistent across both symbols and across time when comparing experiments.')

page('Research notes (section 04)', '05 / Construction in the repo sheet')
f('x_tilde = min(c, max(-c, x))\ny_tilde = min(c, max(-c, y))\nrho_clip = Corr(x_tilde, y_tilde)')
p('Section 04 in forex-formulas-explained.pdf describes this construction. Pearson on clipped data matches scipy.stats.pearsonr applied to the clipped arrays.')
p('Clipping discards information about crash <i>size</i> — two days both beyond +c look identical. That is intentional for robustness, but it can hide risk.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['x, y', 'Raw daily returns.'],
    ['c', 'Clip bound (positive).'],
    ['x_tilde, y_tilde', 'Clipped returns.'],
    ['rho_clip', 'Pearson r on clipped series.'],
    ['r', 'Raw Pearson on unclipped series.'],
    ['n', 'Count of matched days in the window.'],
    ['cap-hit count', 'Days where |return| > c before clipping — report separately.'],
], [120, 350])
p('Clipping is symmetric: positive and negative tails use the same c. After clipping, means and standard deviations change, so rho_clip can move even when rank order stays similar.')

page('Formula step by step', '07 / Clip then correlate')
f('x_tilde_i = min(c, max(-c, x_i))\ny_tilde_i = min(c, max(-c, y_i))\nrho_clip = Pearson(x_tilde, y_tilde)')
p('Clipping is applied row-wise before any mean or sum. Constants (all values inside the band) make correlation undefined — same rule as Pearson.')
p('The min/max form never drops rows: a -5% day stays in the sample as -c. That differs from deleting outliers, which would change n.')
p('Compute raw r on the same rows for fair comparison; do not clip one leg only unless that asymmetry is part of the research design.')

page('Hand example (teaching)', '08 / c = 0.02')
p('Small made-up decimal returns:')
table([
    ['Day', 'x', 'x_tilde', 'y', 'y_tilde'],
    [1, 0.010, 0.010, 0.008, 0.008],
    [2, -0.050, -0.020, -0.040, -0.020],
    [3, 0.003, 0.003, 0.001, 0.001],
    [4, 0.020, 0.020, 0.015, 0.015],
], [45, 70, 80, 70, 80])
f(f'rho_clip (computed) ≈ {RHO_CLIP:.4f}\n(raw x had a -5% day clipped to -2%)')
p('The crash day still counts, but its push on r is limited. Compare to raw r on x, y to quantify sensitivity.')

page('Daily majors workflow', '09 / How to use it')
h('1. Choose c from economic sense')
p('Try c = 0.02 (±2%) as a starting sensitivity line for daily majors, then sweep c = 0.01 and 0.03 in experiments.')
h('2. Pair with raw Pearson')
p('If raw r is high but rho_clip collapses, outliers or crisis days may be driving the story.')
h('3. Document both')
p('Future experiments under experiments/v001/ should store r, rho_clip, c, and n in NOTES.')

page('Limits', '10 / What clipping cannot tell you')
p('rho_clip is not a VaR model, not a hedge ratio, and not proof of stability. It hides tail sizes — two different crises can look the same after clipping.')
p('Choosing c after seeing results can overfit. Fix c before looking at pair outcomes when possible.')
p('If almost every day hits the cap, rho_clip reflects mainly sign agreement inside a flat band — read cap-hit counts before interpreting the score.')

page('Software check', '11 / Reproduce teaching arrays')
f('c = 0.02\nx = [0.01, -0.05, 0.003, 0.02]\ny = [0.008, -0.04, 0.001, 0.015]\nx_t = [min(c, max(-c, v)) for v in x]\ny_t = [min(c, max(-c, v)) for v in y]\nfrom scipy.stats import pearsonr\npearsonr(x_t, y_t)')
p(f'Built-in assert target rho_clip = {RHO_CLIP:.6f} for the teaching table.')

page('Sensitivity mindset', '12 / Why keep raw r')
p('Report: date range, n, raw r, rho_clip at stated c, and how many days hit the cap on each leg. Days hitting the cap are flags for manual review.')
p('Run a small grid (c = 0.01, 0.02, 0.03) in experiments to see whether conclusions are stable. If rho_clip jumps when c moves slightly, the pair may be outlier-driven.')
p('Document the grid in NOTES rather than cherry-picking the c that makes a pair look best.')

page('Practice', '13 / Quick checks')
p('<b>Q:</b> x = 0.10 with c = 0.02 — x_tilde? <b>A:</b> 0.02.')
p('<b>Q:</b> Does clipping add data? <b>A:</b> No, it transforms existing rows.')
p('<b>Q:</b> x = -0.03 with c = 0.02 — x_tilde? <b>A:</b> -0.02.')
p('<b>Q:</b> If raw r = 0.9 and rho_clip = 0.4, what might that mean? <b>A:</b> A few extreme days may be driving raw Pearson — inspect cap hits.')
p('Always clip both legs with the same c unless you document an asymmetric design.')

page('Sources', '14 / Research trail')
p('Links checked when this guide was built. Bracket numbers point to the references below. Teaching examples and cap-hit logic in this PDF are original walkthrough material for method 04.')
refs = [
    ('1', 'SciPy documentation: scipy.stats.pearsonr.', 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html', 'Used on clipped arrays for rho_clip.'),
    ('2', 'forex-formulas-explained.pdf — section 04 (this repository).', '../forex-formulas-explained.pdf', 'Clipped correlation construction.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Reading tip: confirm c in decimal return units, then reproduce rho_clip on the teaching table before running full major-pair panels.')

page('Folder checklist', '15 / Before experiments')
p('Freeze c, return type, and cap-hit counts. Keep raw and clipped correlations in the same table.')
p('When experiments/v001/ lands, mirror method 01 pair lists so clipped and raw columns line up row-for-row on date.')
p('Rebuild this PDF after formula edits: python build_guide.py from this folder.')
p('End of robust clipped correlation beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 04  |  ROBUST CLIPPED CORRELATION')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Robust Clipped Correlation - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert XT == [0.01, -0.02, 0.003, 0.02]
assert abs(RHO_CLIP - pearson_r(XT, YT)) < 1e-12
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
