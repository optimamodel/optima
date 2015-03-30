"""
Creates and updates cost-coverage curves and coverage-outcome curves
    
Version: 2015jan16 by cliffk
"""
###############################################################################
## Set up
###############################################################################

from math import log
from numpy import linspace, exp, isnan, multiply, arange, mean, array
from numpy import log as nplog
from rtnorm import rtnorm
from printv import printv
from copy import deepcopy
from datetime import date

## Set coverage parameters...
coverage_params = ['numost','numpmtct','numfirstline','numsecondline']
default_nxpts = 100 # Set the number of points to make the lines
default_verbose = 2
######################################################################
def makecc(D=None, progname=None, ccparams=None, arteligcutoff=None, verbose=default_verbose, nxpts=default_nxpts):
    '''Make cost coverage curve.
    Input:
    D: main data structure
<<<<<<< HEAD
    progname: string
    ccparams: dict containing parameters for the cost-coverage curves, obtained from the GUI. Can be empty.
    artelig: string containing the denominator for ART coverage
    '''
    
    # Check inputs... 
    if unicode(progname) not in [p['name'] for p in D['programs']]:
        raise Exception('Please select one of the following programs %s' % [p['name'] for p in D['programs']])
    if not(isinstance(ccparams,dict)): print('Cost-coverage parameters not provided, will plot data only....')
    if not (isinstance(arteligcutoff,str)):
        print('Assuming universal ART coverage since not otherwise specified....')
        arteligcutoff = D['G']['healthstates'][0]
    states, artindex = range(D['G']['nstates']), []
    for i in range(len(D['G'][arteligcutoff])-1): artindex.extend(states[D['G'][arteligcutoff][i+1]:D['G'][D['G']['healthstates'][-1]][i+1]+1])
    if verbose>=2: print('makecc %s %s' % (progname, ccparams))


    # Initialise output structure
    plotdata = {}

    # Extract basic info from data structure
    prognumber = [p['name'] for p in D['programs']].index(progname) # get program number    
    totalcost = D['data']['costcov']['realcost'][prognumber] # get total cost

    # Adjust cost data to year specified by user (if given)
    if ccparams and ccparams['cpibaseyear']:
        from financialanalysis import expanddata
        cpi = expanddata(D['data']['econ']['cpi']['past'][0], len(D['data']['epiyears']), D['data']['econ']['cpi']['future'][0][0], interp=False, dt=None)
        cpibaseyear = ccparams['cpibaseyear']
        cpibaseyearindex = D['data']['epiyears'].index(cpibaseyear) # get index of CPI base year
        if len(totalcost)==1: # If it's an assumption, assume it's already in current prices
            totalcost = [totalcost[0]*cpi[cpibaseyearindex]]
        else:
            totalcost = [totalcost[j]*(cpi[cpibaseyearindex]/cpi[j]) if ~isnan(totalcost[j]) else float('nan') for j in xrange(len(totalcost))]
    else:
        cpibaseyear = min(D['data']['epiyears'][-1],date.today().year)

    # Flag to indicate whether we will adjust by population or not
    popadj = 0
    if (ccparams and 'perperson' in ccparams.keys() and ccparams['perperson']): popadj = ccparams['perperson']

    # Get coverage and target population size (in separate function)       
    coverage, targetpopsize, coveragelabel = getcoverage(D=D, artindex=artindex, progname=progname)

    # Adjust cost data by target population size, if requested by user 
    if (ccparams and 'perperson' in ccparams.keys() and ccparams['perperson']):
        totalcost = totalcost/targetpopsize if len(totalcost)>1 else totalcost/mean(targetpopsize)

    # Get upper limit of x axis for plotting
    xupperlim = max([x if ~isnan(x) else 0.0 for x in totalcost])*1.5
    if (ccparams and 'xupperlim' in ccparams.keys() and ccparams['xupperlim']): xupperlim = ccparams['xupperlim'] 
        
    # Populate output structure with scatter data 
    totalcost, coverage = getscatterdata(totalcost, coverage)
    plotdata['xscatterdata'] = totalcost
    plotdata['yscatterdata'] = coverage

    # Are there parameters (either given by the user or previously stored)?
    if (ccparams or D['programs'][prognumber]['ccparams']):
        if not ccparams: ccparams = D['programs'][prognumber]['ccparams']
        convertedccparams = convertparams(D=D, ccparams=ccparams)

        # X data
        xvalscc = linspace(0,xupperlim,nxpts) # take nxpts points between 0 and user-specified max
        xvalsccpop = linspace(0,xupperlim*targetpopsize[-1],nxpts) if popadj else xvalscc

        # Y data
        if ccparams['scaleup']:
            yvalsccl = cceqn(xvalsccpop, convertedccparams[0])
            yvalsccm = cceqn(xvalsccpop, convertedccparams[1])
            yvalsccu = cceqn(xvalsccpop, convertedccparams[2])
            yvalscc = [yvalsccl, yvalsccm, yvalsccu]
        else:
            yvalsccl = cc2eqn(xvalsccpop, convertedccparams[0])
            yvalsccm = cc2eqn(xvalsccpop, convertedccparams[1])
            yvalsccu = cc2eqn(xvalsccpop, convertedccparams[2])
            yvalscc = [yvalsccl, yvalsccm, yvalsccu]

        if coveragelabel=='Number covered':
            for j in range(len(yvalscc)):
                yvalscc[j] = [yvalscc[j][k]*targetpopsize[-1] for k in range(len(yvalscc[j]))]

        # Populate output structure 
        plotdata['xlinedata'] = xvalscc
        plotdata['ylinedata'] = yvalscc 

        # Store parameters and lines
        D['programs'][prognumber]['ccparams'] = ccparams
        D['programs'][prognumber]['convertedccparams'] = convertedccparams
        if not ccparams['nonhivdalys']: ccparams['nonhivdalys'] = 0.0
        D['programs'][prognumber]['nonhivdalys'] = [ccparams['nonhivdalys']]

    # Populate output structure with axis limits
    plotdata['xlowerlim'], plotdata['ylowerlim']  = 0.0, 0.0
    plotdata['xupperlim'] = xupperlim 
    if coveragelabel == 'Proportion covered':
        plotdata['yupperlim']  = 1.0
    else:
        plotdata['yupperlim']  = max([x if ~isnan(x) else 0.0 for x in coverage])*1.5
        if ccparams: plotdata['yupperlim']  = max(yvalscc[2][-1]*1.5,plotdata['yupperlim'])

    # Populate output structure with labels and titles
    plotdata['title'] = progname
    plotdata['xlabel'] = 'USD'+ ', ' + str(int(cpibaseyear)) + ' prices'
    plotdata['ylabel'] = coveragelabel
    
    return plotdata, D

######################################################################
def makeco(D=None, progname=None, effect=None, coparams=None, coverage_params=coverage_params, arteligcutoff=None, verbose=default_verbose, nxpts = default_nxpts):
    '''
    Make a single coverage outcome curve.
    
    Inputs: 
    D: main data structure
    progname: string
    effect: bunch structure
    coparams: list. Contains parameters for the coverage-outcome curves, obtained from the GUI
        coparams[0] = the lower bound for the outcome when coverage = 0
        coparams[1] = the upper bound for the outcome when coverage = 0
        coparams[2] = the lower bound for the outcome when coverage = 1
        coparams[3] = the upper bound for the outcome when coverage = 1

    Output:
    plotdata, storeparams
    '''
    from parameters import input_parameter_name
    
    # Check inputs
    if unicode(progname) not in [p['name'] for p in D['programs']]:
        raise Exception('Please select one of the following programs %s' % [p['name'] for p in D['programs']])
    if not (isinstance(arteligcutoff,str)):
        print('Assuming universal ART coverage since not otherwise specified....')
        arteligcutoff = D['G']['healthstates'][0]
    states, artindex = range(D['G']['nstates']), []
    for i in range(len(D['G'][arteligcutoff])-1):
        artindex.extend(states[D['G'][arteligcutoff][i+1]:D['G'][D['G']['healthstates'][-1]][i+1]+1])

    prognumber = [p['name'] for p in D['programs']].index(progname) # get program number    

    # Check that the selected parameter is in the list of parameters belonging to this program
    short_effectname = [effect['paramtype'], effect['param'], effect['popname']] # only matching by effect "signature"
    short_effectlist = [[effect['paramtype'], e['param'], e['popname']] for e in D['programs'][prognumber]['effects']]
    if short_effectname not in short_effectlist:
        print "makeco short_effectname: %s short_effectlist: %s" % (short_effectname, short_effectlist)
        raise Exception('Please select one of the following effects %s' % D['programs'][prognumber]['effects'])
    
    # Initialise output structures
    plotdata = {}

    # Get population and parameter info
    partype, parname, popname = effect['paramtype'], effect['param'], effect['popname']

    # Only going to make cost-outcome curves for programs where the affected parameter is not coverage
    if parname not in coverage_params:
        if popname not in D['data']['meta']['pops']['short']: raise Exception('Cannot recognise population %s, it is not in %s' % (popname, D['data']['meta']['pops']['short']))
        else: popnumber = D['data']['meta']['pops']['short'].index(popname)
        
        # Get data for scatter plots
        outcome = D['data'][partype][parname][popnumber]
        coverage, targetpopsize, coveragelabel = getcoverage(D=D, artindex=artindex, progname=progname)

        # Populate output structure with axis limits
        plotdata['xlowerlim'], plotdata['ylowerlim']  = 0.0, 0.0
        plotdata['xupperlim'] = 1.0 if coveragelabel == 'Proportion covered' else max([j if ~isnan(j) else 0.0 for j in coverage])*1.5
        plotdata['yupperlim'] = 1.0 if any(j < 1 for j in outcome) else max([j if ~isnan(j) else 0.0 for j in outcome])*1.5

        # Populate output structure with scatter data 
        coverage, outcome = getscatterdata(coverage, outcome)
        plotdata['xscatterdata'] = coverage 
        plotdata['yscatterdata'] = outcome 
           
        # Get params for plotting - either from GUI or get previously stored ones
        if not coparams and (coparams in effect.keys()): coparams = effect['coparams']
        if coparams:
            if not len(coparams) == 4:
                raise Exception('Not all of the coverage-outcome parameters have been specified. Please enter the missing parameters to define the curve.')
            
            # Generate and store converted parameters
            muz, stdevz, muf, stdevf = makecosampleparams(coparams, verbose=verbose)
            convertedcoparams = [muz, stdevz, muf, stdevf]

            # General set of coverage-outcome relationships
            xvalsco = linspace(0,plotdata['xupperlim'],nxpts) # take nxpts points
            ymin, ymax = linspace(coparams[0],coparams[2],nxpts), linspace(coparams[1],coparams[3],nxpts)
            
            # Populate output structure with coverage-outcome curves for plotting
            effect['coparams'] = coparams 
            effect['convertedcoparams'] = convertedcoparams 

            # Populate output structure with coverage-outcome curves for plotting
            plotdata['xlinedata'] = xvalsco # X data for all line plots
            plotdata['ylinedata'] = [linspace(muz,muf,nxpts), ymax, ymin] # ALL Y data (for three lines)

        # Populate output structure with labels and titles
        plotdata['title'] = input_parameter_name(parname)+ ' - ' + popname
        plotdata['xlabel'] = coveragelabel
        plotdata['ylabel'] = 'Outcome'
        
    return plotdata, effect

#################################################################################
def makecco(D=None, progname=None, effect=None, ccparams=None, coparams=None, arteligcutoff=None, coverage_params=coverage_params, verbose=default_verbose, nxpts=default_nxpts):
    '''
    Make a single cost outcome curve.
    
    Inputs: 
    D: main data structure
    progname: string
    effect: bunch struct
    ccparams: dict containing parameters for the cost-coverage curves, obtained from the GUI. Can be empty.
    coparams: list. Contains parameters for the coverage-outcome curves
        coparams(0) = the lower bound for the outcome when coverage = 0
        coparams(1) = the upper bound for the outcome when coverage = 0
        coparams(2) = the lower bound for the outcome when coverage = 1
        coparams(3) = the upper bound for the outcome when coverage = 1
    '''
    from parameters import input_parameter_name
    
    printv("makecco(%s, %s, %s, %s, %s, %s, %s)" % (progname, effect['popname'], effect['param'], ccparams, coparams, verbose, nxpts), 2, verbose)

    # Check inputs
    if unicode(progname) not in [p['name'] for p in D['programs']]:
        printv("progname: %s programs: %s" % (unicode(progname), [p['name'] for p in D['programs']]), 5, verbose)
        raise Exception('Please select one of the following programs %s' % [p['name'] for p in D['programs']])
    if not (isinstance(arteligcutoff,str)):
        print('Assuming universal ART coverage since not otherwise specified....')
        arteligcutoff = D['G']['healthstates'][0]
    states, artindex = range(D['G']['nstates']), []
    for i in range(len(D['G'][arteligcutoff])-1):
        artindex.extend(states[D['G'][arteligcutoff][i+1]:D['G'][D['G']['healthstates'][-1]][i+1]+1])

    prognumber = [p['name'] for p in D['programs']].index(progname) # get program number    

    # Check that the selected effect is in the list of effects
    short_effectname = [effect['paramtype'], effect['param'], effect['popname']] # only matching by effect "signature"
    short_effectlist = [[e['paramtype'], e['param'], e['popname']] for e in D['programs'][prognumber]['effects']]
    if short_effectname not in short_effectlist:
        print "makeco short_effectname: %s short_effectlist: %s" % (short_effectname, short_effectlist)
        raise Exception('Please select one of the following effects %s' % D['programs'][prognumber]['effects'])

    # Initialise output structures
    plotdata, plotdata_co, xupperlim = {}, {}, None

    # Get population and parameter info
    partype, parname, popname = effect['paramtype'], effect['param'], effect['popname']

    # Only going to make cost-outcome curves for programs where the affected parameter is not coverage
    if parname not in coverage_params:
        if popname not in D['data']['meta']['pops']['short']: raise Exception('Cannot recognise population %s, it is not in %s' % (popname, D['data']['meta']['pops']['short']))
        else: popnumber = D['data']['meta']['pops']['short'].index(popname)

        # Extract cost data and adjust to base year specified by user (if given)
        totalcost = D['data']['costcov']['realcost'][prognumber] # get total cost data

        if ccparams and ccparams['cpibaseyear']:
            from financialanalysis import expanddata
            cpi = expanddata(D['data']['econ']['cpi']['past'][0], len(D['data']['epiyears']), D['data']['econ']['cpi']['future'][0][0], interp=False, dt=None)
            cpibaseyear = ccparams['cpibaseyear']
            cpibaseyearindex = D['data']['epiyears'].index(cpibaseyear) # get index of CPI base year
            if len(totalcost)==1: # If it's an assumption, assume it's already in current prices
                totalcost = [totalcost[0]*cpi[cpibaseyearindex]]
            else:
                totalcost = [totalcost[j]*(cpi[cpibaseyearindex]/cpi[j]) if ~isnan(totalcost[j]) else float('nan') for j in xrange(len(totalcost))]
        else:
            cpibaseyear = min(D['data']['epiyears'][-1],date.today().year)

        # Extract outcome data
        outcome = D['data'][partype][parname][popnumber]

        # Flag to indicate whether we will adjust by population or not, default is not
        popadj = 0
        if (ccparams and 'perperson' in ccparams.keys() and ccparams['perperson']): popadj = ccparams['perperson']

        # Get target population size (in separate function)       
        coverage, targetpopsize, coveragelabel = getcoverage(D, artindex=artindex, progname=progname)

        # Adjust cost data by target population size, if requested by user 
        if (ccparams and 'perperson' in ccparams.keys() and ccparams['perperson']):
            totalcost = totalcost/targetpopsize if len(totalcost)>1 else totalcost/mean(targetpopsize)

        # Get upper limit of x axis for plotting
        xupperlim = max([x if ~isnan(x) else 0.0 for x in totalcost])*1.5
        if (ccparams and 'xupperlim' in ccparams.keys() and ccparams['xupperlim']): xupperlim = ccparams['xupperlim'] 
            
        # Populate output structure with scatter data 
        totalcost, outcome = getscatterdata(totalcost, outcome)

        # Cliff's code to append the current conditions #TODO fix
        plottotalcost = deepcopy(totalcost)
        plotoutcome = deepcopy(outcome)
        currentcost = D['data']['origalloc'][prognumber]
        currentoutcome = None
        try:
            timepoint = D['opt']['partvec'].index(float(min(D['data']['epiyears'][-1], date.today().year)))
            currentoutcome = D['M'][parname][popnumber][timepoint]
        except:
            try:
                tmp = array(D['data'][partype][parname][popnumber])
                currentoutcome = tmp[~isnan(tmp)][-1]
                print('Parameter %s not found, using last data value %f' % (parname, currentoutcome))
            except:
                print('Parameter %s not found, and could not append a point from data: %s' % (parname, tmp))
        if currentcost is not None and currentoutcome is not None:
            plottotalcost.append(currentcost) # WARNING KLUDGY, force-append last data point
            plotoutcome.append(currentoutcome)
            
        plotdata['xscatterdata'] = plottotalcost # X scatter data
        plotdata['yscatterdata'] = plotoutcome # Y scatter data

        # Do we have parameters for making curves?
        if (ccparams or D['programs'][prognumber].ccparams) and (coparams or (effect['coparams'] and len(effect['coparams'])>3)):

            if not ccparams: ccparams = D['programs'][prognumber]['ccparams']
            convertedccoparams = convertparams(D=D, ccparams=ccparams)
            if coparams: # Get coparams from  GUI... 
                muz, stdevz, muf, stdevf = makecosampleparams(coparams, verbose=verbose)
                convertedcoparams = [muz, stdevz, muf, stdevf]
                effect['coparams'] = coparams 
                effect['convertedcoparams'] = convertedcoparams 
            else: # ... or access previously stored ones
                coparams = effect['coparams']
                convertedcoparams = effect['convertedcoparams']

            for j in range(3): convertedccoparams[j].extend([convertedcoparams[0],convertedcoparams[2]])
            effect['convertedccoparams'] = convertedccoparams 

            # Create x dataset and initialise y dataset
            xvalscco = linspace(0,xupperlim,nxpts)
            xvalsccpop = linspace(0,xupperlim*targetpopsize[-1],nxpts) if popadj else xvalscco
    
            # Min, Median and Max lines
            if ccparams['scaleup']:
                mediancco = ccoeqn(xvalsccpop, convertedccoparams[0])# Generate min cost-outcome curve
                mincco = ccoeqn(xvalsccpop, [convertedccoparams[1][0], convertedccoparams[1][1], convertedccoparams[1][2], coparams[0], coparams[2]])# Generate min cost-outcome curve
                maxcco = ccoeqn(xvalsccpop, [convertedccoparams[2][0], convertedccoparams[2][1], convertedccoparams[2][2], coparams[1], coparams[3]])# Generate max cost-outcome curve
            else:
                mediancco = cco2eqn(xvalsccpop, convertedccoparams[0])# Generate min cost-outcome curve
                mincco = cco2eqn(xvalsccpop, [convertedccoparams[1][0], convertedccoparams[1][1], coparams[0], coparams[2]])# Generate min cost-outcome curve
                maxcco = cco2eqn(xvalsccpop, [convertedccoparams[2][0], convertedccoparams[2][1], coparams[1], coparams[3]])# Generate max cost-outcome curve

            # Populate output structure with cost-outcome curves for plotting
            plotdata['xlinedata'] = xvalscco # X data for all line plots
            plotdata['ylinedata'] = [mediancco,maxcco,mincco] # Y data for second line plot

        # Get the coverage-outcome relationships (this should be kept in the outer level, 
        # unless the intention is do not produce coverage-outcome relationships when ccparams / coparams are not present - AN)
        plotdata_co, effect = makeco(D=D, progname=progname, effect=effect, coparams=coparams, arteligcutoff=arteligcutoff, verbose=verbose)

        # Populate output structure with axis limits
        plotdata['xlowerlim'], plotdata['ylowerlim']  = 0.0, 0.0
        plotdata['xupperlim']  = xupperlim
        plotdata['yupperlim'] = 1.0 if any(j < 1 for j in outcome) else max([j if ~isnan(j) else 0.0 for j in outcome])*1.5
    
        # Populate output structure with labels and titles
        plotdata['title'] = input_parameter_name(parname)+ ' - ' + popname
        plotdata['xlabel'] = 'USD'+ ', ' + str(int(cpibaseyear)) + ' prices'
        plotdata['ylabel'] = 'Outcome'
        
    return plotdata, plotdata_co, effect

################################################################################
def plotallcurves(D=None, progname=None, ccparams=None, coparams=None, verbose=default_verbose):
    '''
    Make all cost outcome curves for a given program.
    '''
    from copy import deepcopy
    # Get the cost-coverage and coverage-outcome relationships     
    plotdata_cc, D = makecc(D=D, progname=progname, ccparams=ccparams, verbose=verbose)

   # Check that the selected program is in the program list 
    if progname not in [p['name'] for p in D['programs']]:
        raise Exception('Please select one of the following programs %s' % [p['name'] for p in D['programs']])
    prognumber = [p['name'] for p in D['programs']].index(progname) # get program number    

    # Initialise storage of outputs   
    plotdata_co = {}
    plotdata = {}    
    effects = {}     

    # Loop over behavioural effects
    for effectnumber, effect in enumerate(D['programs'][prognumber]['effects']):

        # Get parameter info
        parname = effect['param']

        # Only going to make cost-outcome curves for programs where the affected parameter is not coverage
        if parname not in coverage_params:

            # Store outputs
            plotdata[effectnumber], plotdata_co[effectnumber], new_effect = makecco(D=D, progname=progname, effect=effect, ccparams=D['programs'][prognumber]['ccparams'], coparams=coparams, verbose=verbose)
            D['programs'][prognumber]['effects'][effectnumber] = deepcopy(new_effect)
            effects[effectnumber] = deepcopy(new_effect)

    return plotdata, plotdata_co, plotdata_cc, effects, D      

################################################################################
def makeallccocs(D=None, verbose=default_verbose):
    '''
    Make all curves for all programs.
    '''

    for program in D['programs']:
        progname = program['name']
        plotdata_cco, plotdata_co, plotdata_cc, effects, D = plotallcurves(D, unicode(progname))
    return D

###############################################################################


###############################################################################
# Helper functions
###############################################################################
def getcoverage(D=None, artindex=None, progname=None):
    '''
    Get coverage levels.
    '''
    
    coverage = None
    coveragelabel = ''

    # Extract basic info from data structure
    prognumber = D['data']['meta']['progs']['short'].index(progname) # get program number
    ndatayears = len(D['data']['epiyears']) # get number of data years

    # Sort out time vector and indexing
    tvec = arange(D['G']['datastart'], D['G']['dataend']+D['opt']['dt'], D['opt']['dt']) # Extract the time vector from the sim
    npts = len(tvec) # Number of sim points

    # Figure out the targeted population(s) 
    targetpops = []
    targetpars = []
    popnumbers = []
    for effect in D['programs'][prognumber]['effects']:
        targetpops.append(effect['popname'])
        targetpars.append(effect['param'])
        if effect['popname'] in D['data']['meta']['pops']['short']:
            popnumbers.append(D['data']['meta']['pops']['short'].index(effect['popname']))
    targetpops = list(set(targetpops))
    targetpars = list(set(targetpars))
    popnumbers = list(set(popnumbers))

    # Figure out the total model-estimated size of the targeted population(s)
    for thispar in targetpars: # Loop through parameters
        if len(D['P'][thispar]['p'])==D['G']['npops']: # For parameters whose effect is differentiated by population, we add up the targeted populations
            targetpopmodel = D['S']['people'][:,popnumbers,0:npts].sum(axis=(0,1))
        elif len(D['P'][thispar]['p'])==1: # For parameters whose effects are not differentiated by population, we make special cases depending on the parameter
            if thispar == 'aidstest': # Target population = diagnosed PLHIV, AIDS stage
                targetpopmodel = D['S']['people'][27:31,:,0:npts].sum(axis=(0,1))
            elif thispar in ['numost','sharing']: # Target population = the sum of all populations that inject
                injectindices = [i for i, x in enumerate(D['data']['meta']['pops']['injects']) if x == 1]
                targetpopmodel = D['S']['people'][:,injectindices,0:npts].sum(axis = (0,1))
            elif thispar == 'numpmtct': # Target population = HIV+ pregnant women
                targetpopmodel = multiply(D['M']['birth'][:,0:npts], D['S']['people'][artindex,:,0:npts].sum(axis=0)).sum(axis=0)
            elif thispar == 'breast': # Target population = HIV+ breastfeeding women
                targetpopmodel = multiply(D['M']['birth'][:,0:npts], D['M']['breast'][0:npts], D['S']['people'][artindex,:,0:npts].sum(axis=0)).sum(axis=0)
            elif thispar in ['numfirstline','numsecondline']: # Target population = diagnosed PLHIV
                targetpopmodel = D['S']['people'][artindex,:,0:npts].sum(axis=(0,1))
            else:
                print('WARNING, Unrecognized parameter %s' % thispar)
        else:
            print('WARNING, Parameter %s of odd length %s' % (thispar, len(D['P'][thispar]['p'])))
    if len(targetpars)==0:
        print('WARNING, no target parameters for program %s' % progname)
                
    # We only want the model-estimated size of the targeted population(s) for actual years, not the interpolated years
    yearindices = xrange(0,npts,int(1/D['opt']['dt']))
    targetpop = targetpopmodel[yearindices]

    coverage = D['data']['costcov']['cov'][prognumber] 
    coveragelabel = 'Number covered' if any(j > 1 for j in D['data']['costcov']['cov'][prognumber]) else 'Proportion covered'

    return coverage, targetpop, coveragelabel

###############################################################################
def convertparams(D=None, ccparams=None):
    ''' Convert GUI inputs into the form needed for the calculations '''

    convertedccparams = []

    if ccparams['scaleup']:
        growthratel = exp((1-ccparams['scaleup'])*log(ccparams['saturation']/ccparams['coveragelower']-1)+log(ccparams['funding']))
        growthratem = exp((1-ccparams['scaleup'])*log(ccparams['saturation']/((ccparams['coveragelower']+ccparams['coverageupper'])/2)-1)+log(ccparams['funding']))
        growthrateu = exp((1-ccparams['scaleup'])*log(ccparams['saturation']/ccparams['coverageupper']-1)+log(ccparams['funding']))
        convertedccparams = [[ccparams['saturation'], growthratem, ccparams['scaleup']], [ccparams['saturation'], growthratel, ccparams['scaleup']], [ccparams['saturation'], growthrateu, ccparams['scaleup']]]
    else:
        growthratel = (-1/ccparams['funding'])*log((2*ccparams['saturation'])/(ccparams['coveragelower']+ccparams['saturation']) - 1)        
        growthratem = (-1/ccparams['funding'])*log((2*ccparams['saturation'])/(((ccparams['coveragelower']+ccparams['coverageupper'])/2)+ccparams['saturation']) - 1)        
        growthrateu = (-1/ccparams['funding'])*log((2*ccparams['saturation'])/(ccparams['coverageupper']+ccparams['saturation']) - 1)        
        convertedccparams = [[ccparams['saturation'], growthratem], [ccparams['saturation'], growthratel], [ccparams['saturation'], growthrateu]]
                    
    return convertedccparams

###############################################################################
def getscatterdata(xdata, ydata):
    '''
    Short function to remove nans and make sure the right scatter data is sent to FE
    '''
    from numpy import isnan

    xdatascatter = []
    ydatascatter = []

    if (len(xdata) == 1 and len(ydata) > 1):
        xdatascatter = xdata
        ydata = array(ydata)
        ydata = ydata[~isnan(ydata)]
        ydatascatter = [ydata[-1]]
    elif (len(ydata) == 1 and len(xdata) > 1): 
        ydatascatter = ydata
        xdata = array(xdata)
        xdata = xdata[~isnan(xdata)]
        xdatascatter = [xdata[-1]]
    else:
        for j in xrange(len(xdata)):
            if (~isnan(xdata[j]) and ~isnan(ydata[j])):
                xdatascatter.append(xdata[j])
                ydatascatter.append(ydata[j])
    
    return xdatascatter, ydatascatter
        
###############################################################################
def cc2eqn(x, p):
    '''
    2-parameter equation defining cc curves.
    x is total cost, p is a list of parameters (of length 2):
        p[0] = saturation
        p[1] = growth rate
    Returns y which is coverage. '''
    y =  2*p[0] / (1 + exp(-p[1]*x)) - p[0]
    return y
    
###############################################################################
def cco2eqn(x, p):
    '''
    4-parameter equation defining cost-outcome curves.
    x is total cost, p is a list of parameters (of length 2):
        p[0] = saturation
        p[1] = growth rate
        p[2] = outcome at zero coverage
        p[3] = outcome at full coverage
    Returns y which is coverage.'''
    y = (p[3]-p[2]) * (2*p[0] / (1 + exp(-p[1]*x)) - p[0]) + p[2]
    return y

###############################################################################
def cceqn(x, p, eps=1e-3):
    '''
    3-parameter equation defining cost-coverage curve.
    x is total cost, p is a list of parameters (of length 3):
        p[0] = saturation
        p[1] = inflection point
        p[2] = growth rate... 
    Returns y which is coverage.
    '''
    y = p[0] / (1 + exp((log(p[1])-nplog(x))/max(1-p[2],eps)))

    return y
    
###############################################################################
def ccoeqn(x, p):
    '''
    5-parameter equation defining cost-outcome curves.
    x is total cost, p is a list of parameters (of length 5):
        p[0] = saturation
        p[1] = inflection point
        p[2] = growth rate...
        p[3] = outcome at zero coverage
        p[4] = outcome at full coverage
    Returns y which is coverage.
    '''
    y = (p[4]-p[3]) * (p[0] / (1 + exp((log(p[1])-nplog(x))/(1-p[2])))) + p[3]

    return y

###############################################################################
def makecosampleparams(coparams, verbose=default_verbose):
    ''' Convert inputs from GUI into parameters needed for defining curves.'''

    muz, stdevz = (coparams[0]+coparams[1])/2, (coparams[1]-coparams[0])/6 # Mean and standard deviation calcs
    muf, stdevf = (coparams[2]+coparams[3])/2, (coparams[3]-coparams[2])/6 # Mean and standard deviation calcs
    
    printv("coparams: %s muz: %s stdevz: %s muf: %s stdevf: %s" % (coparams, muz, stdevz, muf, stdevf), 5, verbose)
    return muz, stdevz, muf, stdevf


###############################################################################
def makesamples(coparams, muz, stdevz, muf, stdevf, samplesize=1, randseed=None):
    ''' Generate samples of behaviour at zero and full coverage '''
    from numpy.random import seed # Reset seed optionally
    if randseed>=0: seed(randseed)
    
    # Generate samples of zero-coverage and full-coverage behaviour
    zerosample = rtnorm(coparams[0], coparams[1], mu=muz, sigma=stdevz, size=samplesize)[0]
    fullsample = rtnorm(coparams[2], coparams[3], mu=muf, sigma=stdevf, size=samplesize)[0]
        
    return zerosample, fullsample

