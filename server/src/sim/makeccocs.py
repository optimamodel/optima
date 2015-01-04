"""
Creates and updates cost-coverage curves and coverage-outcome curves
    
Version: 2014nov26 by cliffk
"""
###############################################################################
## Set up
###############################################################################

from math import log
from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title, scatter
from numpy import linspace, exp, isnan, zeros, asarray
from rtnorm import rtnorm
from bunch import float_array
from printv import printv
#from scipy.stats import truncnorm
from parameters import parameters, input_parameter_name

## Set defaults for testing
default_progname = 'OST'
default_numbercov = [0, 0, 1, 0, 0, 1, 1] # should equal 1 if coverage is specified as a number rather than as a percentage. This will be replaced by D.data.meta.progs.numbercov
default_startup = 0 # select 0 for programs with no startup costs or 1 for programs with startup costs
default_ccparams = [0.9, 0.2, 800000.0, 7e6]
default_coparams = []
default_init_coparams = [[0.3, 0.5], [0.7, 0.9]]
default_makeplot = 1
default_effectname = [['sex', 'condomcas'], [u'MSM programs'], [[0.3, 0.5], [0.7, 0.9]]]


###############################################################################
## Show cost-coverage data
###############################################################################
def showdata(D=None, progname=default_progname, numbercov=default_numbercov, makeplot=default_makeplot):
    '''
    Extract and display cost/coverage scatter data
    '''
    
    # Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())
    
    # Extract basic info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program index number
    ndatayears = len(D.data.epiyears)

    # Figure out the size of the total population from data
    totalpopdata = [0.0]*ndatayears
    for j in range(len(D.data.key.popsize[0])):
        if len(D.data.key.popsize[0][j])==1: # If an assumption has been used, keep this constant over time
            totalpopdata = [sum(x) for x in zip(totalpopdata, D.data.key.popsize[0][j]*ndatayears)]
        else:
            totalpopdata = [sum(x) for x in zip(totalpopdata, D.data.key.popsize[0][j])]

    # Figure out the size of the total population from model
    totalpopmodel = D.S.people[:,:,:].sum(axis=(0,1))

    # Figure out the targeted population(s) 
    targetpops = []
    for effect in D.programs[progname]:
        targetpops.append(effect[1][0])
    targetpops = set(targetpops)

    # Figure out the total size of the targeted population(s)
    targetpopdata = [0.0]*ndatayears
    targetpopmodel = [0.0]*ndatayears    
    for thispop in targetpops: # Loop through populations
        if thispop in D.data.meta.pops.short: # Program affects a particular population
            thispopnumber = D.data.meta.pops.short.index(thispop)
            if len(D.data.key.popsize[0][thispopnumber])==1: # If an assumption has been used, keep this constant over time
                targetpopdata = [sum(x) for x in zip(targetpopdata, D.data.key.popsize[0][thispopnumber]*ndatayears)]
            else:
                targetpopdata = [sum(x) for x in zip(targetpopdata, D.data.key.popsize[0][thispopnumber])]
            targetpopmodel = [sum(x) for x in zip(targetpopmodel, D.S.people[:,thispopnumber,:].sum(axis=0))]
        else: # Program affects all populations in model
            targetpopdata = totalpopdata
            targetpopmodel = totalpopmodel
            continue

    # How has coverage been specified, as a number or a percentage?
    if numbercov[prognumber]:
        coveragenumber = D.data.costcov.cov[prognumber] 
        if len(coveragenumber)==1: # If an assumption has been used, keep this constant over time
            coveragenumber = coveragenumber*ndatayears
        coverage = coveragenumber # this is unnecessary atm but might be useful later to set it up this way
        coveragepercent = [(coveragenumber[j]/targetpopdata[j])*100 for j in range(ndatayears)] # get program coverage
    else:
        coveragepercent = D.data.costcov.cov[prognumber] 
        if len(coveragepercent)==1: # If an assumption has been used, keep this constant over time
            coveragepercent = coveragepercent*ndatayears
        coverage = coveragepercent # this is unnecessary now but might be useful later to set it up this way
        coveragenumber = [coveragepercent[j] * targetpopdata[j] for j in range(ndatayears)] # get program coverage 

    # If the cost data has been entered as total cost, we can just use this directly (NB, this is indicated via the code 'saturating', #TODO change this)
    if D.data.meta.progs.saturating[prognumber]:
        totalcost = D.data.costcov.cost[prognumber]
        if len(totalcost)==1: # If an assumption has been used, keep this constant over time
            totalcost = totalcost*ndatayears

    # If the cost data is specified as an average (unit) cost, we need to get the number of people covered to calculate the total cost
    else:
        unitcost = D.data.costcov.cost[prognumber]
        if len(unitcost)==1: # If an assumption has been used, keep this constant over time
            unitcost = unitcost*ndatayears
        totalcost = [unitcost[j]*coveragenumber[j] for j in range(ndatayears)]
        
    # Store plot data
    scatterplotdata = {}
    scatterplotdata['xdata'] = totalcost
    scatterplotdata['ydata'] = coverage
    scatterplotdata['title'] = progname
    scatterplotdata['xlabel'] = 'USD'
    if numbercov[prognumber]:
        scatterplotdata['ylabel'] = 'Number covered'
    else: 
        scatterplotdata['ylabel'] = 'Percentage covered'
    
    # Plot (to check it's working; delete once plotting enabled in GUI)
    if makeplot:
        figure()
        hold(True)
        scatter(scatterplotdata['xdata'], scatterplotdata['ydata'])
        title(scatterplotdata['title'])
        xlabel(scatterplotdata['xlabel'])
        ylabel(scatterplotdata['ylabel'])
    
    return scatterplotdata

###############################################################################
## Make cost coverage curve
###############################################################################
def makecc(D=None, progname=default_progname, startup=default_startup, numbercov=default_numbercov, ccparams=default_ccparams, makeplot=default_makeplot, verbose=2, nxpts = 1000):
    
    if verbose>=2:
        print('makecc %s %s' % (progname, ccparams))

    # Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())

    # Extract info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number
    coverage = D.data.costcov.cov[prognumber] # get program coverage levels
        
    # For saturating programs... 
    if D.data.meta.progs.saturating[prognumber]:
        totalcost = D.data.costcov.cost[prognumber]
        
        ## Check inputs from GUI 
        if (ccparams[0] <= 0 or ccparams[0] > 1):
            raise Exception('Please enter a value between 0 and 1 for the saturation coverage level')
        if (ccparams[1] < 0 or ccparams[1] > 1):
            raise Exception('Please enter a value between 0 and 1 for the coverage level in Question 2')
        if (ccparams[1] == 0 or ccparams[2] == 0):
            raise Exception('Please enter non-zero values for the cost and coverage level estimates in Question 2')
        if ccparams[2] < 0:
            raise Exception('Negative funding levels are not permitted, please revise')

        # Convert inputs from GUI into parameters needed for curves
        saturation = ccparams[0]
        growthrate = (-1/ccparams[2])*log((2*ccparams[0])/(ccparams[1]+ccparams[0]) - 1)
        xupperlim = ccparams[3] 

        # Store parameters for access later
        storeparams = [saturation, growthrate]

        # Create logistic relationship 
        xvalscc = linspace(0,xupperlim,nxpts) # take nxpts points between 0 and user-specified max
        yvalscc = 2*saturation / (1 + exp(-growthrate*xvalscc)) - saturation # calculate logistic function

    # ... for unit cost programs...
    else:
        unitcost = D.data.costcov.cost[prognumber]
        totalcost = []
        for i in range(len(unitcost)):
            totalcost.append(unitcost[i]*coverage[i])
            if not isnan(unitcost[i]):
                slope = unitcost[i] # this updates so the slope is the most recent unit cost

        # Store parameters for access later
        storeparams = [slope]

        ## Create linear relationship
        xvalscc = linspace(0,ccparams[3],nxpts) # take nxpts points between 0 and some arbitrary max
        yvalscc = xvalscc*slope # calculate linear function

    # Get scatter data
    if (len(coverage) == 1 and len(totalcost) > 1): 
        totalcost = float_array(totalcost)
        totalcost = totalcost[~isnan(totalcost)]
        totalcost = totalcost[-1]
    elif (len(totalcost) == 1 and len(coverage) > 1):
        coverage = float_array(coverage)
        coverage = coverage[~isnan(coverage)]
        coverage = coverage[-1]
        
    # Create and populate output structure with plotting data
    plotdata = {}
    plotdata['xlinedata'] = xvalscc
    plotdata['ylinedata'] = yvalscc
    plotdata['xscatterdata'] = totalcost
    plotdata['yscatterdata'] = coverage
    plotdata['title'] = progname
    plotdata['xlabel'] = 'USD'
    plotdata['ylabel'] = 'Proportion covered'
    
    # Plot (to check it's working; delete once plotting enabled in GUI)
    if makeplot:
        printv("plotting cc for program %s" % progname, 4, verbose)   
        figure()
        hold(True)
        plot(plotdata['xlinedata'], plotdata['ylinedata'], 'k-', lw = 2)
        plot(plotdata['xscatterdata'], plotdata['yscatterdata'], 'ro')
        title(plotdata['title'])
        xlabel(plotdata['xlabel'])
        ylabel(plotdata['ylabel'])
    
    return plotdata, storeparams

###############################################################################
## Make coverage outcome curve
# Inputs: 
#    Input types:
#    1. datain: EITHER a bunch (if project data already loaded) OR a string specifying the project name (which will then be load a bunch)
#    2. progname: string. 
#    3. effectname: list. 
#    4. coparams: list. Contains parameters for the coverage-outcome curves, obtained from the GUI or spreadsheet
#        coparams(0) = the lower bound for the outcome when coverage = 0
#        coparams(1) = the upper bound for the outcome when coverage = 0
#        coparams(2) = the lower bound for the outcome when coverage = 1
#        coparams(3) = the upper bound for the outcome when coverage = 1

#    Output types:
#    1. plotdata
#    2. D
###############################################################################
def makeco(D, progname=default_progname, effectname=default_effectname, coparams=default_coparams, makeplot=default_makeplot, verbose=2,nxpts = 1000):
    
    ## Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())
    ## Check that the selected program is in the program list 
    short_effectname = effectname[:2] # only matching by effect "signature"
    short_effectlist = [e[:2] for e in D.programs[progname]]
    if short_effectname not in short_effectlist:
        print "makeco short_effectname: %s short_effectlist: %s" % (short_effectname, short_effectlist)
        raise Exception('Please select one of the following effects %s' % D.programs[progname])

    ## Extract info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number
    
    ## Get population info
    popname = effectname[1]

    ## Only going to make cost-outcome curves if a program affects a SPECIFIC population -- otherwise will just make cost-coverage curves
    if not D.data.meta.progs.saturating[prognumber]:
#    if popname[0] not in D.data.meta.pops.short:
        return [], D
    else:
        if popname[0] in D.data.meta.pops.short:
            popnumber = D.data.meta.pops.short.index(popname[0])
        else: 
            popnumber = 0
        
        # Get data for scatter plots
        outcome = D.data[effectname[0][0]][effectname[0][1]][popnumber]
        coverage = D.data.costcov.cov[prognumber] # get program coverage data

        if (len(coverage) == 1 and len(outcome) > 1): 
            outcome = asarray(outcome)
            outcome = outcome[~isnan(outcome)]
            outcome = outcome[-1]
        elif (len(outcome) == 1 and len(coverage) > 1):
            coverage = asarray(coverage)
            coverage = coverage[~isnan(coverage)]
            coverage = coverage[-1]

        # Get inputs from either GUI or spreadsheet
        if coparams and len(coparams)>=3: ## TODO: would be better to use a dictionary, so that the order doesn't have to be fixed
            zeromin = coparams[0] # Assumptions of behaviour at zero coverage (lower bound)
            zeromax = coparams[1] # Assumptions of behaviour at zero coverage (upper bound)
            fullmin = coparams[2] # Assumptions of behaviour at maximal coverage (lower bound)
            fullmax = coparams[3] # Assumptions of behaviour at maximal coverage (upper bound)
        else: 
            zeromin = effectname[2][0][0] # Assumptions of behaviour at zero coverage (lower bound)
            zeromax = effectname[2][0][1] # Assumptions of behaviour at zero coverage (upper bound)
            fullmin = effectname[2][1][0] # Assumptions of behaviour at maximal coverage (lower bound)
            fullmax = effectname[2][1][1] # Assumptions of behaviour at maximal coverage (upper bound)
            coparams = [zeromin, zeromax, fullmin, fullmax] # Store for output

        # Check inputs
        if (coparams < [0,0,0,0] or coparams > [1,1,1,1]):
            raise Exception('Please enter values between 0 and 1 for the ranges of behaviour at zero and full coverage')
            
        # Generate sample of zero-coverage behaviour
        muz, stdevz, muf, stdevf = makecosampleparams(coparams, verbose=verbose)
        zerosample, fullsample = makesamples(coparams, muz, stdevz, muf, stdevf, D.opt.nsims)

        # Store parameters for access later
        storeparams = [muz, stdevz, muf, stdevf]
        
        # General set of coverage-outcome relationships
        xvalsco = linspace(0,1,nxpts) # take nxpts points along the unit interval
#        yvalsco = zeros((nxpts,len(fullsample)))
#        for i in range(len(fullsample)):
#            yvalsco[:,i] = linspace(zerosample[i],fullsample[i],nxpts) # Generate D.opt.nsims straight lines
            
        # Upper and lower bounds of line set
#        ymin, ymax = zeros(nxpts), zeros(nxpts)
#        for i in range(nxpts):
#            ymax[i] = max(yvalsco[i,:])
#            ymin[i] = min(yvalsco[i,:])
        ymin, ymax = linspace(coparams[0],coparams[2],nxpts), linspace(coparams[1],coparams[3],nxpts)
            
        # Plot results (probably delete once in GUI)  
        plot_title = input_parameter_name(effectname[0][1])+ ' - ' + effectname[1][0]
                          
        if makeplot:
            figure()
            hold(True)
            plot(xvalsco, linspace(muz,muf,nxpts), color = 'b', lw = 2)
            plot(xvalsco, ymax, 'k--', lw = 2)
            plot(xvalsco, ymin, 'k--', lw = 2)
            plot(coverage, outcome, 'ro')
            title(plot_title)
            xlabel('proportion covered')
            ylabel('outcome')
    
        # Create and populate output structure with plotting data
        plotdata = {}
        plotdata['xlinedata'] = xvalsco # X data for all line plots
        plotdata['ylinedata'] = [linspace(muz,muf,nxpts), ymax, ymin] # ALL Y data (for three lines)
        plotdata['ylinedata1'] = linspace(muz,muf,nxpts) # Y data for first line on plot
        plotdata['ylinedata2'] = ymax  # Y data for second line on plot
        plotdata['ylinedata3'] = ymin  # Y data for third line on plot
        plotdata['xscatterdata'] = coverage # X scatter data
        plotdata['yscatterdata'] = outcome # Y scatter data
        plotdata['title'] = plot_title
        plotdata['xlabel'] = 'Proportion covered'
        plotdata['ylabel'] = 'Outcome'
    
        return plotdata, storeparams

###############################################################################
# Create cco and cc equations
###############################################################################
def ccoeqn(x, p):
    '''
    Equation defining cco curves.
    '''
    y = (p[3]-p[2]) * ( 2*p[0] / (1 + exp(-p[1]*x)) - p[0]) + p[2]
    return y

def cceqn(x, p):
    '''
    Equation defining cc curves.
    X is total cost, p is unit cost. Returns y which is coverage
    '''
    y = float(x)/p
    return y
    
###############################################################################
## Make single cost outcome curve
# Inputs: 
#    Input types:
#    1. effectname: list. Needs to be a 
#    2. datain: EITHER a bunch (if project data already loaded) OR a string specifying the project name (which will then be load a bunch)
#    3. progname: string. Needs to be one of the keys of D.programs
#    4. coparams: list. Contains parameters for the coverage-outcome curves, obtained from the GUI or spreadsheet
#        coparams(0) = the lower bound for the outcome when coverage = 0
#        coparams(1) = the upper bound for the outcome when coverage = 0
#        coparams(2) = the lower bound for the outcome when coverage = 1
#        coparams(3) = the upper bound for the outcome when coverage = 1

#    Output 
#    1. plotdata
#    2. D
###############################################################################
def makecco(D=None, progname = default_progname, effectname = default_effectname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot, verbose=2,nxpts = 1000):
    
    printv("makecco(%s, %s, %s, %s, %s, %s, %s)" % (progname, effectname, ccparams, coparams, makeplot, verbose, nxpts), 2, verbose)

    # Check that the selected program is in the program list 
    if unicode(progname) not in D.programs.keys():
        printv("progname: %s programs: %s" % (unicode(progname), D.programs.keys()), 5, verbose)
        raise Exception('Please select one of the following programs %s' % D.programs.keys())
    # Check that the selected program is in the program list 
    short_effectname = effectname[:2] # only matching by effect "signature"
    short_effectlist = [e[:2] for e in D.programs[progname]]
    if short_effectname not in short_effectlist:
        print "makecco short_effectname: %s short_effectlist: %s" % (short_effectname, short_effectlist)
        raise Exception('Please select one of the following effects %s' % D.programs[progname])

    # Extract info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number

    # Get population info
    popname = effectname[1]

    # Only going to make cost-outcome curves if a program affects a SPECIFIC population -- otherwise will just make cost-coverage curves
    if not D.data.meta.progs.saturating[prognumber]:
        return [], [], []
    else:
        if popname[0] in D.data.meta.pops.short:
            popnumber = D.data.meta.pops.short.index(popname[0])
        else: 
            popnumber = 0
        
        printv("coparams in makecco: %s" % coparams, 5, verbose)
        # Get inputs from either GUI... 
        if coparams and len(coparams)>=3: # TODO: would it be better to use a dictionary structure, so that the order doesn't have to be fixed?
            zeromin = coparams[0] # Assumptions of behaviour at zero coverage (lower bound)
            zeromax = coparams[1] # Assumptions of behaviour at zero coverage (upper bound)
            fullmin = coparams[2] # Assumptions of behaviour at maximal coverage (lower bound)
            fullmax = coparams[3] # Assumptions of behaviour at maximal coverage (upper bound)
        # ... or spreadsheet
        else: 
            zeromin = effectname[2][0][0] # Assumptions of behaviour at zero coverage (lower bound)
            zeromax = effectname[2][0][1] # Assumptions of behaviour at zero coverage (upper bound)
            fullmin = effectname[2][1][0] # Assumptions of behaviour at maximal coverage (lower bound)
            fullmax = effectname[2][1][1] # Assumptions of behaviour at maximal coverage (upper bound)
            coparams = [zeromin,zeromax,fullmin,fullmax] # Put all this in a list to pass to makeco
        
        # Parameters for cost-coverage curves
        saturation = ccparams[0]
        growthrate = (-1/ccparams[2])*log((2*saturation)/(ccparams[1]+saturation) - 1)
        xupperlim = ccparams[3]

        # Generate samples of zero-coverage and full-coverage behaviour
        muz, stdevz, muf, stdevf = makecosampleparams(coparams, verbose=verbose)
        zerosample, fullsample = makesamples(coparams, muz, stdevz, muf, stdevf, D.opt.nsims)

        # Generate samples of zero-coverage and full-coverage behaviour
        storeparams = [muz, stdevz, muf, stdevf, saturation, growthrate]

        # Get the coverage-outcome relationships            
        plotdata_co, storeparams_co = makeco(D, progname, effectname, coparams, makeplot=makeplot, verbose=verbose)

        # Create x dataset and initialise y dataset
        xvalscco = linspace(0,xupperlim,nxpts)
        
        # Min, Median and Max lines
        mediancco = ccoeqn(xvalscco, [saturation, growthrate, muz, muf])# Generate median cost-outcome curve
        mincco = ccoeqn(xvalscco, [saturation, growthrate, coparams[0], coparams[2]])# Generate min cost-outcome curve
        maxcco = ccoeqn(xvalscco, [saturation, growthrate, coparams[1], coparams[3]])# Generate max cost-outcome curve

        # Extract scatter data
        totalcost = D.data.costcov.cost[prognumber] # get total cost data
        outcome = D.data[effectname[0][0]][effectname[0][1]][popnumber]

        # Get around situations where there's an assumption for coverage but not for behaviour, or vice versa
        if (len(totalcost) == 1 and len(outcome) > 1): 
            outcome = float_array(outcome)
            outcome = outcome[~isnan(outcome)]
            outcome = outcome[-1]
        elif (len(outcome) == 1 and len(totalcost) > 1):
            totalcost = float_array(totalcost)
            totalcost = totalcost[~isnan(totalcost)]
            totalcost = totalcost[-1]

        plot_title = input_parameter_name(effectname[0][1])+ ' - ' + effectname[1][0]

        # Create and populate output structure with plotting data
        plotdata = {}
        plotdata['xlinedata'] = xvalscco # X data for all line plots
        plotdata['ylinedata'] = [mediancco,maxcco,mincco] # Y data for second line plot
        plotdata['ylinedata1'] = mediancco # Y data for second line plot
        plotdata['ylinedata2'] = maxcco  # Y data for third line plot
        plotdata['ylinedata3'] = mincco  # Y data for fourth line plot
        plotdata['xscatterdata'] = totalcost
        plotdata['yscatterdata'] = outcome
        plotdata['title'] = plot_title
        plotdata['xlabel'] = 'USD'
        plotdata['ylabel'] = 'Outcome'
        
        # Plot results (probably delete once in GUI)                            
        if makeplot:
            figure()
            hold(True)

            ## Plot curves
            plot(plotdata['xlinedata'], plotdata['ylinedata1'], color = 'b', lw = 2)
            plot(plotdata['xlinedata'], plotdata['ylinedata2'], 'k--', lw = 2)
            plot(plotdata['xlinedata'], plotdata['ylinedata3'], 'k--', lw = 2)
            plot(plotdata['xscatterdata'], plotdata['yscatterdata'], 'ro')
                
            title(plotdata['title'])
            xlabel(plotdata['xlabel'])
            ylabel(plotdata['ylabel'] )
    
        return plotdata, plotdata_co, storeparams

###############################################################################
## Make all cost outcome curves for a given program
###############################################################################
def plotallcurves(D=None, progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot, verbose=2):
    
     # Get the cost-coverage and coverage-outcome relationships     
    plotdata_cc, storeparams_cc = makecc(D=D, progname=progname, ccparams=ccparams, makeplot=makeplot, verbose=verbose)

   ## Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())

    # Extract info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number

    ## Initialise storage of outputs   
    plotdata_co = {}
    plotdata = {}    
    effectnames = {}     

    # Loop over behavioural effects
    for effectname in D.programs[progname]:

        # Only going to make cost-outcome curves for non-saturating programs (#TODO check this is ok)
        if not D.data.meta.progs.saturating[prognumber]:
            if len(effectname) == 3: # There's no existing info here, append
                effectname.append(storeparams_cc)
            else:
                effectname[3] = storeparams_cc # There is existing info here, overwrite

        else:
            # Store outputs
            effectnumber = D.programs[progname].index(effectname)    
            effectnames[effectnumber] = effectname
            plotdata[effectnumber], plotdata_co[effectnumber], storeparams = makecco(D=D, progname=progname, effectname=effectname, ccparams=ccparams, coparams=coparams, makeplot=makeplot, verbose=verbose)

            ## Store outputs
            if len(effectname) == 3: # There's no existing info here, append
               effectname.append(storeparams)
            else:
                effectname[3] = storeparams # There is existing info here, overwrite
            D.programs[progname][effectnumber] = effectname
            

    return plotdata, plotdata_co, plotdata_cc, effectnames, D      

###############################################################################
## Make all curves for all programs
###############################################################################
def makeallccocs(D=None, verbose=2, makeplot = default_makeplot):
    for progname in D.programs.keys():
        plotdata_cco, plotdata_co, plotdata_cc, effectnames, D = plotallcurves(D, unicode(progname), makeplot = makeplot)
    return D

###############################################################################
## Generate samples of behaviour at zero and full coverage
###############################################################################
def makecosampleparams(coparams, verbose=2):
    
    ## Convert inputs from GUI into parameters needed for lines
    muz, stdevz = (coparams[0]+coparams[1])/2, (coparams[1]-coparams[0])/6 # Mean and standard deviation calcs
    muf, stdevf = (coparams[2]+coparams[3])/2, (coparams[3]-coparams[2])/6 # Mean and standard deviation calcs
    
    printv("coparams: %s muz: %s stdevz: %s muf: %s stdevf: %s" % (coparams, muz, stdevz, muf, stdevf), 5, verbose)
    return muz, stdevz, muf, stdevf

def makesamples(coparams, muz, stdevz, muf, stdevf, samplesize=1000):
    
    # Generate samples of zero-coverage and full-coverage behaviour
    zerosample = rtnorm((coparams[0] - muz) / stdevz, (coparams[1] - muz) / stdevz, mu=muz, sigma=stdevz, size = samplesize)
    fullsample = rtnorm((coparams[2] - muf) / stdevf, (coparams[3] - muf) / stdevf, mu=muf, sigma=stdevf, size = samplesize)
        
    return zerosample, fullsample

#plotdata = showdata(D, progname=default_progname, numbercov=default_numbercov, makeplot=default_makeplot)
# plotallcurves(D, progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot, verbose=2)