from pathlib import Path
from math import sqrt
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader
import numpy as np
import pywt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Wavelet_Correlation_and_Coherence_Complete_Simple_Guide.pdf'
EXPECTED_PAGES = 15
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyEasy', fontName='Helvetica', fontSize=11, leading=16, spaceAfter=10))
styles.add(ParagraphStyle(name='HeadEasy', fontName='Helvetica-Bold', fontSize=23, leading=28, textColor=colors.HexColor('#15364A'), spaceAfter=18))
styles.add(ParagraphStyle(name='SubEasy', fontName='Helvetica-Bold', fontSize=13, leading=18, textColor=colors.HexColor('#087F8C'), spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name='FormulaEasy', fontName='Courier', fontSize=10, leading=15, backColor=colors.HexColor('#EDF5F7'), borderPadding=10, spaceBefore=8, spaceAfter=17))
styles.add(ParagraphStyle(name='SmallEasy', fontName='Helvetica', fontSize=9, leading=13, spaceAfter=8))
story = []

TEACH_X = np.array([0.01, -0.005, 0.002, -0.008, 0.003, 0.004, -0.002, 0.001, -0.006, 0.002,
                    0.005, -0.003, 0.001, 0.002, -0.004, 0.003, -0.001, 0.004, -0.002, 0.001])
TEACH_Y = TEACH_X * 0.75 + np.array([0.001, -0.001, 0.0005, -0.0005, 0.0002, 0.0003, -0.0001, 0.0001,
                                     -0.0004, 0.0002, 0.0003, -0.0002, 0.0001, 0.0001, -0.0003, 0.0002,
                                     -0.0001, 0.0003, -0.0001, 0.0001])
SCALE = 2.0
WAV = 'morl'


def wavelet_corr_at_scale(x, y, scale, wavelet=WAV):
    wx, _ = pywt.cwt(x, np.array([scale]), wavelet)
    wy, _ = pywt.cwt(y, np.array([scale]), wavelet)
    a = wx[0].real
    b = wy[0].real
    a = a - a.mean()
    b = b - b.mean()
    num = np.sum(a * b)
    den = sqrt(np.sum(a ** 2) * np.sum(b ** 2))
    if den == 0:
        return 0.0
    return float(num / den)


RHO_W = wavelet_corr_at_scale(TEACH_X, TEACH_Y, SCALE)


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


page('Wavelet correlation and coherence', 'Method 22 / A complete beginner guide')
p('<b>Question this method answers:</b> At which time–scale (horizon) are two FX return series linked, and when during the sample does that linkage appear?')
p('Wavelets localize fluctuations in both time t and scale s. Correlation compares coefficients at a scale; coherence adds a smoothed strength R²(s,t) with separate phase.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Time-scale view versus global r'],
    ['3', 'FX percent math (majors)'],
    ['4', 'Coefficients W_x(s,t)'],
    ['5', 'Research notes (Grinsted et al. 2004)'],
    ['6', 'Symbol dictionary'],
    ['7-9', 'ρ_wavelet and R² formulas'],
    ['10-11', 'Edge leakage and workflow'],
    ['12', 'Software (PyWavelets)'],
    ['13-15', 'Limits, practice, sources'],
], [65, 405])
p('Teaching returns only — no published wavelet coherence maps from snapshots.')
p('Prepared for: 22 - Wavelet Correlation and Coherence. README status: not started.')

page('See both time and horizon', '02 / The basic idea')
p('Rolling Pearson r slides one time window. Wavelets use many scales s at once: short scales react to fast wiggles; long scales react to slow drifts. You can compare EUR/USD and GBP/USD at multi-week horizons while still seeing when linkage fades.')
h('Two related objects')
table([
    ['ρ_wavelet(s)', 'Correlation of wavelet coefficients at scale s across time.'],
    ['R²(s,t)', 'Local coherence strength after smoothing cross and auto spectra.'],
    ['Phase', 'Timing offset — separate from R² magnitude.'],
], [150, 320])

page('FX percent math (majors)', '03 / Returns on each day')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('1.1000 → 1.1110 is about +1% simple return. Feed return series into the transform — not raw price levels — unless you have a documented reason.')
p('Example from the formula sheet: two majors may correlate on multi-week scales while short horizons look weak during the same calendar span.')

page('Wavelet coefficients', '04 / W(s,t)')
p('Continuous wavelet transform (CWT) produces complex coefficients W_x(s,t) for each scale s and time index t. Real-part correlation is a teaching simplification; full coherence uses complex conjugates in the cross term.')
p('Mother wavelet choice (Morlet, Paul, etc.) changes scale meaning — freeze the wavelet name in experiment NOTES.')

page('Research notes', '05 / Grinsted, Moore and Jevrejeva (2004)')
p('<b>Application of the cross wavelet transform and wavelet coherence to geophysical time series.</b> Nonlinear Processes in Geophysics, 11, 561–566.')
p('Popular reference for wavelet coherence diagrams: arrows for phase, contour lines for significant regions. FX researchers reuse the workflow with return series instead of climate variables.')
p('Significance testing needs careful handling of autocorrelation — do not copy climate defaults blindly to FX.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['W_x(s,t)', 'Wavelet coefficient of series x at scale s, time t.'],
    ['s', 'Scale / effective horizon (depends on wavelet and sampling).'],
    ['ρ_wavelet(s)', 'Corr(W_x(s,·), W_y(s,·)) on real parts or as defined.'],
    ['R²(s,t)', 'Smoothed local coherence strength.'],
    ['S', 'Smoothing operator in time and/or scale.'],
    ['*', 'Complex conjugate in cross-wavelet spectrum.'],
], [120, 350])
p('Section 22 in forex-formulas-explained.pdf lists the same ρ_wavelet and R² structure.')

page('Wavelet correlation', '07 / Scale-by-scale score')
f('rho_wavelet(s) = Corr( W_x(s,·), W_y(s,·) )')
p('Compute one correlation per scale using coefficient series over t. Compare scales side by side — a high ρ at large s with low ρ at small s matches the “linked on weeks, not days” story.')
f(f'Teaching: Morlet CWT, scale={SCALE}, rho_wavelet ≈ {RHO_W:.4f}')
p('Demean coefficients before correlating to match Pearson-style centering on the coefficient path.')

page('Wavelet coherence R²', '08 / Local strength')
f('R^2(s,t) = | S( s^-1 W_x W_y* ) |^2 /\n         ( S(s^-1 |W_x|^2) * S(s^-1 |W_y|^2) )')
p('Smoothing S reduces noisy speckles in raw cross-wavelet power. R²(s,t) lies in [0, 1] like spectral coherence but is indexed by both scale and time.')
p('Phase arg(W_xy) shows lead/lag locally — coherence magnitude alone does not show direction or causation.')

page('Edge leakage warning', '09 / Two-sided filters')
p('CWT uses filters that extend beyond each t. At series starts and ends, coefficients borrow from missing neighbors — edge regions are unreliable (cone of influence in Grinsted plots).')
p('Two-sided non-causal filters must never use future returns in live forecasting — research on historical panels is fine if edges are masked in charts.')
p('Padding choices (zero, mirror, extend) change edges — document padding in code.')

page('Daily majors workflow', '10 / Repo usage')
h('1. Align business-day returns')
p('Same snapshot discipline as other methods.')
h('2. Mask edge cones in plots')
p('Do not interpret bright R² at the very last dates without checking leakage.')
h('3. Pre-specify wavelet, scales, smoothing')
p('Scale grids tuned after seeing pair rankings invite overfit.')

page('Versus spectral coherence', '11 / Complementary frequency tools')
p('Method 21 (spectral coherence) assumes stationary spectra across time. Wavelets allow evolving linkage — useful around crises. Both are linear tools in their coefficient domain.')
p('Neither replaces tail dependence counts (method 19) or DCCA long-memory scaling (method 23).')

page('Software reproduction', '12 / PyWavelets CWT')
f('import pywt\nWx, _ = pywt.cwt(x, scales, "morl")\nWy, _ = pywt.cwt(y, scales, "morl")\n# correlate Wx[i] and Wy[i] per scale i')
p('Full wavelet coherence toolkits implement smoothing S and significance contours — verify against Grinsted et al. when publishing figures.')
p('Install PyWavelets in the environment that builds this PDF so asserts match runtime.')

page('Limits', '13 / What wavelets cannot tell you')
p('Scale labels are approximate in days — calibrate with known test signals. Complex-valued noise and volume gaps distort coefficients.')
p('High ρ_wavelet(s) at one scale does not prove stable out-of-sample linkage.')
p('Chasing max R²(s,t) across pairs without pre-registration overstates significance.')

page('Practice', '14 / Quick checks')
p('<b>Q:</b> Does R² show causation? <b>A:</b> No — phase hints at timing, not mechanism.')
p('<b>Q:</b> Can edges be ignored? <b>A:</b> No — mask cone-of-influence regions.')
p(f'<b>Check:</b> teaching ρ_wavelet at scale {SCALE} ≈ {RHO_W:.4f}.')
p('<b>Q:</b> Is ρ_wavelet the same as Pearson r? <b>A:</b> No — it is on wavelet coefficients at scale s.')

page('Sources', '15 / Research trail')
refs = [
    ('1', 'Grinsted, A., Moore, J. C., & Jevrejeva, S. (2004). Application of the cross wavelet transform and wavelet coherence to geophysical time series. Nonlinear Processes in Geophysics, 11, 561–566.', 'https://doi.org/10.5194/npg-11-561-2004', 'Cross wavelet and coherence reference.'),
    ('2', 'forex-formulas-explained.pdf — section 22 (this repository).', '../forex-formulas-explained.pdf', 'ρ_wavelet and R² formulas.'),
    ('3', 'PyWavelets documentation: pywt.cwt.', 'https://pywavelets.readthedocs.io/', 'CWT implementation.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Rebuild: python build_guide.py. End of wavelet correlation and coherence beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 22  |  WAVELET CORRELATION AND COHERENCE')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Wavelet Correlation and Coherence - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert -1.0 <= RHO_W <= 1.0
assert RHO_W > 0.5
assert abs(RHO_W - wavelet_corr_at_scale(TEACH_X, TEACH_Y, SCALE)) < 1e-9
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
