def makeresults(D, quantiles=None, verbose=2):
    """
    Generate all outputs required for the model:
        Prevalence
        Incidence
        DALYs
        Deaths
        Number of people on treatment
        Number of diagnoses
    
    For each, calculate for both overall and per population.

    Version: 2014nov23
    """
    
    
    ##########################################################################
    ## Preliminaries
    ##########################################################################
    
    from matplotlib.pylab import zeros, array
    from bunch import Bunch as struct, int_array, float_array
    from printv import printv
    from quantile import quantile
    printv('Calculating results...', 1, verbose)
    
    D.R = struct()
    D.R.__doc__ = 'Output structure containing everything that might need to be plotted'
    D.R.tvec = D.S.tvec # Copy time vector
    npts = len(D.R.tvec)
    if quantiles==None: quantiles=D.opt.quantiles # If not supplied as an argument, use pre-saved quantiles
    nquantiles = len(quantiles)
    
    for epi in ['prev', 'inci', 'daly', 'death', 'tx1', 'tx2', 'dx']:
        D.R[epi] = struct()
        D.R[epi].pops = []
        D.R[epi].tot = []
        for q in range(nquantiles): # Create an array for storing data for each quantile
            D.R[epi].pops.append(zeros((D.G.npops, npts))) # Careful, can't use pop since it's a method!
            D.R[epi].tot.append(zeros(npts))
        
        
        ##########################################################################
        ## Prevalence
        ##########################################################################
        if epi=='prev':
            
            printv('Calculating prevalence...', 3, verbose)
            
            allpeople = array([D.S[s].people for s in range(D.S.opt.nsims)]) # WARNING, might use stupid amounts of memory
            tmpprevpops = allpeople[:,1:,:,:].sum(axis=1) / allpeople[:,:,:,:].sum(axis=1)
            D.R.prev.pops = quantile(tmpprevpops, quantiles=quantiles)
        
            # Calculate prevalence
            for t in range(npts):
                D.R.prev.pops[:,t] = D.S.people[1:,:,t].sum(axis=0) / D.S.people[:,:,t].sum(axis=0)
                D.R.prev.tot[t] = D.S.people[1:,:,t].sum() / D.S.people[:,:,t].sum()
            


        ##########################################################################
        ## Incidence
        ##########################################################################
        if epi=='inci':
            
            printv('Calculating incidence...', 3, verbose)
        
            # Calculate incidence
            for t in range(npts):
                D.R.inci.pops[:,t] = D.S.inci[:,t] # Simple
                D.R.inci.tot[t] = D.S.inci[:,t].sum()
            


        ##########################################################################
        ## Deaths
        ##########################################################################
        if epi=='death':
            
            printv('Calculating deaths...', 3, verbose)
        
            # Calculate incidence
            for t in range(npts):
                D.R.death.pops[:,t] = D.S.death[:,t] # Simple
                D.R.death.tot[t] = D.S.death[:,t].sum()
            



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
                        D.R.daly.pops[p,t] += sum(D.S.people[int_array(state),p,t] * float_array(disutils))
                    for state in [D.G.tx1, D.G.tx2]:
                        D.R.daly.pops[p,t] += sum(D.S.people[int_array(state),p,t] * D.P.cost.disutil.tx)
                
                D.R.daly.tot[t] = D.R.daly.pops[:,t].sum()
            


   
    
    printv('...done calculating results.', 2, verbose)
    return D