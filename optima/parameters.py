"""
This module defines the Constant, Metapar, Timepar, and Popsizepar classes, which are 
used to define a single parameter (e.g., hivtest) and the full set of
parameters, the Parameterset class.

Version: 2.0 (2016nov05)
"""

from numpy import array, nan, isnan, zeros, argmax, mean, log, polyfit, exp, maximum, minimum, Inf, linspace, median, shape, ones
from numpy.random import random, seed
from optima import OptimaException, odict, printv, sanitize, uuid, today, getdate, smoothinterp, dcp, defaultrepr, isnumber, findinds, getvaliddata # Utilities 
from optima import Settings, getresults, convertlimits, gettvecdt # Heftier functions

defaultsmoothness = 1.0 # The number of years of smoothing to do by default


#############################################################################################################################
### Define the parameters!
##  NOTE, this should be consistent with the spreadsheet http://optimamodel.com/file/parameters
##  Edit there, then copy and paste from there into here; be sure to include header row
#############################################################################################################################
partable = '''
name	dataname	short	datashort	limits	by	partype	fittable	auto	cascade	coverage	visible	proginteract	fromdata
Initial HIV prevalence	None	initprev	initprev	(0, 1)	pop	initprev	pop	init	0	None	0	None	1
Population size	Population size	popsize	popsize	(0, 'maxpopsize')	pop	popsize	exp	popsize	0	None	0	None	1
Force-of-infection (unitless)	None	force	force	(0, 'maxmeta')	pop	meta	pop	force	0	None	0	None	0
Inhomogeneity (unitless)	None	inhomo	inhomo	(0, 'maxmeta')	pop	meta	pop	inhomo	0	None	0	None	0
Risk transitions (average number of years before movement)	Risk-related population transitions (average number of years before movement)	risktransit	risktransit	(0, 'maxrate')	array	meta	no	no	0	None	0	None	1
Age transitions (average number of years before movement)	Aging	agetransit	agetransit	(0, 'maxrate')	array	meta	no	no	0	None	0	None	1
Birth transitions (fraction born/year)	Births	birthtransit	birthtransit	(0, 'maxrate')	array	meta	no	no	0	None	0	None	1
Mortality rate (per year)	Percentage of people who die from non-HIV-related causes per year	death	death	(0, 'maxrate')	pop	timepar	meta	other	0	0	1	random	1
HIV testing rate (per year)	Percentage of population tested for HIV in the last 12 months	hivtest	hivtest	(0, 'maxrate')	pop	timepar	meta	test	0	0	1	random	1
AIDS testing rate (per year)	Probability of a person with CD4 <200 being tested per year	aidstest	aidstest	(0, 'maxrate')	tot	timepar	meta	test	0	0	1	random	1
STI prevalence	Prevalence of any ulcerative STIs	stiprev	stiprev	(0, 1)	pop	timepar	meta	other	0	0	1	random	1
Tuberculosis prevalence	Tuberculosis prevalence	tbprev	tbprev	(0, 1)	pop	timepar	meta	other	0	0	1	random	1
Number of people on treatment	Number of people on treatment	numtx	numtx	(0, 'maxpopsize')	tot	timepar	meta	treat	0	1	1	additive	1
Number of people on PMTCT	Number of women on PMTCT (Option B/B+)	numpmtct	numpmtct	(0, 'maxpopsize')	tot	timepar	meta	other	0	1	1	additive	1
Proportion of women who breastfeed	Percentage of HIV-positive women who breastfeed	breast	breast	(0, 1)	tot	timepar	meta	other	0	0	1	random	1
Birth rate (births/woman/year)	Birth rate (births per woman per year)	birth	birth	(0, 'maxrate')	fpop	timepar	meta	other	0	0	1	random	1
Male circumcision prevalence	Percentage of males who have been circumcised	propcirc	propcirc	(0, 1)	mpop	timepar	meta	other	0	0	1	random	1
Number of circumcisions	None	numcirc	numcirc	(0, 'maxpopsize')	mpop	timepar	no	other	0	1	1	additive	0
Number of PWID on OST	Number of people who inject drugs who are on opiate substitution therapy	numost	numost	(0, 'maxpopsize')	tot	timepar	meta	other	0	1	1	random	1
Probability of needle sharing (per injection)	Average percentage of people who receptively shared a needle/syringe at last injection	sharing	sharing	(0, 1)	pop	timepar	meta	other	0	0	1	random	1
Proportion of people on PrEP	Percentage of people covered by pre-exposure prophylaxis	prep	prep	(0, 1)	pop	timepar	meta	other	0	0	1	random	1
Number of regular acts (acts/year)	Average number of acts with regular partners per person per year	actsreg	numactsreg	(0, 'maxacts')	pship	timepar	meta	other	0	0	1	random	1
Number of casual acts (acts/year)	Average number of acts with casual partners per person per year	actscas	numactscas	(0, 'maxacts')	pship	timepar	meta	other	0	0	1	random	1
Number of commercial acts (acts/year)	Average number of acts with commercial partners per person per year	actscom	numactscom	(0, 'maxacts')	pship	timepar	meta	other	0	0	1	random	1
Number of injecting acts (injections/year)	Average number of injections per person per year	actsinj	numactsinj	(0, 'maxacts')	pship	timepar	meta	other	0	0	1	random	1
Condom use for regular acts	Percentage of people who used a condom at last act with regular partners	condreg	condomreg	(0, 1)	pship	timepar	meta	other	0	0	1	random	1
Condom use for casual acts	Percentage of people who used a condom at last act with casual partners	condcas	condomcas	(0, 1)	pship	timepar	meta	other	0	0	1	random	1
Condom use for commercial acts	Percentage of people who used a condom at last act with commercial partners	condcom	condomcom	(0, 1)	pship	timepar	meta	other	0	0	1	random	1
Average time taken to be linked to care (years)	Average time taken to be linked to care (years)	linktocare	linktocare	(0, 'maxduration')	pop	timepar	meta	cascade	1	0	1	random	1
Average time taken to be linked to care for people with CD4<200 (years)	Average time taken to be linked to care for people with CD4<200 (years)	aidslinktocare	aidslinktocare	(0, 'maxduration')	tot	timepar	meta	cascade	1	0	1	random	1
Viral load monitoring (number/year)	Viral load monitoring (number/year)	freqvlmon	freqvlmon	(0, 'maxrate')	tot	timepar	meta	cascade	1	0	1	random	1
Loss to follow-up rate (per year)	Percentage of people in care who are lost to follow-up per year (%/year)	leavecare	leavecare	(0, 'maxrate')	pop	timepar	meta	cascade	1	0	1	random	1
AIDS loss to follow-up rate (per year)	Percentage of people with CD4<200 lost to follow-up (%/year)	aidsleavecare	aidsleavecare	(0, 'maxrate')	tot	timepar	meta	cascade	1	0	1	random	1
PLHIV aware of their status	None	propdx	propdx	(0, 1)	tot	timepar	no	other	0	0	1	None	0
Diagnosed PLHIV in care	None	propcare	propcare	(0, 1)	tot	timepar	no	other	1	0	1	None	0
PLHIV in care on treatment	None	proptx	proptx	(0, 1)	tot	timepar	no	other	0	0	1	None	0
People on ART with viral suppression	None	propsupp	propsupp	(0, 1)	tot	timepar	no	other	1	0	1	None	0
Pregnant women and mothers on PMTCT	None	proppmtct	proppmtct	(0, 1)	tot	timepar	no	other	0	0	1	None	0
Male-female insertive transmissibility (per act)	constant	transmfi	transmfi	(0, 1)	tot	constant	const	const	0	None	0	None	1
Male-female receptive transmissibility (per act)	constant	transmfr	transmfr	(0, 1)	tot	constant	const	const	0	None	0	None	1
Male-male insertive transmissibility (per act)	constant	transmmi	transmmi	(0, 1)	tot	constant	const	const	0	None	0	None	1
Male-male receptive transmissibility (per act)	constant	transmmr	transmmr	(0, 1)	tot	constant	const	const	0	None	0	None	1
Injection-related transmissibility (per injection)	constant	transinj	transinj	(0, 1)	tot	constant	const	const	0	None	0	None	1
Mother-to-child breastfeeding transmissibility	constant	mtctbreast	mtctbreast	(0, 1)	tot	constant	const	const	0	None	0	None	1
Mother-to-child no-breastfeeding transmissibility	constant	mtctnobreast	mtctnobreast	(0, 1)	tot	constant	const	const	0	None	0	None	1
Relative transmissibility for acute HIV (unitless)	constant	cd4transacute	cd4transacute	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None	1
Relative transmissibility for CD4>500 (unitless)	constant	cd4transgt500	cd4transgt500	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None	1
Relative transmissibility for CD4>350 (unitless)	constant	cd4transgt350	cd4transgt350	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None	1
Relative transmissibility for CD4>200 (unitless)	constant	cd4transgt200	cd4transgt200	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None	1
Relative transmissibility for CD4>50 (unitless)	constant	cd4transgt50	cd4transgt50	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None	1
Relative transmissibility for CD4<50 (unitless)	constant	cd4translt50	cd4translt50	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None	1
Relative transmissibility with STIs (unitless)	constant	effsti	effsti	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None	1
Progression time from acute HIV (years)	constant	progacute	progacute	(0, 'maxduration')	tot	constant	const	const	0	None	0	None	1
Progression from CD4>500 (years)	constant	proggt500	proggt500	(0, 'maxduration')	tot	constant	const	const	0	None	0	None	1
Progression from CD4>350 (years)	constant	proggt350	proggt350	(0, 'maxduration')	tot	constant	const	const	0	None	0	None	1
Progression from CD4>200 (years)	constant	proggt200	proggt200	(0, 'maxduration')	tot	constant	const	const	0	None	0	None	1
Progression from CD4>50 (years)	constant	proggt50	proggt50	(0, 'maxduration')	tot	constant	const	const	0	None	0	None	1
Treatment recovery into CD4>500 (years)	constant	svlrecovgt350	svlrecovgt350	(0, 'maxduration')	tot	constant	const	const	0	None	0	None	1
Treatment recovery into CD4>350 (years)	constant	svlrecovgt200	svlrecovgt200	(0, 'maxduration')	tot	constant	const	const	0	None	0	None	1
Treatment recovery into CD4>200 (years)	constant	svlrecovgt50	svlrecovgt50	(0, 'maxduration')	tot	constant	const	const	0	None	0	None	1
Treatment recovery into CD4>50 (years)	constant	svlrecovlt50	svlrecovlt50	(0, 'maxduration')	tot	constant	const	const	0	None	0	None	1
Time after initiating ART to achieve viral suppression (years)	constant	treatvs	treatvs	(0, 'maxduration')	tot	constant	const	const	0	None	0	None	1
Progression from CD4>500 to CD4>350 on unsuppressive ART	constant	usvlproggt500	usvlproggt500	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Recovery from CD4>350 to CD4>500 on unsuppressive ART	constant	usvlrecovgt350	usvlrecovgt350	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Progression from CD4>350 to CD4>200 on unsuppressive ART	constant	usvlproggt350	usvlproggt350	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Recovery from CD4>200 to CD4>350 on unsuppressive ART	constant	usvlrecovgt200	usvlrecovgt200	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Progression from CD4>200 to CD4>50 on unsuppressive ART	constant	usvlproggt200	usvlproggt200	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Recovery from CD4>50 to CD4>200 on unsuppressive ART	constant	usvlrecovgt50	usvlrecovgt50	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Progression from CD4>50 to CD4<50 on unsuppressive ART	constant	usvlproggt50	usvlproggt50	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Recovery from CD4<50 to CD4>50 on unsuppressive ART	constant	usvlrecovlt50	usvlrecovlt50	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Treatment failure rate	constant	treatfail	treatfail	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Death rate for acute HIV (per year)	constant	deathacute	deathacute	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Death rate for CD4>500 (per year)	constant	deathgt500	deathgt500	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Death rate for CD4>350 (per year)	constant	deathgt350	deathgt350	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Death rate for CD4>200 (per year)	constant	deathgt200	deathgt200	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Death rate for CD4>50 (per year)	constant	deathgt50	deathgt50	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Death rate for CD4<50 (per year)	constant	deathlt50	deathlt50	(0, 'maxrate')	tot	constant	const	const	0	None	0	None	1
Relative death rate on suppressive ART (unitless)	constant	deathsvl	deathsvl	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None	1
Relative death rate on unsuppressive ART (unitless)	constant	deathusvl	deathusvl	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None	1
Relative death rate with tuberculosis (unitless)	constant	deathtb	deathtb	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None	1
Efficacy of unsuppressive ART	constant	efftxunsupp	efftxunsupp	(0, 1)	tot	constant	const	const	1	None	0	None	1
Efficacy of suppressive ART	constant	efftxsupp	efftxsupp	(0, 1)	tot	constant	const	const	1	None	0	None	1
Efficacy of PMTCT	constant	effpmtct	effpmtct	(0, 1)	tot	constant	const	const	0	None	0	None	1
Efficacy of PrEP	constant	effprep	effprep	(0, 1)	tot	constant	const	const	0	None	0	None	1
Efficacy of condoms	constant	effcondom	effcondom	(0, 1)	tot	constant	const	const	0	None	0	None	1
Efficacy of circumcision	constant	effcirc	effcirc	(0, 1)	tot	constant	const	const	0	None	0	None	1
Efficacy of OST	constant	effost	effost	(0, 1)	tot	constant	const	const	0	None	0	None	1
Efficacy of diagnosis for behavior change	constant	effdx	effdx	(0, 1)	tot	constant	const	const	0	None	0	None	1
Disutility of acute HIV	constant	disutilacute	disutilacute	(0, 1)	tot	constant	no	no	0	None	0	None	1
Disutility of CD4>500	constant	disutilgt500	disutilgt500	(0, 1)	tot	constant	no	no	0	None	0	None	1
Disutility of CD4>350	constant	disutilgt350	disutilgt350	(0, 1)	tot	constant	no	no	0	None	0	None	1
Disutility of CD4>200	constant	disutilgt200	disutilgt200	(0, 1)	tot	constant	no	no	0	None	0	None	1
Disutility of CD4>50	constant	disutilgt50	disutilgt50	(0, 1)	tot	constant	no	no	0	None	0	None	1
Disutility of CD4<50	constant	disutillt50	disutillt50	(0, 1)	tot	constant	no	no	0	None	0	None	1
Disutility on treatment	constant	disutiltx	disutiltx	(0, 1)	tot	constant	no	no	0	None	0	None	1
Number of HIV tests per year	Number of HIV tests per year	None	optnumtest	None	tot	None	no	no	0	None	0	None	1
Number of HIV diagnoses per year	Number of HIV diagnoses per year	None	optnumdiag	None	tot	None	no	no	0	None	0	None	1
Modeled estimate of new HIV infections per year	Modeled estimate of new HIV infections per year	None	optnuminfect	None	tot	None	no	no	0	None	0	None	1
Modeled estimate of HIV prevalence	Modeled estimate of HIV prevalence	None	optprev	None	tot	None	no	no	0	None	0	None	1
Modeled estimate of number of PLHIV	Modeled estimate of number of PLHIV	None	optplhiv	None	tot	None	no	no	0	None	0	None	1
Number of HIV-related deaths	Number of HIV-related deaths	None	optdeath	None	tot	None	no	no	0	None	0	None	1
Number of people initiating ART each year	Number of people initiating ART each year	None	optnewtreat	None	tot	None	no	no	0	None	0	None	1
PLHIV aware of their status (%)	PLHIV aware of their status (%)	None	optpropdx	None	tot	None	no	no	0	None	0	None	1
Diagnosed PLHIV in care (%)	Diagnosed PLHIV in care (%)	None	optpropcare	None	tot	None	no	no	0	None	0	None	1
PLHIV in care on treatment (%)	PLHIV in care on treatment (%)	None	optproptx	None	tot	None	no	no	0	None	0	None	1
Pregnant women on PMTCT (%)	Pregnant women on PMTCT (%)	None	optproppmtct	None	tot	None	no	no	0	None	0	None	1
People on ART with viral suppression (%)	People on ART with viral suppression (%)	None	optpropsupp	None	tot	None	no	no	0	None	0	None	1
Interactions between regular partners	Interactions between regular partners	partreg	partreg	None	tot	None	no	no	0	None	0	None	1
Interactions between casual partners	Interactions between casual partners	partcas	partcas	None	tot	None	no	no	0	None	0	None	1
Interactions between commercial partners	Interactions between commercial partners	partcom	partcom	None	tot	None	no	no	0	None	0	None	1
Interactions between people who inject drugs	Interactions between people who inject drugs	partinj	partinj	None	tot	None	no	no	0	None	0	None	1
'''


def loadpartable(inputpartable=None):
    ''' 
    Function to parse the parameter definitions above and return a structure that can be used to generate the parameters
    '''
    if inputpartable is None: inputpartable = partable # Use default defined one if not supplied as an input
    rawpars = []
    alllines = inputpartable.split('\n')[1:-1] # Load all data, and remove first and last lines which are empty
    for l in range(len(alllines)): alllines[l] = alllines[l].split('\t') # Remove end characters and split from tabs
    attrs = alllines.pop(0) # First line is attributes
    for l in range(len(alllines)): # Loop over parameters
        rawpars.append(dict()) # Create an odict to store attributes
        for i,attr in enumerate(attrs): # Loop over attributes
            try:
                if attr in ['limits', 'coverage', 'visible', 'cascade', 'fromdata']: alllines[l][i] = eval(alllines[l][i]) # Turn into actual values
                if alllines[l][i]=='None': alllines[l][i] = None # Turn any surviving 'None' values to actual None
                rawpars[l][attr] = alllines[l][i] # Store attributes
            except:
                errormsg = 'Error processing parameter line "%s"' % alllines[l]
                raise OptimaException(errormsg)
    return rawpars


#############################################################################################################################
### Define the allowable transitions!
##  NOTE, this should be consistent with the spreadsheet https://docs.google.com/spreadsheets/d/1ALJ3v8CXD7BkinGoUrfWPkxAg22l0PMTzWnMFldAYV0/edit?usp=sharing
##  Edit there, then copy and paste from there into here; include row and column numbers
#############################################################################################################################
transtable = '''
	0	1	2	3	4	5	6	7	8	9	10	11	12	13	14	15	16	17	18	19	20	21	22	23	24	25	26	27	28	29	30	31	32	33	34	35	36	37
0	1		1																																			
1		1	1																																			
2			1	1					1	1																												
3				1	1					1	1																											
4					1	1					1	1																										
5						1	1					1	1																									
6							1	1					1	1																								
7								1						1																								
8									1	1					1	1																						
9										1	1					1	1																					
10											1	1					1	1																				
11												1	1					1	1																			
12													1	1					1	1																		
13														1						1																		
14															1	1																	1	1				
15																1	1																	1	1			
16																	1	1																	1	1		
17																		1	1																	1	1	
18																			1	1																	1	1
19																				1																		1
20																					1	1					1	1					1	1				
21																						1	1					1	1					1	1			
22																						1	1	1				1	1	1				1	1	1		
23																							1	1	1				1	1	1				1	1	1	
24																								1	1	1				1	1	1				1	1	1
25																									1	1					1	1					1	1
26																					1	1					1	1					1	1				
27																						1						1						1				
28																						1	1					1	1					1	1			
29																							1	1					1	1					1	1		
30																								1	1					1	1					1	1	
31																									1	1					1	1					1	1
32															1	1																	1	1				
33																1	1																	1	1			
34																	1	1																	1	1		
35																		1	1																	1	1	
36																			1	1																	1	1
37																				1																		1
'''

def loadtranstable(npops=None,inputtranstable=None):
    ''' 
    Function to parse the parameter definitions above and return a structure that can be used to generate the parameters
    '''
    if inputtranstable is None: inputtranstable = transtable # Use default defined one if not supplied as an input
    if npops is None: npops = 1 # Use just one population if not told otherwise
    rawtransit = []
    alllines = inputtranstable.split('\n')[1:-1] # Load all data, and remove first and last lines which are empty
    for l in range(len(alllines)): alllines[l] = alllines[l].split('\t') # Remove end characters and split from tabs
    attrs = alllines.pop(0) # First line is tostates
    for l in range(len(alllines)): # Loop over all healthstates 
        rawtransit.append([[],[]]) # Create a list to store states that you can move to
        for i,attr in enumerate(attrs): # Loop over attributes
            try:
                if alllines[l][i] and attrs[i]:
                    rawtransit[l][0].append(int(attrs[i]))
                    rawtransit[l][1].append(ones(npops))
            except:
                errormsg = 'Error processing transition line "%s"' % alllines[l]
                raise OptimaException(errormsg)
        rawtransit[l][1] = array(rawtransit[l][1])
    return rawtransit




### Define the functions for handling the parameters

def grow(exponent, tvec):
    ''' Return a time vector for a population growth '''
    return exp(tvec*exponent) # Simple exponential growth



def getvalidyears(years, validdata, defaultind=0):
    ''' Return the years that are valid based on the validity of the input data '''
    if sum(validdata): # There's at least one data point entered
        if len(years)==len(validdata): # They're the same length: use for logical indexing
            validyears = array(array(years)[validdata]) # Store each year
        elif len(validdata)==1: # They're different lengths and it has length 1: it's an assumption
            validyears = array([array(years)[defaultind]]) # Use the default index; usually either 0 (start) or -1 (end)
    else: validyears = array([0.0]) # No valid years, return 0 -- NOT an empty array, as you might expect!
    return validyears



def data2prev(data=None, keys=None, index=0, blh=0, **defaultargs): # WARNING, "blh" means "best low high", currently upper and lower limits are being thrown away, which is OK here...?
    """ Take an array of data return either the first or last (...or some other) non-NaN entry -- used for initial HIV prevalence only so far... """
    par = Metapar(y=odict(), **defaultargs) # Create structure
    for row,key in enumerate(keys):
        par.y[key] = sanitize(data['hivprev'][blh][row])[index] # Return the specified index -- usually either the first [0] or last [-1]

    return par



def data2popsize(data=None, keys=None, blh=0, uniformgrowth=False, doplot=False, **defaultargs):
    ''' Convert population size data into population size parameters '''
    par = Popsizepar(m=1, **defaultargs)
    
    # Parse data into consistent form
    sanitizedy = odict() # Initialize to be empty
    sanitizedt = odict() # Initialize to be empty
    for row,key in enumerate(keys):
        sanitizedy[key] = sanitize(data['popsize'][blh][row]) # Store each extant value
        sanitizedt[key] = array(data['years'])[~isnan(data['popsize'][blh][row])] # Store each year
    
    # Store a list of population sizes that have at least 2 data points
    atleast2datapoints = [] 
    for key in keys:
        if len(sanitizedy[key])>=2:
            atleast2datapoints.append(key)
    if len(atleast2datapoints)==0:
        errormsg = 'Not more than one data point entered for any population size\n'
        errormsg += 'To estimate growth trends, at least one population must have at least 2 data points'
        raise OptimaException(errormsg)
        
    largestpopkey = atleast2datapoints[argmax([mean(sanitizedy[key]) for key in atleast2datapoints])] # Find largest population size (for at least 2 data points)
    
    # Perform 2-parameter exponential fit to data
    startyear = data['years'][0]
    par.start = data['years'][0]
    tdata = odict()
    ydata = odict()
    for key in atleast2datapoints:
        tdata[key] = sanitizedt[key]-startyear
        ydata[key] = log(sanitizedy[key])
        try:
            fitpars = polyfit(tdata[key], ydata[key], 1)
            par.i[key] = exp(fitpars[1]) # Intercept/initial value
            par.e[key] = fitpars[0] # Exponent
        except:
            errormsg = 'Fitting population size data for population "%s" failed' % key
            raise OptimaException(errormsg)
    
    # Handle populations that have only a single data point
    only1datapoint = list(set(keys)-set(atleast2datapoints))
    thisyear = odict()
    thispopsize = odict()
    for key in only1datapoint:
        largest_i = par.i[largestpopkey] # Get the parameters from the largest population
        largest_e = par.e[largestpopkey]
        if len(sanitizedt[key]) != 1:
            errormsg = 'Error interpreting population size for population "%s"\n' % key
            errormsg += 'Please ensure at least one time point is entered'
            raise OptimaException(errormsg)
        thisyear[key] = sanitizedt[key][0]
        thispopsize[key] = sanitizedy[key][0]
        largestthatyear = largest_i*grow(largest_e, thisyear[key]-startyear)
        par.i[key] = largest_i*thispopsize[key]/largestthatyear # Scale population size
        par.e[key] = largest_e[1] # Copy exponent
    par.i = par.i.sort(keys) # Sort to regain the original key order -- WARNING, causes horrendous problems later if this isn't done!
    par.e = par.e.sort(keys)
    
    if uniformgrowth:
        for key in keys:
            par.e[key] = par.e[largestpopkey] # Reset exponent to match the largest population
            meanpopulationsize = mean(sanitizedy[key]) # Calculate the mean of all the data
            weightedyear = mean(sanitizedy[key][:]*sanitizedt[key][:])/meanpopulationsize # Calculate the "mean year"
            par.i[key] = meanpopulationsize*(1+par.e[key])**(startyear-weightedyear) # Project backwards to starting population size
    
    if doplot:
        from pylab import figure, subplot, plot, scatter, arange, show, title
        nplots = len(par.keys())
        figure()
        tvec = arange(data['years'][0], data['years'][-1]+1)
        yvec = par.interp(tvec=tvec)
        for k,key in enumerate(par.keys()):
            subplot(nplots,1,k+1)
            if key in atleast2datapoints: scatter(tdata[key]+startyear, exp(ydata[key]))
            elif key in only1datapoint: scatter(thisyear[key], thispopsize[key])
            else: raise OptimaException('This population is nonexistent')
            plot(tvec, yvec[k])
            title('Pop size: ' + key)
            print([par.i[key], par.e[key]])
            show()
    
    return par



def data2timepar(data=None, keys=None, defaultind=0, verbose=2, **defaultargs):
    """ Take an array of data and turn it into default parameters -- here, just take the means """
    # Check that at minimum, name and short were specified, since can't proceed otherwise
    try: 
        name, short = defaultargs['name'], defaultargs['short']
    except: 
        errormsg = 'Cannot create a time parameter without keyword arguments "name" and "short"! \n\nArguments:\n %s' % defaultargs.items()
        raise OptimaException(errormsg)
        
    par = Timepar(m=1, y=odict(), t=odict(), **defaultargs) # Create structure
    for row,key in enumerate(keys):
        try:
            validdata = ~isnan(data[short][row]) # WARNING, this could all be greatly simplified!!!! Shouldn't need to call this and sanitize()
            par.t[key] = getvaliddata(data['years'], validdata, defaultind=defaultind) 
            if sum(validdata): 
                par.y[key] = sanitize(data[short][row])
            else:
                printv('data2timepar(): no data for parameter "%s", key "%s"' % (name, key), 3, verbose) # Probably ok...
                par.y[key] = array([0.0]) # Blank, assume zero -- WARNING, is this ok?
                par.t[key] = array([0.0])
        except:
            errormsg = 'Error converting time parameter "%s", key "%s"' % (name, key)
            raise OptimaException(errormsg)

    return par


## Acts
def balance(act=None, which=None, data=None, popkeys=None, limits=None, popsizepar=None, eps=None):
    ''' 
    Combine the different estimates for the number of acts or condom use and return the "average" value.
    
    Set which='numacts' to compute for number of acts, which='condom' to compute for condom.
    '''
    if eps is None: eps = Settings().eps   # If not supplied (it won't be), get from default settings  
    
    if which not in ['numacts','condom']: raise OptimaException('Can only balance numacts or condom, not "%s"' % which)
    mixmatrix = array(data['part'+act]) # Get the partnerships matrix
    npops = len(popkeys) # Figure out the number of populations
    symmetricmatrix = zeros((npops,npops));
    for pop1 in range(npops):
        for pop2 in range(npops):
            if which=='numacts': symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))
            if which=='condom': symmetricmatrix[pop1,pop2] = bool(symmetricmatrix[pop1,pop2] + mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1])
        
    # Decide which years to use -- use the earliest year, the latest year, and the most time points available
    yearstouse = []    
    for row in range(npops): yearstouse.append(getvaliddata(data['years'], data[which+act][row]))
    minyear = Inf
    maxyear = -Inf
    npts = 1 # Don't use fewer than 1 point
    for row in range(npops):
        minyear = minimum(minyear, min(yearstouse[row]))
        maxyear = maximum(maxyear, max(yearstouse[row]))
        npts = maximum(npts, len(yearstouse[row]))
    if minyear==Inf:  minyear = data['years'][0] # If not set, reset to beginning
    if maxyear==-Inf: maxyear = data['years'][-1] # If not set, reset to end
    ctrlpts = linspace(minyear, maxyear, npts).round() # Force to be integer...WARNING, guess it doesn't have to be?
    
    # Interpolate over population acts data for each year
    tmppar = data2timepar(name='tmp', short=which+act, limits=(0,'maxacts'), data=data, keys=popkeys, by='pop', verbose=0) # Temporary parameter for storing acts
    tmpsim = tmppar.interp(tvec=ctrlpts)
    if which=='numacts': popsize = popsizepar.interp(tvec=ctrlpts)
    npts = len(ctrlpts)
    
    # Compute the balanced acts
    output = zeros((npops,npops,npts))
    for t in range(npts):
        if which=='numacts':
            smatrix = dcp(symmetricmatrix) # Initialize
            psize = popsize[:,t]
            popacts = tmpsim[:,t]
            for pop1 in range(npops): smatrix[pop1,:] = smatrix[pop1,:]*psize[pop1] # Yes, this needs to be separate! Don't try to put in the next for loop, the indices are opposite!
            for pop1 in range(npops): smatrix[:,pop1] = psize[pop1]*popacts[pop1]*smatrix[:,pop1] / float(eps+sum(smatrix[:,pop1])) # Divide by the sum of the column to normalize the probability, then multiply by the number of acts and population size to get total number of acts
        
        # Reconcile different estimates of number of acts, which must balance
        thispoint = zeros((npops,npops));
        for pop1 in range(npops):
            for pop2 in range(npops):
                if which=='numacts':
                    balanced = (smatrix[pop1,pop2] * psize[pop1] + smatrix[pop2,pop1] * psize[pop2])/(psize[pop1]+psize[pop2]) # here are two estimates for each interaction; reconcile them here
                    thispoint[pop2,pop1] = balanced/psize[pop2] # Divide by population size to get per-person estimate
                    thispoint[pop1,pop2] = balanced/psize[pop1] # ...and for the other population
                if which=='condom':
                    thispoint[pop1,pop2] = (tmpsim[pop1,t]+tmpsim[pop2,t])/2.0
                    thispoint[pop2,pop1] = thispoint[pop1,pop2]
    
        output[:,:,t] = thispoint
    
    return output, ctrlpts








def makepars(data=None, label=None, verbose=2):
    """
    Translates the raw data (which were read from the spreadsheet) into
    parameters that can be used in the model. These data are then used to update 
    the corresponding model (project). This method should be called before a 
    simulation is run.
    
    Version: 2016jan14 by cliffk
    """
    
    printv('Converting data to parameters...', 1, verbose)
    
    
    ###############################################################################
    ## Loop over quantities
    ###############################################################################
    
    pars = odict()
    pars['label'] = label # Add optional label, default None
    
    # Shorten information on which populations are male, which are female, which inject, which provide commercial sex
    pars['male'] = array(data['pops']['male']).astype(bool) # Male populations 
    pars['female'] = array(data['pops']['female']).astype(bool) # Female populations
    
    # Set up keys
    totkey = ['tot'] # Define a key for when not separated by population
    popkeys = data['pops']['short'] # Convert to a normal string and to lower case...maybe not necessary
    fpopkeys = [popkey for popno,popkey in enumerate(popkeys) if data['pops']['female'][popno]]
    mpopkeys = [popkey for popno,popkey in enumerate(popkeys) if data['pops']['male'][popno]]
    pars['popkeys'] = dcp(popkeys)
    
    # Read in parameters automatically
    rawpars = loadpartable() # Read the parameters structure
    pars['rawtransit'] = loadtranstable(npops=len(popkeys)) # Read the transitions
    
    for rawpar in rawpars: # Iterate over all automatically read in parameters
        printv('Converting data parameter "%s"...' % rawpar['short'], 3, verbose)
        
        # Shorten key variables
        partype = rawpar.pop('partype')
        parname = rawpar['short']
        by = rawpar['by']
        fromdata = rawpar['fromdata']
        rawpar['verbose'] = verbose # Easiest way to pass it in
        
        
        # Decide what the keys are
        if by=='tot': keys = totkey
        elif by=='pop': keys = popkeys
        elif by=='fpop': keys = fpopkeys
        elif by=='mpop': keys = mpopkeys
        else: keys = [] # They're not necessarily empty, e.g. by partnership, but too complicated to figure out here
        if by in ['fpop', 'mpop']: rawpar['by'] = 'pop' # Reset, since no longer needed
        
        # Decide how to handle it based on parameter type
        if partype=='initprev': # Initialize prevalence only
            pars['initprev'] = data2prev(data=data, keys=keys, **rawpar) # Pull out first available HIV prevalence point
        
        elif partype=='popsize': # Population size only
            pars['popsize'] = data2popsize(data=data, keys=keys, **rawpar)
        
        elif partype=='timepar': # Otherwise it's a regular time par, made from data
            if fromdata: pars[parname] = data2timepar(data=data, keys=keys, **rawpar) 
            else: pars[parname] = Timepar(m=1, y=odict({key:array([nan]) for key in keys}), t=odict({key:array([0.0]) for key in keys}), **rawpar) # Create structure
        
        elif partype=='constant': # The constants, e.g. transmfi
            best = data['const'][parname][0] 
            low = data['const'][parname][1] 
            high = data['const'][parname][2]
            prior = Dist({'dist':'uniform', 'pars':(low, high)}) # Convert to fractional limits
            pars[parname] = Constant(y=best, prior=prior, **rawpar)
        
        elif partype=='meta': # Force-of-infection and inhomogeneity and transitions
            pars[parname] = Metapar(y=odict(), **rawpar)
            
    
    ###############################################################################
    ## Tidy up -- things that can't be converted automatically
    ###############################################################################
    
    # Births rates. This parameter is coupled with the birth matrix defined below
    for key in list(set(popkeys)-set(fpopkeys)): # Births are only female: add zeros
        pars['birth'].y[key] = array([0.0])
        pars['birth'].t[key] = array([0.0])
    pars['birth'].y = pars['birth'].y.sort(popkeys) # Sort them so they have the same order as everything else
    pars['birth'].t = pars['birth'].t.sort(popkeys)
    
    # Birth transitions - these are stored as the proportion of transitions, which is constant, and is multiplied by time-varying birth rates in model.py
    npopkeys = len(popkeys)
    birthtransit = zeros((npopkeys,npopkeys))
    c = 0
    for pkno,popkey in enumerate(popkeys):
        if data['pops']['female'][pkno]: # WARNING, really ugly
            for colno,col in enumerate(data['birthtransit'][c]):
                if sum(data['birthtransit'][c]):
                    birthtransit[pkno,colno] = col/sum(data['birthtransit'][c])
            c += 1
    pars['birthtransit'] = birthtransit 

    # Aging transitions - these are time-constant
    agetransit = zeros((npopkeys,npopkeys))
    duration = array([age[1]-age[0]+1.0 for age in data['pops']['age']])
    for rowno,row in enumerate(data['agetransit']):
        if sum(row):
            for colno,colval in enumerate(row):
                if colval:
                    agetransit[rowno,colno] = sum(row)*duration[rowno]/colval
    pars['agetransit'] = agetransit

    # Risk transitions - these are time-constant
    pars['risktransit'] = array(data['risktransit'])
    
    # Circumcision
    for key in list(set(popkeys)-set(mpopkeys)): # Circumcision is only male
        pars['propcirc'].y[key] = array([0.0])
        pars['propcirc'].t[key] = array([0.0])
        pars['numcirc'].y[key]  = array([0.0])
        pars['numcirc'].t[key]  = array([0.0])
    pars['propcirc'].y = pars['propcirc'].y.sort(popkeys) # Sort them so they have the same order as everything else
    pars['propcirc'].t = pars['propcirc'].t.sort(popkeys)
    pars['numcirc'].y = pars['numcirc'].y.sort(popkeys) # Sort them so they have the same order as everything else
    pars['numcirc'].t = pars['numcirc'].t.sort(popkeys)
    for key in pars['numcirc'].y.keys():
        pars['numcirc'].y[key] = array([0.0]) # Set to 0 for all populations, since program parameter only

    # Metaparameters
    for key in popkeys: # Define values
        pars['force'].y[key] = 1.0
        pars['inhomo'].y[key] = 0.0        
    
    tmpacts = odict()
    tmpcond = odict()
    tmpactspts = odict()
    tmpcondpts = odict()
    for act in ['reg','cas','com', 'inj']: # Number of acts
        actsname = 'acts'+act
        tmpacts[act], tmpactspts[act] = balance(act=act, which='numacts', data=data, popkeys=popkeys, popsizepar=pars['popsize'])
    for act in ['reg','cas','com']: # Condom use
        condname = 'cond'+act
        tmpcond[act], tmpcondpts[act] = balance(act=act, which='condom', data=data, popkeys=popkeys)
        
    # Convert matrices to lists of of population-pair keys
    for act in ['reg', 'cas', 'com', 'inj']: # Will probably include birth matrices in here too...
        actsname = 'acts'+act
        condname = 'cond'+act
        for i,key1 in enumerate(popkeys):
            for j,key2 in enumerate(popkeys):
                if sum(array(tmpacts[act])[i,j,:])>0:
                    pars[actsname].y[(key1,key2)] = array(tmpacts[act])[i,j,:]
                    pars[actsname].t[(key1,key2)] = array(tmpactspts[act])
                    if act!='inj':
                        if i>=j:
                            pars[condname].y[(key1,key2)] = array(tmpcond[act])[i,j,:]
                            pars[condname].t[(key1,key2)] = array(tmpcondpts[act])
    
    # Store information about injecting and commercial sex providing populations -- needs to be here since relies on other calculations
    pars['injects'] = array([pop in [pop1 for (pop1,pop2) in pars['actsinj'].y.keys()] for pop in pars['popkeys']])
    pars['sexworker'] = array([pop in [pop1 for (pop1,pop2) in pars['actscom'].y.keys() if pop1 in fpopkeys] for pop in pars['popkeys']])

    return pars


    
        



def makesimpars(pars, keys=None, start=None, end=None, dt=None, tvec=None, settings=None, smoothness=None, asarray=True, sample=None, onlyvisible=False, verbose=2, name=None, uid=None):
    ''' 
    A function for taking a single set of parameters and returning the interpolated versions -- used
    very directly in Parameterset.
    
    Version: 2016jun
    '''
    
    # Handle inputs and initialization
    simpars = odict() 
    simpars['parsetname'] = name
    simpars['parsetuid'] = uid
    generalkeys = ['male', 'female', 'popkeys', 'injects', 'sexworker', 'rawtransit']
    staticmatrixkeys = ['birthtransit','agetransit','risktransit']
    if start is None: start=2000 # WARNING, should be a better way of declaring defaults...
    if end is None: end=2030
    if dt is None: dt=0.2
    if keys is None: keys = pars.keys() # Just get all keys
    if type(keys)==str: keys = [keys] # Listify if string
    if tvec is not None: simpars['tvec'] = tvec
    elif settings is not None: simpars['tvec'] = settings.maketvec()
    else: simpars['tvec'] = linspace(start, end, round((end-start)/dt)+1) # Store time vector with the model parameters -- use linspace rather than arange because Python can't handle floats properly
    if len(simpars['tvec'])>1: dt = simpars['tvec'][1] - simpars['tvec'][0] # Recalculate dt since must match tvec
    simpars['dt'] = dt  # Store dt
    if smoothness is None: smoothness = int(defaultsmoothness/dt)
    
    # Copy default keys by default
    for key in generalkeys: simpars[key] = dcp(pars[key])
    for key in staticmatrixkeys: simpars[key] = dcp(array(pars[key]))

    # Loop over requested keys
    for key in keys: # Loop over all keys
        if issubclass(type(pars[key]), Par): # Check that it is actually a parameter -- it could be the popkeys odict, for example
            simpars[key] = pars[key].interp(tvec=simpars['tvec'], dt=dt, smoothness=smoothness, asarray=asarray, sample=sample)
            try: 
                if pars[key].visible or not(onlyvisible): # Optionally only show user-visible parameters
                    simpars[key] = pars[key].interp(tvec=simpars['tvec'], dt=dt, smoothness=smoothness, asarray=asarray) # WARNING, want different smoothness for ART
            except OptimaException as E: 
                errormsg = 'Could not figure out how to interpolate parameter "%s"' % key
                errormsg += 'Error: "%s"' % E.message
                raise OptimaException(errormsg)


    return simpars





def applylimits(y, par=None, limits=None, dt=None, warn=True, verbose=2):
    ''' 
    A function to intelligently apply limits (supplied as [low, high] list or tuple) to an output.
    
    Needs dt as input since that determines maxrate.
    
    Version: 2016jan30
    '''
    
    # If parameter object is supplied, use it directly
    parname = ''
    if par is not None:
        if limits is None: limits = par.limits
        parname = par.name
        
    # If no limits supplied, don't do anything
    if limits is None:
        printv('No limits supplied for parameter "%s"' % parname, 4, verbose)
        return y
    
    if dt is None:
        if warn: raise OptimaException('No timestep specified: required for convertlimits()')
        else: dt = 0.2 # WARNING, should probably not hard code this, although with the warning, and being conservative, probably OK
    
    # Convert any text in limits to a numerical value
    limits = convertlimits(limits=limits, dt=dt, verbose=verbose)
    
    # Apply limits, preserving original class -- WARNING, need to handle nans
    if isnumber(y):
        if isnan(y): return y # Give up
        newy = median([limits[0], y, limits[1]])
        if warn and newy!=y: printv('Note, parameter value "%s" reset from %f to %f' % (parname, y, newy), 3, verbose)
    elif shape(y):
        newy = array(y) # Make sure it's an array and not a list
        naninds = findinds(isnan(newy))
        if len(naninds): newy[naninds] = limits[0] # Temporarily reset -- value shouldn't matter
        newy[newy<limits[0]] = limits[0]
        newy[newy>limits[1]] = limits[1]
        newy[naninds] = nan # And return to nan
        if warn and any(newy!=array(y)):
            printv('Note, parameter "%s" value reset from:\n%s\nto:\n%s' % (parname, y, newy), 3, verbose)
    else:
        if warn: raise OptimaException('Data type "%s" not understood for applying limits for parameter "%s"' % (type(y), parname))
        else: newy = array(y)
    
    if shape(newy)!=shape(y):
        errormsg = 'Something went wrong with applying limits for parameter "%s":\ninput and output do not have the same shape:\n%s vs. %s' % (parname, shape(y), shape(newy))
        raise OptimaException(errormsg)
    
    return newy





def comparepars(pars1=None, pars2=None):
    ''' 
    Function to compare two sets of pars. Example usage:
    comparepars(P.parsets[0], P.parsets[1])
    '''
    if type(pars1)==Parameterset: pars1 = pars1.pars # If parset is supplied instead of pars, use that instead
    if type(pars2)==Parameterset: pars2 = pars2.pars
    keys = pars1.keys()
    nkeys = 0
    count = 0
    for key in keys:
        if hasattr(pars1[key],'y'):
            nkeys += 1
            if str(pars1[key].y) != str(pars2[key].y): # Convert to string representation for testing equality
                count += 1
                msg = 'Parameter "%s" differs:\n' % key
                msg += '%s\n' % pars1[key].y
                msg += 'vs\n'
                msg += '%s\n' % pars2[key].y
                msg += '\n\n'
                print(msg)
    if count==0: print('All %i parameters match' % nkeys)
    else:        print('%i of %i parameters did not match' % (count, nkeys))
    return None



def comparesimpars(pars1=None, pars2=None, inds=Ellipsis, inds2=Ellipsis):
    ''' 
    Function to compare two sets of simpars, like what's stored in results.
    comparesimpars(P.results[0].simpars[0][0], Q.results[0].simpars[0])
    '''
    keys = pars1.keys()
    nkeys = 0
    count = 0
    for key in keys:
        nkeys += 1
        thispar1 = pars1[key]
        thispar2 = pars2[key]
        if isinstance(thispar1,dict): keys2 = thispar1.keys()
        else: keys2 = [None]
        for key2 in keys2:
            if key2 is not None:
                this1 = array(thispar1[key2])
                this2 = array(thispar2[key2])
                key2str = '(%s)' % str(key2)
            else:
                this1 = array(thispar1)
                this2 = array(thispar2)
                key2str = ''
            if len(shape(this1))==2:
                pars1str = str(this1[inds2][inds])
                pars2str = str(this2[inds2][inds])
            elif len(shape(this1))==1:
                pars1str = str(this1[inds])
                pars2str = str(this2[inds])
            else:
                pars1str = str(this1)
                pars2str = str(this2)
            if pars1str != pars2str: # Convert to string representation for testing equality
                count += 1
                msg = 'Parameter "%s" %s differs:\n' % (key, key2str)
                msg += '%s\n' % pars1str
                msg += 'vs\n'
                msg += '%s\n' % pars2str
                msg += '\n\n'
                print(msg)
    if count==0: print('All %i parameters match' % nkeys)
    else:        print('%i of %i parameters did not match' % (count, nkeys))
    return None





#################################################################################################################################
### Define the classes
#################################################################################################################################

class Dist(object):
    ''' Define a distribution object for drawing samples from, usually to create a prior '''
    def __init__(self, dist=None, pars=None):
        defaultdist = 'uniform'
        defaultpars = (0.9, 1.1)
        self.dist = dist if dist is not None else defaultdist
        self.pars = pars if pars is not None else defaultpars
    
    def sample(self, n=1, randseed=None):
        ''' Draw random samples from the specified distribution '''
        if randseed is not None: seed(randseed) # Reset the random seed, if specified
        if self.dist=='uniform':
            samples = random(n)
            samples = samples * (self.pars[1] - self.pars[0])  + self.pars[0] # Scale to correct range
            return samples
        else:
            errormsg = 'Distribution "%s" not defined; available choices are: uniform or bust, bro!' % self.dist
            raise OptimaException(errormsg)


class Par(object):
    '''
    The base class for epidemiological model parameters.
    
    There are four subclasses:
        * Constant objects store a single scalar value in y and an uncertainty sample in ysample -- e.g., transmfi
        * Metapar objects store an odict of y values, have a single metaparameter m, and an odict of ysample -- e.g., force
        * Timepar objects store an odict of y values, have a single metaparameter m, and uncertainty scalar msample -- e.g., condcas
        * Popsizepar objects are like Timepar objects except have odicts of i (intercept) and e (exponent) values
    
    These four thus have different structures (where [] denotes dict):
        * Constants   have y, ysample
        * Metapars    have y[], ysample[], m, msample
        * Timepars    have y[], m, msample
        * Popsizepars have i[], e[], m, msample
    
    Consequently, some of them have different sample() and interp() methods; in brief:
        * Constants have sample() = ysample, interp() = y
        * Metapars have sample() = ysample[] & msample, interp() = m*y[]
        * Timepars have sample() = msample, interp() = m*y[]
        * Popsizepars have sample() = msample, interp() = m*i[]*exp(e[])
    
    Version: 2016nov06 by cliffk    
    '''
    def __init__(self, name=None, dataname=None, short=None, datashort=None, m=1., limits=(0.,1.), prior=None, by=None, fittable='', auto='', cascade=False, coverage=None, visible=0, proginteract=None, fromdata=None, verbose=None, **defaultargs): # "type" data needed for parameter table, but doesn't need to be stored
        ''' To initialize with a prior, prior should be a dict with keys 'dist' and 'pars' '''
        self.name = name # The full name, e.g. "HIV testing rate"
        self.short = short # The short name, e.g. "hivtest"
        self.dataname = dataname # The name used in the spreadsheet, e.g. "Percentage of population tested for HIV in the last 12 months"
        self.datashort = datashort # The short name used for the data, e.g. "numactsreg" (which may be different to the paramter name, e.g. "actsreg")
        self.m = m # Multiplicative metaparameter, e.g. 1
        self.msample = None # The latest sampled version of the metaparameter -- None unless uncertainty has been run, and only used for uncertainty runs 
        self.limits = limits # The limits, e.g. (0,1) -- a tuple since immutable
        self.by = by # Whether it's by population, partnership, or total
        self.fittable = fittable # Whether or not this parameter can be manually fitted: options are '', 'meta', 'pop', 'exp', etc...
        self.auto = auto # Whether or not this parameter can be automatically fitted -- see parameter definitions above for possibilities; used in calibration.py
        self.cascade = cascade # Whether or not it's a cascade parameter
        self.coverage = coverage # Whether or not this is a coverage parameter
        self.visible = visible # Whether or not this parameter is visible to the user in scenarios and programs
        self.proginteract = proginteract # How multiple programs with this parameter interact
        self.fromdata = fromdata # Whether or not the parameter is made from data
        if prior is None:             self.prior = Dist() # Not supplied, create default distribution
        elif isinstance(prior, dict): self.prior = Dist(**prior) # Supplied as a dict, use it to create a distribution
        elif isinstance(prior, Dist): self.prior = prior # Supplied as a distribution, use directly
        else:
            errormsg = 'Prior must either be None, a Dist, or a dict with keys "dist" and "pars", not %s' % type(prior)
            raise OptimaException(errormsg)
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = defaultrepr(self)
        return output
    




class Constant(Par):
    ''' The definition of a single constant parameter, which may or may not vary by population '''
    
    def __init__(self, y=None, **defaultargs):
        Par.__init__(self, **defaultargs)
        del self.m # These don't exist for the Constant class
        del self.msample 
        self.y = y # y-value data, e.g. 0.3
        self.ysample = None
    
    def keys(self):
        ''' Constants don't have any keys '''
        return None 
    
    def sample(self, n=1, randseed=None, overwrite=False, output=False):
        ''' Recalculate msample (if n=1), or return a list of samples from the prior (if n>1) -- not used for Constants '''
        if overwrite or self.ysample is None:
            ysample = self.prior.sample(n=n, randseed=randseed)
            self.ysample = self.ysample[0] # Want a scalar, not an array (even though it shouldn't matter for n=1)
        if output: return ysample
        else:      return None
    
    def updateprior(self):
        ''' Update the prior parameters to match the metaparameter, so e.g. can recalibrate and then do uncertainty '''
        if self.prior.dist=='uniform':
            tmppars = array(self.prior.pars) # Convert to array for numerical magic
            self.prior.pars = tuple(self.y*tmppars/tmppars.mean()) # Recenter the limits around the mean
        else:
            errormsg = 'Distribution "%s" not defined; available choices are: uniform or bust, bro!' % self.dist
            raise OptimaException(errormsg)
        return None
    
    def interp(self, tvec=None, dt=None, smoothness=None, asarray=True, sample=False, randseed=None): # Keyword arguments are for consistency but not actually used
        """ Take parameters and turn them into model parameters -- here, just return a constant value at every time point """
        dt = gettvecdt(tvec=tvec, dt=dt, justdt=True) # Method for getting dt
        if sample: 
            if self.ysample is None: self.sample(n=1,randseed=randseed) # msample doesn't exist, make it
            y = self.ysample
        else:
            y = self.y
        output = applylimits(par=self, y=y, limits=self.limits, dt=dt)
        if not asarray: output = odict([('tot',output)])
        return output



class Metapar(Par):
    ''' The definition of a single metaparameter, such as force of infection, which usually does vary by population '''
    
    def __init__(self, y=None, prior=None, **defaultargs):
        Par.__init__(self, **defaultargs)
        self.y = y # y-value data, e.g. {'FSW:'0.3, 'MSM':0.7}
        self.ysample = None
        if type(prior)==odict:
            self.prior = prior
        elif prior is None:
            self.prior = odict()
            for key in self.keys():
                self.prior[key] = Dist() # Initialize with defaults
        else:
            errormsg = 'Prior for metaparameters must be an odict, not %s' % type(prior)
            raise OptimaException(errormsg)
            
    def keys(self):
        ''' Return the valid keys for using with this parameter '''
        return self.y.keys()
    
    def sample(self, n=1, randseed=None):
        ''' Replace the current value of the value y (not the metaparameter!) with a sample from the prior '''
        for key in self.keys():
            self.ysample[key] = self.prior[key].sample(n=n, randseed=randseed) # Unlike other types of parameters, here we need to draw for each key

    
    def interp(self, tvec=None, dt=None, smoothness=None, asarray=True, sample=None, randseed=None): # Keyword arguments are for consistency but not actually used
        """ Take parameters and turn them into model parameters -- here, just return a constant value at every time point """
        
        dt = gettvecdt(tvec=tvec, dt=dt, justdt=True) # Method for getting dt
        
        if asarray: output = zeros(len(self.keys()))
        else: output = odict()
        for pop,key in enumerate(self.keys()): # Loop over each population, always returning an [npops x npts] array
            if sample is None: # Handle metaparameter and uncertainty -- has to be in the loop since depends on the key -- WARNING, KLUDGY
                meta = self.m
            else:
                try: meta = self.posterior[key][sample] # Pull a sample from the posterior
                except: 
                    errormsg ='Sample %i not allowed; length of posterior is %i' % (sample, len(self.posterior))
                    raise OptimaException(errormsg)
            yinterp = applylimits(par=self, y=self.y[key]*meta[key], limits=self.limits, dt=dt)
            if asarray: output[pop] = yinterp
            else: output[key] = yinterp
        return output
    




class Timepar(Par):
    ''' The definition of a single time-varying parameter, which may or may not vary by population '''
    
    def __init__(self, t=None, y=None, m=1., **defaultargs):
        Par.__init__(self, **defaultargs)
        if t is None: t = odict()
        if y is None: y = odict()
        self.t = t # Time data, e.g. [2002, 2008]
        self.y = y # Value data, e.g. [0.3, 0.7]
        self.m = m # Multiplicative metaparameter, e.g. 1
    
    def keys(self):
        ''' Return the valid keys for using with this parameter '''
        return self.y.keys()
    
    def interp(self, tvec=None, dt=None, smoothness=None, asarray=True, sample=None):
        """ Take parameters and turn them into model parameters """
        
        # Validate input
        if tvec is None: 
            errormsg = 'Cannot interpolate parameter "%s" with no time vector specified' % self.name
            raise OptimaException(errormsg)
        tvec, dt = gettvecdt(tvec=tvec, dt=dt) # Method for getting these as best possible
        if smoothness is None: smoothness = int(defaultsmoothness/dt) # Handle smoothness
        meta = self.choosemeta(self, sample)
        
        # Set things up and do the interpolation
        keys = self.keys()
        npops = len(keys)
        if self.by=='pship': asarray= False # Force odict since too dangerous otherwise
        if asarray: output = zeros((npops,len(tvec)))
        else: output = odict()
        for pop,key in enumerate(keys): # Loop over each population, always returning an [npops x npts] array
            yinterp = meta * smoothinterp(tvec, self.t[pop], self.y[pop], smoothness=smoothness) # Use interpolation
            yinterp = applylimits(par=self, y=yinterp, limits=self.limits, dt=dt)
            if asarray: output[pop,:] = yinterp
            else: output[key] = yinterp
        if npops==1 and self.by=='tot' and asarray: return output[0,:] # npops should always be 1 if by==tot, but just be doubly sure
        else: return output






class Popsizepar(Par):
    ''' The definition of the population size parameter '''
    
    def __init__(self, i=None, e=None, m=1., start=2000., **defaultargs):
        Par.__init__(self, **defaultargs)
        if i is None: i = odict()
        if e is None: e = odict()
        self.i = i # Exponential fit intercept, e.g. 3.4e6
        self.e = e # Exponential fit exponent, e.g. 0.03
        self.m = m # Multiplicative metaparameter, e.g. 1
        self.start = start # Year for which population growth start is calibrated to
    
    def keys(self):
        ''' Return the valid keys for using with this parameter '''
        return self.i.keys()

    def interp(self, tvec=None, dt=None, smoothness=None, asarray=True, sample=None): # WARNING: smoothness isn't used, but kept for consistency with other methods...
        """ Take population size parameter and turn it into a model parameters """
        
        # Validate input
        if tvec is None: 
            errormsg = 'Cannot interpolate parameter "%s" with no time vector specified' % self.name
            raise OptimaException(errormsg)
        tvec, dt = gettvecdt(tvec=tvec, dt=dt) # Method for getting these as best possible
        
        # Do interpolation
        keys = self.keys()
        npops = len(keys)
        if asarray: output = zeros((npops,len(tvec)))
        else: output = odict()
        meta = self.choosemeta(self, sample)
        for pop,key in enumerate(keys):
            yinterp = meta * self.i * grow(self.e[key], array(tvec)-self.start)
            yinterp = applylimits(par=self, y=yinterp, limits=self.limits, dt=dt)
            if asarray: output[pop,:] = yinterp
            else: output[key] = yinterp
        return output












class Parameterset(object):
    ''' Class to hold all parameters and information on how they were generated, and perform operations on them'''
    
    def __init__(self, name='default', project=None, progsetname=None, budget=None):
        self.name = name # Name of the parameter set, e.g. 'default'
        self.uid = uuid() # ID
        self.project = project # Store pointer for the project, if available
        self.created = today() # Date created
        self.modified = today() # Date modified
        self.pars = None
        self.popkeys = [] # List of populations
        self.posterior = odict() # an odict, comparable to pars, for storing posterior values of m -- WARNING, not used yet
        self.resultsref = None # Store pointer to results
        self.progsetname = progsetname # Store the name of the progset that generated the parset, if any
        self.budget = budget # Store the budget that generated the parset, if any
        
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output  = defaultrepr(self)
        output += 'Parameter set name: %s\n'    % self.name
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        return output
    
    
    def getresults(self, die=True):
        ''' Method for getting the results '''
        if self.resultsref is not None and self.project is not None:
            results = getresults(project=self.project, pointer=self.resultsref, die=die)
            return results
        else:
            raise OptimaException('No results associated with this parameter set')
    
    
    def parkeys(self):
        ''' Return a list of the keys in pars that are actually parameter objects '''
        parslist = []
        for par,key in self.pars.items():
            if issubclass(type(par), Par):
                parslist.append(key)
        return parslist
    
    
    def getprop(self, proptype='proptreat', year=None, bypop=False, ind='best', die=False):
        ''' Method for getting proportions'''

        if self.resultsref is not None and self.project is not None:

            # Get results
            results = getresults(project=self.project, pointer=self.resultsref, die=die)
            if results is None: # Generate results if there aren't any and die is False (if die is true, it will've already died on the previous step)
                self.project.runsim(name=self.name)
                results = self.project.results[-1]
                

            # Interpret inputs
            if proptype in ['diag','dx','propdiag','propdx']: proptype = 'propdiag'
            elif proptype in ['evercare','everincare','propevercare','propeverincare']: proptype = 'propvercare'
            elif proptype in ['care','incare','propcare','propincare']: proptype = 'propincare'
            elif proptype in ['treat','tx','proptreat','proptx']: proptype = 'proptreat'
            elif proptype in ['supp','suppressed','propsupp','propsuppressed']: proptype = 'propsuppressed'
            else:
                raise OptimaException('Unknown proportion type %s' % proptype)
        
            if ind in ['median', 'm', 'best', 'b', 'average', 'av', 'single',0]: ind=0
            elif ind in ['lower','l','low',1]: ind=1
            elif ind in ['upper','u','up','high','h',2]: ind=2
            else: ind=0 # Return best estimate if can't understand whichone was requested
            
            timeindex = findinds(results.tvec,year) if year else Ellipsis

            if bypop:
                return results.main[proptype].pops[ind][:][timeindex]
            else:
                return results.main[proptype].tot[ind][timeindex]
                
        else:
            raise OptimaException('No results associated with this parameter set')
    
    
    def makepars(self, data=None, verbose=2):
        self.pars = makepars(data=data, verbose=verbose) # Initialize as list with single entry
        self.popkeys = dcp(self.pars['popkeys']) # Store population keys more accessibly
        return None


    def interp(self, keys=None, start=2000, end=2030, dt=0.2, tvec=None, smoothness=20, asarray=True, samples=None, onlyvisible=False, verbose=2):
        """ Prepares model parameters to run the simulation. """
        printv('Making model parameters...', 1, verbose),

        simparslist = []
        if isnumber(tvec): tvec = array([tvec]) # Convert to 1-element array -- WARNING, not sure if this is necessary or should be handled lower down
        if samples is None: sample = [None]
        for sample in samples:
            simpars = makesimpars(pars=self.pars, keys=keys, start=start, end=end, dt=dt, tvec=tvec, smoothness=smoothness, asarray=asarray, sample=sample, onlyvisible=onlyvisible, verbose=verbose, name=self.name, uid=self.uid)
            simparslist.append(simpars) # Wrap up
        
        return simparslist
    
    
    def printpars(self, output=False):
        outstr = ''
        count = 0
        for par in self.pars.values():
            if hasattr(par,'p'): print('WARNING, population size not implemented!')
            if hasattr(par,'y'):
                if hasattr(par.y, 'keys'):
                    count += 1
                    if len(par.y.keys())>1:
                        outstr += '%3i: %s\n' % (count, par.name)
                        for key in par.y.keys():
                            outstr += '     %s = %s\n' % (key, par.y[key])
                    elif len(par.y.keys())==1:
                        outstr += '%3i: %s = %s\n\n' % (count, par.name, par.y[0])
                    elif len(par.y.keys())==0:
                        outstr += '%3i: %s = (empty)' % (count, par.name)
                    else:
                        print('WARNING, not sure what to do with %s: %s' % (par.name, par.y))
                else:
                    count += 1
                    outstr += '%3i: %s = %s\n\n' % (count, par.name, par.y)
        print(outstr)
        if output: return outstr
        else: return None


    def listattributes(self):
        ''' Go through all the parameters and make a list of their possible attributes '''
        
        maxlen = 20
        pars = self.pars[0]
        
        print('\n\n\n')
        print('CONTENTS OF PARS, BY TYPE:')
        partypes = []
        for key in pars: partypes.append(type(pars[key]))
        partypes = set(partypes)
        count1 = 0
        count2 = 0
        for partype in set(partypes): 
            count1 += 1
            print('  %i..%s' % (count1, str(partype)))
            for key in pars:
                if type(pars[key])==partype:
                    count2 += 1
                    print('      %i.... %s' % (count2, str(key)))
        
        print('\n\n\n')
        print('ATTRIBUTES:')
        attributes = {}
        for key in self.parkeys():
            theseattr = pars[key].__dict__.keys()
            for attr in theseattr:
                if attr not in attributes.keys(): attributes[attr] = []
                attributes[attr].append(getattr(pars[key], attr))
        for key in attributes:
            print('  ..%s' % key)
        print('\n\n')
        for key in attributes:
            count = 0
            print('  ..%s' % key)
            items = []
            for item in attributes[key]:
                try: 
                    string = str(item)
                    if string not in items: 
                        if len(string)>maxlen: string = string[:maxlen]
                        items.append(string) 
                except: 
                    items.append('Failed to append item')
            for item in items:
                count += 1
                print('      %i....%s' % (count, str(item)))
        return None


    def manualfitlists(self, parsubset=None):
        ''' WARNING -- not sure if this function is needed; if it is needed, it should be combined with manualgui,py '''
        if not self.pars:
            raise OptimaException("No parameters available!")
    
        # Check parname subset is valid
        if parsubset is None:
            tmppars = self.pars
        else:
            if type(parsubset)==str: parsubset=[parsubset]
            if parsubset and type(parsubset) not in (list, str):
                raise OptimaException("Expecting parsubset to be a list or a string!")
            for item in parsubset:
                if item not in [par.short for par in self.pars.values() if hasattr(par,'fittable') and par.fittable!='no']:
                    raise OptimaException("Parameter %s is not a fittable parameter.")
            tmppars = {par.short:par for par in self.pars.values() if hasattr(par,'fittable') and par.fittable!='no' and par.short in parsubset}
            
        mflists = {'keys': [], 'subkeys': [], 'types': [], 'values': [], 'labels': []}
        keylist = mflists['keys']
        subkeylist = mflists['subkeys']
        typelist = mflists['types']
        valuelist = mflists['values']
        labellist = mflists['labels']

        for key in tmppars.keys():
            par = tmppars[key]
            if hasattr(par,
                       'fittable') and par.fittable != 'no':  # Don't worry if it doesn't work, not everything in tmppars is actually a parameter
                if par.fittable == 'meta':
                    keylist.append(key)
                    subkeylist.append(None)
                    typelist.append(par.fittable)
                    valuelist.append(par.m)
                    labellist.append('%s -- meta' % par.name)
                elif par.fittable == 'const':
                    keylist.append(key)
                    subkeylist.append(None)
                    typelist.append(par.fittable)
                    valuelist.append(par.y)
                    labellist.append(par.name)
                elif par.fittable in ['pop', 'pship']:
                    for subkey in par.y.keys():
                        keylist.append(key)
                        subkeylist.append(subkey)
                        typelist.append(par.fittable)
                        valuelist.append(par.y[subkey])
                        labellist.append('%s -- %s' % (par.name, str(subkey)))
                elif par.fittable == 'exp':
                    for subkey in par.p.keys():
                        keylist.append(key)
                        subkeylist.append(subkey)
                        typelist.append(par.fittable)
                        valuelist.append(par.i[subkey])
                        labellist.append('%s -- %s' % (par.name, str(subkey)))
                else:
                    print('Parameter type "%s" not implemented!' % par.fittable)
    
        return mflists
    
    
    ## Define update step
    def update(self, mflists):
        ''' Update Parameterset with new results -- WARNING, duplicates the function in gui.py!!!! '''
        if not self.pars:
            raise OptimaException("No parameters available!")
    
        tmppars = self.pars
    
        keylist = mflists['keys']
        subkeylist = mflists['subkeys']
        typelist = mflists['types']
        valuelist = mflists['values']
    
        ## Loop over all parameters and update them
        verbose = 0
        for (key, subkey, ptype, value) in zip(keylist, subkeylist, typelist, valuelist):
            if ptype == 'meta':  # Metaparameters
                vtype = type(tmppars[key].m)
                tmppars[key].m = vtype(value)
                printv('%s.m = %s' % (key, value), 4, verbose)
            elif ptype in ['pop', 'pship']:  # Populations or partnerships
                vtype = type(tmppars[key].y[subkey])
                tmppars[key].y[subkey] = vtype(value)
                printv('%s.y[%s] = %s' % (key, subkey, value), 4, verbose)
            elif ptype == 'exp':  # Population growth
                vtype = type(tmppars[key].i[subkey])
                tmppars[key].i[subkey] = vtype(value)
                printv('%s.i[%s] = %s' % (key, subkey, value), 4, verbose)
            elif ptype == 'const':  # Constants
                vtype = type(tmppars[key].y)
                tmppars[key].y = vtype(value)
                printv('%s.y = %s' % (key, value), 4, verbose)
            else:
                print('Parameter type "%s" not implemented!' % ptype)
    
                # parset.interp() and calculate results are supposed to be called from the outside
    
    def export(self, filename=None, compare=None):
        '''
        Little function to export code for the current parameter set. To use, do something like:
        
        pars = P.parsets[0].pars[0]
        
        and then paste in the output of this function.
        
        If compare is not None, then only print out parameter values that differ. Most useful for
        comparing to default, e.g.
        P.parsets[-1].export(compare='default')
        '''
        cpars, cvalues = None, None
        if compare is not None:
            try: 
                cpars = self.project.parsets[compare].pars
            except: 
                print('Could not compare parset %s to parset %s; printing all parameters' % (self.name, compare))
                compare = None
        
        def oneline(values): return str(values).replace('\n',' ') 
        
        output = ''
        for parname,par in self.pars.items():
            if hasattr(par,'fittable'):
                if par.fittable=='pop': 
                    values = par.y[:].tolist()
                    prefix = "pars['%s'].y[:] = " % parname
                    if cpars is not None: cvalues = cpars[parname].y[:].tolist()
                elif par.fittable=='const': 
                    values = par.y
                    prefix = "pars['%s'].y = " % parname
                    if cpars is not None: cvalues = cpars[parname].y
                elif par.fittable=='meta':
                    values = par.m
                    prefix = "pars['%s'].m = " % parname
                    if cpars is not None: cvalues = cpars[parname].m
                elif par.fittable=='no':
                    values = None
                else: 
                    print('Parameter fittable type "%s" not implemented' % par.fittable)
                    values = None
                if values is not None:
                    if compare is None or (values!=cvalues):
                        output += prefix+oneline(values)+'\n'
        
        if filename is not None:
            with open(filename, 'w') as f:
                f.write(output)
        else:
            return output
            
                