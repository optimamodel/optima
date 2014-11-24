def gatherplotdata(D, verbose=2):
    """
    Generate all outputs required for the model:
        Prevalence
        Incidence
        DALYs
        Deaths
    
    For each, calculate for both overall and per population.

    Version: 2014nov24
    """
    
    
    ##########################################################################
    ## Preliminaries
    ##########################################################################
    
    from matplotlib.pylab import zeros, nan, size, asarray
    from bunch import Bunch as struct, float_array
    from printv import printv
    printv('Calculating epidemiology results...', 1, verbose)
    
    D.O = struct()
    D.O.__doc__ = 'Output structure containing everything that might need to be plotted'
    D.O.tvec = D.R.tvec # Copy time vector
    D.O.poplabels = D.G.meta.pops.long
    D.O.colorm = (0,0.3,1) # Model color
    D.O.colord = (0,0,0) # Data color
    D.O.xdata = D.data.epiyears
    ndatayears = len(D.O.xdata)
    
    for epi in ['prev', 'inci', 'daly', 'death', 'dx', 'tx1', 'tx2']:
        D.O[epi] = struct()
        D.O[epi].pops = []
        D.O[epi].tot = struct()
        for p in range(D.G.npops):
            D.O[epi].pops.append(struct())
            D.O[epi].pops[p].best = D.R[epi].pops[0][p,:]
            D.O[epi].pops[p].low = D.R[epi].pops[1][p,:]
            D.O[epi].pops[p].high = D.R[epi].pops[2][p,:]
        D.O[epi].tot.best = D.R[epi].tot[0]
        D.O[epi].tot.low = D.R[epi].tot[1]
        D.O[epi].tot.high = D.R[epi].tot[2]
        D.O[epi].xlabel = 'Years'
        
        if epi=='prev':
            printv('Gathering prevalence...', 3, verbose)
            epidata = asarray(D.data.key.hivprev[0]) # TODO: include uncertainties
            D.O.prev.ydata = zeros((D.G.npops,ndatayears))
            D.O.prev.ylabel = 'Prevalence (%)'

        if epi=='inci':
            printv('Calculating incidence...', 3, verbose)
            epidata = D.data.opt.numinfect[0]
            D.O.inci.ydata = zeros(ndatayears)
            D.O.inci.ylabel = 'New HIV infections per year'

        if epi=='death':
            printv('Calculating deaths...', 3, verbose)
            epidata = D.data.opt.death[0]
            D.O.death.ydata = zeros(ndatayears)
            D.O.death.ylabel = 'HIV-related deaths per year'

        if epi=='daly':
            printv('Calculating DALYs...', 3, verbose)
            epidata = nan+zeros(ndatayears) # No data
            D.O.daly.ydata = zeros(ndatayears)
            D.O.daly.ylabel = 'Disability-adjusted life years per year'
            
        if epi=='dx':
            printv('Calculating diagnoses...', 3, verbose)
            epidata = D.data.opt.numdiag[0]
            D.O.dx.ydata = zeros(ndatayears)
            D.O.dx.ylabel = 'New HIV diagnoses per year'
        
        if epi=='tx1':
            printv('Calculating first-line treatment...', 3, verbose)
            epidata = D.data.txrx.numfirstline[0]
            D.O.tx1.ydata = zeros(ndatayears)
            D.O.tx1.ylabel = 'Number of people on first-line treatment'
        
        if epi=='tx2':
            printv('Calculating second-line treatment...', 3, verbose)
            epidata = D.data.txrx.numsecondline[0]
            D.O.tx2.ydata = zeros(ndatayears)
            D.O.tx2.ylabel = 'Number of people on second-line treatment'

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