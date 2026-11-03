from pathlib import Path
from math import isclose
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Tail_Dependence_Complete_Simple_Guide.pdf'
EXPECTED_PAGES = 15
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyEasy', fontName='Helvetica', fontSize=11, leading=16, spaceAfter=10))
styles.add(ParagraphStyle(name='HeadEasy', fontName='Helvetica-Bold', fontSize=23, leading=28, textColor=colors.HexColor('#15364A'), spaceAfter=18))
styles.add(ParagraphStyle(name='SubEasy', fontName='Helvetica-Bold', fontSize=13, leading=18, textColor=colors.HexColor('#087F8C'), spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name='FormulaEasy', fontName='Courier', fontSize=10, leading=15, backColor=colors.HexColor('#EDF5F7'), borderPadding=10, spaceBefore=8, spaceAfter=17))
styles.add(ParagraphStyle(name='SmallEasy', fontName='Helvetica', fontSize=9, leading=13, spaceAfter=8))
story = []

JOINT_TAIL = 12
COND_TAIL = 20
L_HAT = JOINT_TAIL / COND_TAIL
ALPHA_TEACH = 0.05


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


page('Tail dependence', 'Method 19 / A complete beginner guide')
p('<b>Question this method answers:</b> When one FX return is in an extreme tail, how often is the other in its tail too?')
p('Tail dependence is not one Pearson r. It is a conditional frequency in the joint tails of uniform transforms u and v built from returns.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Lower-tail idea and conditioning'],
    ['3', 'FX percent math (majors)'],
    ['4', 'From returns to u and v'],
    ['5', 'Research notes (Patton 2006)'],
    ['6', 'Symbol dictionary'],
    ['7-8', 'L̂(α) and λL definitions'],
    ['9', 'Teaching counts 12/20 = 0.60'],
    ['10-11', 'Reporting and workflow'],
    ['12', 'Software outline'],
    ['13-15', 'Limits, practice, sources'],
], [65, 405])
p('Made-up event counts only — no live pair tail estimates from snapshots.')
p('Prepared for: 19 - Tail Dependence. README status: not started.')

page('Extreme days together', '02 / The basic idea')
p('Pearson r averages co-movement across all days. Tail dependence asks about <i>worst</i> days: if GBP/USD has a very low return, is EUR/USD also very low that day or soon after?')
h('Condition on one tail')
table([
    ['L̂(α)', 'Share of conditioning-tail dates where both legs are in the chosen tail.'],
    ['λL', 'Theoretical limit as α → 0 for lower-tail co-crash probability.'],
    ['Not the same', 'A 5% cutoff estimate is finite-sample; it is not automatically λL.'],
], [120, 350])

page('FX percent math (majors)', '03 / Returns before tails')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('1.1000 → 1.1110 is about +1% simple return. Tail events are defined on return distributions — usually after converting each leg to ranks or fitted CDF values u and v in (0,1).')
p('A −1% day is not automatically “in the 5% tail” unless your rank or model says so. Keep the return type and window fixed.')

page('Uniforms u and v', '04 / Where α lives')
f('u_i = F_hat_X(x_i)\nv_i = F_hat_Y(y_i)')
p('F_hat can be empirical ranks, a GARCH-filtered residual CDF, or another margin model. The tail cutoff α (such as 0.05) applies to these uniforms, not to raw percent returns.')
p('Section 19 in forex-formulas-explained.pdf matches this repo placement. Method 18 (copulas) uses the same u,v building blocks with a different summary object.')

page('Research notes', '05 / Patton (2006)')
p('<b>Modelling asymmetric exchange rate dependence.</b> International Economic Review, 47(2), 527–556. DOI: 10.1111/j.1468-2354.2006.00387.x.')
p('Shows FX dependence is often asymmetric across tails — joint crashes can differ from joint rallies. Copula tail parameters and empirical tail frequencies both target that asymmetry; this method focuses on countable tail events.')
p('Future experiment outputs should cite the same margin pipeline used to build u and v.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['u, v', 'Uniform transforms of X and Y returns on each date.'],
    ['α (alpha)', 'Small tail threshold on [0,1], e.g. 0.05.'],
    ['L̂(α)', 'Empirical conditional tail frequency (see formula page).'],
    ['λL', 'Lower-tail dependence coefficient; limit as α → 0.'],
    ['λU', 'Upper-tail analogue using u ≥ 1−α, v ≥ 1−α.'],
    ['Event counts', 'Numerator and denominator counts — always report them.'],
], [120, 350])

page('Finite-sample estimator L̂', '07 / Counting rule')
f('L̂(α) = (# dates with u ≤ α AND v ≤ α)\n         / (# dates with v ≤ α)')
p('The conditioning series here is v (formula sheet convention). Swapping roles changes the ratio unless dependence is symmetric.')
p('Each counted date is one row in your aligned return panel. Missing quotes drop that row before ranks are formed.')
h('This frequency is a percent')
p(f'When the denominator is {COND_TAIL} dates, the numerator {JOINT_TAIL} means {100*L_HAT:.0f}% of those conditioning-tail dates also had u in the lower tail at the chosen α. That percentage applies to the tail subset — not to all calendar days.')

page('Asymptotic λL', '08 / Limit versus cutoff')
f('λL = lim α→0 P(u ≤ α | v ≤ α)')
p('λL describes the extreme lower tail under a copula or probability model. With finite data, α = 0.05 gives a stable teaching cutoff but estimates a thicker tail region than the limit.')
p('Do not report L̂(0.05) = 0.60 as if it were λL without explanation. Show α, counts, and the margin method used for u and v.')

page('Teaching example', '09 / 12 of 20 joint lower-tail days')
table([
    ['Quantity', 'Value', 'Plain reading'],
    ['α cutoff', '0.05 (illustrative)', 'Lower-tail threshold on uniforms'],
    ['Dates with v ≤ α', str(COND_TAIL), 'Conditioning-tail event count (denominator)'],
    ['Also u ≤ α', str(JOINT_TAIL), 'Joint lower-tail event count (numerator)'],
    ['L̂(α)', f'{JOINT_TAIL}/{COND_TAIL} = {L_HAT:.2f}', 'Conditional frequency among v-tail dates'],
], [130, 100, 240])
p('If 12 of 20 GBP/USD lower-tail dates also have EUR/USD in its lower tail, the illustrative conditional frequency is 0.60. That is 60% of the conditioning-tail dates — not 60% of all trading days in the window.')
p('Repeat the count table for upper tails or opposite tails when your FX question needs them.')

page('Report like a lab note', '10 / Event counts first')
h('Minimum reporting block')
p('1. Sample dates and pair names. 2. Return type (simple/log). 3. How u and v were built. 4. α and which leg conditions. 5. Numerator, denominator, and L̂. 6. Whether the number is a teaching cutoff or an extrapolated λ estimate.')
p('A table beats a lone decimal: readers can see whether the denominator is large enough.')
h('Versus Pearson and copulas')
p('Pearson r can be high while tail co-crash frequency is low (Gaussian-like margins). Copula θ may encode tail shape but still needs margins. L̂ is a direct frequency readers can audit by hand on small samples.')

page('Daily majors workflow', '11 / Repo usage')
h('1. Freeze margins before tail counts')
p('Use one ranked or filtered pipeline per experiment version in experiments/v001/ when built.')
h('2. Pre-specify α and tail direction')
p('Lower, upper, or pairwise opposite tails — document before scanning pairs.')
h('3. Store counts, not only ratios')
p('Export numerator and denominator CSV columns alongside L̂ so reruns are comparable.')
p('Load snapshots from data/snapshots/; do not open MT5 from this folder.')

page('Software outline', '12 / Reproduce the ratio')
f(f'joint = {JOINT_TAIL}\ncond = {COND_TAIL}\nL_hat = joint / cond  # {L_HAT:.2f}')
p('In Python, build u,v arrays, then boolean masks (u <= alpha) & (v <= alpha) for the numerator and (v <= alpha) for the denominator. Copula packages estimate parametric λ; this guide emphasizes transparent counting first.')
p('Align dates across majors; a tail in one pair on a holiday mismatch breaks pairs silently if you merge carelessly.')

page('Limits', '13 / What tail counts cannot tell you')
p('Small denominators make L̂ unstable. Changing α or margin models changes counts. Regime shifts mix crises with calm periods unless you slice time.')
p('Tail dependence is not Granger causality and not a hedge ratio. Joint tail days may share a common shock (USD factor) rather than one pair “causing” the other.')
p('L̂ at α = 0.05 is a practical FX research cutoff; it is not the same object as an extrapolated λL unless you model the limit explicitly.')

page('Practice', '14 / Quick checks')
p('<b>Q:</b> Is L̂ = 0.60 the same as “60% of all days”? <b>A:</b> No — it is 60% of conditioning-tail dates (here 12/20).')
p('<b>Q:</b> Can u,v come from price levels? <b>A:</b> Use return margins, not trending prices.')
p(f'<b>Check:</b> {JOINT_TAIL}/{COND_TAIL} = {L_HAT:.2f} at α = {ALPHA_TEACH} in the teaching table.')
p('<b>Q:</b> Does a high Pearson r prove high L̂? <b>A:</b> No — tails can differ from the center of the distribution.')

page('Sources', '15 / Research trail')
refs = [
    ('1', 'Patton, A. J. (2006). Modelling asymmetric exchange rate dependence. International Economic Review, 47(2), 527–556.', 'https://doi.org/10.1111/j.1468-2354.2006.00387.x', 'FX asymmetric tail motivation.'),
    ('2', 'forex-formulas-explained.pdf — section 19 (this repository).', '../forex-formulas-explained.pdf', 'Project L̂ and λL definitions.'),
    ('3', '18 - Copulas — related u,v margin workflow.', '../18%20-%20Copulas/README.md', 'Copula tail parameter context.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Rebuild: python build_guide.py. End of tail dependence beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 19  |  TAIL DEPENDENCE')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Tail Dependence - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert isclose(L_HAT, JOINT_TAIL / COND_TAIL)
assert isclose(L_HAT, 0.60)
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
