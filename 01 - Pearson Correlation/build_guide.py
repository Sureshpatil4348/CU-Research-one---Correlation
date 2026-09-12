from pathlib import Path
from math import sqrt, log, exp, tanh, atanh
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Pearson_Correlation_Complete_Simple_Guide.pdf'
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyEasy', fontName='Helvetica', fontSize=11, leading=16, spaceAfter=10))
styles.add(ParagraphStyle(name='HeadEasy', fontName='Helvetica-Bold', fontSize=23, leading=28, textColor=colors.HexColor('#15364A'), spaceAfter=18))
styles.add(ParagraphStyle(name='SubEasy', fontName='Helvetica-Bold', fontSize=13, leading=18, textColor=colors.HexColor('#087F8C'), spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name='FormulaEasy', fontName='Courier', fontSize=10, leading=15, backColor=colors.HexColor('#EDF5F7'), borderPadding=10, spaceBefore=8, spaceAfter=17))
styles.add(ParagraphStyle(name='SmallEasy', fontName='Helvetica', fontSize=9, leading=13, spaceAfter=8))
story=[]
def p(t): story.append(Paragraph(t, styles['BodyEasy']))
def h(t): story.append(Paragraph(t, styles['SubEasy']))
def f(t): story.append(Paragraph(escape(t).replace('\n','<br/>'), styles['FormulaEasy']))
def page(title, tag):
    if story: story.append(PageBreak())
    story.append(Paragraph(tag.upper(), styles['SubEasy']))
    story.append(Paragraph(title, styles['HeadEasy']))
def table(rows, widths=None):
    data=[[Paragraph(escape(str(v)), styles['SmallEasy']) for v in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DBEDF0')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#B8CCD2')),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.append(t); story.append(Spacer(1,12))
class Plots(Flowable):
    def __init__(self): Flowable.__init__(self); self.width=470; self.height=300
    def draw(self):
        c=self.canv
        sets=[('Upward: r = +1',[-2,-1,0,1,2],[-2,-1,0,1,2]),('Downward: r = -1',[-2,-1,0,1,2],[2,1,0,-1,-2]),('No straight tilt: r = 0',[-2,-1,0,1,2],[1,-2,2,-2,1]),('A curve: r = 0',[-2,-1,0,1,2],[4,1,0,1,4])]
        for k,(title,x,y) in enumerate(sets):
            ox=20+(k%2)*240; oy=35+(1-k//2)*150
            c.setFillColor(colors.HexColor('#15364A')); c.setFont('Helvetica-Bold',10); c.drawString(ox,oy+115,title)
            c.setStrokeColor(colors.HexColor('#AABCC2')); c.line(ox,oy,ox+190,oy); c.line(ox,oy,ox,oy+100)
            c.setFont('Helvetica',8); c.drawString(ox+185,oy-12,'X'); c.drawString(ox-12,oy+94,'Y')
            for a,b in zip(x,y):
                xx=ox+12+(a-min(x))/(max(x)-min(x))*160; yy=oy+10+(b-min(y))/(max(y)-min(y))*80
                c.setFillColor(colors.HexColor('#087F8C')); c.circle(xx,yy,3.5,fill=1,stroke=0)

page('Pearson correlation', 'Method 01 / A complete beginner guide')
p('<b>How two sets of numbers move together.</b> A slow, step-by-step guide with research notes, formulas, small examples, and checks.')
p('Start here: When X is high, is Y often high too? Or is Y often low? Pearson correlation gives one number to help answer this. It looks for a pattern that is close to a straight line.')
h('Read it in three parts')
p('<b>First:</b> Learn the idea and see the dots. <b>Next:</b> Do the math by hand. <b>Last:</b> Learn how to check and report the result.')
p('The words aim to be very simple. Some math terms are needed. Each one is explained when it first appears. The advanced pages are marked so you can come back to them later.')
table([['Pages','What you will learn'],['2-3','The idea, the sign, and what the dots show'],['4','The research behind the method'],['5-9','The symbols, full formula, and hand calculation'],['10-11','How to choose and clean paired data'],['12-13','Chance tests and a range for the true value'],['14-15','Limits, common errors, and software'],['16-18','A full workflow, practice, and sources']], [65,405])
p('All examples are made-up teaching data. This is a guide to Pearson correlation only. It is not a report of a new study or a promise about future results.')
p('Prepared for the folder: 01 - Pearson Correlation<br/>7 September 2026')

page('What does it actually do?', '02 / The basic idea')
p('Think of five plants. For each plant, you write down how much water it got and how much it grew. Each plant gives one pair of numbers. Water is X. Growth is Y.')
p('You now ask: Do plants with more water tend to grow more? Pearson correlation looks at all the pairs at once. It checks how closely the dots follow a straight path.')
h('The answer is called r')
p('The letter <b>r</b> is the score from your data. Its value goes from -1 to +1. It has no unit. It is not in days, dollars, or metres.')
table([['Value','Plain meaning'],['r = +1','All dots lie exactly on an upward straight line.'],['r is above 0','Higher X tends to go with higher Y.'],['r = 0','There is no overall straight-line tilt. A curve may still exist.'],['r is below 0','Higher X tends to go with lower Y.'],['r = -1','All dots lie exactly on a downward straight line.']], [90,380])
h('Two things to read')
p('<b>The sign</b> tells you the direction. Plus means up together. Minus means one tends to be high when the other is low. <b>The size</b>, ignoring the sign, tells you how close the pattern is to a straight line.')
p('A value of -0.90 is closer to a straight line than +0.30. A minus sign does not mean the link is weak or bad.')
p('There is no single score that counts as strong in every field. Use the dots, the number of pairs, and the purpose of the study. Always report the actual number.')

page('See the pattern first', '03 / A dot plot')
p('A dot plot is also called a scatter plot. Put X along the bottom. Put Y up the side. Draw one dot for each pair. The sketches below use five pairs each.')
story.append(Plots())
h('Why the last picture matters')
p('In the last plot, Y equals X squared. That means Y = X times X. The dots form a U. X tells us Y exactly, yet Pearson r is zero. The left and right sides cancel in the straight-line score.')
p('So, <b>r = 0 does not mean there is no link</b>. It means Pearson found no straight-line tilt. Look at the plot before you judge the score.')
p('For these sketches, each axis is scaled to fit its own data. Use the dot shape to see the idea. Do not compare the slopes across the four pictures.')

page('Where did the method come from?', '04 / Research notes')
h('A key early paper: Karl Pearson, 1895 [1]')
p('<i>Note on Regression and Inheritance in the Case of Two Parents.</i> Proceedings of the Royal Society of London, volume 58, pages 240-242. DOI: 10.1098/rspl.1895.0041.')
p('The topic was how a trait in parents relates to the same trait in their children. A trait can be a measured feature, such as height. The paper used differences from group means and measures of spread. Its opening assumes those differences follow, exactly or nearly, a normal, bell-shaped pattern.')
p('Its setting was inheritance. It was not a study of exchange rates. It is a key early reference in the history of Pearson correlation, not the source of every later test used with r. The modern hand calculation in this guide is a teaching example, not a copy of its data.')
h('Why later research was needed [2, 3]')
p('One small sample can give a high r by chance. R. A. Fisher studied how r varies across samples in his 1915 paper. His 1921 paper dealt with error in a correlation found from a small sample. This work helps explain why a single score needs a measure of uncertainty.')
p('A later practical tool is the Fisher transformation. It changes r to a scale on which a range is easier to estimate. We use its common modern form on page 13.')
h('What has been checked')
p('The paper titles, dates, and publication details were checked against journal or archive records. The 1895 opening description was available in an indexed scan excerpt. This guide does not claim a full line-by-line review of the historical papers. Modern formulas are explained separately, with current technical references [4, 5].')
p('The sources on page 18 let you go from this simple guide to the original research records. Historical language and symbols may differ from those used here.')

page('Meet the symbols', '05 / A small math dictionary')
p('You only need pairs of numbers, adding, taking away, multiplying, dividing, and a square root to calculate r by hand.')
table([['Symbol used here','What it means'],['X and Y','The two things you measure.'],['x_i and y_i','The X and Y values in row i. The small i is a row label.'],['n','The number of complete pairs.'],['x_bar and y_bar','The means. A mean is the sum divided by the count.'],['dx and dy','A value minus its own mean. These are deviations.'],['SUM','Add all the terms, one for each row. Often written as the Greek letter sigma.'],['a^2','a times a. This is called a square.'],['sqrt(a)','The positive square root. For example, sqrt(9) = 3.'],['r','The correlation in the sample you have.'],['rho','The correlation in the whole population or process. Usually unknown.']], [125,345])
h('A sample is a small part')
p('A sample might be 100 days chosen from many days, or 30 plants from a large crop. The population is the full group or process you want to learn about. Your sample r is an estimate of the unknown rho.')
p('The formula below uses plain keyboard symbols so you can type it easily. SUM means the same thing each time: add over all complete rows.')

page('The main formula', '06 / What each part does')
f('dx_i = x_i - x_bar\ndy_i = y_i - y_bar\n\nr = SUM(dx_i * dy_i) /\n    sqrt(SUM(dx_i^2) * SUM(dy_i^2))')
h('Step 1: Find each mean')
p('Add the X values and divide by n. Do the same for Y. These means are the middle reference points for the two lists.')
h('Step 2: Take away each mean')
p('A positive difference is above the mean. A negative difference is below it. Do this for each row, keeping each X with its matching Y.')
h('Step 3: Multiply the two differences')
p('If both are above their means, the product is positive. If both are below their means, it is also positive: minus times minus is plus. If one is above and one is below, the product is negative.')
h('Step 4: Add, then scale')
p('The top adds these products. The bottom measures the size of the two lists of differences. Dividing by it puts the answer on the fixed scale from -1 to +1.')
p('The score is undefined if either list has no spread. Then the bottom is zero. Do not replace an undefined score with zero. Zero is a real result with a different meaning. [4]')

page('Calculate it by hand: start', '07 / Worked example, part one')
p('Use these five made-up pairs. X could be hours of light. Y could be plant growth in centimetres. The labels help tell the story; they do not prove that light caused the growth.')
table([['Row','X','Y'],[1,1,2],[2,2,1],[3,3,4],[4,4,3],[5,5,5]], [65,150,150])
h('1. Find the count and means')
f('n = 5\nx_bar = (1 + 2 + 3 + 4 + 5) / 5 = 3\ny_bar = (2 + 1 + 4 + 3 + 5) / 5 = 3')
h('2. Find the differences')
table([['Row','X - 3 = dx','Y - 3 = dy'],[1,-2,-1],[2,-1,-2],[3,0,1],[4,1,0],[5,2,2]], [65,180,180])
p('Check: the X differences add to zero. The Y differences also add to zero. This is what should happen when you take away each list\'s exact mean.')
p('Keep the signs. For row 1, 1 - 3 is -2, not +2. Signs tell the formula which way the values move.')

page('Calculate it by hand: finish', '08 / Worked example, part two')
table([['Row','dx','dy','dx * dy','dx^2','dy^2'],[1,-2,-1,2,4,1],[2,-1,-2,2,1,4],[3,0,1,0,0,1],[4,1,0,0,1,0],[5,2,2,4,4,4],['Sum',0,0,8,10,10]], [55,60,60,95,90,90])
h('3. Put the sums into the formula')
f('Top = 8\nBottom = sqrt(10 * 10) = sqrt(100) = 10\nr = 8 / 10 = 0.80')
h('4. Say what the score means')
p('In these five pairs, larger X tends to go with larger Y. The pattern has a clear upward tilt. It is not a perfect line. Five pairs are too few to be sure that the same pattern holds in a large group.')
p('<b>Do not say:</b> X makes Y rise 80% of the time. Pearson r is not the share of times that two things go up together. It uses the sizes and signs of differences from their means.')
h('5. A quick cross-check')
p('Swap the X and Y columns. You still get 0.80. The product in each row is the same and the two sums in the bottom only swap places. Pearson correlation treats the two lists symmetrically.')
p('You can check this example in Excel or Python on page 15. Keep full values during the math. Round the final result for display.')

page('Other forms of the same formula', '09 / Deeper math, in small steps')
h('Covariance means shared movement')
p('Sample covariance is the average paired product with an n - 1 divisor. A sample standard deviation tells us the typical spread in one list. Its symbol here is s. All sums below use the same n pairs.')
f('cov_xy = SUM(dx * dy) / (n - 1)\ns_x = sqrt(SUM(dx^2) / (n - 1))\ns_y = sqrt(SUM(dy^2) / (n - 1))\nr = cov_xy / (s_x * s_y)')
p('For our example: cov_xy = 8/4 = 2. Each standard deviation is sqrt(10/4), about 1.5811. So r = 2/(1.5811 times 1.5811) = 0.80, using unrounded values. The n - 1 factors cancel.')
h('A standard score form')
f('zx_i = (x_i - x_bar) / s_x\nzy_i = (y_i - y_bar) / s_y\nr = SUM(zx_i * zy_i) / (n - 1)')
p('A standard score says how many units of spread a value is above or below its mean. If you use sample standard deviations, divide the sum by n - 1, not n.')
h('A raw-sum form for a second check')
f('r = [n*SUM(x*y) - SUM(x)*SUM(y)] /\n sqrt([n*SUM(x^2) - SUM(x)^2] *\n      [n*SUM(y^2) - SUM(y)^2])')
p('Here SUM(x*y) = 53, SUM(x) = SUM(y) = 15, and both square sums are 55. The top is 40. Each bracket below is 50. So r = 40/50 = 0.80. For very large values with tiny differences, use a well-tested centred calculation; subtracting large near-equal numbers can lose precision.')

page('Choose the right pairs', '10 / Data rules')
h('One row must mean one matched case')
p('Match a plant with that same plant. Match a day with that same day. Do not pair one person\'s height with another person\'s weight. Do not sort the two lists on their own. That breaks the pairs and can make a false pattern.')
h('Use numbers with a clear meaning')
p('Pearson uses the distances between values. A code such as 1 = red, 2 = blue, 3 = green does not have a real numeric distance. The score would depend on your choice of codes. Do not use such labels as measured numbers.')
h('Missing is not zero')
p('If X or Y is missing, that row is not a complete pair. A simple analysis uses only complete pairs. Record how many rows were lost and why. If the missing rows differ from the kept rows, the result may be biased. Dropping rows is not a cure for that bias.')
h('Check errors and unusual values')
p('Look for wrong units, extra zeros, repeat rows, and dates out of order. Fix a confirmed error from the source. A very unusual but real value is called an outlier. It can have a large effect on r. Do not remove it just because you dislike the score.')
h('When the calculation is possible')
p('You need at least two complete pairs and some spread in both lists. With only two nonconstant pairs, r is always +1 or -1. That tells you almost nothing about a wider group. More data helps only when the rows are useful and correctly matched.')
p('You do not need bell-shaped data just to compute r. Extra assumptions matter when you attach a usual p-value or confidence interval. Those are explained next. [4, 5]')

page('If your data are prices or FX', '11 / A worked data setup')
p('This page shows how to prepare time data for Pearson correlation. The same Pearson formula still applies. Choose what you want to study before you calculate.')
h('Price level or return?')
p('A price level is the price itself. A return is its change as a share of the old price. If you want to study same-period moves, returns usually match that question better. Two price lists can both trend over time and show a large r even when their short-term moves are weakly linked.')
f('Simple return at time t = P_t / P_previous - 1\nPercent return = 100 * simple return\nLog return = ln(P_t / P_previous)')
p('P is price. ln is the natural log, a calculator function. Log returns require positive prices. Choose one return type for both lists. Simple and log returns can give different r values.')
table([['Date','Price A','Price B','Return A','Return B'],['Day 0',100,200,'-','-'],['Day 1',102,202,'2.00%','1.00%'],['Day 2',101,204,'-0.9804%','0.9901%'],['Day 3',103,203,'1.9802%','-0.4902%']], [65,75,75,120,120])
p('Four price dates give only three returns. Each return pair must cover the same time span. This tiny table is a setup example, not evidence for a stable market link.')
h('Keep the clock and quote direction clear')
p('Use matching times, time zones, and sampling intervals. Do not turn a missing quote into a zero return by accident. Gaps can make one return cover more time than another.')
p('For an FX rate, write what one unit buys. Reversing a quote reverses the sign of its log return exactly. Simple returns do not reverse by a simple minus sign. Mixing quote directions can change how the score reads.')
p('Returns do not fix every problem. A time series may have linked rows and changing behaviour. The usual independent-row test can then give a misleading p-value.')

page('Could chance make this score?', '12 / Optional: a test')
p('A high r in a small sample may happen by chance. A test asks how surprising the sample score would be under a stated starting model. It does not prove a cause.')
h('The usual starting model')
p('The null hypothesis is rho = 0: the population has zero Pearson correlation. For the standard exact test, the pairs are independent draws from the same bivariate normal population. This means the joint X-Y pattern has a two-variable bell-shaped form. A normal-looking X list and Y list alone are not enough to ensure that joint shape.')
f('t = r * sqrt((n - 2) / (1 - r^2))\ndegrees of freedom = n - 2')
p('The t score is compared with a t distribution, a reference curve. Degrees of freedom selects the curve. For a two-sided test, count outcomes at least as far from zero in either direction.')
h('Apply it to the five-pair example')
f('r = 0.80; n = 5\nt = 0.80 * sqrt(3 / 0.36) = 2.3094\ndegrees of freedom = 3\ntwo-sided p-value is about 0.1041')
p('If the null model and its assumptions were true, scores at least this extreme would occur in about 10.4% of repeated samples of this size. The p-value is not the chance that the null is true.')
p('At a pre-chosen 0.05 cutoff, this example does not reject the null. That does not prove no link. We have very little data. Also, a tiny p-value in a huge sample can go with a small, unhelpful effect.')
p('This t formula needs n greater than 2 and |r| less than 1. Perfect sample lines and tiny samples need special handling. Repeated or time-linked rows violate independence. Do not apply this test blindly to daily market data. [4]')

page('Give a range, not just a point', '13 / Optional: uncertainty')
p('A confidence interval gives a range made by a method with a stated long-run success rate. A 95% method aims to cover the fixed true rho in about 95 out of 100 repeated samples under its assumptions.')
h('The common Fisher method [3, 5]')
f('z = 0.5 * ln((1 + r) / (1 - r))\nSE = 1 / sqrt(n - 3)\nz_low = z - 1.96 * SE\nz_high = z + 1.96 * SE\nr_bound = (exp(2*z_bound) - 1) /\n          (exp(2*z_bound) + 1)')
p('SE means standard error: a measure of sample-to-sample noise on the z scale. exp means the exponential function, found on a scientific calculator. Convert both bounds back to get the range for rho.')
h('The same example')
f('r = 0.80; n = 5\nz = 1.0986; SE = 0.7071\nz range = about -0.2873 to 2.4845\nr range = about -0.2796 to 0.9862')
p('The range is very wide. It even includes negative values. This shows why r = 0.80 from only five pairs is not firm evidence for a precise population value.')
p('This is an approximate method for independent pairs from a bivariate normal population. It needs n greater than 3 and r strictly between -1 and +1. With very small samples its accuracy is limited. It is not an automatic fix for unusual distributions or linked time data.')
p('A confidence interval is not a range for tomorrow\'s X or Y. It is a range for the population correlation. It does not mean there is a 95% chance that a fixed parameter moved into this already calculated interval.')

page('What Pearson cannot tell you', '14 / Limits and useful facts')
h('It cannot prove cause')
p('Ice-cream sales and swimming may both rise on hot days. Heat can affect both. A correlation alone cannot tell which thing caused which, or whether a third thing caused both.')
h('It is not a slope or a forecast')
p('A slope tells how much Y changes for one unit of X. Pearson r has no units. In a simple least-squares line with an intercept, slope b = r * s_y / s_x. For our example b = 0.80 and intercept a = y_bar - b*x_bar = 0.60. The fitted line is Y_hat = 0.60 + 0.80*X. Y_hat is an estimate, not a guarantee.')
p('In that same one-X regression with an intercept, R squared equals r squared. Here 0.80 squared is 0.64. The fitted line accounts for 64% of the sample squared variation in Y around its mean. This is not 64% forecast accuracy or proof of cause.')
h('Outliers, curves, and groups can fool one score')
p('One far-away dot may create or hide a large r. A U-shape may have zero r. Two separate groups may show a pattern when pooled that differs from the pattern within each group. A narrow slice of X values can also change r. Inspect these features before making a claim.')
h('Changes of units have a simple rule')
p('Add a fixed amount to all X values: r stays the same. Multiply X by a positive number: r stays the same. Multiply it by a negative number: the sign flips. Apply this to both lists and two flips cancel. Multiplying by zero removes all spread and makes r undefined.')
p('Taking logs, squaring values, or changing to returns is a different kind of change. It can change r. Record such choices. Pearson also cannot show which series leads, how a link changes over time, or whether the link will last.')

page('Calculate it with software', '15 / Reproduce the example')
h('Excel: the short route')
p('Type X values 1, 2, 3, 4, 5 in A2:A6. Type Y values 2, 1, 4, 3, 5 in B2:B6. Each row must stay matched. Start with complete numeric pairs.')
f('=CORREL(A2:A6,B2:B6)\nExpected answer: 0.8')
p('For a manual check, put =A2-AVERAGE($A$2:$A$6) in C2 and =B2-AVERAGE($B$2:$B$6) in D2. Fill both down to row 6. Then use the formula below.')
f('=SUMPRODUCT(C2:C6,D2:D6)/\n SQRT(SUMSQ(C2:C6)*SUMSQ(D2:D6))')
h('Python: no extra package needed for r')
f('from math import sqrt\nx = [1, 2, 3, 4, 5]\ny = [2, 1, 4, 3, 5]\nassert len(x) == len(y) and len(x) >= 2\nmx, my = sum(x)/len(x), sum(y)/len(y)\ndx = [v-mx for v in x]\ndy = [v-my for v in y]\ntop = sum(a*b for a, b in zip(dx, dy))\nbot = sqrt(sum(a*a for a in dx) *\n           sum(b*b for b in dy))\nif bot == 0:\n    raise ValueError("A list has no spread")\nprint(top/bot)  # 0.8')
p('This small script assumes finite numeric values with no missing rows. For a modern SciPy installation, scipy.stats.pearsonr(x, y) returns r and a p-value. Its result.confidence_interval() method gives a Fisher interval by default. Check the assumptions before reporting either. [4]')

page('A full study, step by step', '16 / Your working method')
h('1. Write the question before the calculation')
p('Example: Over this fixed set of dates, how closely do the two daily return lists follow a straight-line pattern? Name X, Y, the units, the dates, the source, and why this sample fits the question.')
h('2. Make and check the paired file')
p('Use one row per case or time. Keep the raw data. Make a separate cleaned copy. Log each correction, removed row, missing value rule, and change of units. Count the complete pairs.')
h('3. Draw the dots and compute r')
p('Look for a line, a curve, groups, and unusual dots. Check that neither list is constant. Calculate r on the exact rows shown in the plot. Use a second calculation to check the result when possible.')
h('4. Decide whether a chance test is valid')
p('Ask whether the rows are independent and whether the joint model is reasonable. If they are not, report r as a sample description and explain the limit. Do not attach the usual test just because software supplies it.')
h('5. Check how much the answer depends on choices')
p('Review confirmed errors and unusual real rows. If you show results with and without an unusual row, label both and say why. Do not search through many dates and keep only the result you like. Many tests increase the chance of a false finding.')
h('6. Save a clear report')
p('Keep the data, cleaning notes, plot, calculation, and report inside this Pearson folder. State the limits next to the result. A new dataset or a changed time range is a new check, not proof that the old score will hold.')
p('<b>Example wording:</b> In five made-up matched pairs, Pearson r was 0.80. Under the independent bivariate-normal model, the two-sided p-value was about 0.104 and the approximate 95% Fisher interval was -0.280 to 0.986. The small sample leaves great uncertainty. This does not establish cause.')

page('Try it yourself', '17 / Practice and quick answers')
h('A. A perfect upward line')
p('X = 1, 2, 3. Y = 2, 4, 6. Find the means, then the differences, then r.')
p('<b>Answer:</b> Means are 2 and 4. The top is 4. The square sums are 2 and 8. The bottom is sqrt(16) = 4. So r = +1. This does not mean Y equals X. It means the dots sit on an exact upward line.')
h('B. A perfect downward line')
p('X = 1, 2, 3. Y = 6, 4, 2. The top is -4. The bottom is 4. So r = -1.')
h('C. A list with no spread')
p('X = 2, 2, 2. Y = 1, 3, 5. Every X difference is zero. The bottom is zero. The result is undefined, not r = 0.')
h('D. A curve that cancels')
p('X = -2, -1, 0, 1, 2. Y = 4, 1, 0, 1, 4. Means are 0 and 2. The paired products are -4, 1, 0, -1, 4. They add to zero. Both lists have spread, so r = 0. Yet Y = X squared exactly.')
h('E. Read a result carefully')
p('Does r = 0.70 mean 70% of days move together? <b>No.</b> Does r = -0.90 mean a weak link? <b>No.</b> Does a low p-value prove cause? <b>No.</b> Does r = 0 rule out a curve? <b>No.</b>')
h('The six checks to remember')
p('Right pairs. Clear units. No constant list. Inspect the dots. Check the assumptions. Report the uncertainty. These habits matter as much as getting the division right.')

page('Sources and further reading', '18 / Research trail')
p('Links checked on 7 September 2026. The short explanations, worked data, plots, and calculations in this guide are original teaching material. Bracket numbers point to the sources below.')
refs=[
('1','Pearson, K. (1895). Note on Regression and Inheritance in the Case of Two Parents. Proceedings of the Royal Society of London, 58, 240-242.','https://www.jstor.org/stable/115794','Journal record; DOI 10.1098/rspl.1895.0041. The UCL archive also holds working papers under PEARSON/3/6/5.'),
('2','Fisher, R. A. (1915). Frequency Distribution of the Values of the Correlation Coefficient in Samples from an Indefinitely Large Population. Biometrika, 10(4), 507-521.','https://repository.rothamsted.ac.uk/item/8w284/frequency-distribution-of-the-values-of-the-correlation-coefficient-in-samples-from-an-indefinitely-large-population','Research archive record with a paper download; DOI 10.2307/2331838.'),
('3','Fisher, R. A. (1921). On the "Probable Error" of a Coefficient of Correlation Deduced from a Small Sample. Metron, 1, 3-32.','https://digital.library.adelaide.edu.au/items/002ad8fb-c23c-407b-8a89-f036d8da6030','University archive record and access to the paper.'),
('4','SciPy documentation: scipy.stats.pearsonr.','https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html','Modern implementation, formula, null test, constant-input behaviour, and examples.'),
('5','SciPy documentation: PearsonRResult.confidence_interval.','https://scipy.github.io/devdocs/reference/generated/scipy.stats._result_classes.PearsonRResult.confidence_interval.html','Fisher transformation, standard error, assumptions, and interval limitations.')]
for no,title,url,note in refs:
    story.append(Paragraph(f'<b>[{no}] {escape(title)}</b><br/>{escape(note)}<br/><link href="{url}" color="#087F8C">Open source</link>', styles['SmallEasy']))
    story.append(Spacer(1,8))
p('Reading tip: Begin with the examples in this guide. Then use source [4] to check the modern calculation. The old research papers are a next step; their language is much harder than the explanation here.')

def footer(c,doc):
    c.setStrokeColor(colors.HexColor('#C7D8DD')); c.line(48,43,547,43)
    c.setFont('Helvetica',8); c.setFillColor(colors.HexColor('#55707B'))
    c.drawString(48,29,'METHOD 01  |  PEARSON CORRELATION')
    c.drawRightString(547,29,str(doc.page))
doc=SimpleDocTemplate(str(OUT),pagesize=(595.28,841.89),rightMargin=55,leftMargin=55,topMargin=43,bottomMargin=59,title='Pearson Correlation - Complete Simple Guide',author='Research CO-1',pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
reader=PdfReader(OUT)
assert len(reader.pages)==18, f'Unexpected page count: {len(reader.pages)}'
for i,pg in enumerate(reader.pages):
    text=pg.extract_text()
    assert len(text)>350, (i+1,len(text))
assert abs(8/sqrt(100)-0.8)<1e-12
assert abs(tanh(atanh(.8)-1.96/sqrt(2))-(-.2796))<.0001
print(f'Created and checked {len(reader.pages)} pages: {OUT}')
