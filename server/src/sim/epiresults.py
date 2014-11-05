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
    
    from printv import printv
    printv('Calculating epidemiology results...', 1, verbose)
    
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
            
            printv('Calculating prevalence...', 3, verbose)
        
            # Calculate prevalence
            for t in range(npts):
                D.O.prev.pops[:,t] = D.S.people[1:,:,t].sum(axis=0) / D.S.people[:,:,t].sum(axis=0) * D.O.percent
                D.O.prev.tot[t] = D.S.people[1:,:,t].sum() / D.S.people[:,:,t].sum() * D.O.percent
            
            # Find prevalence data    
            epidata = D.data.key.hivprev[0] # TODO: include uncertainties
            D.O.prev.ylabel = 'Prevalence (%)'



        ##########################################################################
        ## Incidence
        ##########################################################################
        if epi=='inci':
            
            printv('Calculating incidence...', 3, verbose)
        
            # Calculate incidence
            for t in range(npts):
                D.O.inci.pops[:,t] = D.S.inci[:,t] # Simple
                D.O.inci.tot[t] = D.S.inci[:,t].sum()
            
            # Find incidence data    
            epidata = D.data.opt.numinfect # TODO: include uncertainties
            D.O.inci.ylabel = 'New HIV infections per year'



        ##########################################################################
        ## Deaths
        ##########################################################################
        if epi=='death':
            
            printv('Calculating deaths...', 3, verbose)
        
            # Calculate incidence
            for t in range(npts):
                D.O.death.pops[:,t] = D.S.death[:,t] # Simple
                D.O.death.tot[t] = D.S.death[:,t].sum()
            
            # Find incidence data    
            epidata = D.data.opt.death # TODO: include uncertainties
            D.O.death.ylabel = 'HIV-related deaths per year'




        ##########################################################################
        ## DALYs
        ##########################################################################
        if epi=='daly':
            
            printv('Calculating DALYs...', 3, verbose)
        
            # Calculate DALYs
            for t in range(npts):
                D.O.inci.pops[:,t] = D.S.inci[:,t] # Simple
                D.O.inci.tot[t] = D.S.inci[:,t].sum()
            
            # Find DALYs data haha LOL
            epidata = nan+zeros(ndatayears) # No data
            D.O.daly.ylabel = 'Disability-adjusted life years per year'
            
            

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

   
    
    printv('...done running epidemiology results.', 2, verbose)
    return D