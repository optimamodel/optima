def gatherplotdata(D, verbose=2):
    """
    Generate all outputs required for the model:
        Prevalence
        Incidence
        DALYs
        Deaths
    
    For each, calculate for both overall and per population.

    Version: 2014nov22
    """
    
    
    ##########################################################################
    ## Preliminaries
    ##########################################################################
    
    from matplotlib.pylab import zeros, nan, size, asarray
    from bunch import Bunch as struct, int_array, float_array
    from vectocolor import vectocolor
    from printv import printv
    printv('Calculating epidemiology results...', 1, verbose)
    
    D.O = struct()
    D.O.__doc__ = 'Output structure containing everything that might need to be plotted'
    D.O.tvec = D.S.tvec # Copy time vector
    npts = len(D.O.tvec)
    D.O.poplabels = D.G.meta.pops.long
    D.O.popcolors = vectocolor(D.G.npops)
    D.O.colorm = (0,0.3,1) # Model color
    D.O.colord = (0,0,0) # Data color
    D.O.xdata = D.data.epiyears
    ndatayears = len(D.O.xdata)
    
    for epi in ['prev', 'inci', 'daly', 'death']:
        D.O[epi] = struct()
        D.O[epi].pops = zeros((D.G.npops, npts)) # Careful, can't use pop since it's a method!
        D.O[epi].tot = zeros(npts)
        D.O[epi].xlabel = 'Years'
        
        
        ##########################################################################
        ## Prevalence
        ##########################################################################
        if epi=='prev':
            
            printv('Calculating prevalence...', 3, verbose)
        
            # Calculate prevalence
            for t in range(npts):
                D.O.prev.pops[:,t] = D.S.people[1:,:,t].sum(axis=0) / D.S.people[:,:,t].sum(axis=0)
                D.O.prev.tot[t] = D.S.people[1:,:,t].sum() / D.S.people[:,:,t].sum()
            
            # Find prevalence data    
            epidata = asarray(D.data.key.hivprev[0]) # TODO: include uncertainties            
            D.O.prev.ydata = zeros((D.G.npops,ndatayears))
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
            epidata = D.data.opt.numinfect[0]
            D.O.inci.ydata = zeros(ndatayears)
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
            epidata = D.data.opt.death[0]
            D.O.death.ydata = zeros(ndatayears)
            D.O.death.ylabel = 'HIV-related deaths per year'




        ##########################################################################
        ## DALYs
        ##########################################################################
        if epi=='daly':
            
            printv('Calculating DALYs...', 3, verbose)
        
            # Calculate DALYs
            disutils = [D.P.cost.disutil[key] for key in ['acute', 'gt500', 'gt350', 'gt200', 'aids']]
            for t in range(npts):
                for p in range(D.G.npops):
                    for state in [D.G.undx, D.G.dx, D.G.fail]:
                        D.O.daly.pops[p,t] += sum(D.S.people[int_array(state),p,t] * float_array(disutils))
                    for state in [D.G.tx1, D.G.tx2]:
                        D.O.daly.pops[p,t] += sum(D.S.people[int_array(state),p,t] * D.P.cost.disutil.tx)
                
                D.O.daly.tot[t] = D.O.daly.pops[:,t].sum()
            
            # Find DALYs data haha LOL
            epidata = nan+zeros(ndatayears) # No data
            D.O.daly.ydata = zeros(ndatayears)
            D.O.daly.ylabel = 'Disability-adjusted life years per year'



        ##########################################################################
        ## Finish processing data
        ##########################################################################
        if size(epidata[0])==1: # TODO: make this less shitty, easier way of checking what shape the data is I'm sure
            D.O[epi].ydata[:] = float_array(epidata)
        elif size(epidata)==D.G.npops:
            for p in range(D.G.npops):
                thispopdata = epidata[p]
                if len(thispopdata) == 1: 
                    thispopdata = nan+zeros(ndatayears) # If it's an assumption, just set with nans
                elif len(thispopdata) != ndatayears:
                    raise Exception('Expect data length of 1 or %i, actually %i' % (ndatayears, len(thispopdata)))
                D.O[epi].ydata[p,:] = float_array(thispopdata)
        else:
            raise Exception("Can't figure out size of epidata; doesn't seem to be a vector or a matrix")

   
    
    printv('...done running epidemiology results.', 2, verbose)
    return D