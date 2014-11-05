def epiresults(D, verbose=2):
    """
    Generate all outputs required for the model:
        Prevalence
        Incidence
        DALYs
        Deaths
    
    For each, calculate for both overall and per population.

    Version: 2014nov05
    """
    
    if verbose>=1: print('Calculating epidemiology results...')
    
    ##########################################################################
    ## Preliminaries
    ##########################################################################
    
    from matplotlib.pylab import zeros
    from bunch import Bunch as struct
    from vectocolor import vectocolor
    D.O = struct()
    D.O.__doc__ = 'Output structure containing everything that might need to be plotted'
    D.O.tvec = D.S.tvec # Copy time vector
    npts = len(D.O.tvec)
    D.O.poplabels = D.G.meta.pops.long
    D.O.popcolors = vectocolor(D.G.npops)
    
    
    ##########################################################################
    ## Prevalence
    ##########################################################################
    if verbose>=3: print('  Calculating prevalence...')
    D.O.prev = struct()
    D.O.prev.pop = zeros((D.G.npops, npts))
    D.O.prev.tot = zeros(npts)
    
    # Calculate prevalence
    for t in range(npts):
        D.O.prev.pop[:,t] = D.S.people[1:,:,t].sum(axis=0) / D.S.people[:,:,t].sum(axis=0) * 100
        D.O.prev.tot[t] = D.S.people[1:,:,t].sum() / D.S.people[:,:,t].sum() * 100
    
    D.O.prev.xlabel = 'Years'
    D.O.prev.ylabel = 'Prevalence (%)'
    
    
    
    
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
#    nplots = 6
#    plotdata = []
#    for p in range(nplots):
#        plotdata.append(struct())
#        plotdata[p].xmodeldata = r_[2000:endyear+1] # Model output
#        plotdata[p].ymodeldata = exp(-rand(len(plotdata[p].xmodeldata)))
#        plotdata[p].xexpdata = [2000, 2005, 2008] # Experimental data
#        plotdata[p].yexpdata = [0.3, 0.4, 0.6]
#        plotdata[p].xlabel = 'Year'
#        plotdata[p].ylabel = 'Prevalence'
        
        # e.g. 
#        from matplotlib.pylab import plot, hold, scatter, subplot
#        subplot(3,2,p)
#        plot(plotdata[p].xmodeldata, plotdata[p].ymodeldata)
#        hold(True)
#        scatter(plotdata[p].xexpdata, plotdata[p].yexpdata);
    
    if verbose>=2: print('  ...done running epidemiology results.')
    return D

epiresults(D)