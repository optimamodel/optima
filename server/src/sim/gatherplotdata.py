def gatherepidata(D, R, verbose=2):
    """ Gather standard epidemiology results into a form suitable for plotting. """
    
    from matplotlib.pylab import zeros, nan, size, array
    from bunch import Bunch as struct, float_array
    from printv import printv
    printv('Calculating epidemiology results...', 1, verbose)
    
    E = struct()
    E.__doc__ = 'Output structure containing everything that might need to be plotted'
    E.tvec = R.tvec # Copy time vector
    E.poplabels = D.G.meta.pops.long
    E.colorm = (0,0.3,1) # Model color
    E.colord = (0,0,0) # Data color
    E.xdata = D.data.epiyears
    ndatayears = len(E.xdata)
    
    for epi in ['prev', 'inci', 'daly', 'death', 'dx', 'tx1', 'tx2']:
        E[epi] = struct()
        E[epi].pops = []
        E[epi].tot = struct()
        for p in range(D.G.npops):
            E[epi].pops.append(struct())
            E[epi].pops[p].best = R[epi].pops[0][p,:]
            E[epi].pops[p].low = R[epi].pops[1][p,:]
            E[epi].pops[p].high = R[epi].pops[2][p,:]
        E[epi].tot.best = R[epi].tot[0]
        E[epi].tot.low = R[epi].tot[1]
        E[epi].tot.high = R[epi].tot[2]
        E[epi].xlabel = 'Years'
        
        if epi=='prev':
            printv('Gathering prevalence...', 3, verbose)
            epidata = array(D.data.key.hivprev[0]) # TODO: include uncertainties
            E.prev.ydata = zeros((D.G.npops,ndatayears))
            E.prev.ylabel = 'Prevalence (%)'

        if epi=='inci':
            printv('Calculating incidence...', 3, verbose)
            epidata = D.data.opt.numinfect[0]
            E.inci.ydata = zeros(ndatayears)
            E.inci.ylabel = 'New HIV infections per year'

        if epi=='death':
            printv('Calculating deaths...', 3, verbose)
            epidata = D.data.opt.death[0]
            E.death.ydata = zeros(ndatayears)
            E.death.ylabel = 'HIV-related deaths per year'

        if epi=='daly':
            printv('Calculating DALYs...', 3, verbose)
            epidata = nan+zeros(ndatayears) # No data
            E.daly.ydata = zeros(ndatayears)
            E.daly.ylabel = 'Disability-adjusted life years per year'
            
        if epi=='dx':
            printv('Calculating diagnoses...', 3, verbose)
            epidata = D.data.opt.numdiag[0]
            E.dx.ydata = zeros(ndatayears)
            E.dx.ylabel = 'New HIV diagnoses per year'
        
        if epi=='tx1':
            printv('Calculating first-line treatment...', 3, verbose)
            epidata = D.data.txrx.numfirstline[0]
            E.tx1.ydata = zeros(ndatayears)
            E.tx1.ylabel = 'Number of people on first-line treatment'
        
        if epi=='tx2':
            printv('Calculating second-line treatment...', 3, verbose)
            epidata = D.data.txrx.numsecondline[0]
            E.tx2.ydata = zeros(ndatayears)
            E.tx2.ylabel = 'Number of people on second-line treatment'


        if size(epidata[0])==1: # TODO: make this less shitty, easier way of checking what shape the data is I'm sure
            E[epi].ydata[:] = float_array(epidata)
        elif size(epidata)==D.G.npops:
            for p in range(D.G.npops):
                thispopdata = epidata[p]
                if len(thispopdata) == 1: 
                    thispopdata = nan+zeros(ndatayears) # If it's an assumption, just set with nans
                elif len(thispopdata) != ndatayears:
                    raise Exception('Expect data length of 1 or %i, actually %i' % (ndatayears, len(thispopdata)))
                E[epi].ydata[p,:] = float_array(thispopdata)
        else:
            raise Exception("Can't figure out size of epidata; doesn't seem to be a vector or a matrix")

    printv('...done running epidemiology results.', 2, verbose)
    return E




def gathermultidata(D, R, verbose=2):
    """ Gather multi-simulation results (scenarios and optimizations) into a form suitable for plotting. """
    
    from bunch import Bunch as struct
    from printv import printv
    printv('Calculating multi-simulation results...', 1, verbose)
    
    M = struct()
    M.__doc__ = 'Output structure containing everything that might need to be plotted'
    M.tvec = R.tvec # Copy time vector
    M.poplabels = D.G.meta.pops.long
    M.colorm = (0,0.3,1) # Model color
    M.colord = (0,0,0) # Data color
    
    for epi in ['prev', 'inci', 'daly', 'death', 'dx', 'tx1', 'tx2']:
        M[epi] = struct()
        M[epi].pops = []
        M[epi].tot = struct()
        for p in range(D.G.npops):
            M[epi].pops.append(struct())
            M[epi].pops[p].best = R[epi].pops[0][p,:]
            M[epi].pops[p].low = R[epi].pops[1][p,:]
            M[epi].pops[p].high = R[epi].pops[2][p,:]
        M[epi].tot.best = R[epi].tot[0]
        M[epi].tot.low = R[epi].tot[1]
        M[epi].tot.high = R[epi].tot[2]
        M[epi].xlabel = 'Years'
        
    printv('...done running multi-simulation results.', 2, verbose)
    return M


def gatheroptimdata(D, A):
    """ Return the data for plotting the two pie charts -- current allocation and optimal. """
    from bunch import Bunch as struct
    
    O = struct()
    O.legend = D.data.meta.progs.short
    
    O.pie1 = struct()
    O.pie1.name = 'Original'
    O.pie1.val = A.orig.cost
    
    O.pie2 = struct()
    O.pie2.name = 'Optimal'
    O.pie2.val = A.optimal.cost
    
    return O