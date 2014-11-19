"""
Creates and updates cost-coverage curves and coverage-outcome curves
    
Version: 2014nov13
"""
###############################################################################
## Set up
###############################################################################

import numpy as np
import math
from matplotlib.pylab import zeros, figure, plot, hold, xlabel, ylabel, title
import scipy.stats as stats
from bunch import Bunch as struct
from dataio import loaddata, savedata

## Set defaults
default_progname = 'FSW'
default_ccparams = [0.9, 0.2, 800000.0, 7e6]
default_coparams = []
default_makeplot = 1

###############################################################################
## Make cost coverage curve
# Inputs:
#    D is the data structure generated from reading in the spreadsheet
#    progname is the program
#    ccparams is the parameter structure for the cost-coverage curves, obtained from the GUI
#        ccparams(0) = the saturation value
#        ccparams(1) = the 'known' coverage level
#        ccparams(2) = the 'known' funding requirements to achieve ccparams(2)
#        ccparams(3) = desired upper x limit
###############################################################################
def makecc(D = [], projectname = 'example', progname = default_progname, ccparams = default_ccparams, makeplot = default_makeplot):
    
    ## Load data structure if it hasn't been passed as an argument... 
    if not D:
        D = loaddata(projectname+'.prj')
    
    ## Extract info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number
    totalcost = D.data.costcov.total[prognumber] # get total cost data
    coverage = D.data.costcov.cov[prognumber] # get program coverage data

    ## Get scatter data
    if (len(coverage) == 1 and len(totalcost) > 1): 
        totalcost = np.asarray(totalcost)
        totalcost = totalcost[~np.isnan(totalcost)]
        totalcost = totalcost[-1]
    elif (len(totalcost) == 1 and len(coverage) > 1):
        coverage = np.asarray(coverage)
        coverage = coverage[~np.isnan(coverage)]
        coverage = coverage[-1]
#    else:
#        for i in range(len(coverage)):
#            if (~math.isnan(coverage[i]) and ~math.isnan(totalcost[i])):
#                plot(totalcost[i], coverage[i], 'ro')
    
    ## Check inputs from GUI 
    if (ccparams[0] <= 0 or ccparams[0] > 1):
        raise Exception('Please enter a value between 0 and 1 for the saturation coverage level')
    if (ccparams[1] < 0 or ccparams[1] > 1):
        raise Exception('Please enter a value between 0 and 1 for the coverage level in Question 2')
    if (ccparams[1] == 0 or ccparams[2] == 0):
        raise Exception('Please enter non-zero values for the cost and coverage level estimates in Question 2')
    if ccparams[2] < 0:
        raise Exception('Negative funding levels are not permitted, please revise')

    ## Convert inputs from GUI into parameters needed for curves
    saturation = ccparams[0]
    growthrate = (-1/ccparams[2])*math.log((2*ccparams[0])/(ccparams[1]+ccparams[0]) - 1)
    xupperlim = ccparams[3] 

    ## Create lines to plot    
    xvalscc = np.linspace(0,xupperlim,1000) # take 1000 points between 0 and user-specified max
    yvalscc = 2*saturation / (1 + np.exp(-growthrate*xvalscc)) - saturation # calculate logistic function

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
    plotdata = struct()
    plotdata.xlinedata = xvalscc
    plotdata.ylinedata = yvalscc
    plotdata.xscatterdata = totalcost
    plotdata.yscatterdata = coverage
    plotdata.title = progname
    plotdata.xlabel = 'USD'
    plotdata.ylabel = 'Proportion covered'
    
    return plotdata, xvalscc, yvalscc


###############################################################################
## Make coverage outcome curve
# Inputs: 
#    D is the data structure generated from reading in the spreadsheet
#    effectname is e.g. effectname = D.programs.FSW[0]
#    progname is the program
#    coparams is the parameter structure for the coverage-outcome curves, obtained from the GUI
#        coparams(0) = the lower bound for the outcome when coverage = 0
#        coparams(1) = the upper bound for the outcome when coverage = 0
#        coparams(2) = the lower bound for the outcome when coverage = 1
#        coparams(3) = the upper bound for the outcome when coverage = 1
###############################################################################
def makeco(effectname, D = [], projectname='example', progname = default_progname, coparams=default_coparams, makeplot = default_makeplot):

    ## Load data structure if it hasn't been passed as an argument... 
    if not D:
        D = loaddata(projectname+'.prj')

    ## Extract info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number
    
    ## Get population info
    popname = effectname[1]
    effectnumber = D.programs[progname].index(effectname)
        
    ## Only going to make cost-outcome curves if a program affects a SPECIFIC population -- otherwise will just make cost-coverage curves
    if popname[0] not in D.data.meta.pops.short:
        return [], D
    else:
        popnumber = D.data.meta.pops.short.index(popname[0]) 
        
        # Get data for scatter plots
        outcome = D.data[effectname[0][0]][effectname[0][1]][popnumber]
        coverage = D.data.costcov.cov[prognumber] # get program coverage data

        if (len(coverage) == 1 and len(outcome) > 1): 
            outcome = np.asarray(outcome)
            outcome = outcome[~np.isnan(outcome)]
            outcome = outcome[-1]
        elif (len(outcome) == 1 and len(coverage) > 1):
            coverage = np.asarray(coverage)
            coverage = coverage[~np.isnan(coverage)]
            coverage = coverage[-1]
#        else:
#            for i in range(len(coverage)):
#                if (~math.isnan(outcome[i]) and ~math.isnan(coverage[i])):
#                    plot(coverage[i], outcome[i], 'ro')

        ## Get inputs from either GUI or spreadsheet
        if coparams: ## TODO: would be better to use a dictionary structure, so that the order doesn't have to be fixed
            zeromin = coparams[0] # Assumptions of behaviour at zero coverage (lower bound)
            zeromax = coparams[1] # Assumptions of behaviour at zero coverage (upper bound)
            fullmin = coparams[2] # Assumptions of behaviour at maximal coverage (lower bound)
            fullmax = coparams[3] # Assumptions of behaviour at maximal coverage (upper bound)
        else: 
            zeromin = effectname[2][0][0] # Assumptions of behaviour at zero coverage (lower bound)
            zeromax = effectname[2][0][1] # Assumptions of behaviour at zero coverage (upper bound)
            fullmin = effectname[2][1][0] # Assumptions of behaviour at maximal coverage (lower bound)
            fullmax = effectname[2][1][1] # Assumptions of behaviour at maximal coverage (upper bound)

        ## Check inputs
        if ([zeromin, zeromax, fullmin, fullmax] < [0,0,0,0] or [zeromin, zeromax, fullmin, fullmax] > [1,1,1,1]):
            raise Exception('Please enter values between 0 and 1 for the ranges of behaviour at zero and full coverage')
            
        ## Convert inputs from GUI into parameters needed for lines
        muz, stdevz = (zeromax+zeromin)/2, (zeromax-zeromin)/4 # Mean and standard deviation calcs
        muf, stdevf = (fullmax+fullmin)/2, (fullmax-fullmin)/4 # Mean and standard deviation calcs
        
        ## Generate sample of zero-coverage behaviour
        zerosample = stats.truncnorm.rvs((0 - muz) / stdevz, (1 - muz) / stdevz, loc=muz, scale=stdevz, size = 1000)
    
        ## Generate sample of full-coverage behaviour
        fullsample = zeros(len(zerosample))
        if muf > muz: # Apply this if the c/o curve is increasing
            for i in range(len(zerosample)):
                fullsample[i] = stats.truncnorm.rvs((zerosample[i] - muf) / stdevf, (1 - muf) / stdevf, loc=muf, scale=stdevf, size = 1) # draw possible values for behvaiour at maximal coverage
        else:  # Apply this if the c/o curve is decreasing
            for i in range(len(zerosample)):
                fullsample[i] = stats.truncnorm.rvs((0 - muf) / stdevf, (zerosample[i] - muf) / stdevf, loc=muf, scale=stdevf, size = 1) # draw possible values for behvaiour at maximal coverage
        
        ## General set of coverage-outcome relationships
        xvalsco = np.linspace(0,1,1000) # take 1000 points along the unit interval
        yvalsco = zeros((1000,len(fullsample)))
        for i in range(len(fullsample)):
            yvalsco[:,i] = np.linspace(zerosample[i],fullsample[i],1000) # Generate 1000 straight lines
            
        ## Upper and lower bounds of line set
        ymin, ymax = zeros(1000), zeros(1000)
        for i in range(1000):
            ymax[i] = max(yvalsco[i,:])
            ymin[i] = min(yvalsco[i,:])
            
        ## Append range of start and end points to data structure NB THERE MUST BE A BETTER WAY TO DO THIS
        if len(effectname) == 3: # There's no existing info here, append
            effectname.append([zerosample, fullsample])
        else:
            effectname[3] = [zerosample, fullsample] # There is existing info here, overwrite
        D.programs[progname][effectnumber] = effectname

        ## Plot results (probably delete once in GUI)                            
        if makeplot:
            figure()
            hold(True)
#            plot(xvalsco, yvalsco, color = '0.75')
            plot(xvalsco, np.linspace(muz,muf,1000), color = 'b', lw = 2)
            plot(xvalsco, ymax, 'k--', lw = 2)
            plot(xvalsco, ymin, 'k--', lw = 2)
            plot(coverage, outcome, 'ro')
            title(effectname[0][1]+ ' ' + effectname[1][0])
            xlabel('proportion covered')
            ylabel('outcome')
    
        # Create and populate output structure with plotting data
        plotdata = struct()
        plotdata.xlinedata = xvalsco # X data for all line plots
        plotdata.ylinedata1 = yvalsco # Y data for first line plot
        plotdata.ylinedata2 = np.linspace(muz,muf,1000) # Y data for second line plot
        plotdata.ylinedata3 = ymax  # Y data for third line plot
        plotdata.ylinedata4 = ymin  # Y data for fourth line plot
        plotdata.xscatterdata = coverage
        plotdata.yscatterdata = outcome
        plotdata.title = effectname[0][1]+ ' ' + effectname[1][0]
        plotdata.xlabel = 'Proportion covered'
        plotdata.ylabel = 'Outcome'
    
        return plotdata, D


###############################################################################
## Make cost outcome curve
###############################################################################
def makecco(D = [], projectname='example', progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, makeplot=default_makeplot):

    ## Load data structure if it hasn't been passed as an argument... 
    if not D:
        D = loaddata(projectname+'.prj')

    ## Extract info from data structure
    prognumber = D.data.meta.progs.short.index(progname) # get program number

    # Get the cost-coverage and coverage-outcome relationships            
    plotdata_cc, xvalscc, yvalscc = makecc(D)
    
    ## Initialise storage of outputs   
    plotdata_co = {}
    plotdata = {}         

    # Loop over behavioural effects
    for effectname in D.programs[progname]:

        ## Get population info
        popname = effectname[1]
        effectnumber = D.programs[progname].index(effectname)
            
        ## Only going to make cost-outcome curves if a program affects a specific population -- otherwise will just make cost-coverage curves
        if popname[0] not in D.data.meta.pops.short:
            return [], plotdata_cc, []
        else:            
            ## Initialise storage of plotting data
            popnumber = D.data.meta.pops.short.index(popname[0]) 

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
            
            # Parameters for cost-coverage curves
            saturation = ccparams[0]
            growthrate = (-1/ccparams[2])*math.log((2*saturation)/(ccparams[1]+saturation) - 1)

            # Parameters for coverage-outcome curves
            muz, muf = (zeromax+zeromin)/2, (fullmax+fullmin)/2  # Mean calcs
            plotdata_co[effectnumber], D = makeco(effectname, D)

            # Extract samples of start and end points
            zerosample = D.programs[progname][effectnumber][3][0]
            fullsample = D.programs[progname][effectnumber][3][1]

            # CCreate x dataset and initialise y dataset
            xvalscco = xvalscc
            yvalscco = zeros((1000, len(fullsample)))
            
            # Create line set
            for i in range(len(fullsample)):
                yvalscco[:,i] = (fullsample[i]-zerosample[i])*(2*saturation / (1 + np.exp(-growthrate*xvalscco)) - saturation) + zerosample[i] # Generate 1000 cost-outcome curves
        
            # Median line
            mediancco = (muf-muz)*(2*saturation / (1 + np.exp(-growthrate*xvalscco)) - saturation) + muz # Generate median cost-outcome curve
            
            ## Create upper and lower bounds of line set
            ymin, ymax = zeros(1000), zeros(1000)
            for i in range(1000):
                ymax[i] = max(yvalscco[i,:])
                ymin[i] = min(yvalscco[i,:])
                    
            ## Extract scatter data
            totalcost = D.data.costcov.total[prognumber] # get total cost data
            outcome = D.data[effectname[0][0]][effectname[0][1]][popnumber]

            ## Get around situations where there's an assumption for coverage but not for behaviour, or vice versa
            if (len(totalcost) == 1 and len(outcome) > 1): 
                outcome = np.asarray(outcome)
                outcome = outcome[~np.isnan(outcome)]
                outcome = outcome[-1]
            elif (len(outcome) == 1 and len(totalcost) > 1):
                totalcost = np.asarray(totalcost)
                totalcost = totalcost[~np.isnan(totalcost)]
                totalcost = totalcost[-1]
#            else:
#                for i in range(len(totalcost)):
#                    if (~math.isnan(outcome[i]) and ~math.isnan(totalcost[i])):
                
            ## Plot results (probably delete once in GUI)                            
            if makeplot:
                figure()
                hold(True)

                ## Plot curves
#                plot(xvalscco, yvalscco, color = '0.75')
                plot(xvalscco, mediancco, color = 'b', lw = 2)
                plot(xvalscco, ymax, 'k--', lw = 2)
                plot(xvalscco, ymin, 'k--', lw = 2)
                plot(totalcost, outcome, 'ro')
                    
                title(effectname[0][1]+ ' ' + effectname[1][0])
                xlabel('USD')
                ylabel('outcome')
                
            # Create and populate output structure with plotting data
            plotdata[effectnumber] = struct()
            plotdata[effectnumber].xlinedata = xvalscco # X data for all line plots
            plotdata[effectnumber].ylinedata1 = yvalscco # Y data for first line plot
            plotdata[effectnumber].ylinedata2 = mediancco # Y data for second line plot
            plotdata[effectnumber].ylinedata3 = ymax  # Y data for third line plot
            plotdata[effectnumber].ylinedata4 = ymin  # Y data for fourth line plot
            plotdata[effectnumber].xscatterdata = totalcost
            plotdata[effectnumber].yscatterdata = outcome
            plotdata[effectnumber].title = effectname[0][1]+ ' ' + effectname[1][0]
            plotdata[effectnumber].xlabel = 'USD'
            plotdata[effectnumber].ylabel = 'Outcome'
    
    return plotdata, plotdata_cc, plotdata_co
                
## Example of use
plotdata_cco, plotdata_cc, plotdata_co = makecco()

