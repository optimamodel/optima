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
    
    from matplotlib.pylab import zeros, nan, array
    from bunch import Bunch as struct
    from vectocolor import vectocolor
    D.O = struct()
    D.O.__doc__ = 'Output structure containing everything that might need to be plotted'
    D.O.tvec = D.S.tvec # Copy time vector
    npts = len(D.O.tvec)
    D.O.poplabels = D.G.meta.pops.long
    D.O.popcolors = vectocolor(D.G.npops)
    D.O.colorm = (0,0.3,1) # Model color
    D.O.colord = (0,0,0) # Data color
    D.O.percent = 100 # Whether or not to use percents
    D.O.xdata = D.data.epiyears
    ndatayears = len(D.O.xdata)
    
    for epi in ['prev', 'inci', 'daly', 'death']:
        D.O[epi] = struct()
        D.O[epi].pops = zeros((D.G.npops, npts)) # Careful, can't use pop since it's a method!
        D.O[epi].tot = zeros(npts)
        D.O[epi].ydata = zeros((D.G.npops,ndatayears))
        D.O[epi].xlabel = 'Years'
        
        
        ##########################################################################
        ## Prevalence
        ##########################################################################
        if epi=='prev':
            
            if verbose>=3: print('  Calculating prevalence...')
        
            # Calculate prevalence
            for t in range(npts):
                D.O.prev.pops[:,t] = D.S.people[1:,:,t].sum(axis=0) / D.S.people[:,:,t].sum(axis=0) * D.O.percent
                D.O.prev.tot[t] = D.S.people[1:,:,t].sum() / D.S.people[:,:,t].sum() * D.O.percent
            
            # Find prevalence data    
            D.O.prev.ydata = zeros((D.G.npops,ndatayears))
            epidata = D.data.key.hivprev[0]
            D.O.prev.ylabel = 'Prevalence (%)'
            
            

        ##########################################################################
        ## Finish processing data
        ##########################################################################
        for p in range(D.G.npops):
            thispopdata = epidata[p]
            if len(thispopdata) == 1: 
                thispopdata = nan+zeros(ndatayears) # If it's an assumption, just set with nans
            elif len(thispopdata) != ndatayears:
                raise Exception('Expect data length of 1 or %i, actually %i' % (ndatayears, len(thispopdata)))
            D.O[epi].ydata[p,:] = array(thispopdata) * D.O.percent
#
#            
#    
#    
#    
#    ##########################################################################
#    ## Incidence
#    ##########################################################################
#    if verbose>=3: print('  Calculating incidence...')
#    D.O.prev = struct()
#    D.O.prev.pops = zeros((D.G.npops, npts)) # Careful, can't use pop since it's a method!
#    D.O.prev.tot = zeros(npts)
#    
#    # Calculate prevalence
#    for t in range(npts):
#        D.O.prev.pops[:,t] = D.S.people[1:,:,t].sum(axis=0) / D.S.people[:,:,t].sum(axis=0) * D.O.percent
#        D.O.prev.tot[t] = D.S.people[1:,:,t].sum() / D.S.people[:,:,t].sum() * D.O.percent
#    
#    # Find prevalence data    
#    D.O.prev.xdata = D.data.epiyears
#    ndatayears = len(D.O.prev.xdata)
#    D.O.prev.ydata = zeros((D.G.npops,ndatayears))
#    for p in range(D.G.npops):
#        thispopprev = D.data.key.hivprev[0][p]
#        if len(thispopprev) == 1: 
#            thispopprev = nan+zeros(ndatayears) # If it's an assumption, just set with nans
#        elif len(thispopprev) != ndatayears:
#            raise Exception('Expect data length of 1 or %i, actually %i' % (ndatayears, len(thispopprev)))
#        D.O.prev.ydata[p,:] = array(thispopprev) * D.O.percent
#        
#    # Define labels
#    D.O.prev.xlabel = 'Years'
#    D.O.prev.ylabel = 'Prevalence (%)'
    
    
    
    ##########################################################################
    ## DALYs
    ##########################################################################
    
    
    
    
    ##########################################################################
    ## Deaths
    ##########################################################################
   
    
    if verbose>=2: print('  ...done running epidemiology results.')
    return D