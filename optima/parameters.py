"""
This module defines the Timepar, Popsizepar, and Constant classes, which are 
used to define a single parameter (e.g., hivtest) and the full set of
parameters, the Parameterset class.

Version: 2016jan30
"""

from numpy import array, isnan, zeros, argmax, mean, log, polyfit, exp, maximum, minimum, Inf, linspace, median, shape
from optima import OptimaException, odict, printv, sanitize, uuid, today, getdate, smoothinterp, dcp, defaultrepr, objrepr # Utilities 
from optima import getresults, convertlimits, gettvecdt # Heftier functions

eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero when calculating acts
defaultsmoothness = 1.0 # The number of years of smoothing to do by default


#############################################################################################################################
### Define the parameters!
##  NOTE, this should be consistent with the spreadsheet http://optimamodel.com/file/parameters
##  Edit there, then copy and paste from there into here; be sure to include header row
#############################################################################################################################
partable = '''
name	short	limits	by	partype	fittable	auto	cascade	coverage	visible	proginteract
Initial HIV prevalence (%)	initprev	(0, 1)	pop	initprev	pop	init	0	None	0	None
Population size	popsize	(0, 'maxpopsize')	pop	popsize	exp	popsize	0	None	0	None
Force-of-infection (unitless)	force	(0, 'maxmeta')	pop	meta	pop	force	0	None	0	None
Inhomogeneity (unitless)	inhomo	(0, 'maxmeta')	pop	meta	pop	inhomo	0	None	0	None
Risk transitions (% moving/year)	risktransit	(0, 'maxrate')	array	meta	no	no	0	None	0	None
Age transitions (% moving/year)	agetransit	(0, 'maxrate')	array	meta	no	no	0	None	0	None
Birth transitions (% born into each population/year)	birthtransit	(0, 'maxrate')	array	meta	no	no	0	None	0	None
Mortality rate (%/year)	death	(0, 'maxrate')	pop	timepar	meta	other	0	0	1	random
HIV testing rate (%/year)	hivtest	(0, 'maxrate')	pop	timepar	meta	test	0	0	1	random
AIDS testing rate (%/year)	aidstest	(0, 'maxrate')	tot	timepar	meta	test	0	0	1	random
STI prevalence (%)	stiprev	(0, 1)	pop	timepar	meta	other	0	0	1	random
Tuberculosis prevalence (%)	tbprev	(0, 1)	pop	timepar	meta	other	0	0	1	random
Number of people on treatment	numtx	(0, 'maxpopsize')	tot	timepar	meta	treat	0	1	1	random
Number of people on PMTCT	numpmtct	(0, 'maxpopsize')	tot	timepar	meta	other	0	1	1	random
Proportion of women who breastfeed (%)	breast	(0, 1)	tot	timepar	meta	other	0	0	1	random
Birth rate (births/woman/year)	birth	(0, 'maxrate')	fpop	timepar	meta	other	0	0	1	random
Male circumcision prevalence (%)	circum	(0, 1)	mpop	timepar	meta	other	0	0	1	random
Number of PWID on OST	numost	(0, 'maxpopsize')	tot	timepar	meta	other	0	1	1	random
Probability of needle sharing (%/injection)	sharing	(0, 1)	pop	timepar	meta	other	0	0	1	random
Proportion of people on PrEP (%)	prep	(0, 1)	pop	timepar	meta	other	0	0	1	random
Number of regular acts (acts/year)	actsreg	(0, 'maxacts')	pship	timepar	meta	other	0	0	1	random
Number of casual acts (acts/year)	actscas	(0, 'maxacts')	pship	timepar	meta	other	0	0	1	random
Number of commercial acts (acts/year)	actscom	(0, 'maxacts')	pship	timepar	meta	other	0	0	1	random
Number of injecting acts (injections/year)	actsinj	(0, 'maxacts')	pship	timepar	meta	other	0	0	1	random
Condom use for regular acts (%)	condreg	(0, 1)	pship	timepar	meta	other	0	0	1	random
Condom use for casual acts (%)	condcas	(0, 1)	pship	timepar	meta	other	0	0	1	random
Condom use for commercial acts (%)	condcom	(0, 1)	pship	timepar	meta	other	0	0	1	random
People on ART with viral suppression (%)	successprop	(0, 1)	tot	timepar	meta	cascade	1	0	1	random
Immediate linkage to care (%)	immediatecare	(0, 1)	pop	timepar	meta	cascade	1	0	1	random
Viral suppression when initiating ART (%)	treatvs	(0, 1)	tot	timepar	meta	cascade	1	0	1	random
HIV-diagnosed people linked to care (%/year)	linktocare	(0, 'maxrate')	pop	timepar	meta	cascade	1	0	1	random
Viral load monitoring (number/year)	vlmonfr	(0, 'maxrate')	tot	timepar	meta	cascade	1	0	1	random
HIV-diagnosed people who are in care (%)	pdhivcare	(0, 1)	tot	timepar	meta	cascade	1	0	1	random
Rate of ART re-initiation (%/year)	restarttreat	(0, 'maxrate')	tot	timepar	meta	cascade	1	0	1	random
Rate of people on ART who stop (%/year)	stoprate	(0, 'maxrate')	pop	timepar	meta	cascade	1	0	1	random
People in care lost to follow-up (%/year)	leavecare	(0, 'maxrate')	pop	timepar	meta	cascade	1	0	1	random
Biological failure rate (%/year)	biofailure	(0, 'maxrate')	tot	timepar	meta	cascade	1	0	1	random
PLHIV aware of their status (%)	propdx	(0, 1)	tot	timepar	no	no	0	0	1	None
Diagnosed PLHIV in care (%)	propcare	(0, 1)	tot	timepar	no	no	1	0	1	None
PLHIV in care on treatment (%)	proptx	(0, 1)	tot	timepar	no	no	0	0	1	None
Male-female insertive transmissibility (per act)	transmfi	(0, 1)	tot	constant	const	const	0	None	0	None
Male-female receptive transmissibility (per act)	transmfr	(0, 1)	tot	constant	const	const	0	None	0	None
Male-male insertive transmissibility (per act)	transmmi	(0, 1)	tot	constant	const	const	0	None	0	None
Male-male receptive transmissibility (per act)	transmmr	(0, 1)	tot	constant	const	const	0	None	0	None
Injection-related transmissibility (per injection)	transinj	(0, 1)	tot	constant	const	const	0	None	0	None
Mother-to-child breastfeeding transmissibility (%)	mtctbreast	(0, 1)	tot	constant	const	const	0	None	0	None
Mother-to-child no-breastfeeding transmissibility (%)	mtctnobreast	(0, 1)	tot	constant	const	const	0	None	0	None
Relative transmissibility for acute HIV (unitless)	cd4transacute	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None
Relative transmissibility for CD4>500 (unitless)	cd4transgt500	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None
Relative transmissibility for CD4>350 (unitless)	cd4transgt350	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None
Relative transmissibility for CD4>200 (unitless)	cd4transgt200	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None
Relative transmissibility for CD4>50 (unitless)	cd4transgt50	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None
Relative transmissibility for CD4<50 (unitless)	cd4translt50	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None
Relative transmissibility with STIs (unitless)	effsti	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None
Progression rate for acute HIV (%/year)	progacute	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Progression rate for CD4>500 (%/year)	proggt500	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Progression rate for CD4>350 (%/year)	proggt350	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Progression rate for CD4>200 (%/year)	proggt200	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Progression rate for CD4>50 (%/year)	proggt50	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Treatment recovery rate into CD4>500 (%/year)	recovgt500	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Treatment recovery rate into CD4>350 (%/year)	recovgt350	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Treatment recovery rate into CD4>200 (%/year)	recovgt200	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Treatment recovery rate into CD4>50 (%/year)	recovgt50	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Death rate for acute HIV (%/year)	deathacute	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Death rate for CD4>500 (%/year)	deathgt500	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Death rate for CD4>350 (%/year)	deathgt350	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Death rate for CD4>200 (%/year)	deathgt200	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Death rate for CD4>50 (%/year)	deathgt50	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Death rate for CD4<50 (%/year)	deathlt50	(0, 'maxrate')	tot	constant	const	const	0	None	0	None
Relative death rate on treatment (unitless)	deathtreat	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None
Relative death rate with tuberculosis (unitless)	deathtb	(0, 'maxmeta')	tot	constant	const	const	0	None	0	None
Efficacy of unsuppressive ART (%)	efftxunsupp	(0, 1)	tot	constant	const	const	1	None	0	None
Efficacy of suppressive ART (%)	efftxsupp	(0, 1)	tot	constant	const	const	1	None	0	None
Efficacy of PMTCT (%)	effpmtct	(0, 1)	tot	constant	const	const	0	None	0	None
Efficacy of PrEP (%)	effprep	(0, 1)	tot	constant	const	const	0	None	0	None
Efficacy of condoms (%)	effcondom	(0, 1)	tot	constant	const	const	0	None	0	None
Efficacy of circumcision (%)	effcirc	(0, 1)	tot	constant	const	const	0	None	0	None
Efficacy of OST (%)	effost	(0, 1)	tot	constant	const	const	0	None	0	None
Efficacy of diagnosis for behavior change (%)	effdx	(0, 1)	tot	constant	const	const	0	None	0	None
Disutility of acute HIV (%)	disutilacute	(0, 1)	tot	constant	const	const	0	None	0	None
Disutility of CD4>500 (%)	disutilgt500	(0, 1)	tot	constant	const	const	0	None	0	None
Disutility of CD4>350 (%)	disutilgt350	(0, 1)	tot	constant	const	const	0	None	0	None
Disutility of CD4>200 (%)	disutilgt200	(0, 1)	tot	constant	const	const	0	None	0	None
Disutility of CD4>50 (%)	disutilgt50	(0, 1)	tot	constant	const	const	0	None	0	None
Disutility of CD4<50 (%)	disutillt50	(0, 1)	tot	constant	const	const	0	None	0	None
Disutility on treatment (%)	disutiltx	(0, 1)	tot	constant	const	const	0	None	0	None
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
                if attr in ['limits', 'coverage', 'visible']: alllines[l][i] = eval(alllines[l][i]) # Turn into actual values
                if alllines[l][i]=='None': alllines[l][i] = None # Turn any surviving 'None' values to actual None
                rawpars[l][attr] = alllines[l][i] # Store attributes
            except:
                errormsg = 'Error processing parameter line "%s"' % alllines[l]
                raise OptimaException(errormsg)
    return rawpars






### Define the functions for handling the parameters

def popgrow(exppars, tvec):
    ''' Return a time vector for a population growth '''
    return exppars[0]*exp(tvec*exppars[1]) # Simple exponential growth



def getvalidyears(years, validdata, defaultind=0):
    ''' Return the years that are valid based on the validity of the input data '''
    if sum(validdata): # There's at least one data point entered
        if len(years)==len(validdata): # They're the same length: use for logical indexing
            validyears = array(array(years)[validdata]) # Store each year
        elif len(validdata)==1: # They're different lengths and it has length 1: it's an assumption
            validyears = array([array(years)[defaultind]]) # Use the default index; usually either 0 (start) or -1 (end)
    else: validyears = array([0]) # No valid years, return 0 -- NOT an empty array, as you might expect!
    return validyears



def data2prev(data=None, keys=None, index=0, blh=0, **defaultargs): # WARNING, "blh" means "best low high", currently upper and lower limits are being thrown away, which is OK here...?
    """ Take an array of data return either the first or last (...or some other) non-NaN entry -- used for initial HIV prevalence only so far... """
    par = Constant(y=odict(), **defaultargs) # Create structure
    for row,key in enumerate(keys):
        par.y[key] = sanitize(data['hivprev'][blh][row])[index] # Return the specified index -- usually either the first [0] or last [-1]

    return par



def data2popsize(data=None, keys=None, blh=0, **defaultargs):
    ''' Convert population size data into population size parameters '''
    par = Popsizepar(m=1, **defaultargs)
    
    # Parse data into consistent form
    sanitizedy = odict() # Initialize to be empty
    sanitizedt = odict() # Initialize to be empty
    for row,key in enumerate(keys):
        sanitizedy[key] = sanitize(data['popsize'][blh][row]) # Store each extant value
        sanitizedt[key] = array(data['years'])[~isnan(data['popsize'][blh][row])] # Store each year

    largestpop = argmax([mean(sanitizedy[key]) for key in keys]) # Find largest population size
    
    # Store a list of population sizes that have at least 2 data points
    atleast2datapoints = [] 
    for key in keys:
        if len(sanitizedy[key])>=2:
            atleast2datapoints.append(key)
    if len(atleast2datapoints)==0:
        errormsg = 'Not more than one data point entered for any population size\n'
        errormsg += 'To estimate growth trends, at least one population must have at least 2 data points'
        raise OptimaException(errormsg)
    
    # Perform 2-parameter exponential fit to data
    startyear = data['years'][0]
    par.start = data['years'][0]
    for key in atleast2datapoints:
        tdata = sanitizedt[key]-startyear
        ydata = log(sanitizedy[key])
        try:
            fitpars = polyfit(tdata, ydata, 1)
            par.p[key] = array([exp(fitpars[1]), fitpars[0]])
        except:
            errormsg = 'Fitting population size data for population "%s" failed' % key
            raise OptimaException(errormsg)
    
    # Handle populations that have only a single data point
    only1datapoint = list(set(keys)-set(atleast2datapoints))
    for key in only1datapoint:
        largestpars = par.p[largestpop] # Get the parameters from the largest population
        if len(sanitizedt[key]) != 1:
            errormsg = 'Error interpreting population size for population "%s"\n' % key
            errormsg += 'Please ensure at least one time point is entered'
            raise OptimaException(errormsg)
        thisyear = sanitizedt[key][0]
        thispopsize = sanitizedy[key][0]
        largestthatyear = popgrow(largestpars, thisyear-startyear)
        par.p[key] = [largestpars[0]*thispopsize/largestthatyear, largestpars[0]]
    
    return par





def data2timepar(data=None, keys=None, defaultind=0, **defaultargs):
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
            validdata = ~isnan(data[short][row])
            par.t[key] = getvalidyears(data['years'], validdata, defaultind=defaultind) 
            if sum(validdata): 
                par.y[key] = sanitize(data[short][row])
            else:
                print('WARNING, no data entered for parameter "%s", key "%s"' % (name, key))
                par.y[key] = array([0]) # Blank, assume zero -- WARNING, is this ok?
        except:
            errormsg = 'Error converting time parameter "%s", key "%s"' % (name, key)
            raise OptimaException(errormsg)

    return par


## Acts
def balance(act=None, which=None, data=None, popkeys=None, limits=None, popsizepar=None):
    ''' 
    Combine the different estimates for the number of acts or condom use and return the "average" value.
    
    Set which='numacts' to compute for number of acts, which='condom' to compute for condom.
    '''
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
    for row in range(npops): yearstouse.append(getvalidyears(data['years'], ~isnan(data[which+act][row])))
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
    tmppar = data2timepar(name='tmp', short=which+act, limits=(0,'maxacts'), data=data, keys=popkeys, by='pop') # Temporary parameter for storing acts
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








def makepars(data, label=None, verbose=2):
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
    pars['injects'] = array(data['pops']['injects']).astype(bool) # Populations that inject
    pars['sexworker'] = array(data['pops']['sexworker']).astype(bool) # Populations that provide commercial sex
    
    # Set up keys
    totkey = ['tot'] # Define a key for when not separated by population
    popkeys = data['pops']['short'] # Convert to a normal string and to lower case...maybe not necessary
    fpopkeys = [popkey for popno,popkey in enumerate(popkeys) if data['pops']['female'][popno]]
    mpopkeys = [popkeys[i] for i in range(len(popkeys)) if pars['male'][i]] # WARNING, these two lines should be consistent -- they both work, so the question is which is more elegant -- if pars['male'] is a dict then could do: [popkeys[key] for key in popkeys if pars['male'][key]]
    pars['popkeys'] = dcp(popkeys)
    
    # Read in parameters automatically -- WARNING, not currently implemented
    rawpars = loadpartable() # Read the parameters structure
    for rawpar in rawpars: # Iterate over all automatically read in parameters
        printv('Converting data parameter "%s"...' % rawpar['short'], 3, verbose)
        
        # Shorten key variables
        partype = rawpar.pop('partype')
        parname = rawpar['short']
        by = rawpar['by']
        
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
            pars[parname] = data2timepar(data=data, keys=keys, **rawpar) 
        
        elif partype=='constant': # The constants, e.g. transmfi
            best = data['const'][parname][0] # low = data['const'][parname][1] ,  high = data['const'][parname][2]
            pars[parname] = Constant(y=best, **rawpar) # WARNING, should the limits be the limits defined in the spreadsheet? Or the actual mathematical limits?
        
        elif partype=='meta': # Force-of-infection and inhomogeneity and transitions
            pars[parname] = Constant(y=odict(), **rawpar)
            
    

    ###############################################################################
    ## Tidy up -- things that can't be converted automatically
    ###############################################################################    
    
    # Births rates. This parameter is coupled with the birth matrix defined below
    for key in list(set(popkeys)-set(fpopkeys)): # Births are only female: add zeros
        pars['birth'].y[key] = array([0])
        pars['birth'].t[key] = array([0])
    pars['birth'].y = pars['birth'].y.sort(popkeys) # Sort them so they have the same order as everything else
    pars['birth'].t = pars['birth'].t.sort(popkeys)
    
    # Birth transitions - these are stored as the proportion of transitions, which is constant, and is multiplied by time-varying birth rates in model.py
    normalised_birthtransit = [[0]*len(popkeys)]*len(popkeys)
    c = 0
    for pk,popkey in enumerate(popkeys):
        if data['pops']['female'][pk]:
            normalised_birthtransit[pk] = [col/sum(data['birthtransit'][c]) if sum(data['birthtransit'][c]) else 0 for col in data['birthtransit'][c]]
            c += 1
    pars['birthtransit'] = normalised_birthtransit 

    # Aging transitions - these are time-constant transition rates
    duration = [age[1]-age[0]+1 for age in data['pops']['age']]
    normalised_agetransit = [[col/sum(row)*1/duration[rowno] if sum(row) else 0 for col in row] for rowno,row in enumerate(data['agetransit'])]
    pars['agetransit'] = normalised_agetransit

    # Risk transitions - these are time-constant transition rates
    normalised_risktransit = [[1/col if col else 0 for col in row] for row in data['risktransit']]
    pars['risktransit'] = normalised_risktransit 
    
    # Circumcision
    for key in list(set(popkeys)-set(mpopkeys)): # Circumcision is only male
        pars['circum'].y[key] = array([0])
        pars['circum'].t[key] = array([0])
    pars['circum'].y = pars['circum'].y.sort(popkeys) # Sort them so they have the same order as everything else
    pars['circum'].t = pars['circum'].t.sort(popkeys)

    # Metaparameters
    for key in popkeys: # Define values
        pars['force'].y[key] = 1
        pars['inhomo'].y[key] = 0
    
    
    # Balance partnerships parameters    
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
                        pars[condname].y[(key1,key2)] = array(tmpcond[act])[i,j,:]
                        pars[condname].t[(key1,key2)] = array(tmpcondpts[act])
    
    printv('...done converting data to parameters.', 2, verbose)
    
    return pars


    
        



def makesimpars(pars, inds=None, keys=None, start=2000, end=2030, dt=0.2, tvec=None, settings=None, smoothness=None, verbose=2, name=None, uid=None):
    ''' 
    A function for taking a single set of parameters and returning the interpolated versions -- used
    very directly in Parameterset.
    
    Version: 2016jan18 by cliffk
    '''
    
    # Handle inputs and initialization
    simpars = odict() # Used to be called M
    simpars['parsetname'] = name
    simpars['parsetuid'] = uid
    generalkeys = ['male', 'female', 'injects', 'sexworker', 'popkeys']
    staticmatrixkeys = ['birthtransit','agetransit','risktransit']
    if keys is None: keys = pars.keys() # Just get all keys
    if tvec is not None: simpars['tvec'] = tvec
    elif settings is not None: simpars['tvec'] = settings.maketvec()
    else: simpars['tvec'] = linspace(start, end, round((end-start)/dt)+1) # Store time vector with the model parameters -- use linspace rather than arange because Python can't handle floats properly
    dt = simpars['tvec'][1] - simpars['tvec'][0] # Recalculate dt since must match tvec
    simpars['dt'] = dt  # Store dt
    if smoothness is None: smoothness = int(defaultsmoothness/dt)
    
    # Copy default keys by default
    for key in generalkeys: simpars[key] = dcp(pars[key])
    for key in staticmatrixkeys: simpars[key] = dcp(array(pars[key]))

    # Loop over requested keys
    for key in keys: # Loop over all keys
        if issubclass(type(pars[key]), Par): # Check that it is actually a parameter -- it could be the popkeys odict, for example
            try: 
                simpars[key] = pars[key].interp(tvec=simpars['tvec'], dt=dt, smoothness=smoothness) # WARNING, want different smoothness for ART
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
    
    # Apply limits, preserving original class
    if isinstance(y, (int, float)):
        newy = median([limits[0], y, limits[1]])
        if warn and newy!=y: printv('Note, parameter value "%s" reset from %f to %f' % (parname, y, newy), 3, verbose)
    elif shape(y):
        newy = array(y) # Make sure it's an array and not a list
        newy[newy<limits[0]] = limits[0]
        newy[newy>limits[1]] = limits[1]
        if warn and any(newy!=array(y)):
            printv('Note, parameter "%s" value reset from:\n%s\nto:\n%s' % (parname, y, newy), 3, verbose)
    else:
        if warn: raise OptimaException('Data type "%s" not understood for applying limits for parameter "%s"' % (type(y), parname))
        else: newy = array(y)
    
    if shape(newy)!=shape(y):
        errormsg = 'Something went wrong with applying limits for parameter "%s":\ninput and output do not have the same shape:\n%s vs. %s' % (parname, shape(y), shape(newy))
        raise OptimaException(errormsg)
    
    return newy







#################################################################################################################################
### Define the classes
#################################################################################################################################


class Par(object):
    ''' The base class for parameters '''
    def __init__(self, name=None, short=None, limits=(0,1), by=None, fittable='', auto='', cascade=False, coverage=None, visible=0, proginteract=None): # "type" data needed for parameter table, but doesn't need to be stored
        self.name = name # The full name, e.g. "HIV testing rate"
        self.short = short # The short name, e.g. "hivtest"
        self.limits = limits # The limits, e.g. (0,1) -- a tuple since immutable
        self.by = by # Whether it's by population, partnership, or total
        self.fittable = fittable # Whether or not this parameter can be manually fitted: options are '', 'meta', 'pop', 'exp', etc...
        self.auto = auto # Whether or not this parameter can be automatically fitted -- see parameter definitions above for possibilities; used in calibration.py
        self.cascade = cascade # Whether or not it's a cascade parameter
        self.coverage = coverage # Whether or not this is a coverage parameter
        self.visible = visible # Whether or not this parameter is visible to the user in scenarios and programs
        self.proginteract = proginteract # How multiple programs with this parameter interact
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = defaultrepr(self)
        return output




class Timepar(Par):
    ''' The definition of a single time-varying parameter, which may or may not vary by population '''
    
    def __init__(self, t=None, y=None, m=1, **defaultargs):
        Par.__init__(self, **defaultargs)
        if t is None: t = odict()
        if y is None: y = odict()
        self.t = t # Time data, e.g. [2002, 2008]
        self.y = y # Value data, e.g. [0.3, 0.7]
        self.m = m # Multiplicative metaparameter, e.g. 1
    
    
    def interp(self, tvec=None, dt=None, smoothness=None):
        """ Take parameters and turn them into model parameters """
        
        # Validate input
        if tvec is None: 
            errormsg = 'Cannot interpolate parameter "%s" with no time vector specified' % self.name
            raise OptimaException(errormsg)
        tvec, dt = gettvecdt(tvec=tvec, dt=dt) # Method for getting these as best possible
        if smoothness is None: smoothness = int(defaultsmoothness/dt) # 
        
        # Set things up and do the interpolation
        keys = self.y.keys()
        npops = len(keys)
        if self.by=='pship': # Have odict
            output = odict()
            for pop,key in enumerate(keys): # Loop over each population, always returning an [npops x npts] array
                yinterp = self.m * smoothinterp(tvec, self.t[pop], self.y[pop], smoothness=smoothness) # Use interpolation
                output[key] = applylimits(par=self, y=yinterp, limits=self.limits, dt=dt)
        else: # Have 2D matrix: pop, time
            output = zeros((npops,len(tvec)))
            for pop,key in enumerate(keys): # Loop over each population, always returning an [npops x npts] array
                yinterp = self.m * smoothinterp(tvec, self.t[pop], self.y[pop], smoothness=smoothness) # Use interpolation
                output[pop,:] = applylimits(par=self, y=yinterp, limits=self.limits, dt=dt)
        if npops==1 and self.by=='tot': return output[0,:] # npops should always be 1 if by==tot, but just be doubly sure
        else: return output






class Popsizepar(Par):
    ''' The definition of the population size parameter '''
    
    def __init__(self, p=None, m=1, start=2000, **defaultargs):
        Par.__init__(self, **defaultargs)
        if p is None: p = odict()
        self.p = p # Exponential fit parameters
        self.m = m # Multiplicative metaparameter, e.g. 1
        self.start = start # Year for which population growth start is calibrated to
    

    def interp(self, tvec=None, dt=None, smoothness=None): # WARNING: smoothness isn't used, but kept for consistency with other methods...
        """ Take population size parameter and turn it into a model parameters """
        
        # Validate input
        if tvec is None: 
            errormsg = 'Cannot interpolate parameter "%s" with no time vector specified' % self.name
            raise OptimaException(errormsg)
        tvec, dt = gettvecdt(tvec=tvec, dt=dt) # Method for getting these as best possible
        
        # Do interpolation
        keys = self.p.keys()
        npops = len(keys)
        output = zeros((npops,len(tvec)))
        for pop,key in enumerate(keys):
            yinterp = self.m * popgrow(self.p[key], array(tvec)-self.start)
            output[pop,:] = applylimits(par=self, y=yinterp, limits=self.limits, dt=dt)
        return output





class Constant(Par):
    ''' The definition of a single constant parameter, which may or may not vary by population '''
    
    def __init__(self, y=None, **defaultargs):
        Par.__init__(self, **defaultargs)
        self.y = y # y-value data, e.g. [0.3, 0.7]
    
    
    def interp(self, tvec=None, dt=None, smoothness=None): # Keyword arguments are for consistency but not actually used
        """ Take parameters and turn them into model parameters -- here, just return a constant value at every time point """
        
        dt = gettvecdt(tvec=tvec, dt=dt, justdt=True) # Method for getting dt     
        
        if isinstance(self.y, (int, float)) or len(self.y)==1: # Just a simple constant
            output = applylimits(par=self, y=self.y, limits=self.limits, dt=dt)
        else: # No, it has keys, return as an array
            keys = self.y.keys()
            npops = len(keys)
            output = zeros(npops)
            for pop,key in enumerate(keys): # Loop over each population, always returning an [npops x npts] array
                output[pop] = applylimits(par=self, y=self.y[key], limits=self.limits, dt=dt)
        return output






class Parameterset(object):
    ''' Class to hold all parameters and information on how they were generated, and perform operations on them'''
    
    def __init__(self, name='default', project=None, progsetname=None, budget=None):
        self.name = name # Name of the parameter set, e.g. 'default'
        self.uid = uuid() # ID
        self.project = project # Store pointer for the project, if available
        self.created = today() # Date created
        self.modified = today() # Date modified
        self.pars = [] # List of dicts holding Parameter objects -- only one if no uncertainty
        self.popkeys = [] # List of populations
        self.resultsref = None # Store pointer to results
        self.progsetname = progsetname # Store the name of the progset that generated the parset, if any
        self.budget = budget # Store the budget that generated the parset, if any
        
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output =  '============================================================\n'
        output += 'Parameter set name: %s\n'    % self.name
        output += '    Number of runs: %s\n'    % len(self.pars)
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output
    
    
    def getresults(self, die=True):
        ''' Method for getting the results '''
        if self.resultsref is not None and self.project is not None:
            results = getresults(project=self.project, pointer=self.resultsref, die=die)
            return results
        else:
            raise OptimaException('No results associated with this parameter set')
    
    
    def makepars(self, data, verbose=2):
        self.pars = [makepars(data, verbose=verbose)] # Initialize as list with single entry
        self.popkeys = dcp(self.pars[-1]['popkeys']) # Store population keys more accessibly
        return None


    def interp(self, inds=None, keys=None, start=2000, end=2030, dt=0.2, tvec=None, smoothness=20, verbose=2):
        """ Prepares model parameters to run the simulation. """
        printv('Making model parameters...', 1, verbose)
        
        simparslist = []
        if isinstance(tvec, (int, float)): tvec = array([tvec]) # Convert to 1-element array -- WARNING, not sure if this is necessary or should be handled lower down
        if isinstance(inds, (int, float)): inds = [inds]
        if inds is None:inds = range(len(self.pars))
        for ind in inds:
            simpars = makesimpars(pars=self.pars[ind], keys=keys, start=start, end=end, dt=dt, tvec=tvec, smoothness=smoothness, verbose=verbose, name=self.name, uid=self.uid)
            simparslist.append(simpars) # Wrap up
        
        printv('...done making model parameters.', 2, verbose)
        return simparslist


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
        for key in pars:
            if issubclass(type(pars[key]), Par):
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






    def manualfitlists(self, ind=0):
        ''' WARNING -- not sure if this function is needed; if it is needed, it should be combined with manualgui,py '''
        if not self.pars:
            raise OptimaException("No parameters available!")
        elif len(self.pars)<=ind:
            raise OptimaException("Parameter with index {} not found!".format(ind))

        tmppars = self.pars[ind]

        mflists = {'keys':[], 'subkeys':[], 'types':[], 'values':[], 'labels':[]}
        keylist = mflists['keys']
        subkeylist = mflists['subkeys']
        typelist = mflists['types']
        valuelist = mflists['values']
        labellist = mflists['labels']

        for key in tmppars.keys():
            par = tmppars[key]
            if (not hasattr(par,'fittable')) or (par.fittable == 'no'): # Don't worry if it doesn't work, not everything in tmppars is actually a parameter
                continue
            if par.fittable == 'meta':
                keylist.append(key)
                subkeylist.append(None)
                typelist.append(par.fittable)
                valuelist.append(par.m)
                labellist.append('{} -- meta'.format(par.name))
            elif par.fittable in ['pop', 'pship']:
                for subkey in par.y.keys():
                    keylist.append(key)
                    subkeylist.append(subkey)
                    typelist.append(par.fittable)
                    valuelist.append(par.y[subkey])
                    labellist.append('{} -- {}'.format(par.name, str(subkey)))
            elif par.fittable == 'exp':
                for subkey in par.p.keys():
                    keylist.append(key)
                    subkeylist.append(subkey)
                    typelist.append(par.fittable)
                    valuelist.append(par.p[subkey][0])
                    labellist.append('{} -- {}'.format(par.name, str(subkey)))
            else:
                print('Parameter type "%s" not implemented!' % par.fittable)

        return mflists

    ## Define update step
    def update(self, mflists, ind=0):
        from optima import printv
        ''' Update Parameterset with new results '''
        if not self.pars:
            raise OptimaException("No parameters available!")
        elif len(self.pars)<=ind:
            raise OptimaException("Parameter with index {} not found!".format(ind))

        tmppars = self.pars[ind]

        keylist = mflists['keys']
        subkeylist = mflists['subkeys']
        typelist = mflists['types']
        valuelist = mflists['values']

        ## Loop over all parameters and update them
        verbose = 0
        for (key, subkey, ptype, value) in zip(keylist, subkeylist, typelist, valuelist):
            if ptype == 'meta': # Metaparameters
                vtype = type(tmppars[key].m)
                tmppars[key].m = vtype(value)
                printv('%s.m = %s' % (key, value), verbose)
            elif ptype in ['pop', 'pship']: # Populations or partnerships
                vtype = type(tmppars[key].y[subkey])
                tmppars[key].y[subkey] = vtype(value)
                printv('%s.y[%s] = %s' % (key, subkey, value), verbose)
            elif ptype == 'exp': # Population growth
                vtype = type(tmppars[key].p[subkey][0])
                tmppars[key].p[subkey][0] = vtype(value)
                printv('%s.p[%s] = %s' % (key, subkey, value), verbose)
            else:
                print('Parameter type "%s" not implemented!' % ptype)

        # parset.interp() and calculate results are supposed to be called from the outside        
