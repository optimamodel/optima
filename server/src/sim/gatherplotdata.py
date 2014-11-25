epititles = {'prev':'Prevalence', 'inci':'New infections', 'daly':'DALYs', 'death':'Deaths', 'dx':'Diagnoses', 'tx1':'First-line treatment', 'tx2':'Second-line treatment'}
epiylabels = {'prev':'Prevalence (%)', 'inci':'New HIV infections per year', 'daly':'DALYs per year', 'death':'HIV-related deaths per year', 'dx':'HIV diagnoses per year', 'tx1':'People on 1st-line treatment', 'tx2':'People on 2nd-line treatment'}

def gatherepidata(D, R, verbose=2):
    """ Gather standard epidemiology results into a form suitable for plotting. """
    from matplotlib.pylab import zeros, nan, size, array
    from bunch import Bunch as struct, float_array
    from printv import printv
    printv('Gathering epidemiology results...', 3, verbose)
    
    E = struct()
    E.__doc__ = 'Output structure containing everything that might need to be plotted'
    E.tvec = R.tvec # Copy time vector
    E.poplabels = D.G.meta.pops.short
    E.colorm = (0,0.3,1) # Model color
    E.colord = (0,0,0) # Data color
    E.legend = ('Model', 'Data')
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
            E[epi].pops[p].title = epititles[epi] + ' - ' + D.G.meta.pops.short[p]
            E[epi].pops[p].ylabel = epiylabels[epi]
        E[epi].tot.best = R[epi].tot[0]
        E[epi].tot.low = R[epi].tot[1]
        E[epi].tot.high = R[epi].tot[2]
        E[epi].tot.title = epititles[epi] + ' - Overall'
        E[epi].tot.ylabel = epiylabels[epi]
        E[epi].xlabel = 'Years'
        
        if epi=='prev':
            epidata = array(D.data.key.hivprev[0]) # TODO: include uncertainties
            E.prev.ydata = zeros((D.G.npops,ndatayears))
        if epi=='inci':
            epidata = D.data.opt.numinfect[0]
            E.inci.ydata = zeros(ndatayears)
        if epi=='death':
            epidata = D.data.opt.death[0]
            E.death.ydata = zeros(ndatayears)
        if epi=='daly':
            epidata = nan+zeros(ndatayears) # No data
            E.daly.ydata = zeros(ndatayears)
        if epi=='dx':
            epidata = D.data.opt.numdiag[0]
            E.dx.ydata = zeros(ndatayears)
        if epi=='tx1':
            epidata = D.data.txrx.numfirstline[0]
            E.tx1.ydata = zeros(ndatayears)
        if epi=='tx2':
            epidata = D.data.txrx.numsecondline[0]
            E.tx2.ydata = zeros(ndatayears)


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

    printv('...done gathering epidemiology results.', 4, verbose)
    return E




def gathermultidata(D, Rarr, verbose=2):
    """ Gather multi-simulation results (scenarios and optimizations) into a form suitable for plotting. """
    from bunch import Bunch as struct
    from printv import printv
    printv('Gathering multi-simulation results...', 3, verbose)
    
    
    M = struct()
    M.__doc__ = 'Output structure containing everything that might need to be plotted'
    M.nsims = len(Rarr) # Number of simulations
    M.tvec = Rarr[0].R.tvec # Copy time vector
    M.poplabels = D.G.meta.pops.long
    
    for epi in ['prev', 'inci', 'daly', 'death', 'dx', 'tx1', 'tx2']:
        M[epi] = struct()
        M[epi].pops = []
        for p in range(D.G.npops):
            M[epi].pops.append(struct())
            M[epi].pops[p].data = []
            M[epi].pops[p].legend = []
            M[epi].pops[p].title = epititles[epi] + ' - ' + D.G.meta.pops.short[p]
            M[epi].pops[p].ylabel = epiylabels[epi]
            for sim in range(M.nsims):
                M[epi].pops[p].data.append(Rarr[sim].R[epi].pops[0][p,:])
                M[epi].pops[p].legend.append(Rarr[sim].label)
        M[epi].tot = struct()
        M[epi].tot.data = []
        M[epi].tot.legend = []
        M[epi].tot.title = epititles[epi] + ' - Overall'
        M[epi].tot.ylabel = epiylabels[epi]
        for sim in range(M.nsims):
            M[epi].tot.data.append(Rarr[sim].R[epi].tot[0])
            M[epi].tot.legend.append(Rarr[sim].label) # Add legends
        M[epi].xlabel = 'Years'
        
    printv('...done gathering multi-simulation results.', 4, verbose)
    return M


def gatheroptimdata(D, A, verbose=2):
    """ Return the data for plotting the two pie charts -- current allocation and optimal. """
    from bunch import Bunch as struct
    from printv import printv
    printv('Gathering optimization results...', 3, verbose)
    
    O = struct()
    O.legend = D.G.meta.progs.short
    
    O.pie1 = struct()
    O.pie1.name = 'Original'
    O.pie1.val = A[0].alloc
    
    O.pie2 = struct()
    O.pie2.name = 'Optimal'
    O.pie2.val = A[1].alloc
    
    printv('...done gathering optimization results.', 4, verbose)
    return O