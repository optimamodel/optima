"""
Creates and updates cost-coverage curves and coverage-outcome curves
    
Version: 2014nov26 by cliffk
"""
###############################################################################
## Set up
###############################################################################

from math import log
from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title, xlim, ylim
from numpy import linspace, exp, isnan, zeros, asarray, multiply
from rtnorm import rtnorm
from bunch import float_array
from printv import printv
#from scipy.stats import truncnorm
from parameters import parameters, input_parameter_name

## Set defaults for testing
default_progname = 'ART'
default_startup = 0 # select 0 for programs with no startup costs or 1 for programs with startup costs
default_ccparams = [0.8, 0.6, 400000.0, 1e6]
default_coparams = []
default_init_coparams = [] #this is used in loadworkbook
default_makeplot = 1
default_effectname = [['sex', 'condomcas'], [u'MSM'], []] # D.programs[default_progname][0] 
default_artelig = range(6,26)
coverage_params = ['numost','numpmtct','numfirstline','numsecondline']

######################################################################
def makecc(D=None, progname=default_progname, startup=default_startup, ccparams=default_ccparams, artelig=default_artelig, makeplot=default_makeplot, verbose=2, nxpts = 1000):
    '''Make cost coverage curve.

    Input:
    D: main data structure
    progname: string. Needs to be one of the keys of D.programs
    startup: #TODO (not implemented yet)
    ccparams: list. Contains parameters for the cost-coverage curves, obtained from the GUI. Can be empty.
            ccparams(0) = the saturation value
            ccparams(1) = the 'known' coverage level
            ccparams(2) = the 'known' funding requirements to achieve ccparams(2)
            ccparams(3) = desired upper x limit
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

    # Get coverage (in separate function)
    coverage, coveragelabel, storeparams = getcoverage(D, ccparams, artelig=default_artelig, progname=progname)

    # Check parameters, if necessary
    if ccparams:
        if (ccparams[0] <= 0 or ccparams[0] > 1):
            raise Exception('Please enter a value between 0 and 1 for the saturation coverage level')
        if (ccparams[1] < 0 or ccparams[1] > 1):
            raise Exception('Please enter a value between 0 and 1 for the coverage level in Question 2')
        if (ccparams[1] == 0 or ccparams[2] == 0):
            raise Exception('Please enter non-zero values for the cost and coverage level estimates in Question 2')
        if ccparams[2] < 0:
            raise Exception('Negative funding levels are not permitted, please revise')

        saturation, growthrate, xupperlim = storeparams[0], storeparams[1], storeparams[2] # Get parameters for making curve 
        
        # Create curve
        xvalscc = linspace(0,xupperlim,nxpts) # take nxpts points between 0 and user-specified max
        yvalscc = 2*saturation / (1 + exp(-growthrate*xvalscc)) - saturation # calculate logistic function
        
        # Populate output structure with scatter data 
        plotdata['xlinedata'] = xvalscc
        plotdata['ylinedata'] = yvalscc

    elif D.programs[progname][0][3]:
        saturation, growthrate, xupperlim = D.programs[progname][0][3][0], D.programs[progname][0][3][1], D.programs[progname][0][3][2] # Get previously-stored parameters 
        storeparams = [saturation, growthrate, xupperlim]

        # Create curve
        xvalscc = linspace(0,xupperlim,nxpts) # take nxpts points between 0 and user-specified max
        yvalscc = 2*saturation / (1 + exp(-growthrate*xvalscc)) - saturation # calculate logistic function
        
        # Populate output structure with scatter data 
        plotdata['xlinedata'] = xvalscc
        plotdata['ylinedata'] = yvalscc
    
    # Populate output structure with axis limits
    plotdata['xlowerlim'], plotdata['ylowerlim']  = 0.0, 0.0
    plotdata['xupperlim'], plotdata['yupperlim']  = max([x if ~isnan(x) else 0.0 for x in totalcost])*1.5, max([x if ~isnan(x) else 0.0 for x in coverage])*1.5

    # Check the lengths or coverage and cost are the same.
    if (len(totalcost) == 1 and len(coverage) > 1):
        coverage = float_array(coverage)
        coverage = coverage[~isnan(coverage)]
        coverage = coverage[-1]
    elif (len(coverage) == 1 and len(totalcost) > 1): 
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
                
    # Populate output structure with scatter data 
    plotdata['xscatterdata'] = totalcost
    plotdata['yscatterdata'] = coverage

    # Populate output structure with labels and titles
    plotdata['title'] = progname
    plotdata['xlabel'] = 'USD'
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

    return plotdata, storeparams

######################################################################
def makeco(D, progname=default_progname, effectname=default_effectname, coparams=default_coparams, makeplot=default_makeplot, verbose=2,nxpts = 1000):
    '''
    Make a single coverage outcome curve.
    
    Inputs: 
    D: main data structure
    progname: string, needs to be one of the keys of D.programs
    effectname: list. 
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
    short_effectname = effectname[:2] # only matching by effect "signature"
    short_effectlist = [e[:2] for e in D.programs[progname]]
    if short_effectname not in short_effectlist:
        print "makeco short_effectname: %s short_effectlist: %s" % (short_effectname, short_effectlist)
        raise Exception('Please select one of the following effects %s' % D.programs[progname])
    
    # Initialise output structures
    plotdata = {}
    storeparams = []

    # Get population and parameter info
    popname = effectname[1]
    parname = effectname[0][1]

    # Only going to make cost-outcome curves for programs where the affected parameter is not coverage
    if parname not in coverage_params:
        if popname[0] in D.data.meta.pops.short:
            popnumber = D.data.meta.pops.short.index(popname[0])
        else:
            popnumber = 0
        
        # Get data for scatter plots
        outcome = D.data[effectname[0][0]][effectname[0][1]][popnumber]
        coverage, coveragelabel, storeccparams = getcoverage(D, params=[], artelig=default_artelig, progname=progname)

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
        if coparams and len(coparams)>=3:
            zeromin = coparams[0] # Assumptions of behaviour at zero coverage (lower bound)
            zeromax = coparams[1] # Assumptions of behaviour at zero coverage (upper bound)
            fullmin = coparams[2] # Assumptions of behaviour at maximal coverage (lower bound)
            fullmax = coparams[3] # Assumptions of behaviour at maximal coverage (upper bound)
        elif effectname[3] and len(effectname[2])>0:
            zeromin = effectname[3][3] # Assumptions of behaviour at zero coverage (lower bound)
            zeromax = effectname[3][4] # Assumptions of behaviour at zero coverage (upper bound)
            fullmin = effectname[3][5] # Assumptions of behaviour at maximal coverage (lower bound)
            fullmax = effectname[3][6] # Assumptions of behaviour at maximal coverage (upper bound)
            coparams = [zeromin, zeromax, fullmin, fullmax] # Store for output

        print("coparams", coparams, "effectname", effectname)
        # Get inputs from GUI, if they have been given
        if coparams and len(coparams)>0:
            if not len(coparams)==4:
                raise Exception('Not all of the coverage-outcome parameters have been specified. Please enter the missing parameters to define the curve.')

            # Check inputs
            if any((j<0 or j>1) for j in coparams):
                raise Exception('Please enter values between 0 and 1 for the ranges of behaviour at zero and full coverage')
            
            # Generate sample of zero-coverage behaviour
            muz, stdevz, muf, stdevf = makecosampleparams(coparams, verbose=verbose)
            zerosample, fullsample = makesamples(coparams, muz, stdevz, muf, stdevf, D.opt.nsims)

            # Store parameters for access later
            storeparams = [muz, stdevz, muf, stdevf]
        
            # General set of coverage-outcome relationships
            xvalsco = linspace(0,1,nxpts) # take nxpts points along the unit interval
            ymin, ymax = linspace(coparams[0],coparams[2],nxpts), linspace(coparams[1],coparams[3],nxpts)
            
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
        plotdata['title'] = input_parameter_name(effectname[0][1])+ ' - ' + effectname[1][0]
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
        
    return plotdata, storeparams

###############################################################################
def ccoeqn(x, p):
    '''
    Equation defining cco curves.
    '''
    y = (p[3]-p[2]) * ( 2*p[0] / (1 + exp(-p[1]*x)) - p[0]) + p[2]
    return y

###############################################################################
def cceqn(x, p):
    '''
    Equation defining cc curves.
    X is total cost, p is unit cost. Returns y which is coverage
    '''
    y = float(x)/p
    return y
    
###############################################################################
def makecco(D=None, progname=default_progname, effectname=default_effectname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot, verbose=2,nxpts = 1000):
    '''
    Make a single cost outcome curve.
    
    Inputs: 
    D: main data structure
    progname: string. Needs to be one of the keys of D.programs
    effectname: list. 
    ccparams: list. Contains parameters for the cost-coverage curves, obtained from the GUI
        ccparams(0) = the saturation value
        ccparams(1) = the 'known' coverage level
        ccparams(2) = the 'known' funding requirements to achieve ccparams(2)
        ccparams(3) = desired upper x limit
    coparams: list. Contains parameters for the coverage-outcome curves
        coparams(0) = the lower bound for the outcome when coverage = 0
        coparams(1) = the upper bound for the outcome when coverage = 0
        coparams(2) = the lower bound for the outcome when coverage = 1
        coparams(3) = the upper bound for the outcome when coverage = 1

    Output:
    plotdata, plotdata_co, storeparams, 
    '''
    
    printv("makecco(%s, %s, %s, %s, %s, %s, %s)" % (progname, effectname, ccparams, coparams, makeplot, verbose, nxpts), 2, verbose)

    # Check that the selected program is in the program list 
    if unicode(progname) not in D.programs.keys():
        printv("progname: %s programs: %s" % (unicode(progname), D.programs.keys()), 5, verbose)
        raise Exception('Please select one of the following programs %s' % D.programs.keys())

    # Check that the selected effect is in the list of effects
    short_effectname = effectname[:2] # only matching by effect "signature"
    short_effectlist = [e[:2] for e in D.programs[progname]]
    print("short_effectname", short_effectname)
    print("short_effectlist", short_effectlist)
    if short_effectname not in short_effectlist:
        print "makecco short_effectname: %s short_effectlist: %s" % (short_effectname, short_effectlist)
        raise Exception('Please select one of the following effects %s' % D.programs[progname])

    # Initialise output structures
    plotdata = {}
    plotdata_co = {}
    storeparams = []

    # Extract info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number

    # Get population and parameter info
    popname = effectname[1]
    parname = effectname[0][1]
    print("popname", popname, "parname", parname)

    # Only going to make cost-outcome curves for programs where the affected parameter is not coverage
    if parname not in coverage_params:
        if popname[0] in D.data.meta.pops.short:
            popnumber = D.data.meta.pops.short.index(popname[0])
        else:
            popnumber = 0
        printv("coparams in makecco: %s" % coparams, 5, verbose)
                
        # Get inputs from  GUI or access previously stored ones
        if (ccparams or D.programs[progname][0][3]):
            
            if ccparams:        
                # Get parameters for cost-coverage curves
                saturation = ccparams[0]
                growthrate = (-1/ccparams[2])*log((2*saturation)/(ccparams[1]+saturation) - 1)
                xupperlim = ccparams[3]

            elif D.programs[progname][0][3]:
                saturation, growthrate, xupperlim = D.programs[progname][0][3][0], D.programs[progname][0][3][1], D.programs[progname][0][3][2] # Get previously-stored parameters 
            
            # Get inputs from  GUI, if these have been provided
            if (coparams or len(D.programs[progname][0][3])>3):

                if not coparams:
                    zeromin = effectname[3][3] # Assumptions of behaviour at zero coverage (lower bound)
                    zeromax = effectname[3][4] # Assumptions of behaviour at zero coverage (upper bound)
                    fullmin = effectname[3][5] # Assumptions of behaviour at maximal coverage (lower bound)
                    fullmax = effectname[3][6] # Assumptions of behaviour at maximal coverage (upper bound)
                    coparams = [zeromin, zeromax, fullmin, fullmax] # Store for output
        
                # Generate samples of zero-coverage and full-coverage behaviour
                muz, stdevz, muf, stdevf = makecosampleparams(coparams, verbose=verbose)
                zerosample, fullsample = makesamples(coparams, muz, stdevz, muf, stdevf, D.opt.nsims)

                # Generate samples of zero-coverage and full-coverage behaviour
                storeparams = [muz, stdevz, muf, stdevf, saturation, growthrate]

                # Create x dataset and initialise y dataset
                xvalscco = linspace(0,xupperlim,nxpts)
        
                # Min, Median and Max lines
                mediancco = ccoeqn(xvalscco, [saturation, growthrate, muz, muf])# Generate median cost-outcome curve
                mincco = ccoeqn(xvalscco, [saturation, growthrate, coparams[0], coparams[2]])# Generate min cost-outcome curve
                maxcco = ccoeqn(xvalscco, [saturation, growthrate, coparams[1], coparams[3]])# Generate max cost-outcome curve

                # Populate output structure with cost-outcome curves for plotting
                plotdata['xlinedata'] = xvalscco # X data for all line plots
                plotdata['ylinedata'] = [mediancco,maxcco,mincco] # Y data for second line plot
                plotdata['ylinedata1'] = mediancco # Y data for second line plot
                plotdata['ylinedata2'] = maxcco  # Y data for third line plot
                plotdata['ylinedata3'] = mincco  # Y data for fourth line plot

                # Get the coverage-outcome relationships
                plotdata_co, storeparams_co = makeco(D, progname, effectname, coparams, makeplot=makeplot, verbose=verbose)

        # Extract scatter data
        totalcost = D.data.costcov.cost[prognumber] # get total cost data
        outcome = D.data[effectname[0][0]][effectname[0][1]][popnumber]

        # Populate output structure with axis limits
        plotdata['xlowerlim'], plotdata['ylowerlim']  = 0.0, 0.0
        plotdata['xupperlim'], plotdata['yupperlim']  = max([j if ~isnan(j) else 0.0 for j in totalcost])*1.5, 1.0

        # Get around situations where there's an assumption for coverage but not for behaviour, or vice versa
        if (len(totalcost) == 1 and len(outcome) > 1): 
            outcome = float_array(outcome)
            outcome = outcome[~isnan(outcome)]
            outcome = outcome[-1]
        elif (len(outcome) == 1 and len(totalcost) > 1):
            totalcost = float_array(totalcost)
            totalcost = totalcost[~isnan(totalcost)]
            totalcost = totalcost[-1]
        else:
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

        # Populate output structure with labels and titles
        plotdata['title'] = input_parameter_name(effectname[0][1])+ ' - ' + effectname[1][0]
        plotdata['xlabel'] = 'USD'
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
    
    return plotdata, plotdata_co, storeparams

###############################################################################
def plotallcurves(D=None, progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot, verbose=2):
    '''
    Make all cost outcome curves for a given program.
    '''
    
     # Get the cost-coverage and coverage-outcome relationships     
    plotdata_cc, storeparams_cc = makecc(D=D, progname=progname, ccparams=ccparams, makeplot=makeplot, verbose=verbose)

   ## Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())

    ## Initialise storage of outputs   
    plotdata_co = {}
    plotdata = {}    
    effectnames = {}     

    # Loop over behavioural effects
    for effectnumber, effectname in enumerate(D.programs[progname]):

        # Default storeparams
        storeparams = storeparams_cc
        storeparams_co = []

        # Get parameter info
        parname = effectname[0][1]

        # Only going to make cost-outcome curves for programs where the affected parameter is not coverage
        if parname not in coverage_params:

            # Store outputs
            effectnames[effectnumber] = effectname
            plotdata[effectnumber], plotdata_co[effectnumber], storeparams_co = makecco(D=D, progname=progname, effectname=effectname, ccparams=ccparams, coparams=coparams, makeplot=makeplot, verbose=verbose)

        # Store outputs
        storeparams.extend(storeparams_co)
        if len(effectname) == 3: # There's no existing info here, append
            effectname.append(storeparams)
        else:
            effectname[3] = storeparams # There is existing info here, overwrite
        #no need to assign effectname back to D.programs[progname][effectnumber] - they are equal by reference (AN)

    return plotdata, plotdata_co, plotdata_cc, effectnames, D      

###############################################################################
def makeallccocs(D=None, verbose=2, makeplot = default_makeplot):
    '''
    Make all curves for all programs.
    '''

    for progname in D.programs.keys():
        plotdata_cco, plotdata_co, plotdata_cc, effectnames, D = plotallcurves(D, unicode(progname), makeplot = makeplot)
    return D

###############################################################################
def getcoverage(D=None, params=[], artelig=default_artelig, progname=default_progname):
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
    for effect in D.programs[progname]:
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
                
    # We only want the model-estimated size of the targeted population(s) for actual years, not the interpolated years
    yearindices = range(0, len(D.S.tvec), int(1/D.opt.dt))
    targetpop = targetpopmodel[yearindices]

    storeparams = []
    coverage = None
    coveragelabel = ''

    # Check if coverage was entered as a number, and if so convert it to a %. 
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
            growthrate = (-1/params[2])*log((2*params[0])/(params[1]+params[0]) - 1)        
            storeparams = [saturation, growthrate, params[3]]
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
            growthrate = (-1/params[2])*log((2*params[0]*targetpop[-1])/(params[1]*targetpop[-1]+params[0]*targetpop[-1]) - 1)
            storeparams = [saturation, growthrate, params[3]]
                
    return coverage, coveragelabel, storeparams

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
#plotdata, storeparams = makecc(D, progname=default_progname, startup=default_startup, ccparams=default_ccparams, artelig=default_artelig, makeplot=default_makeplot, verbose=2, nxpts = 1000)
#plotdata, storeparams = makeco(D, progname=default_progname, effectname=default_effectname, coparams=default_coparams, makeplot=default_makeplot, verbose=2,nxpts = 1000)
#plotdata, plotdata_co, storeparams = makecco(D, progname=default_progname, effectname=default_effectname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot, verbose=2,nxpts = 1000)
#plotdata, plotdata_co, plotdata_cc, effectnames, D = plotallcurves(D, progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot, verbose=2)
#D = makeallccocs(D, verbose=2, makeplot=default_makeplot)
