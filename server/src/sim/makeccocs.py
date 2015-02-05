"""
Creates and updates cost-coverage curves and coverage-outcome curves
    
Version: 2015jan16 by cliffk
"""
###############################################################################
## Set up
###############################################################################

from math import log
from numpy import linspace, exp, isnan, multiply, arange, mean
from numpy import log as nplog
from rtnorm import rtnorm
from bunch import float_array
from printv import printv
#from scipy.stats import truncnorm
from parameters import input_parameter_name

## Set defaults for testing makeccocs
default_progname = 'ART'
default_ccparams = []# [0.9, 0.1, 0.3, 4000000.0, None, None] #
default_ccplot = []#[1000000, None, 0]
default_coparams = []#[0.3, 0.5, 0.7, 0.9] 
default_effect = [['sex', 'condomcas'], [u'MSM']] # D.programs[default_progname]['effects'][0] 
default_artelig = range(6,31)
coverage_params = ['numost','numpmtct','numfirstline','numsecondline']

## Set defaults for use in getcurrentbudget. The parameters are stored as [median, lower bound, upperbound]
default_convertedccparams = [[0.8, 4.9e-06], [0.8, 4.7e-06], [0.8, 5.1e-06]]
default_convertedccoparams = [[0.8, 4.9e-06, 0.4, 0.8, 0], [0.8, 4.7e-06, 5.1e-06, 0.4, 0.8, 0], [0.8, 4.9e-06, 0.4, 0.8, 0]]

######################################################################
def makecc(D=None, progname=default_progname, ccparams=default_ccparams, ccplot=default_ccplot, artelig=default_artelig, verbose=2, nxpts = 1000):
    '''Make cost coverage curve.

    Input:
    D: main data structure
    progname: string. Needs to be one of the keys of D.programs
    ccparams: list. Contains parameters for the cost-coverage curves, obtained from the GUI. Can be empty.
            ccparams[0] = the saturation value
            ccparams[1] = the lower bound of the 'known' coverage level
            ccparams[2] = the upper bound of the 'known' coverage level
            ccparams[3] = the 'known' funding requirements to achieve ccparams(2)
            ccparams[4] = scale-up rate
            ccparams[5] = non-hiv-dalys averted
    ccplot: list. Contains options for plotting the cost-coverage curves, obtained from the GUI. Can be empty.
            ccplot[0] = upper limit for x axis
            ccplot[1] = None if cost data is to be displayed in current prices
                        year if cost data is to be displayed in [year]'s prices
            ccplot[3] = 0 if we are not adjusting by pop size
                      = 1 if we are
    artelig: list containing the indices for the denominator or ART coverage

    Output:
    plotdata
    storeparams
    '''
    
    if verbose>=2:
        print('makecc %s %s' % (progname, ccparams))

    # Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())

    # Initialise output structure
    plotdata = {}

    # Extract basic info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number    
    totalcost = D.data.costcov.cost[prognumber] # get total cost

    # Adjust cost data to year specified by user (if given)
    if ccplot and ccplot[1]:
        cpi = D.data.econ.cpi.past[0] # get CPI
        cpibaseyear = ccplot[1]
        cpibaseyearindex = D.data.econyears.index(cpibaseyear)
        if len(totalcost)==1: # If it's an assumption, assume it's already in current prices
            totalcost = [totalcost[0]*cpi[cpibaseyearindex]]
        else:
            totalcost = [totalcost[j]*(cpi[cpibaseyearindex]/cpi[j]) if ~isnan(totalcost[j]) else float('nan') for j in range(len(totalcost))]
    else:
        cpibaseyear = D.data.epiyears[-1]

    # Flag to indicate whether we will adjust by population or not
    popadj = 0
    if ccplot and len(ccplot)==3 and ccplot[2]:
        popadj = ccplot[2]

    # Get coverage and target population size (in separate function)       
    coverage, targetpopsize, coveragelabel, convertedccparams, ccplottingparams = getcoverage(D, ccparams, popadj=popadj, artelig=default_artelig, progname=progname)

    # Adjust cost data by target population size, if requested by user 
    if (ccplot and len(ccplot)==3 and ccplot[2]):
        totalcost = totalcost/targetpopsize if len(totalcost)>1 else totalcost/mean(targetpopsize)

    # Get upper limit of x axis for plotting
    xupperlim = max([x if ~isnan(x) else 0.0 for x in totalcost])*1.5
#    if (ccplot and ccplot[0]): xupperlim = max(xupperlim, ccplot[0]) if not (len(ccplot)==3 and ccplot[2]) else max(xupperlim, ccplot[0]/targetpopsize[-1]) if len(totalcost)>1 else max(xupperlim, ccplot[0]/mean(targetpopsize)) 
    if (ccplot and ccplot[0]): xupperlim = ccplot[0] #if not (len(ccplot)==3 and ccplot[2]) else max(xupperlim, ccplot[0]/targetpopsize[-1]) if len(totalcost)>1 else max(xupperlim, ccplot[0]/mean(targetpopsize)) 
        
    # Populate output structure with scatter data 
    totalcost, coverage = getscatterdata(totalcost, coverage)
    plotdata['xscatterdata'] = totalcost
    plotdata['yscatterdata'] = coverage

    # Are there parameters (either given by the user or previously stored)?
    if (ccparams or D.programs[progname]['ccparams']):
        if not ccparams:
            ccparams = D.programs[progname]['ccparams']
        coverage, targetpopsize, coveragelabel, convertedccparams, ccplottingparams = getcoverage(D, ccparams, popadj=popadj, artelig=default_artelig, progname=progname)
        
        # Create curve
        xvalscc = linspace(0,xupperlim,nxpts) # take nxpts points between 0 and user-specified max
        if isinstance(ccparams[4], float):
            yvalsccl = cceqn(xvalscc, ccplottingparams[0])
            yvalsccm = cceqn(xvalscc, ccplottingparams[1])
            yvalsccu = cceqn(xvalscc, ccplottingparams[2])
            yvalscc = [yvalsccl, yvalsccm, yvalsccu]
        else:
            yvalsccl = cc2eqn(xvalscc, ccplottingparams[0])
            yvalsccm = cc2eqn(xvalscc, ccplottingparams[1])
            yvalsccu = cc2eqn(xvalscc, ccplottingparams[2])
            yvalscc = [yvalsccl, yvalsccm, yvalsccu]

        # Populate output structure 
        plotdata['xlinedata'] = xvalscc
        plotdata['ylinedata'] = yvalscc

        # Store parameters and lines
        D.programs[progname]['ccparams'] = ccparams
        D.programs[progname]['ccplot'] = ccplot
        D.programs[progname]['convertedccparams'] = convertedccparams
        if not isinstance(ccparams[5], float):
            ccparams[5] = 0.0
        D.programs[progname]['nonhivdalys'] = [ccparams[5]]

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
def makeco(D, progname=default_progname, effect=default_effect, coparams=default_coparams, verbose=2,nxpts = 1000):
    '''
    Make a single coverage outcome curve.
    
    Inputs: 
    D: main data structure
    progname: string, needs to be one of the keys of D.programs
    effect: list. 
    coparams: list. Contains parameters for the coverage-outcome curves, obtained from the GUI
        coparams[0] = the lower bound for the outcome when coverage = 0
        coparams[1] = the upper bound for the outcome when coverage = 0
        coparams[2] = the lower bound for the outcome when coverage = 1
        coparams[3] = the upper bound for the outcome when coverage = 1

    Output:
    plotdata, storeparams
    '''
    
    # Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())

    # Check that the selected program is in the program list 
    short_effectname = effect[:2] # only matching by effect "signature"
    short_effectlist = [e[:2] for e in D.programs[progname]['effects']]
    if short_effectname not in short_effectlist:
        print "makeco short_effectname: %s short_effectlist: %s" % (short_effectname, short_effectlist)
        raise Exception('Please select one of the following effects %s' % D.programs[progname])
    
    # Initialise output structures
    plotdata = {}

    # Get population and parameter info
    popname = effect[1]
    parname = effect[0][1]

    # Only going to make cost-outcome curves for programs where the affected parameter is not coverage
    if parname not in coverage_params:
        if popname[0] in D.data.meta.pops.short:
            popnumber = D.data.meta.pops.short.index(popname[0])
        else:
            popnumber = 0
        
        # Get data for scatter plots
        outcome = D.data[effect[0][0]][effect[0][1]][popnumber]
        coverage, targetpopsize, coveragelabel, convertedccparams, ccplottingparams = getcoverage(D, params=[], popadj=0, artelig=default_artelig, progname=progname)

        # Populate output structure with axis limits
        plotdata['xlowerlim'], plotdata['ylowerlim']  = 0.0, 0.0
        if coveragelabel == 'Proportion covered':
            plotdata['xupperlim'], plotdata['yupperlim']  = 1.0, 1.0
        else:
            plotdata['xupperlim'], plotdata['yupperlim']  = max([j if ~isnan(j) else 0.0 for j in coverage])*1.5, max([j if ~isnan(j) else 0.0 for x in outcome])*1.5

        # Populate output structure with scatter data 
        coverage, outcome = getscatterdata(coverage, outcome)
        plotdata['xscatterdata'] = coverage # [coverage[j]*100.0 for j in range(len(coverage))]
        plotdata['yscatterdata'] = outcome #[outcome[j]*100.0 for j in range(len(outcome))]
           
        # Get inputs from GUI (#TODO simplify?)
        if coparams and len(coparams)>3:
            zeromin = coparams[0] # Assumptions of behaviour at zero coverage (lower bound)
            zeromax = coparams[1] # Assumptions of behaviour at zero coverage (upper bound)
            fullmin = coparams[2] # Assumptions of behaviour at maximal coverage (lower bound)
            fullmax = coparams[3] # Assumptions of behaviour at maximal coverage (upper bound)
        elif len(effect)>2 and len(effect[2])>3:
            zeromin = effect[2][0] # Assumptions of behaviour at zero coverage (lower bound)
            zeromax = effect[2][1] # Assumptions of behaviour at zero coverage (upper bound)
            fullmin = effect[2][2] # Assumptions of behaviour at maximal coverage (lower bound)
            fullmax = effect[2][3] # Assumptions of behaviour at maximal coverage (upper bound)
            coparams = [zeromin, zeromax, fullmin, fullmax] # Store for output

        # Get inputs from GUI, if they have been given
        if coparams and len(coparams)>0:
            if not len(coparams)==4:
                raise Exception('Not all of the coverage-outcome parameters have been specified. Please enter the missing parameters to define the curve.')
            
            # Generate and store converted parameters
            muz, stdevz, muf, stdevf = makecosampleparams(coparams, verbose=verbose)
            convertedcoparams = [muz, stdevz, muf, stdevf]

            # General set of coverage-outcome relationships
            xvalsco = linspace(0,1.0,nxpts) # take nxpts points along the unit interval
            ymin, ymax = linspace(coparams[0],coparams[2],nxpts), linspace(coparams[1],coparams[3],nxpts)
            
            # Populate output structure with coverage-outcome curves for plotting
            if len(effect) == 2: # There's no existing info here, append
                effect.append(coparams)
                effect.append(convertedcoparams)
            else: # There is existing info here, overwrite it
                effect[2] = coparams
                effect[3] = convertedcoparams

            # Populate output structure with coverage-outcome curves for plotting
            plotdata['xlinedata'] = xvalsco # X data for all line plots
            plotdata['ylinedata'] = [linspace(muz,muf,nxpts), ymax, ymin] # ALL Y data (for three lines)
            plotdata['ylinedata1'] = linspace(muz,muf,nxpts) # Y data for first line on plot
            plotdata['ylinedata2'] = ymax  # Y data for second line on plot
            plotdata['ylinedata3'] = ymin  # Y data for third line on plot

        # Populate output structure with labels and titles
        plotdata['title'] = input_parameter_name(effect[0][1])+ ' - ' + effect[1][0]
        plotdata['xlabel'] = coveragelabel
        plotdata['ylabel'] = 'Outcome'
        
    return plotdata, effect

###############################################################################
def makecco(D=None, progname=default_progname, effect=default_effect, ccparams=default_ccparams, ccplot=default_ccplot, coparams=default_coparams, verbose=2,nxpts = 1000):
    '''
    Make a single cost outcome curve.
    
    Inputs: 
    D: main data structure
    progname: string. Needs to be one of the keys of D.programs
    effectname: list. 
    ccparams: list. Contains parameters for the cost-coverage curves, obtained from the GUI. Can be empty.
            ccparams[0] = the saturation value
            ccparams[1] = the 'known' coverage level
            ccparams[2] = the 'known' funding requirements to achieve ccparams(2)
            ccparams[3] = scale-up rate
            ccparams[4] = non-hiv-dalys averted
    ccplot: list. Contains options for plotting the cost-coverage curves, obtained from the GUI. Can be empty.
            ccplot[0] = upper limit for x axis
            ccplot[1] = None if cost data is to be displayed in current prices
                        year if cost data is to be displayed in [year]'s prices
            ccplot[3] = 0 if we are not adjusting by pop size
                      = 1 if we are
    coparams: list. Contains parameters for the coverage-outcome curves
        coparams(0) = the lower bound for the outcome when coverage = 0
        coparams(1) = the upper bound for the outcome when coverage = 0
        coparams(2) = the lower bound for the outcome when coverage = 1
        coparams(3) = the upper bound for the outcome when coverage = 1

    Output:
    plotdata, plotdata_co, effect
    '''
    
    printv("makecco(%s, %s, %s, %s, %s, %s, %s)" % (progname, effect, ccparams, ccplot, coparams, verbose, nxpts), 2, verbose)

    # Check that the selected program is in the program list 
    if unicode(progname) not in D.programs.keys():
        printv("progname: %s programs: %s" % (unicode(progname), D.programs.keys()), 5, verbose)
        raise Exception('Please select one of the following programs %s' % D.programs.keys())

    # Check that the selected effect is in the list of effects
    short_effectname = effect[:2] # only matching by effect "signature"
    short_effectlist = [e[:2] for e in D.programs[progname]['effects']]
    if short_effectname not in short_effectlist:
        print "makecco short_effectname: %s short_effectlist: %s" % (short_effectname, short_effectlist)
        raise Exception('Please select one of the following effects %s' % D.programs[progname])

    # Initialise output structures
    plotdata = {}
    plotdata_co = {}
    saturation, growthrate, xupperlim = None, None, None

    # Extract info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number

    # Get population and parameter info
    popname = effect[1]
    parname = effect[0][1]

    # Only going to make cost-outcome curves for programs where the affected parameter is not coverage
    if parname not in coverage_params:
        if popname[0] in D.data.meta.pops.short:
            popnumber = D.data.meta.pops.short.index(popname[0])
        else:
            popnumber = 0
        printv("coparams in makecco: %s" % coparams, 5, verbose)

        # Extract cost data and adjust to base year specified by user (if given)
        totalcost = D.data.costcov.realcost[prognumber] # get total cost data
        if ccplot and ccplot[1]:
            cpi = D.data.econ.cpi.past[0] # get CPI
            cpibaseyear = ccplot[1]
            cpibaseyearindex = D.data.econyears.index(cpibaseyear)
            if len(totalcost)==1: # If it's an assumption, assume it's already in current prices
                totalcost = totalcost
            else:
                totalcost = [totalcost[j]*(cpi[cpibaseyearindex]/cpi[j]) if ~isnan(totalcost[j]) else float('nan') for j in range(len(totalcost))]
        else:
            cpibaseyear = D.data.epiyears[-1]

        # Extract outcome data
        outcome = D.data[effect[0][0]][parname][popnumber]

        # Flag to indicate whether we will adjust by population or not
        popadj = 0
        if ccplot and len(ccplot)==3 and ccplot[2]:
            popadj = ccplot[2]

        # Get target population size (in separate function)       
        coverage, targetpopsize, coveragelabel, convertedccparams, ccplottingparams = getcoverage(D, params=[], popadj=0, artelig=default_artelig, progname=progname)

        # Adjust cost data by target population size, if requested by user 
        if (ccplot and len(ccplot)==3 and ccplot[2]):
            totalcost = totalcost/targetpopsize if len(totalcost)>1 else totalcost/mean(targetpopsize)
    
        # Get upper limit of x axis for plotting
        xupperlim = max([x if ~isnan(x) else 0.0 for x in totalcost])*1.5
        if (ccplot and ccplot[0]): xupperlim = ccplot[0] #max(xupperlim, ccplot[0]/targetpopsize[-1]) if len(totalcost)>1 else max(xupperlim, ccplot[0]/mean(targetpopsize)) if (len(ccplot)==3 and ccplot[2]) else max(xupperlim, ccplot[0])

        # Populate output structure with scatter data 
        totalcost, outcome = getscatterdata(totalcost, outcome)
        plotdata['xscatterdata'] = totalcost # X scatter data
        plotdata['yscatterdata'] = outcome # Y scatter data
#        plotdata['yscatterdata'] = [outcome[j]*100.0 for j in range(len(outcome))] # Y scatter data
    
        # Do we have parameters for making curves?
        if (ccparams or D.programs[progname]['ccparams']) and (coparams or (len(effect)>2 and len(effect[2])>3)):

            if not ccparams: # Don't have new ccparams, get previously stored ones
                ccparams = D.programs[progname]['ccparams']
            costparam = ccparams[3]
            if popadj:
                costparam = costparam/targetpopsize
                costparam = mean(costparam) if len(coverage)==1 else [costparam[j] for j in range(len(coverage)) if ~isnan(coverage[j])][0]
            saturation = ccparams[0]
            if isinstance(ccparams[4], float):
                growthratel = exp(ccparams[4]*log(ccparams[0]/ccparams[1]-1)+log(ccparams[3]))
                growthratem = exp(ccparams[4]*log(ccparams[0]/((ccparams[1]+ccparams[2])/2)-1)+log(ccparams[3]))
                growthrateu = exp(ccparams[4]*log(ccparams[0]/ccparams[2]-1)+log(ccparams[3]))
                growthrateplotl = exp(ccparams[4]*log(ccparams[0]/ccparams[1]-1)+log(costparam))
                growthrateplotm = exp(ccparams[4]*log(ccparams[0]/((ccparams[1]+ccparams[2])/2)-1)+log(costparam))
                growthrateplotu = exp(ccparams[4]*log(ccparams[0]/ccparams[2]-1)+log(costparam))
                convertedccoparams = [[saturation, growthratem, ccparams[4]], [saturation, growthratel, ccparams[4]], [saturation, growthrateu, ccparams[4]]]
                convertedccoplotparams = [[saturation, growthrateplotm, ccparams[4]], [saturation, growthrateplotl, ccparams[4]], [saturation, growthrateplotu, ccparams[4]]]
            else:
                growthratel = (-1/ccparams[3])*log((2*ccparams[0])/(ccparams[1]+ccparams[0]) - 1)
                growthratem = (-1/ccparams[3])*log((2*ccparams[0])/(((ccparams[1]+ccparams[2])/2)+ccparams[0]) - 1)
                growthrateu = (-1/ccparams[3])*log((2*ccparams[0])/(ccparams[2]+ccparams[0]) - 1)
                growthrateplotl = (-1/costparam)*log((2*ccparams[0])/(ccparams[1]+ccparams[0]) - 1)        
                growthrateplotm = (-1/costparam)*log((2*ccparams[0])/(((ccparams[1]+ccparams[2])/2)+ccparams[0]) - 1)        
                growthrateplotu = (-1/costparam)*log((2*ccparams[0])/(ccparams[2]+ccparams[0]) - 1)        
                convertedccoparams = [[saturation, growthratem], [saturation, growthratel], [saturation, growthrateu]]
                convertedccoplotparams = [[saturation, growthrateplotm], [saturation, growthrateplotl], [saturation, growthrateplotu]]

            if coparams: # Get coparams from  GUI... 
                muz, stdevz, muf, stdevf = makecosampleparams(coparams, verbose=verbose)
                convertedcoparams = [muz, stdevz, muf, stdevf]
                if len(effect) == 2: # There's no existing info here, append
                    effect.append(coparams)
                    effect.append(convertedcoparams)
                else:
                    effect[2] = coparams
                    effect[3] = convertedcoparams
            else: # ... or access previously stored ones
                coparams = effect[2]
                convertedcoparams = effect[3]

            for j in range(3): convertedccoparams[j].extend([convertedcoparams[0],convertedcoparams[2]])
            for j in range(3): convertedccoplotparams[j].extend([convertedcoparams[0],convertedcoparams[2]])
            if len(effect) < 5: # There's no existing info here, append
                effect.append(convertedccoparams)
            else:
                effect[4] = convertedccoparams

            # Create x dataset and initialise y dataset
            xvalscco = linspace(0,xupperlim,nxpts)
    
            # Min, Median and Max lines
            if isinstance(ccparams[4], float):
                mediancco = ccoeqn(xvalscco, convertedccoplotparams[0])# Generate min cost-outcome curve
                mincco = ccoeqn(xvalscco, [convertedccoplotparams[1][0], convertedccoplotparams[1][1], convertedccoplotparams[1][2], coparams[0], coparams[2]])# Generate min cost-outcome curve
                maxcco = ccoeqn(xvalscco, [convertedccoplotparams[2][0], convertedccoplotparams[2][1], convertedccoplotparams[2][2], coparams[1], coparams[3]])# Generate max cost-outcome curve
            else:
                mediancco = cco2eqn(xvalscco, convertedccoplotparams[0])# Generate min cost-outcome curve
                mincco = cco2eqn(xvalscco, [convertedccoplotparams[1][0], convertedccoplotparams[1][1], coparams[0], coparams[2]])# Generate min cost-outcome curve
                maxcco = cco2eqn(xvalscco, [convertedccoplotparams[2][0], convertedccoplotparams[2][1], coparams[1], coparams[3]])# Generate max cost-outcome curve

            # Populate output structure with cost-outcome curves for plotting
            plotdata['xlinedata'] = xvalscco # X data for all line plots
            plotdata['ylinedata'] = [mediancco,maxcco,mincco] # Y data for second line plot
            plotdata['ylinedata1'] = mediancco # Y data for second line plot
            plotdata['ylinedata2'] = maxcco  # Y data for third line plot
            plotdata['ylinedata3'] = mincco  # Y data for fourth line plot

        # Get the coverage-outcome relationships (this should be kept in the outer level, 
        # unless the intention is do not produce coverage-outcome relationships when ccparams / coparams are not present - AN)
        plotdata_co, effect = makeco(D, progname, effect, coparams, verbose=verbose)

        # Populate output structure with axis limits
        plotdata['xlowerlim'], plotdata['ylowerlim']  = 0.0, 0.0
        plotdata['xupperlim'], plotdata['yupperlim']  = xupperlim, 1.0
    
        # Populate output structure with labels and titles
        plotdata['title'] = input_parameter_name(effect[0][1])+ ' - ' + effect[1][0]
        plotdata['xlabel'] = 'USD'+ ', ' + str(int(cpibaseyear)) + ' prices'
        plotdata['ylabel'] = 'Outcome'
        
    return plotdata, plotdata_co, effect

###############################################################################
def plotallcurves(D=None, progname=default_progname, ccparams=default_ccparams, ccplot=default_ccplot, coparams=default_coparams, verbose=2):
    '''
    Make all cost outcome curves for a given program.
    '''
    
     # Get the cost-coverage and coverage-outcome relationships     
    plotdata_cc, D = makecc(D=D, progname=progname, ccplot=ccplot, ccparams=ccparams, verbose=verbose)

   ## Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())

    ## Initialise storage of outputs   
    plotdata_co = {}
    plotdata = {}    
    effects = {}     

    # Loop over behavioural effects
    for effectnumber, effect in enumerate(D.programs[progname]['effects']):

        # Get parameter info
        parname = effect[0][1]

        # Only going to make cost-outcome curves for programs where the affected parameter is not coverage
        if parname not in coverage_params:

            # Store outputs
            effects[effectnumber] = effect 
            plotdata[effectnumber], plotdata_co[effectnumber], effect = makecco(D=D, progname=progname, effect=effect, ccplot=ccplot, ccparams=D.programs[progname]['ccparams'], coparams=coparams, verbose=verbose)
            effects[effectnumber] = effect 

    return plotdata, plotdata_co, plotdata_cc, effects, D      

###############################################################################
def makeallccocs(D=None, verbose=2):
    '''
    Make all curves for all programs.
    '''

    for progname in D.programs.keys():
        plotdata_cco, plotdata_co, plotdata_cc, effects, D = plotallcurves(D, unicode(progname))
    return D

###############################################################################
def getcoverage(D=None, params=[], popadj=0, artelig=default_artelig, progname=default_progname):
    '''
    Get coverage levels.
    '''
    
    # Extract basic info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number
    ndatayears = len(D.data.epiyears) # get number of data years
    
    # Sort out time vector and indexing
    tvec = arange(D.G.datastart, D.G.dataend+D.opt.dt, D.opt.dt) # Extract the time vector from the sim
    npts = len(tvec) # Number of sim points

    # Figure out the targeted population(s) 
    targetpops = []
    targetpars = []
    popnumbers = []
    for effect in D.programs[progname]['effects']:
        targetpops.append(effect[1][0])
        targetpars.append(effect[0][1])
        if effect[1][0] in D.data.meta.pops.short:
            popnumbers.append(D.data.meta.pops.short.index(effect[1][0]))
    targetpops = list(set(targetpops))
    targetpars = list(set(targetpars))
    popnumbers = list(set(popnumbers))

    # Figure out the total model-estimated size of the targeted population(s)
    for thispar in targetpars: # Loop through parameters
        if len(D.P[thispar].p)==D.G.npops: # For parameters whose effect is differentiated by population, we add up the targeted populations
            targetpopmodel = D.S.people[:,popnumbers,0:npts].sum(axis=(0,1))
        elif len(D.P[thispar].p)==1: # For parameters whose effects are not differentiated by population, we make special cases depending on the parameter
            if thispar == 'aidstest': # Target population = diagnosed PLHIV, AIDS stage
                targetpopmodel = D.S.people[27:31,:,0:npts].sum(axis=(0,1))
            elif thispar in ['numost','sharing']: # Target population = the sum of all populations that inject
                injectindices = [i for i, x in enumerate(D.data.meta.pops.injects) if x == 1]
                targetpopmodel = D.S.people[:,injectindices,0:npts].sum(axis = (0,1))
            elif thispar == 'numpmtct': # Target population = HIV+ pregnant women
                targetpopmodel = multiply(D.M.birth[:,0:npts], D.S.people[artelig,:,0:npts].sum(axis=0)).sum(axis=0)
            elif thispar == 'breast': # Target population = HIV+ breastfeeding women
                targetpopmodel = multiply(D.M.birth[:,0:npts], D.M.breast[0:npts], D.S.people[artelig,:,0:npts].sum(axis=0)).sum(axis=0)
            elif thispar in ['numfirstline','numsecondline']: # Target population = diagnosed PLHIV
                targetpopmodel = D.S.people[artelig,:,0:npts].sum(axis=(0,1))
            else:
                print('WARNING, Unrecognized parameter %s' % thispar)
        else:
            print('WARNING, Parameter %s of odd length %s' % (thispar, len(D.P[thispar].p)))
    if len(targetpars)==0:
        print('WARNING, no target parameters for program %s' % progname)
                
    # We only want the model-estimated size of the targeted population(s) for actual years, not the interpolated years
    yearindices = range(0,npts,int(1/D.opt.dt))
    targetpop = targetpopmodel[yearindices]

    # Do population adjustments if required
    storeparams = params
    plottingparams = params
    coverage = None
    coveragelabel = ''

    # Check if coverage was entered as a percentage, and if not convert it to a %. 
    if any(j < 1 for j in D.data.costcov.cov[prognumber]):
        coveragepercent = D.data.costcov.cov[prognumber] 
        if len(coveragepercent)==1: # If an assumption has been used, keep this constant over time
            coveragenumber = coveragepercent * targetpop
        else:
            coveragenumber = [coveragepercent[j] * targetpop[j] for j in range(ndatayears)] # get program coverage 
        coverage = coveragepercent # this is unnecessary now but might be useful later to set it up this way
        coveragelabel = 'Proportion covered'
        if params:
            costparam = params[3]
            if popadj:
                costparam = params[3]/targetpop
                costparam = mean(costparam) if len(coverage)==1 else [costparam[j] for j in range(len(coverage)) if ~isnan(coverage[j])][0]
            saturation = params[0]
            if isinstance(params[4], float):
                growthratel = exp((1-params[4])*log(params[0]/params[1]-1)+log(params[3]))
                growthratem = exp((1-params[4])*log(params[0]/((params[1]+params[2])/2)-1)+log(params[3]))
                growthrateu = exp((1-params[4])*log(params[0]/params[2]-1)+log(params[3]))
                growthrateplotl = exp((1-params[4])*log(params[0]/params[1]-1)+log(costparam))
                growthrateplotm = exp((1-params[4])*log(params[0]/((params[1]+params[2])/2)-1)+log(costparam))
                growthrateplotu = exp((1-params[4])*log(params[0]/params[2]-1)+log(costparam))
                storeparams = [[saturation, growthratem, params[4]], [saturation, growthratel, params[4]], [saturation, growthrateu, params[4]]]
                plottingparams = [[saturation, growthrateplotm, params[4]], [saturation, growthrateplotl, params[4]], [saturation, growthrateplotu, params[4]]]
            else:
                growthratel = (-1/params[3])*log((2*params[0])/(params[1]+params[0]) - 1)        
                growthratem = (-1/params[3])*log((2*params[0])/(((params[1]+params[2])/2)+params[0]) - 1)        
                growthrateu = (-1/params[3])*log((2*params[0])/(params[2]+params[0]) - 1)        
                growthrateplotl = (-1/costparam)*log((2*params[0])/(params[1]+params[0]) - 1)        
                growthrateplotm = (-1/costparam)*log((2*params[0])/(((params[1]+params[2])/2)+params[0]) - 1)        
                growthrateplotu = (-1/costparam)*log((2*params[0])/(params[2]+params[0]) - 1)        
                storeparams = [[saturation, growthratem], [saturation, growthratel], [saturation, growthrateu]]
                plottingparams = [[saturation, growthrateplotm], [saturation, growthrateplotl], [saturation, growthrateplotu]]
    else:
        coveragenumber = D.data.costcov.cov[prognumber] 
        if len(coveragenumber)==1: # If an assumption has been used, keep this constant over time
            coveragepercent = (coveragenumber/targetpop)*100
        else:
            coveragepercent = [(coveragenumber[j]/targetpop[j])*100 for j in range(ndatayears)] # get program coverage
        coverage = coveragenumber # this is unnecessary atm but might be useful later to set it up this way
        coveragelabel = 'Number covered'
        if params:
            costparam = params[3]
            if popadj:
                costparam = params[3]/targetpop
                costparam = mean(costparam) if len(coverage)==1 else [costparam[j] for j in range(len(coverage)) if ~isnan(coverage[j])][0]
            saturation = params[0]*targetpop[-1]
            if isinstance(params[4], float):
                growthratel = exp((1-params[4])*log(params[0]/params[1]-1)+log(params[3]))
                growthratem = exp((1-params[4])*log(params[0]/((params[1]+params[2])/2)-1)+log(params[3]))
                growthrateu = exp((1-params[4])*log(params[0]/params[2]-1)+log(params[3]))
                growthrateplotl = exp((1-params[4])*log(params[0]/params[1]-1)+log(costparam))
                growthrateplotm = exp((1-params[4])*log(params[0]/((params[1]+params[2])/2)-1)+log(costparam))
                growthrateplotu = exp((1-params[4])*log(params[0]/params[2]-1)+log(costparam))
                storeparams = [[saturation, growthratem, params[4]], [saturation, growthratel, params[4]], [saturation, growthrateu, params[4]]]
                plottingparams = [[saturation, growthrateplotm, params[4]], [saturation, growthrateplotl, params[4]], [saturation, growthrateplotu, params[4]]]
            else:
                growthratel = (-1/params[3])*log((2*params[0]*targetpop[-1])/(params[1]*targetpop[-1]+params[0]*targetpop[-1]) - 1)
                growthratem = (-1/params[3])*log((2*params[0]*targetpop[-1])/(((params[1]+params[2])/2)*targetpop[-1]+params[0]*targetpop[-1]) - 1)
                growthrateu = (-1/params[3])*log((2*params[0]*targetpop[-1])/(params[2]*targetpop[-1]+params[0]*targetpop[-1]) - 1)
                growthrateplotl = (-1/costparam)*log((2*params[0]*targetpop[-1])/(params[1]*targetpop[-1]+params[0]*targetpop[-1]) - 1)
                growthrateplotm = (-1/costparam)*log((2*params[0]*targetpop[-1])/(((params[1]+params[2])/2)*targetpop[-1]+params[0]*targetpop[-1]) - 1)
                growthrateplotu = (-1/costparam)*log((2*params[0]*targetpop[-1])/(params[2]*targetpop[-1]+params[0]*targetpop[-1]) - 1)
                storeparams = [[saturation, growthratem], [saturation, growthratel], [saturation, growthrateu]]
                plottingparams = [[saturation, growthrateplotm], [saturation, growthrateplotl], [saturation, growthrateplotu]]
                    
    return coverage, targetpop, coveragelabel, storeparams, plottingparams


###############################################################################
def getscatterdata(xdata, ydata):
    '''
    Short function to remove nans and make sure the right scatter data is sent to FE
    '''
    xdatascatter = []
    ydatascatter = []

    if (len(xdata) == 1 and len(ydata) > 1):
        xdatascatter = xdata
        ydata = float_array(ydata)
        ydata = ydata[~isnan(ydata)]
        ydatascatter = [ydata[-1]]
    elif (len(ydata) == 1 and len(xdata) > 1): 
        ydatascatter = ydata
        xdata = float_array(xdata)
        xdata = xdata[~isnan(xdata)]
        xdatascatter = [xdata[-1]]
    else:
        for j in range(len(xdata)):
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
    Returns y which is coverage.
    '''
    y =  2*p[0] / (1 + exp(-p[1]*x)) - p[0]
    return y
    
###############################################################################
def cco2eqn(x, p):
    '''
    Equation defining cco curves.
    '''
    y = (p[3]-p[2]) * (2*p[0] / (1 + exp(-p[1]*x)) - p[0]) + p[2]
    return y

###############################################################################
def cceqn(x, p, eps=1e-3):
    '''
    3-parameter equation defining cc curves.

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
    Equation defining cco curves.

    x is total cost, p is a list of parameters (of length 3):
        p[0] = saturation
        p[1] = inflection point
        p[2] = growth rate...

    Returns y which is coverage.
    '''
    y = (p[4]-p[3]) * (p[0] / (1 + exp((log(p[1])-nplog(x))/(1-p[2])))) + p[3]

    return y


###############################################################################
def makecosampleparams(coparams, verbose=2):
    '''
    Convert inputs from GUI into parameters needed for defining curves.
    '''

    muz, stdevz = (coparams[0]+coparams[1])/2, (coparams[1]-coparams[0])/6 # Mean and standard deviation calcs
    muf, stdevf = (coparams[2]+coparams[3])/2, (coparams[3]-coparams[2])/6 # Mean and standard deviation calcs
    
    printv("coparams: %s muz: %s stdevz: %s muf: %s stdevf: %s" % (coparams, muz, stdevz, muf, stdevf), 5, verbose)
    return muz, stdevz, muf, stdevf


###############################################################################
def makesamples(coparams, muz, stdevz, muf, stdevf, samplesize=1000, randseed=None):
    '''
    Generate samples of behaviour at zero and full coverage
    '''
    from numpy.random import seed # Reset seed optionally
    if randseed>=0: seed(randseed)
    
    # Generate samples of zero-coverage and full-coverage behaviour
    zerosample = rtnorm(coparams[0], coparams[1], mu=muz, sigma=stdevz, size=samplesize)[0]
    fullsample = rtnorm(coparams[2], coparams[3], mu=muf, sigma=stdevf, size=samplesize)[0]
        
    return zerosample, fullsample


