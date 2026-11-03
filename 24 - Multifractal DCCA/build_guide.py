from pathlib import Path
from math import sqrt, log
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Multifractal_DCCA_Complete_Simple_Guide.pdf'
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


def mf_term(c, q):
    return (1 if c >= 0 else -1) * abs(c) ** (q / 2)


def g_q(values, q):
    return sum(mf_term(c, q) for c in values) / len(values)


CROSS_V = [0.0002, 0.0003, 0.0001]
FX_X = [0.0010, 0.0020, 0.0015]
FX_Y = [0.0011, 0.0019, 0.0014]
Q2 = 2.0
G_XY_2 = g_q(CROSS_V, Q2)
G_XX_2 = g_q(FX_X, Q2)
G_YY_2 = g_q(FX_Y, Q2)
RHO_Q2 = G_XY_2 / sqrt(G_XX_2 * G_YY_2)
FX_SIMPLE = 1.1110 / 1.1000 - 1
FX_LOG = log(1.1110 / 1.1000)


page('Multifractal DCCA', 'Method 24 / A complete beginner guide')
p('<b>How does cross-correlation of detrended FX profiles change when you weight large fluctuations more?</b> Multifractal detrended cross-correlation analysis (MF-DCCA) extends DCCA (folder 23) with an order parameter q.')
p('This guide uses <b>positive q only</b>. At q = 2 you recover ordinary DCCA scaling behaviour. Teaching numbers only; experiments in this folder have not started.')
h('Read it in three parts')
p('<b>First:</b> Idea, percent returns, and profiles. <b>Next:</b> Kwapień et al. (2015) context and the G and rho_q formulas. <b>Last:</b> A hand check, limits, and software notes.')
table([['Pages', 'What you will learn'], ['2', 'Idea; is rho_q a percent?'], ['3', 'FX percent on 1.1000 to 1.1110'], ['4', 'Profiles, scales s, and segments v'], ['5', 'Research: Kwapień, Oświęcimka, Drożdż 2015'], ['6-9', 'Symbols, MF-DCCA formulas, hand calc'], ['10-11', 'Positive q, q = 2 link to DCCA'], ['12-14', 'Limits, checks, and sources']], [65, 405])
p('Prepared for the folder: 24 - Multifractal DCCA<br/>3 November 2026')

page('What does MF-DCCA do?', '02 / The basic idea')
p('Start from two cumulative return profiles (integrated series). Cut them into windows of length s, remove a local trend in each window, and form a cross-fluctuation measure in segment v at scale s.')
h('The score rho_q(s)')
f('G_xy(q,s) = mean_v[ sign(c_v) * |c_v|^(q/2) ]\nG_xx(q,s) and G_yy(q,s) use the same rule on each leg\n\nrho_q(s) = G_xy(q,s) / sqrt( G_xx(q,s) * G_yy(q,s) )')
p('Here c_v is the detrended cross-covariance fluctuation in segment v (notation varies in papers; see source [1]). rho_q is on roughly [-1, +1] after scaling, like a correlation. It is <b>not</b> a price percent.')
h('Is rho_q a percent?')
p('<b>No.</b> Returns may be labelled 1.00%. rho_q describes weighted co-movement of detrended fluctuations at scale s. q is a dimensionless order, not a percent.')

page('FX percent math on one move', '03 / Returns in plain numbers')
p('Take a quote move from <b>1.1000 to 1.1110</b> in one bar (same units).')
f('Simple return = 1.1110 / 1.1000 - 1 = 0.01  (1.00% label)\nLog return = ln(1.1110 / 1.1000) = about 0.009950')
p('MF-DCCA is built on return series (often log returns), then cumulative profiles. Use one return definition for both legs. Document quote direction and bar time before you integrate.')
p('Integrating returns builds the profile; MF-DCCA then studies how cross-fluctuations scale with window length s. A 1% daily move is input data, not the output rho_q.')

page('Profiles, scales, and segments', '04 / Data rules')
h('Same length, aligned time')
p('Both profiles must share the same index after integration. Missing bars break segment counts; record your gap rule in experiment notes when v001 exists.')
h('Scale s')
p('s is the window length in points (bars). You compute rho_q(s) for several s values and study scaling. This guide shows one scale with three teaching segments v = 1, 2, 3.')
h('Relation to folder 23')
p('Standard DCCA is the q = 2 case of the same G construction. Multifractal analysis asks whether rho_q(s) changes with q, which signals heterogeneous fluctuation sizes across segments.')
p('We do not invent EURUSD scaling exponents here. When experiments start, tie every plot to a snapshot id and fixed (q, s) grid.')

page('Where did MF-DCCA come from?', '05 / Research notes')
h('Kwapień, Oświęcimka, Drożdż (2015) [1]')
p('<i>Physica A</i>, 436, 122-132. The paper develops MF-DCCA for multifractal cross-correlations between two time series, extending the DCCA family with the order q generalisation used in this guide.')
p('Earlier DCCA work (folder 23) removed local trends before measuring cross-correlations at long horizons. MF-DCCA adds the q-weighted average so large and small fluctuations can contribute differently.')
h('What this guide claims')
p('We teach the rho_q scaling definition and the q = 2 link to DCCA. Full scaling regressions, spectrum estimation, and bootstrap inference belong in the paper and in your analysis code.')
p('Check DOI 10.1016/j.physa.2015.05.028 when you need exact algorithm steps and figure notation.')

page('Meet the symbols', '06 / Dictionary')
table([['Symbol', 'Meaning'], ['q', 'Order parameter; q &gt; 0 in this guide; q = 2 is DCCA.'], ['s', 'Segment (window) length in points.'], ['v', 'Segment index after tiling the profile.'], ['c_v', 'Detrended cross-fluctuation in segment v at scale s.'], ['G_xy(q,s)', 'q-weighted mean of signed power terms across v.'], ['rho_q(s)', 'Normalised cross measure at order q and scale s.']], [125, 345])
p('G_xx and G_yy apply the same mean_v[ sign(c)|c|^(q/2) ] pattern to each single-series fluctuation series inside segment v.')
p('Software packages may name c_v differently; map their output to G_xy before you compare to rho_q here.')

page('The main formulas', '07 / What each part does')
f('Term_v(q) = sign(c_v) * |c_v|^(q/2)\n\nG_xy(q,s) = (1/V) * SUM_v Term_v(q)   on cross c_v\n\nrho_q(s) = G_xy / sqrt(G_xx * G_yy)')
h('When q = 2')
p('Then |c_v|^(q/2) = |c_v| and sign(c_v)*|c_v| = c_v. The cross term becomes an ordinary average of c_v across segments, matching the DCCA-type q = 2 case described in [1].')
h('Positive q only here')
p('Negative q emphasises small fluctuations and needs extra care with zeros and estimation noise. This beginner guide stays with q &gt; 0 so terms stay real for nonzero c_v.')
p('rho_q is not a return forecast. It summarises how detrended cross-fluctuations co-scale at s for the chosen q.')

page('Calculate by hand: q = 2', '08 / Worked example')
p('Three teaching segments at one scale s. Cross-fluctuations c_v (decimals) and single-leg fluctuation magnitudes for G_xx and G_yy:')
table([['v', 'c_v (cross)', 'f_x,v', 'f_y,v'], ['1', '0.0002', '0.0010', '0.0011'], ['2', '0.0003', '0.0020', '0.0019'], ['3', '0.0001', '0.0015', '0.0014']], [45, 120, 120, 120])
p('For q = 2, each G is the plain mean of the column (because sign(c)*|c| = c for cross, and f columns are positive teaching magnitudes).')
f('G_xy(2,s) = (0.0002 + 0.0003 + 0.0001) / 3 = 0.0002\nG_xx(2,s) = 0.0015\nG_yy(2,s) = (0.0011 + 0.0019 + 0.0014) / 3 = about 0.001467\n\nrho_2(s) = 0.0002 / sqrt(0.0015 * 0.001467)\n         = about 0.1348')
p('This tiny table only checks algebra. Real MF-DCCA also loops over many s and may estimate multifractal spectra from how G behaves with s.')

page('Changing q changes emphasis', '09 / Reading q')
h('Larger q')
p('Larger q puts more weight on segments where |c_v| is big. rho_q(s) can differ from rho_2(s) when large and small co-fluctuations disagree.')
h('Do not mix with Pearson on returns')
p('Same-bar Pearson (folder 01) does not detrend local segments or scan scales. MF-DCCA answers a long-memory / scaling question, not a one-bar linear tilt.')
p('When you report rho_q, always give q, s, return type, and segment construction. A single number without scale context is easy to misread.')

page('Using MF-DCCA on FX', '10 / Practice habits')
h('Long samples')
p('You need enough points to tile multiple windows at each s. Very short histories make rho_q(s) unstable.')
h('Sessions and microstructure')
p('Changing bar size changes s in physical time. A 5-minute segment is not the same object as a daily segment.')
h('No invented pair results')
p('Experiments are not started. Do not cite made-up EURUSD multifractal spectra in reports. Future work uses frozen snapshots per docs/VERSIONING.md.')

page('Limits and common errors', '11 / What MF-DCCA cannot tell you')
h('Not a trading signal')
p('Scaling similarity does not, by itself, imply profitable hedges or lead-lag rules.')
h('Trend removal choice')
p('Polynomial detrending degree and overlapping vs non-overlapping windows change c_v. Match your software to the paper you cite.')
h('Versus DCCA (folder 23)')
p('Folder 23 is the q = 2 detrended cross-correlation path. Folder 24 adds the q spectrum for heterogeneous fluctuation sizes.')
h('Versus Pearson rolling (folder 05)')
p('Rolling Pearson tracks local linear correlation. MF-DCCA studies detrended fluctuation scaling across window lengths.')

page('Check your understanding', '12 / Quick questions')
h('A. Is rho_q a percent?')
p('<b>No.</b> Returns can be percent-labelled; rho_q is a scaled cross-fluctuation score.')
h('B. What does q = 2 mean?')
p('You recover the DCCA-type averaging of c_v in the G_xy construction used here.')
h('C. Can I use negative q in this guide?')
p('Not in this beginner path; positive q only. See [1] for the full multifractal treatment.')
h('D. One scale, three segments')
p('The hand example checks rho_2(s) algebra. Full studies loop s and q and assess uncertainty.')
p('Save segment c_v lists from code and reproduce G_xy and rho_q in a spreadsheet when experiments begin.')

page('Calculate with software', '13 / Reproduce the teaching row')
f('from math import sqrt\n\ndef g_q(vals, q):\n    return sum((1 if c>=0 else -1)*abs(c)**(q/2) for c in vals)/len(vals)\n\ncross = [2e-4, 3e-4, 1e-4]\nfx = [1e-3, 2e-3, 1.5e-3]\nfy = [1.1e-3, 1.9e-3, 1.4e-3]\nrho2 = g_q(cross,2)/sqrt(g_q(fx,2)*g_q(fy,2))\nprint(rho2)  # about 0.1348')
p('Implement full profile integration, tiling, and detrending before you apply this to snapshot data. Compare one (q,s) row to hand arithmetic first.')

page('Sources and further reading', '14 / Research trail')
p('Links checked on 3 November 2026. Hand arithmetic is original teaching material. Bracket numbers point to primary references.')
refs = [
    ('1', 'Kwapień, J., Oświęcimka, P., & Drożdż, S. (2015). Multifractal cross-correlations between the world oil and precious metal markets. Physica A, 436, 122-132.', 'https://doi.org/10.1016/j.physa.2015.05.028', 'MF-DCCA definition and q order; context for G and rho_q.'),
    ('2', 'Folder 23 DCCA detrended cross-correlation README.', '../23%20-%20DCCA%20Detrended%20Cross-Correlation/README.md', 'q = 2 baseline method in this project tree.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/>'
        f'<link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Next step: experiments/v001 with logged (q, s) grids and detrending settings copied from your chosen library.')

page('Workflow before experiments', '15 / Your working method')
h('1. Write the question first')
p('Example: At daily scale, do EURUSD and USDJPY detrended cross-fluctuations show q-dependent rho_q(s) over s = 32..256? Name returns, snapshot id, and segment rule.')
h('2. Build profiles once')
p('Integrate log returns from the same aligned calendar. Save the integrated series and the return type in experiment notes.')
h('3. Fix q and s grids before you look')
p('Pre-specify positive q values and window lengths s. Scanning many pairs without correction inflates false findings.')
h('4. Report rho_q with context')
p('Give q, s, sample length, detrending degree, and segment count V. State that rho_q is not a price percent and not a causal forecast.')
p('When v001 exists, attach one CSV of c_v values and a screenshot of rho_q(s) versus s for a single q to show reproducibility.')

def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 24  |  MULTIFRACTAL DCCA')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Multifractal DCCA - Complete Simple Guide',
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
assert abs(G_XY_2 - 0.0002) < 1e-15
assert abs(RHO_Q2 - 0.1348399724926484) < 1e-9
print(f'Created and checked {page_count} pages: {OUT}')
