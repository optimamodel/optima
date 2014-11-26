"""
Creates and updates cost-coverage curves and coverage-outcome curves
    
Version: 2014nov16 by cliffk
"""
###############################################################################
## Set up
###############################################################################

import math
from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title
from numpy import linspace, exp, isnan, zeros, asarray
from truncnorm import truncnorm
from bunch import Bunch as struct, float_array
from dataio import loaddata

## Set defaults for testing
default_progname = u'FSW'
default_ccparams = [0.9, 0.2, 800000.0, 7e6]
default_coparams = []
default_makeplot = 1
#default_datain = D # use 'example' or programs
default_effectname = [['sex', 'condomcas'], [u'MSM'], [[0.3, 0.5], [0.7, 0.9]]]


###############################################################################
## Make cost coverage curve
#    Input types:
#    1. datain: EITHER a bunch (if project data already loaded) OR a string specifying the project name (which will then be load a bunch)
#    2. progname: string. Needs to be one of the keys of D.programs
#    3. ccparams: list. Contains parameters for the cost-coverage curves, obtained from the GUI
#            ccparams(0) = the saturation value
#            ccparams(1) = the 'known' coverage level
#            ccparams(2) = the 'known' funding requirements to achieve ccparams(2)
#            ccparams(3) = desired upper x limit

#    Output types:
#    1. plotdata

###############################################################################
def makecc(datain, progname = default_progname, ccparams = default_ccparams, makeplot = default_makeplot):
    
    ## Load data structure if it hasn't been passed as an argument... 
    if isinstance(datain, str):
        D, programs = loaddata(datain+'.prj')
    else:
        D = datain
    
    ## Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())

    ## Extract info from data structure
    prognumber = D.data.meta.progs.code.index(progname) # get program number
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
        growthrate = (-1/ccparams[2])*math.log((2*ccparams[0])/(ccparams[1]+ccparams[0]) - 1)
        xupperlim = ccparams[3] 

        # Store parameters for access later
        storeparams = [saturation, growthrate]

        # Create logistic relationship 
        xvalscc = linspace(0,xupperlim,1000) # take 1000 points between 0 and user-specified max
        yvalscc = 2*saturation / (1 + exp(-growthrate*xvalscc)) - saturation # calculate logistic function

    # ... for unit cost programs...
    else:
        unitcost = D.data.costcov.cost[prognumber]
        totalcost = []
        for i in range(len(unitcost)):
            totalcost.append(unitcost[i]*coverage[i])
            if not isnan(unitcost[i]):
                slope = unitcost[i] # this updates so the slope is the most recent unit cost

        ## Create linear relationship
        xvalscc = linspace(0,7e6,1000) # take 1000 points between 0 and some arbitrary max
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
        

    # Plot (to check it's working; delete once plotting enabled in GUI)
    if makeplot:
        figure()
        hold(True)
        plot(xvalscc, yvalscc, 'k-', lw = 2)
        plot(totalcost, coverage, 'ro')
        title(progname)
        xlabel('USD')
        ylabel('proportion covered')
    
    # Create and populate output structure with plotting data
    plotdata = {}
    plotdata['xlinedata'] = xvalscc
    plotdata['ylinedata'] = yvalscc
    plotdata['xscatterdata'] = totalcost
    plotdata['yscatterdata'] = coverage
    plotdata['title'] = progname
    plotdata['xlabel'] = 'USD'
    plotdata['ylabel'] = 'Proportion covered'
    
    return plotdata, storeparams

###############################################################################
## Generate samples of behaviour at zero and full coverage
###############################################################################
def makecosampleparams(coparams):
    
    ## Convert inputs from GUI into parameters needed for lines
    muz, stdevz = (coparams[0]+coparams[1])/2, (coparams[1]-coparams[0])/4 # Mean and standard deviation calcs
    muf, stdevf = (coparams[2]+coparams[3])/2, (coparams[3]-coparams[2])/4 # Mean and standard deviation calcs
    
    print ("coparams: %s muz: %s stdevz: %s muf: %s stdevf: %s" % (coparams, muz, stdevz, muf, stdevf))
    return muz, stdevz, muf, stdevf

 
def makesamples(muz, stdevz, muf, stdevf, samplesize=1000):
    
    ## Generate sample of zero-coverage behaviour
    zerosample = truncnorm((0 - muz) / stdevz, (1 - muz) / stdevz, loc=muz, scale=stdevz, size = samplesize)
    
    ## Generate sample of full-coverage behaviour
    fullsample = zeros(samplesize)
    if muf > muz: # Apply this if the c/o curve is increasing
        for i in range(samplesize):
            fullsample[i] = truncnorm((zerosample[i] - muf) / stdevf, (1 - muf) / stdevf, loc=muf, scale=stdevf, size = 1) # draw possible values for behvaiour at maximal coverage
    else:  # Apply this if the c/o curve is decreasing
        for i in range(samplesize):
            fullsample[i] = truncnorm((0 - muf) / stdevf, (zerosample[i] - muf) / stdevf, loc=muf, scale=stdevf, size = 1) # draw possible values for behvaiour at maximal coverage
    
    return zerosample, fullsample

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
def makeco(datain, progname = default_progname, effectname = default_effectname, coparams=default_coparams, makeplot = default_makeplot):

    ## Load data structure if it hasn't been passed as an argument... 
    if isinstance(datain, str):
        D = loaddata(datain+'.prj')
    else:
        D = datain
    
    ## Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())
    ## Check that the selected program is in the program list 
    if effectname not in D.programs[progname]:
        raise Exception('Please select one of the following effects %s' % D.programs[progname])

    ## Extract info from data structure
    prognumber = D.data.meta.progs.code.index(progname) # get program number
    
    ## Get population info
    popname = effectname[1]
        
    ## Only going to make cost-outcome curves if a program affects a SPECIFIC population -- otherwise will just make cost-coverage curves
    if popname[0] not in D.data.meta.pops.code:
        return [], D
    else:
        popnumber = D.data.meta.pops.code.index(popname[0]) 
        
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

        ## Get inputs from either GUI or spreadsheet
        if coparams: ## TODO: would be better to use a dictionary, so that the order doesn't have to be fixed
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

        ## Check inputs
        if (coparams < [0,0,0,0] or coparams > [1,1,1,1]):
            raise Exception('Please enter values between 0 and 1 for the ranges of behaviour at zero and full coverage')
            
        ## Generate sample of zero-coverage behaviour
        muz, stdevz, muf, stdevf = makecosampleparams(coparams)
        zerosample, fullsample = makesamples(muz, stdevz, muf, stdevf, 1000)

        # Store parameters for access later
        storeparams = [muz, stdevz, muf, stdevf]
        
        ## General set of coverage-outcome relationships
        xvalsco = linspace(0,1,1000) # take 1000 points along the unit interval
        yvalsco = zeros((1000,len(fullsample)))
        for i in range(len(fullsample)):
            yvalsco[:,i] = linspace(zerosample[i],fullsample[i],1000) # Generate 1000 straight lines
            
        ## Upper and lower bounds of line set
        ymin, ymax = zeros(1000), zeros(1000)
        for i in range(1000):
            ymax[i] = max(yvalsco[i,:])
            ymin[i] = min(yvalsco[i,:])
            
        ## Append range of start and end points to data structure NB THERE MUST BE A BETTER WAY TO DO THIS
 #       if len(effectname) == 3: # There's no existing info here, append
 #           effectname.append([zerosample, fullsample])
 #       else:
 #           effectname[3] = [zerosample, fullsample] # There is existing info here, overwrite
 #       D.programs[progname][effectnumber] = effectname

        ## Plot results (probably delete once in GUI)                            
        if makeplot:
            figure()
            hold(True)
            plot(xvalsco, linspace(muz,muf,1000), color = 'b', lw = 2)
            plot(xvalsco, ymax, 'k--', lw = 2)
            plot(xvalsco, ymin, 'k--', lw = 2)
            plot(coverage, outcome, 'ro')
            title(effectname[0][1]+ ' ' + effectname[1][0])
            xlabel('proportion covered')
            ylabel('outcome')
    
        # Create and populate output structure with plotting data
        plotdata = {}
        plotdata['xlinedata'] = xvalsco # X data for all line plots
        plotdata['ylinedata'] = [linspace(muz,muf,1000), ymax, ymin] # ALL Y data (for three lines)
        plotdata['ylinedata1'] = linspace(muz,muf,1000) # Y data for first line on plot
        plotdata['ylinedata2'] = ymax  # Y data for second line on plot
        plotdata['ylinedata3'] = ymin  # Y data for third line on plot
        plotdata['xscatterdata'] = coverage # X scatter data
        plotdata['yscatterdata'] = outcome # Y scatter data
        plotdata['title'] = effectname[0][1]+ ' ' + effectname[1][0]
        plotdata['xlabel'] = 'Proportion covered'
        plotdata['ylabel'] = 'Outcome'
    
        return plotdata, storeparams

###############################################################################
# Create cco equation
###############################################################################
def ccoeqn(x, p):
    '''
    Equation defining cco curves.
    '''
    y = (p[3]-p[2]) * ( 2*p[0] / (1 + exp(-p[1]*x)) - p[0]) + p[2]
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
def makecco(datain, progname = default_progname, effectname = default_effectname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot):

    ## Load data structure if it hasn't been passed as an argument... 
    if isinstance(datain, str):
        D = loaddata(datain+'.prj')
    else:
        D = datain
    
    ## Check that the selected program is in the program list 
    if unicode(progname) not in D.programs.keys():
        print("progname: %s programs: %s" % (unicode(progname), D.programs.keys()))
        raise Exception('Please select one of the following programs %s' % D.programs.keys())
    ## Check that the selected program is in the program list 
    if effectname not in D.programs[progname]:
        raise Exception('Please select one of the following effects %s' % D.programs[progname])

    ## Extract info from data structure
    prognumber = D.data.meta.progs.code.index(progname) # get program number

    ## Get population info
    popname = effectname[1]
    
    ## Only going to make cost-outcome curves if a program affects a specific population -- otherwise will just make cost-coverage curves
    if popname[0] not in D.data.meta.pops.short:
        return [], [], []
    else:          
        popnumber = D.data.meta.pops.short.index(popname[0]) 
        print("coparams in makecco: %s" % coparams)
        ## Get inputs from either GUI... 
        if coparams: # TODO: would it be better to use a dictionary structure, so that the order doesn't have to be fixed?
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
        growthrate = (-1/ccparams[2])*math.log((2*saturation)/(ccparams[1]+saturation) - 1)
        xupperlim = ccparams[3]

        # Generate samples of zero-coverage and full-coverage behaviour
        muz, stdevz, muf, stdevf = makecosampleparams(coparams)
        zerosample, fullsample = makesamples(muz, stdevz, muf, stdevf, 1000)

        # Generate samples of zero-coverage and full-coverage behaviour
        storeparams = [muz, stdevz, muf, stdevf, saturation, growthrate]

        # Get the coverage-outcome relationships            
        plotdata_co, storeparams_co = makeco(D, progname, effectname, coparams, makeplot)

        # Create x dataset and initialise y dataset
        xvalscco = linspace(0,xupperlim,1000)
        yvalscco = zeros((1000, len(fullsample)))
        
        # Create line set
        for i in range(len(fullsample)):
            yvalscco[:,i] = ccoeqn(xvalscco, [saturation, growthrate, zerosample[i], fullsample[i]]) # Generate 1000 cost-outcome curves

        # Median line
        mediancco = ccoeqn(xvalscco, [saturation, growthrate, muz, muf])# Generate median cost-outcome curve
        
        ## Create upper and lower bounds of line set
        ymin, ymax = zeros(1000), zeros(1000)
        for i in range(1000):
            ymax[i] = max(yvalscco[i,:])
            ymin[i] = min(yvalscco[i,:])
                
        ## Extract scatter data
        totalcost = D.data.costcov.cost[prognumber] # get total cost data
        outcome = D.data[effectname[0][0]][effectname[0][1]][popnumber]

        ## Get around situations where there's an assumption for coverage but not for behaviour, or vice versa
        if (len(totalcost) == 1 and len(outcome) > 1): 
            outcome = float_array(outcome)
            outcome = outcome[~isnan(outcome)]
            outcome = outcome[-1]
        elif (len(outcome) == 1 and len(totalcost) > 1):
            totalcost = float_array(totalcost)
            totalcost = totalcost[~isnan(totalcost)]
            totalcost = totalcost[-1]

        ## Plot results (probably delete once in GUI)                            
        if makeplot:
            figure()
            hold(True)

            ## Plot curves
            plot(xvalscco, mediancco, color = 'b', lw = 2)
            plot(xvalscco, ymax, 'k--', lw = 2)
            plot(xvalscco, ymin, 'k--', lw = 2)
            plot(totalcost, outcome, 'ro')
                
            title(effectname[0][1]+ ' ' + effectname[1][0])
            xlabel('USD')
            ylabel('outcome')

        # Create and populate output structure with plotting data
        plotdata = {}
        plotdata['xlinedata'] = xvalscco # X data for all line plots
        plotdata['ylinedata'] = [mediancco,ymax,ymin] # Y data for second line plot
        plotdata['ylinedata1'] = mediancco # Y data for second line plot
        plotdata['ylinedata2'] = ymax  # Y data for third line plot
        plotdata['ylinedata3'] = ymin  # Y data for fourth line plot
        plotdata['xscatterdata'] = totalcost
        plotdata['yscatterdata'] = outcome
        plotdata['title'] = effectname[0][1]+ ' ' + effectname[1][0]
        plotdata['xlabel'] = 'USD'
        plotdata['ylabel'] = 'Outcome'
    
        return plotdata, plotdata_co, storeparams

###############################################################################
## Make all cost outcome curves for a given program
# Inputs: 
#    Input types:
#    1. effectname: list. Needs to be a 
#    2. datain: EITHER a bunch (if project data already loaded) OR a string specifying the project name (which will then be load a bunch)
#    3. progname: string. Needs to be one of the keys of D.programs
#    4. ccparams: list
#    5. coparams: list. Contains parameters for the coverage-outcome curves, obtained from the GUI or spreadsheet
#        coparams(0) = the lower bound for the outcome when coverage = 0
#        coparams(1) = the upper bound for the outcome when coverage = 0
#        coparams(2) = the lower bound for the outcome when coverage = 1
#        coparams(3) = the upper bound for the outcome when coverage = 1

#    Output:
#    1. plotdata
#    2. plotdata_co
#    2. plotdata_cco
###############################################################################
def plotallcurves(datain, progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot):

    ## Load data structure if it hasn't been passed as an argument... 
    if isinstance(datain, str):
        D = loaddata(datain+'.prj')
    else:
        D = datain
    
     # Get the cost-coverage and coverage-outcome relationships            
    plotdata_cc, storeparams_cc = makecc(D, progname, ccparams, makeplot=1)

   ## Check that the selected program is in the program list 
    if progname not in D.programs.keys():
        raise Exception('Please select one of the following programs %s' % D.programs.keys())

    ## Initialise storage of outputs   
    plotdata_co = {}
    plotdata = {}         

    # Loop over behavioural effects
    for effectname in D.programs[progname]:

        popname = effectname[1]
    
        if popname[0] in D.data.meta.pops.short:

            popnumber = D.data.meta.pops.short.index(popname[0]) 

            ## Store outputs
            effectnumber = D.programs[progname].index(effectname)    
            plotdata[effectnumber], plotdata_co[effectnumber], storeparams = makecco(D, progname, effectname, ccparams, coparams, makeplot)
#            C[effectname[0][1]] = [popname[0], storeparams]

    return plotdata, plotdata_co, plotdata_cc
      
## Example of use
#plotdata_cco, plotdata_co, plotdata_cc, C = plotallcurves()
#plotdata, plotdata_co, storeparams = makecco(D, progname=default_progname, effectname = default_effectname, ccparams = default_ccparams, coparams = default_coparams, makeplot=1)
