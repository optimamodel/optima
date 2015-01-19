"""
Creates and updates cost-coverage curves and coverage-outcome curves
    
Version: 2015jan16 by cliffk
"""
###############################################################################
## Set up
###############################################################################

from math import log
from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title, xlim, ylim
from numpy import linspace, exp, isnan, asarray, multiply
from numpy import log as nplog
from rtnorm import rtnorm
from bunch import float_array
from printv import printv
#from scipy.stats import truncnorm
from parameters import input_parameter_name

## Set defaults for testing makeccocs
default_progname = 'MSM programs'
default_ccparams = []
default_ccplot =  [] #[None, None]
default_coparams = []#[0.3, 0.5, 0.7, 0.9] 
default_makeplot = 0 # CK: Otherwise brings up >100 figures
default_effect = [['sex', 'condomcas'], [u'MSM']] # D.programs[default_progname]['effects'][0] 
default_artelig = range(6,31)
coverage_params = ['numost','numpmtct','numfirstline','numsecondline']

## Set defaults for use in getcurrentbudget
default_convertedccparams = [0.8, 4.86477537263828e-06]
default_convertedccoparams = [0.8, 4.86477537263828e-06, 0.4, 0.8, 0]

######################################################################
def makecc(D=None, progname=default_progname, ccparams=default_ccparams, ccplot=default_ccplot, artelig=default_artelig, makeplot=default_makeplot, verbose=2, nxpts = 1000):
    '''Make cost coverage curve.

    Input:
    D: main data structure
    progname: string. Needs to be one of the keys of D.programs
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
    totalcost = D.data.costcov.realcost[prognumber] # get total cost

    # Adjust cost data to year specified by user (if given)
    if ccplot and ccplot[1]:
        cpi = D.data.econ.cpi[0] # get CPI
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
        ccplot[0] = None

    # Get coverage and target population size (in separate function)       
    coverage, targetpopsize, coveragelabel, convertedccparams, ccplottingparams = getcoverage(D, ccparams, popadj=popadj, artelig=default_artelig, progname=progname)

    # Check the lengths or coverage and cost are the same and extract the appropriate scatter data
    if (len(totalcost) == 1 and len(coverage) > 1):
        coverage = float_array(coverage)
        coverage = coverage[~isnan(coverage)]
        coverage = coverage[-1]
        # Adjust cost data by target population size, if requested by user 
        if (ccplot and len(ccplot)==3 and ccplot[2]):
            totalcost = totalcost/targetpopsize[-1]
    elif (len(coverage) == 1 and len(totalcost) > 1): 
        # Adjust cost data by target population size, if requested by user 
        if (ccplot and len(ccplot)==3 and ccplot[2]):
            totalcost = totalcost/targetpopsize
        totalcost = float_array(totalcost)
        totalcost = totalcost[~isnan(totalcost)]
        totalcost = totalcost[-1]
    else:
        totalcostscatter = []
        coveragescatter = []
        for j in range(len(totalcost)):
            if (~isnan(totalcost[j]) and ~isnan(coverage[j])):
                totalcostscatter.append(totalcost[j])
                coveragescatter.append(coverage[j])
        totalcost = totalcostscatter
        coverage = coveragescatter
        # Adjust cost data by target population size, if requested by user 
        if (ccplot and len(ccplot)==3 and ccplot[2]):
            totalcost = [totalcost[j]/targetpopsize[j] for j in range(len(totalcost))]
        
    # Populate output structure with scatter data 
    plotdata['xscatterdata'] = totalcost
    plotdata['yscatterdata'] = coverage

    # Get upper limit of x axis for plotting
    if ccplot and ccplot[0]:
        xupperlim = max(max([x if ~isnan(x) else 0.0 for x in totalcost])*1.5, ccplot[0])
    else:
        xupperlim = max([x if ~isnan(x) else 0.0 for x in totalcost])*1.5

    # Are there parameters (either given by the user or previously stored)?
    if (ccparams or D.programs[progname]['ccparams']):
        if not ccparams:
            ccparams = D.programs[progname]['ccparams']
        coverage, targetpopsize, coveragelabel, convertedccparams, ccplottingparams = getcoverage(D, ccparams, popadj=popadj, artelig=default_artelig, progname=progname)
        
        # Check inputs
        if (ccparams[0] <= 0 or ccparams[0] > 1):
            raise Exception('Please enter a value between 0 and 1 for the saturation coverage level')
        if (ccparams[1] < 0 or ccparams[1] > 1):
            raise Exception('Please enter a value between 0 and 1 for the coverage level in Question 2')
        if (ccparams[1] == 0 or ccparams[2] == 0):
            raise Exception('Please enter non-zero values for the cost and coverage level estimates in Question 2')
        if ccparams[2] < 0:
            raise Exception('Negative funding levels are not permitted, please revise')

        # Create curve
        xvalscc = linspace(0,xupperlim,nxpts) # take nxpts points between 0 and user-specified max
        if isinstance(ccparams[3], float):
            yvalscc = cceqn(xvalscc, ccplottingparams)
        else:
            yvalscc = cc2eqn(xvalscc, ccplottingparams)

        # Populate output structure 
        plotdata['xlinedata'] = xvalscc
        plotdata['ylinedata'] = yvalscc

        # Store parameters and lines
        D.programs[progname]['ccparams'] = ccparams
        D.programs[progname]['ccplot'] = ccplot
        D.programs[progname]['convertedccparams'] = convertedccparams
        if not isinstance(ccparams[4], float):
            ccparams[4] = 0.0
        D.programs[progname]['nonhivdalys'] = [ccparams[4]]

    # Populate output structure with axis limits
    plotdata['xlowerlim'], plotdata['ylowerlim']  = 0.0, 0.0
    plotdata['xupperlim'] = xupperlim 
    if coveragelabel == 'Proportion covered':
        plotdata['yupperlim']  = 1.0
    else:
        if ccparams:
            plotdata['yupperlim']  = max(convertedccparams[0]*1.2,max([x if ~isnan(x) else 0.0 for x in coverage])*1.2)
        else:
            plotdata['yupperlim']  = max([x if ~isnan(x) else 0.0 for x in coverage])*1.5

    # Populate output structure with labels and titles
    plotdata['title'] = progname
    plotdata['xlabel'] = 'USD'+ ', ' + str(int(cpibaseyear)) + ' prices'
    plotdata['ylabel'] = coveragelabel
    
    # Plot 
    if makeplot:
        printv("plotting cc for program %s" % progname, 4, verbose)   
        figure()
        hold(True)
        if ccparams: plot(plotdata['xlinedata'], plotdata['ylinedata'], 'k-', lw = 2)
        plot(plotdata['xscatterdata'], plotdata['yscatterdata'], 'ro')
        title(plotdata['title'])
        xlabel(plotdata['xlabel'])
        ylabel(plotdata['ylabel'])
        xlim([plotdata['xlowerlim'],plotdata['xupperlim']])
        ylim([plotdata['ylowerlim'],plotdata['yupperlim']])

    return plotdata, D

######################################################################
def makeco(D, progname=default_progname, effect=default_effect, coparams=default_coparams, makeplot=default_makeplot, verbose=2,nxpts = 1000):
    '''
    Make a single coverage outcome curve.
    
    Inputs: 
    D: main data structure
    progname: string, needs to be one of the keys of D.programs
    effect: list. 
    coparams: list. Contains parameters for the coverage-outcome curves, obtained from the GUI
        coparams(0) = the lower bound for the outcome when coverage = 0
        coparams(1) = the upper bound for the outcome when coverage = 0
        coparams(2) = the lower bound for the outcome when coverage = 1
        coparams(3) = the upper bound for the outcome when coverage = 1

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

        if (len(coverage) == 1 and len(outcome) > 1): 
            outcome = asarray(outcome)
            outcome = outcome[~isnan(outcome)]
            outcome = outcome[-1]
        elif (len(outcome) == 1 and len(coverage) > 1):
            coverage = asarray(coverage)
            coverage = coverage[~isnan(coverage)]
            coverage = coverage[-1]
        else:
            coveragescatter = []
            outcomescatter = []
            for j in range(len(coverage)):
                if (~isnan(coverage[j]) and ~isnan(outcome[j])):
                    coveragescatter.append(coverage[j])
                    outcomescatter.append(outcome[j])
            coverage = coveragescatter
            outcome = outcomescatter
            
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

            # Check inputs
#            if any((j<0 or j>1) for j in coparams):
#                raise Exception('Please enter values between 0 and 1 for the ranges of behaviour at zero and full coverage')
            
            # Generate sample of zero-coverage behaviour
            muz, stdevz, muf, stdevf = makecosampleparams(coparams, verbose=verbose)
            zerosample, fullsample = makesamples(coparams, muz, stdevz, muf, stdevf, D.opt.nsims)

            # Store parameters for access later
            convertedcoparams = [muz, stdevz, muf, stdevf]
        
            # General set of coverage-outcome relationships
            xvalsco = linspace(0,1,nxpts) # take nxpts points along the unit interval
            ymin, ymax = linspace(coparams[0],coparams[2],nxpts), linspace(coparams[1],coparams[3],nxpts)
            
            # Populate output structure with coverage-outcome curves for plotting
            # Store parameters and lines
            if len(effect) == 2: # There's no existing info here, append
                effect.append(coparams)
                effect.append(convertedcoparams)
            else:
                effect[2] = coparams
                effect[3] = convertedcoparams

            # Populate output structure with coverage-outcome curves for plotting
            plotdata['xlinedata'] = xvalsco # X data for all line plots
            plotdata['ylinedata'] = [linspace(muz,muf,nxpts), ymax, ymin] # ALL Y data (for three lines)
            plotdata['ylinedata1'] = linspace(muz,muf,nxpts) # Y data for first line on plot
            plotdata['ylinedata2'] = ymax  # Y data for second line on plot
            plotdata['ylinedata3'] = ymin  # Y data for third line on plot

        # Populate output structure with scatter data 
        plotdata['xscatterdata'] = coverage # X scatter data
        plotdata['yscatterdata'] = outcome # Y scatter data

        # Populate output structure with labels and titles
        plotdata['title'] = input_parameter_name(effect[0][1])+ ' - ' + effect[1][0]
        plotdata['xlabel'] = coveragelabel
        plotdata['ylabel'] = 'Outcome'

        # Plot results                           
        if makeplot:
            figure()
            hold(True)
            if coparams:
                plot(plotdata['xlinedata'], plotdata['ylinedata1'], color = 'b', lw = 2)
                plot(plotdata['xlinedata'], plotdata['ylinedata2'], 'k--', lw = 2)
                plot(plotdata['xlinedata'], plotdata['ylinedata3'], 'k--', lw = 2)
            plot(plotdata['xscatterdata'], plotdata['yscatterdata'], 'ro')
            title(plotdata['title'])
            xlabel(plotdata['xlabel'])
            ylabel(plotdata['ylabel'])
            xlim([plotdata['xlowerlim'],plotdata['xupperlim']])
            ylim([plotdata['ylowerlim'],plotdata['yupperlim']])
        
    return plotdata, effect

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
    y = (p[3]-p[2]) * ( 2*p[0] / (1 + exp(-p[1]*x)) - p[0]) + p[2]
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
def makecco(D=None, progname=default_progname, effect=default_effect, ccparams=default_ccparams, ccplot=default_ccplot, coparams=default_coparams, makeplot=default_makeplot, verbose=2,nxpts = 1000):
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
    
    printv("makecco(%s, %s, %s, %s, %s, %s, %s, %s)" % (progname, effect, ccparams, ccplot, coparams, makeplot, verbose, nxpts), 2, verbose)

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

    # Extract info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number

    # Get population and parameter info
    popname = effect[1]
    parname = effect[0][1]

    saturation, growthrate, xupperlim = None, None, None

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
            cpi = D.data.econ.cpi[0] # get CPI
            cpibaseyear = ccplot[1]
            cpibaseyearindex = D.data.econyears.index(cpibaseyear)
            if len(totalcost)==1: # If it's an assumption, assume it's already in current prices
                totalcost = totalcost
            else:
                totalcost = [totalcost[j]*(cpi[cpibaseyearindex]/cpi[j]) if ~isnan(totalcost[j]) else float('nan') for j in range(len(totalcost))]
        else:
            cpibaseyear = D.data.epiyears[-1]

        # Extract outcome data
        outcome = D.data[effect[0][0]][effect[0][1]][popnumber]

        # Flag to indicate whether we will adjust by population or not
        popadj = 0
        if ccplot and len(ccplot)==3 and ccplot[2]:
            popadj = ccplot[2]
            ccplot[0] = None

        # Get target population size (in separate function)       
        coverage, targetpopsize, coveragelabel, convertedccparams, ccplottingparams = getcoverage(D, params=[], popadj=0, artelig=default_artelig, progname=progname)

        # Get around situations where there's an assumption for coverage but not for behaviour, or vice versa
        if (len(totalcost) == 1 and len(outcome) > 1): 
            # Adjust cost data by target population size, if requested by user 
            if (ccplot and len(ccplot)==3 and ccplot[2]):
                totalcost = totalcost/targetpopsize[-1]
            outcome = float_array(outcome)
            outcome = outcome[~isnan(outcome)]
            outcome = [outcome[-1]]
        elif (len(outcome) == 1 and len(totalcost) > 1):
            # Adjust cost data by target population size, if requested by user 
            if (ccplot and len(ccplot)==3 and ccplot[2]):
                totalcost = totalcost/targetpopsize[-1]
            totalcost = float_array(totalcost)
            totalcost = totalcost[~isnan(totalcost)]
            totalcost = [totalcost[-1]]
        else:
            # Adjust cost data by target population size, if requested by user 
            if (ccplot and len(ccplot)==3 and ccplot[2]):
                totalcost = [totalcost[j]/targetpopsize[j] for j in range(len(totalcost))]
            totalcostscatter = []
            outcomescatter = []
            for j in range(len(totalcost)):
                if (~isnan(totalcost[j]) and ~isnan(outcome[j])):
                    totalcostscatter.append(totalcost[j])
                    outcomescatter.append(outcome[j])
            totalcost = totalcostscatter
            outcome = outcomescatter

        # Populate output structure with scatter data 
        plotdata['xscatterdata'] = totalcost # X scatter data
        plotdata['yscatterdata'] = outcome # Y scatter data
    
        # Get upper limit of x axis for plotting
        if ccplot and ccplot[0]:
            xupperlim = max(ccplot[0], max([j if ~isnan(j) else 0.0 for j in totalcost])*1.5)
        else:
            xupperlim = max([x if ~isnan(x) else 0.0 for x in totalcost])*1.5

        # Do we have parameters for making curves?
        if (ccparams or D.programs[progname]['ccparams']) and (coparams or (len(effect)>2 and len(effect[2])>3)):

            if not ccparams: # Don't have new ccparams, get previously stored ones
                ccparams = D.programs[progname]['ccparams']
            costparam = ccparams[2]
            if popadj: costparam = ccparams[2]/targetpopsize[-1]
            saturation = ccparams[0]
            if isinstance(ccparams[3], float):
                growthrate = exp(ccparams[3]*log(ccparams[0]/ccparams[1]-1)+log(ccparams[2]))
                growthrateplot = exp(ccparams[3]*log(ccparams[0]/ccparams[1]-1)+log(costparam))
                convertedccoparams = [saturation, growthrate, ccparams[3]]
                convertedccoplotparams = [saturation, growthrateplot, ccparams[3]]
            else:
                growthrate = (-1/ccparams[2])*log((2*ccparams[0])/(ccparams[1]+ccparams[0]) - 1)        
                growthrateplot = (-1/costparam)*log((2*ccparams[0])/(ccparams[1]+ccparams[0]) - 1)        
                convertedccoparams = [saturation, growthrate]
                convertedccoplotparams = [saturation, growthrateplot]

            if coparams: # Get coparams from  GUI... 
                muz, stdevz, muf, stdevf = makecosampleparams(coparams, verbose=verbose)
                zerosample, fullsample = makesamples(coparams, muz, stdevz, muf, stdevf, D.opt.nsims)
                convertedcoparams = [muz, stdevz, muf, stdevf]
                # Store parameters for access later
                if len(effect) == 2: # There's no existing info here, append
                    effect.append(coparams)
                    effect.append(convertedcoparams)
                else:
                    effect[2] = coparams
                    effect[3] = convertedcoparams
            else: # ... or access previously stored ones
                coparams = effect[2]
                convertedcoparams = effect[3]

            convertedccoparams.extend([convertedcoparams[0],convertedcoparams[2]])
            convertedccoplotparams.extend([convertedcoparams[0],convertedcoparams[2]])
            if len(effect) < 5: # There's no existing info here, append
                effect.append(convertedccoparams)
            else:
                effect[4] = convertedccoparams

            # Create x dataset and initialise y dataset
            xvalscco = linspace(0,xupperlim,nxpts)
    
            # Min, Median and Max lines
            if isinstance(ccparams[3], float):
                mediancco = ccoeqn(xvalscco, convertedccoplotparams)# Generate median cost-outcome curve
                mincco = ccoeqn(xvalscco, [convertedccoplotparams[0], convertedccoplotparams[1], convertedccoplotparams[2], coparams[0], coparams[2]])# Generate min cost-outcome curve
                maxcco = ccoeqn(xvalscco, [convertedccoplotparams[0], convertedccoplotparams[1], convertedccoplotparams[2], coparams[1], coparams[3]])# Generate max cost-outcome curve
            else:
                mediancco = cco2eqn(xvalscco, convertedccoplotparams)# Generate median cost-outcome curve
                mincco = cco2eqn(xvalscco, [convertedccoplotparams[0], convertedccoplotparams[1], coparams[0], coparams[2]])# Generate min cost-outcome curve
                maxcco = cco2eqn(xvalscco, [convertedccoplotparams[0], convertedccoplotparams[1], coparams[1], coparams[3]])# Generate max cost-outcome curve

            # Populate output structure with cost-outcome curves for plotting
            plotdata['xlinedata'] = xvalscco # X data for all line plots
            plotdata['ylinedata'] = [mediancco,maxcco,mincco] # Y data for second line plot
            plotdata['ylinedata1'] = mediancco # Y data for second line plot
            plotdata['ylinedata2'] = maxcco  # Y data for third line plot
            plotdata['ylinedata3'] = mincco  # Y data for fourth line plot

        # Get the coverage-outcome relationships (this should be kept in the outer level, 
        # unless the intention is do not produce coverage-outcome relationships when ccparams / coparams are not present - AN)
        plotdata_co, effect = makeco(D, progname, effect, coparams, makeplot=makeplot, verbose=verbose)

        # Populate output structure with axis limits
        plotdata['xlowerlim'], plotdata['ylowerlim']  = 0.0, 0.0
        plotdata['xupperlim'], plotdata['yupperlim']  = xupperlim, 1.0
    
        # Populate output structure with labels and titles
        plotdata['title'] = input_parameter_name(effect[0][1])+ ' - ' + effect[1][0]
        plotdata['xlabel'] = 'USD'+ ', ' + str(int(cpibaseyear)) + ' prices'
        plotdata['ylabel'] = 'Outcome'
        
        # Plot results 
        if makeplot:
            figure()
            hold(True)
            if coparams and ccparams:
                plot(plotdata['xlinedata'], plotdata['ylinedata1'], color = 'b', lw = 2)
                plot(plotdata['xlinedata'], plotdata['ylinedata2'], 'k--', lw = 2)
                plot(plotdata['xlinedata'], plotdata['ylinedata3'], 'k--', lw = 2)
            plot(plotdata['xscatterdata'], plotdata['yscatterdata'], 'ro')                
            title(plotdata['title'])
            xlabel(plotdata['xlabel'])
            ylabel(plotdata['ylabel'] )
            xlim([plotdata['xlowerlim'],plotdata['xupperlim']])
            ylim([plotdata['ylowerlim'],plotdata['yupperlim']])
    
    return plotdata, plotdata_co, effect

###############################################################################
def plotallcurves(D=None, progname=default_progname, ccparams=default_ccparams, ccplot=default_ccplot, coparams=default_coparams, makeplot=default_makeplot, verbose=2):
    '''
    Make all cost outcome curves for a given program.
    '''
    
     # Get the cost-coverage and coverage-outcome relationships     
    plotdata_cc, D = makecc(D=D, progname=progname, ccplot=ccplot, ccparams=ccparams, makeplot=makeplot, verbose=verbose)

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
            plotdata[effectnumber], plotdata_co[effectnumber], effect = makecco(D=D, progname=progname, effect=effect, ccplot=ccplot, ccparams=D.programs[progname]['ccparams'], coparams=coparams, makeplot=makeplot, verbose=verbose)
            effects[effectnumber] = effect 

    return plotdata, plotdata_co, plotdata_cc, effects, D      

###############################################################################
def makeallccocs(D=None, verbose=2, makeplot=default_makeplot):
    '''
    Make all curves for all programs.
    '''

    for progname in D.programs.keys():
        plotdata_cco, plotdata_co, plotdata_cc, effects, D = plotallcurves(D, unicode(progname), makeplot=makeplot)
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
    simtvec = D.S.tvec # Extract the time vector from the sim
    nsimpts = len(simtvec) # Number of sim points
    simindex = range(nsimpts) # Get the index corresponding to the sim time vector

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
            targetpopmodel = D.S.people[:,popnumbers,:].sum(axis=(0,1))
        elif len(D.P[thispar].p)==1: # For parameters whose effects are not differentiated by population, we make special cases depending on the parameter
            if thispar == 'aidstest': # Target population = diagnosed PLHIV, AIDS stage
                targetpopmodel = D.S.people[22:26,:,:].sum(axis=(0,1))
            elif thispar in ['numost','sharing']: # Target population = the sum of all populations that inject
                injectindices = [i for i, x in enumerate(D.data.meta.pops.injects) if x == 1]
                targetpopmodel = D.S.people[:,injectindices,:].sum(axis = (0,1))
            elif thispar == 'numpmtct': # Target population = HIV+ pregnant women
                targetpopmodel = multiply(D.M.birth[:,simindex], D.S.people[artelig,:,:].sum(axis=0)).sum(axis=0)
            elif thispar == 'breast': # Target population = HIV+ breastfeeding women
                targetpopmodel = multiply(D.M.birth[:,simindex], D.M.breast[simindex], D.S.people[artelig,:,:].sum(axis=0)).sum(axis=0)
            elif thispar in ['numfirstline','numsecondline']: # Target population = diagnosed PLHIV
                targetpopmodel = D.S.people[artelig,:,:].sum(axis=(0,1))
            else:
                print('WARNING, Unrecognized parameter %s' % thispar)
        else:
            print('WARNING, Parameter %s of odd length %s' % (thispar, len(D.P[thispar].p)))
    if len(targetpars)==0:
        print('WARNING, no target parameters for program %s' % progname)
                
    # We only want the model-estimated size of the targeted population(s) for actual years, not the interpolated years
    yearindices = range(0, len(D.opt.tvec), int(1/D.opt.dt))
    targetpop = targetpopmodel[yearindices]

    # Do population adjustments if required
    if params:
        costparam = params[2]
        if popadj: costparam = params[2]/targetpop[-1]
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
            saturation = params[0]
            if isinstance(params[3], float):
                growthrate = exp(params[3]*log(params[0]/params[1]-1)+log(params[2]))
                growthrateplot = exp(params[3]*log(params[0]/params[1]-1)+log(costparam))
                storeparams = [saturation, growthrate, params[3]]
                plottingparams = [saturation, growthrateplot, params[3]]
            else:
                growthrate = (-1/params[2])*log((2*params[0])/(params[1]+params[0]) - 1)        
                growthrateplot = (-1/costparam)*log((2*params[0])/(params[1]+params[0]) - 1)        
                storeparams = [saturation, growthrate]
                plottingparams = [saturation, growthrateplot]
                
    else:
        coveragenumber = D.data.costcov.cov[prognumber] 
        if len(coveragenumber)==1: # If an assumption has been used, keep this constant over time
            coveragepercent = (coveragenumber/targetpop)*100
        else:
            coveragepercent = [(coveragenumber[j]/targetpop[j])*100 for j in range(ndatayears)] # get program coverage
        coverage = coveragenumber # this is unnecessary atm but might be useful later to set it up this way
        coveragelabel = 'Number covered'
        if params:
            saturation = params[0]*targetpop[-1]
            if isinstance(params[3], float):
                growthrate = exp(params[3]*log(params[0]/params[1]-1)+log(params[2]))
                growthrateplot = exp(params[3]*log(params[0]/params[1]-1)+log(costparam))
                storeparams = [saturation, growthrate, params[3]]
                plottingparams = [saturation, growthrateplot, params[3]]
            else:
                growthrate = (-1/params[2])*log((2*params[0]*targetpop[-1])/(params[1]*targetpop[-1]+params[0]*targetpop[-1]) - 1)
                growthrateplot = (-1/costparam)*log((2*params[0]*targetpop[-1])/(params[1]*targetpop[-1]+params[0]*targetpop[-1]) - 1)
                storeparams = [saturation, growthrate]
                plottingparams = [saturation, growthrateplot]
                    
    return coverage, targetpop, coveragelabel, storeparams, plottingparams

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
def makesamples(coparams, muz, stdevz, muf, stdevf, samplesize=1000):
    '''
    Generate samples of behaviour at zero and full coverage
    '''
    
    # Generate samples of zero-coverage and full-coverage behaviour
    zerosample = rtnorm((coparams[0] - muz) / stdevz, (coparams[1] - muz) / stdevz, mu=muz, sigma=stdevz, size = samplesize)
    fullsample = rtnorm((coparams[2] - muf) / stdevf, (coparams[3] - muf) / stdevf, mu=muf, sigma=stdevf, size = samplesize)
        
    return zerosample, fullsample


# For testing... delete later... should make separate file!
#plotdata, D = makecc(D, progname=default_progname, ccparams=default_ccparams, ccplot=default_ccplot, artelig=default_artelig, makeplot=default_makeplot, verbose=2, nxpts = 1000)
#plotdata, effect = makeco(D, progname=default_progname, effect=default_effect, coparams=default_coparams, makeplot=default_makeplot, verbose=2,nxpts = 1000)
#plotdata, plotdata_co, effect = makecco(D, progname=default_progname, effect=default_effect, ccparams=default_ccparams, ccplot=default_ccplot, coparams=default_coparams, makeplot=default_makeplot, verbose=2,nxpts = 1000)
#plotdata, plotdata_co, plotdata_cc, effectnames, D = plotallcurves(D, progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot, verbose=2)
#D = makeallccocs(D, verbose=2, makeplot=default_makeplot)
