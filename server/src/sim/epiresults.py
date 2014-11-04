def epiresults(D, startyear=2000, endyear=2015):
    """
    Generate all outputs required for the model:
        Prevalence
        Incidence
        DALYs
        Deaths
    
    For each, calculate for both overall and per population.

    Version: 2014nov04
    """
    
    ##########################################################################
    ## Prevalence
    ##########################################################################
    
    
    
    
    ##########################################################################
    ## Incidence
    ##########################################################################
    
    
    
    
    ##########################################################################
    ## DALYs
    ##########################################################################
    
    
    
    
    ##########################################################################
    ## Deaths
    ##########################################################################
    
    # Generate data for scatter and line plots
    nplots = 6
    plotdata = []
    for p in range(nplots):
        plotdata.append(struct())
        plotdata[p].xmodeldata = r_[2000:endyear+1] # Model output
        plotdata[p].ymodeldata = exp(-rand(len(plotdata[p].xmodeldata)))
        plotdata[p].xexpdata = [2000, 2005, 2008] # Experimental data
        plotdata[p].yexpdata = [0.3, 0.4, 0.6]
        plotdata[p].xlabel = 'Year'
        plotdata[p].ylabel = 'Prevalence'
        
        # e.g. 
#        from matplotlib.pylab import plot, hold, scatter, subplot
#        subplot(3,2,p)
#        plot(plotdata[p].xmodeldata, plotdata[p].ymodeldata)
#        hold(True)
#        scatter(plotdata[p].xexpdata, plotdata[p].yexpdata);
    
    return O
