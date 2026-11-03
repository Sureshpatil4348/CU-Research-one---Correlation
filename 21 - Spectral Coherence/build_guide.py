from pathlib import Path
from math import isclose
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader
import numpy as np
from scipy import signal

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Spectral_Coherence_Complete_Simple_Guide.pdf'
EXPECTED_PAGES = 15
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyEasy', fontName='Helvetica', fontSize=11, leading=16, spaceAfter=10))
styles.add(ParagraphStyle(name='HeadEasy', fontName='Helvetica-Bold', fontSize=23, leading=28, textColor=colors.HexColor('#15364A'), spaceAfter=18))
styles.add(ParagraphStyle(name='SubEasy', fontName='Helvetica-Bold', fontSize=13, leading=18, textColor=colors.HexColor('#087F8C'), spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name='FormulaEasy', fontName='Courier', fontSize=10, leading=15, backColor=colors.HexColor('#EDF5F7'), borderPadding=10, spaceBefore=8, spaceAfter=17))
styles.add(ParagraphStyle(name='SmallEasy', fontName='Helvetica', fontSize=9, leading=13, spaceAfter=8))
story = []

N_TEACH = 64
T = np.arange(N_TEACH, dtype=float)
FREQ = 0.2
TEACH_X = 0.008 * np.sin(2 * np.pi * FREQ * T)
TEACH_Y = 0.006 * np.sin(2 * np.pi * FREQ * T + 0.3)
FS = 1.0
NPERSEG = 16
F_GRID, COH = signal.coherence(TEACH_X, TEACH_Y, fs=FS, nperseg=NPERSEG)
PEAK_COH = float(np.max(COH))
PEAK_F = float(F_GRID[int(np.argmax(COH))])


def gamma_sq_from_psd(sxx, syy, sxy):
    return (abs(sxy) ** 2) / (sxx * syy)


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


page('Spectral coherence', 'Method 21 / A complete beginner guide')
p('<b>Question this method answers:</b> At which cycle lengths (frequencies) do two FX return series oscillate together?')
p('Spectral coherence γ²(f) is between 0 and 1 at each frequency f. It has no sign — phase carries timing separately.')
h('Page map')
table([
    ['Pages', 'Topic'],
    ['2', 'Frequency view versus time-domain r'],
    ['3', 'FX percent math (majors)'],
    ['4', 'Power and cross-spectra'],
    ['5', 'Welch smoothing (SciPy)'],
    ['6', 'Symbol dictionary'],
    ['7-9', 'γ² formula and teaching sine returns'],
    ['10-11', 'Phase and workflow'],
    ['12', 'Software reproduction'],
    ['13-15', 'Limits, practice, sources'],
], [65, 405])
p('Teaching sinusoid returns only — no live spectral panels from snapshots.')
p('Prepared for: 21 - Spectral Coherence. README status: not started.')

page('Co-movement by frequency', '02 / The basic idea')
p('Daily Pearson r mixes all cycle lengths into one number. Spectral methods split variation across frequencies f (cycles per day). Coherence asks: when X has power at f, does Y share it?')
h('Unsigned strength')
table([
    ['γ²(f) ∈ [0, 1]', '0 = no linear linkage at f; 1 = perfect linear linkage at f.'],
    ['No sign', 'Opposite phase can still yield high γ² if alignment is stable.'],
    ['Smoothing', 'Welch averaging trades bias for variance — window length matters.'],
], [170, 300])

page('FX percent math (majors)', '03 / Returns on the clock')
f('Simple return = P_t / P_{t-1} - 1\nLog return = ln(P_t / P_{t-1})')
p('1.1000 → 1.1110 is about +1% simple return. Spectral coherence is applied to evenly spaced return series (D1 majors). Gaps should be handled before FFT-based steps — do not silently fill with zeros without documenting.')
p('Example from the formula sheet: a five-day cycle corresponds to frequency f = 1/5 cycles per observation when one step equals one trading day.')

page('Spectral building blocks', '04 / Sxx, Syy, Sxy')
p('Sxx(f) measures how much series X wiggles at frequency f. Syy(f) does the same for Y. Sxy(f) is the cross-spectrum linking X and Y at f — it can be complex.')
p('Coherence normalizes |Sxy|² by both own-power spectra so γ² is comparable across pairs.')
p('Think of Sxx as a volume knob per frequency for X alone. When Sxy is large at f but Sxx is tiny, γ² can still be moderate because shared power must be judged relative to each leg’s own activity at that f.')
p('For FX returns, demeaning before FFT/Welch steps removes the zero-frequency spike from slow drift — state whether you demeaned or detrended in experiment NOTES.')

page('Welch method in SciPy', '05 / Magnitude-squared coherence')
p('scipy.signal.coherence implements Welch’s method: segment the series, window each segment, FFT, average periodograms across segments. That smoothing stabilizes γ²(f) for noisy FX returns.')
p('Parameters nperseg, noverlap, and window shape change the frequency grid and bias — freeze them in experiment NOTES.')

page('Symbol dictionary', '06 / Small math dictionary')
table([
    ['Symbol', 'Meaning'],
    ['f', 'Frequency (cycles per observation).'],
    ['Sxx(f), Syy(f)', 'Auto-spectral density (power) at f.'],
    ['Sxy(f)', 'Cross-spectral density at f.'],
    ['γ²(f)', 'Magnitude-squared coherence at f.'],
    ['Phase φ(f)', 'Angle of Sxy — timing offset at f.'],
    ['Welch', 'Averaged periodogram estimator (SciPy default).'],
], [120, 350])
p('Section 21 in forex-formulas-explained.pdf uses the same γ² normalization.')

page('Coherence formula', '07 / Normalize shared power')
f('gamma^2(f) = |S_xy(f)|^2 / ( S_xx(f) * S_yy(f) )')
p('At each f, divide squared cross-power by the product of auto-powers. Values above 1 indicate a numerical or scaling bug — correct implementations clamp to [0, 1].')
p('γ²(f) describes linear co-sinusoidal linkage at f, not nonlinear tail dependence.')

page('Teaching sinusoids', '08 / Shared five-day rhythm')
p(f'Made-up returns follow sin waves with shared period 1/{FREQ:.1f} = 5 days on D1 steps. Amplitudes differ (0.8% versus 0.6%) but phase offset is fixed.')
f(f'Welch peak coherence ≈ {PEAK_COH:.4f}\nPeak frequency ≈ {PEAK_F:.4f} cycles/day')
p('Peak location should sit near the planted frequency after smoothing — small shift is normal when nperseg does not divide the period evenly.')

page('Read phase separately', '09 / Timing at frequency f')
f('S_xy(f) = |S_xy| * exp(i * phi(f))')
p('Phase φ(f) tells whether Y leads or lags X at that cycle length. Coherence alone hides that sign information — report φ(f) alongside γ²(f) when lead-lag matters.')
p('For FX risk, a high γ² at low f (slow cycles) may reflect shared macro drift; high γ² at high f may reflect short-lived liquidity shocks — inspect both.')

page('Daily majors workflow', '10 / Repo usage')
h('1. Evenly spaced return matrix')
p('Align eight majors on common business days from a frozen snapshot.')
h('2. Pre-specify Welch settings')
p('Document nperseg before scanning all pairs.')
h('3. Export γ²(f) curves, not only the max')
p('Peaks can be spurious with short samples — show the whole curve.')

page('Compare to Pearson and lags', '11 / Complementary tools')
p('Pearson r is one number; γ²(f) is a function. Lagged cross-correlation (method 12) stays in the time domain. Use spectral coherence when the hypothesis names a cycle length (weekly rebalancing, month-end flows).')
p('None of these prove causation or deliver a hedge ratio.')

page('Software reproduction', '12 / SciPy call')
f('from scipy import signal\nf, Cxy = signal.coherence(x, y, fs=1.0, nperseg=16)\n# Cxy is magnitude-squared coherence (gamma^2)')
p('Match fs to your sampling (1.0 for one observation per day). Detrend or demean returns if slow drift would dominate low frequencies — state the choice.')
p('Alternative: numpy FFT periodogram without Welch is noisier; prefer signal.coherence for teaching reproducibility.')

page('Limits', '13 / What γ² cannot tell you')
p('Short samples give ragged spectra. Non-stationarity (crisis regimes) violates fixed-spectrum interpretations unless you window data.')
p('Coherence is linear in frequency space — strong nonlinear tail links may be missed.')
p('Sharpening γ² by chasing peak frequency across pairs without pre-registration inflates false positives.')

page('Practice', '14 / Quick checks')
p('<b>Q:</b> Can γ²(f) be negative? <b>A:</b> No — it is squared magnitude, between 0 and 1.')
p('<b>Q:</b> Does high γ² at f = 0.2 prove Y causes X? <b>A:</b> No — use phase and domain knowledge.')
p(f'<b>Check:</b> teaching peak γ² ≈ {PEAK_COH:.4f} with nperseg={NPERSEG}.')
p('<b>Q:</b> Is γ² the same as |Pearson r|? <b>A:</b> No — r mixes all frequencies; γ²(f) is localized.')

page('Sources', '15 / Research trail')
refs = [
    ('1', 'SciPy documentation: scipy.signal.coherence (Welch magnitude-squared coherence).', 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.coherence.html', 'Implementation used in this repo guide.'),
    ('2', 'forex-formulas-explained.pdf — section 21 (this repository).', '../forex-formulas-explained.pdf', 'γ²(f) definition.'),
]
for no, title, url, note in refs:
    story.append(Paragraph(
        f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>',
        styles['SmallEasy'],
    ))
    story.append(Spacer(1, 8))
p('Rebuild: python build_guide.py. End of spectral coherence beginner guide.')


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD'))
    c.line(48, 43, 547, 43)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48, 29, 'METHOD 21  |  SPECTRAL COHERENCE')
    c.drawRightString(547, 29, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=55,
    leftMargin=55,
    topMargin=43,
    bottomMargin=59,
    title='Spectral Coherence - Complete Simple Guide',
    author='Research CO-1',
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == EXPECTED_PAGES, f'Unexpected page count: {len(reader.pages)}'
for i, pg in enumerate(reader.pages):
    text = pg.extract_text() or ''
    assert len(text) > 350, (i + 1, len(text))
assert 0.0 <= PEAK_COH <= 1.0
assert PEAK_COH > 0.9
assert isclose(gamma_sq_from_psd(1.0, 1.0, 0.9), 0.81)
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
