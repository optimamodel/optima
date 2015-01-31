"""
GATHERPLOTDATA

This file gathers all data that could be used for plotting and packs it into a
nice little convenient structure :)

Version: 2015jan06 by cliffk
"""

# Define labels
epititles = {'prev':'Prevalence', 'plhiv':'PLHIV', 'inci':'New infections', 'daly':'DALYs', 'death':'Deaths', 'dx':'Diagnoses', 'tx1':'First-line treatment', 'tx2':'Second-line treatment'}
epiylabels = {'prev':'HIV prevalence (%)', 'plhiv':'Number of PLHIV', 'inci':'New HIV infections per year', 'daly':'HIV-related DALYs per year', 'death':'AIDS-related deaths per year', 'dx':'New HIV diagnoses per year', 'tx1':'People on 1st-line treatment', 'tx2':'People on 2nd-line treatment'}

def gatheruncerdata(D, R, verbose=2):
    """ Gather standard results into a form suitable for plotting with uncertainties. """
    from numpy import zeros, nan, size, array, asarray
    from bunch import Bunch as struct
    from printv import printv
    printv('Gathering epidemiology results...', 3, verbose)
    
    uncer = struct()
    uncer.__doc__ = 'Output structure containing everything that might need to be plotted'
    uncer.tvec = R.tvec.tolist() # Copy time vector
    uncer.poplabels = D.G.meta.pops.short
    uncer.colorm = (0,0.3,1) # Model color
    uncer.colord = (0,0,0) # Data color
    uncer.legend = ('Model', 'Data')
    uncer.xdata = D.data.epiyears
    ndatayears = len(uncer.xdata)
    
    for key in epititles.keys():
        percent = 100 if key=='prev' else 1 # Whether to multiple results by 100
        
        uncer[key] = struct()
        uncer[key].pops = [struct() for p in range(D.G.npops)]
        uncer[key].tot = struct()
        if key!='prev': # For stacked area plots -- an option for everything except prevalence
            uncer[key].popstacked = struct()
            uncer[key].popstacked.pops = []
            uncer[key].popstacked.legend = []
            uncer[key].popstacked.title = epititles[key]
            uncer[key].popstacked.ylabel = epiylabels[key]
        for p in range(D.G.npops):
            uncer[key].pops[p].best = (R[key].pops[0][p,:]*percent).tolist()
            uncer[key].pops[p].low = (R[key].pops[1][p,:]*percent).tolist()
            uncer[key].pops[p].high = (R[key].pops[2][p,:]*percent).tolist()
            uncer[key].pops[p].title = epititles[key] + ' - ' + D.G.meta.pops.short[p]
            uncer[key].pops[p].ylabel = epiylabels[key]
            if key!='prev':
                uncer[key].popstacked.pops.append(uncer[key].pops[p].best)
                uncer[key].popstacked.legend.append(D.G.meta.pops.short[p])
        uncer[key].tot.best = (R[key].tot[0]*percent).tolist()
        uncer[key].tot.low = (R[key].tot[1]*percent).tolist()
        uncer[key].tot.high = (R[key].tot[2]*percent).tolist()
        uncer[key].tot.title = epititles[key] + ' - Overall'
        uncer[key].tot.ylabel = epiylabels[key]
        uncer[key].xlabel = 'Years'
        
        if key=='prev':
            epidata = D.data.key.hivprev[0] # TODO: include uncertainties
            uncer.prev.ydata = zeros((D.G.npops,ndatayears)).tolist()
        if key=='plhiv':
            epidata = nan+zeros(ndatayears) # No data
            uncer.plhiv.ydata = zeros(ndatayears).tolist()
        if key=='inci':
            epidata = D.data.opt.numinfect[0]
            uncer.inci.ydata = zeros(ndatayears).tolist()
        if key=='death':
            epidata = D.data.opt.death[0]
            uncer.death.ydata = zeros(ndatayears).tolist()
        if key=='daly':
            epidata = nan+zeros(ndatayears) # No data
            uncer.daly.ydata = zeros(ndatayears).tolist()
        if key=='dx':
            epidata = D.data.opt.numdiag[0]
            uncer.dx.ydata = zeros(ndatayears).tolist()
        if key=='tx1':
            epidata = D.data.txrx.numfirstline[0]
            uncer.tx1.ydata = zeros(ndatayears).tolist()
        if key=='tx2':
            epidata = D.data.txrx.numsecondline[0]
            uncer.tx2.ydata = zeros(ndatayears).tolist()


        if size(epidata[0])==1: # TODO: make this less shitty, easier way of checking what shape the data is I'm sure
            uncer[key].ydata = (array(epidata)*percent).tolist()
        elif size(epidata)==D.G.npops:
            for p in range(D.G.npops):
                thispopdata = epidata[p]
                if len(thispopdata) == 1: 
                    thispopdata = nan+zeros(ndatayears) # If it's an assumption, just set with nans
                elif len(thispopdata) != ndatayears:
                    raise Exception('Expect data length of 1 or %i, actually %i' % (ndatayears, len(thispopdata)))
                uncer[key].ydata[p] = (asarray(thispopdata)*percent).tolist() # Stupid, but make sure it's an array, then make sure it's a list
        else:
            raise Exception("Can't figure out size of epidata; doesn't seem to be a vector or a matrix")

    
    # Financial outputs
    for key in ['costann', 'costcum']:
        uncer[key] = struct()
        for ac in ['total','future','existing']:
            uncer[key][ac] = struct()
            origkey = 'annual' if key=='costann' else 'cumulative'
            if key=='costcum':
                uncer[key][ac].best = R[key][ac][0].tolist()
                uncer[key][ac].low = R[key][ac][1].tolist()
                uncer[key][ac].high = R[key][ac][2].tolist()
                uncer[key][ac].xdata = R['costshared'][origkey][ac]['xlinedata'].tolist()
                uncer[key][ac].title = R['costshared'][origkey][ac]['title']
                uncer[key][ac].xlabel = R['costshared'][origkey][ac]['xlabel']
                uncer[key][ac].ylabel = R['costshared'][origkey][ac]['ylabel']
                uncer[key][ac].legend = ['Model']
            else:
                for yscale in ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']:
                    uncer[key][ac][yscale] = struct()
                    if 'ylinedata' in R['costshared'][origkey][ac][yscale]:
                        uncer[key][ac][yscale].best = R[key][ac][yscale][0].tolist()
                        uncer[key][ac][yscale].low = R[key][ac][yscale][1].tolist()
                        uncer[key][ac][yscale].high = R[key][ac][yscale][2].tolist()
                        uncer[key][ac][yscale].xdata = R['costshared'][origkey][ac][yscale]['xlinedata'].tolist()
                        uncer[key][ac][yscale].title = R['costshared'][origkey][ac][yscale]['title']
                        uncer[key][ac][yscale].xlabel = R['costshared'][origkey][ac][yscale]['xlabel']
                        uncer[key][ac][yscale].ylabel = R['costshared'][origkey][ac][yscale]['ylabel']
                        uncer[key][ac][yscale].legend = ['Model']
                        
    
    
    printv('...done gathering uncertainty results.', 4, verbose)
    return uncer




def gathermultidata(D, Rarr, verbose=2):
    """ Gather multi-simulation results (scenarios and optimizations) into a form suitable for plotting. """
    from bunch import Bunch as struct
    from printv import printv
    printv('Gathering multi-simulation results...', 3, verbose)
    
    
    multi = struct()
    multi.__doc__ = 'Output structure containing everything that might need to be plotted'
    multi.nsims = len(Rarr) # Number of simulations
    multi.tvec = Rarr[0].R.tvec.tolist() # Copy time vector
    multi.poplabels = D.G.meta.pops.long
    
    for key in epititles.keys():
        percent = 100 if key=='prev' else 1 # Whether to multiple results by 100
        multi[key] = struct()
        multi[key].pops = [struct() for p in range(D.G.npops)]
        for p in range(D.G.npops):
            multi[key].pops[p].data = []
            multi[key].pops[p].legend = []
            multi[key].pops[p].title = epititles[key] + ' - ' + D.G.meta.pops.short[p]
            multi[key].pops[p].ylabel = epiylabels[key]
            for sim in range(multi.nsims):
                thisdata = (Rarr[sim].R[key].pops[0][p,:]*percent).tolist()
                multi[key].pops[p].data.append(thisdata)
                multi[key].pops[p].legend.append(Rarr[sim].label)
        multi[key].tot = struct()
        multi[key].tot.data = []
        multi[key].tot.legend = []
        multi[key].tot.title = epititles[key] + ' - Overall'
        multi[key].tot.ylabel = epiylabels[key]
        multi[key].xlabel = 'Years'
        for sim in range(multi.nsims):
            thisdata =(Rarr[sim].R[key].tot[0]*percent).tolist()
            multi[key].tot.data.append(thisdata)
            multi[key].tot.legend.append(Rarr[sim].label) # Add legends
    
    # Financial outputs
    for key in ['costann', 'costcum']:
        multi[key] = struct()
        for ac in ['total','future','existing']:
            origkey = 'annual' if key=='costann' else 'cumulative'
            multi[key][ac] = struct()
            if key=='costcum':
                multi[key][ac].data = []
                multi[key][ac].legend = []
                for sim in range(multi.nsims):
                    thisdata = Rarr[sim].R[key][ac][0].tolist()
                    multi[key][ac].data.append(thisdata)
                    multi[key][ac].legend.append(Rarr[sim].label) # Add legends
                    multi[key][ac].xdata  = Rarr[sim].R['costshared'][origkey][ac]['xlinedata'].tolist()
                    multi[key][ac].title  = Rarr[sim].R['costshared'][origkey][ac]['title']
                    multi[key][ac].xlabel = Rarr[sim].R['costshared'][origkey][ac]['xlabel']
                    multi[key][ac].ylabel = Rarr[sim].R['costshared'][origkey][ac]['ylabel']
            else:
                for yscale in ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']:
                    multi[key][ac][yscale] = struct()
                    multi[key][ac][yscale].data = []
                    multi[key][ac][yscale].legend = []
                    if 'ylinedata' in Rarr[sim].R['costshared'][origkey][ac][yscale]:
                        for sim in range(multi.nsims):
                           thisdata = Rarr[sim].R[key][ac][yscale][0].tolist()
                           multi[key][ac][yscale].data.append(thisdata)
                           multi[key][ac][yscale].legend.append(Rarr[sim].label) # Add legends
                           multi[key][ac][yscale].xdata = Rarr[sim].R['costshared'][origkey][ac][yscale]['xlinedata'].tolist()
                           multi[key][ac][yscale].title = Rarr[sim].R['costshared'][origkey][ac][yscale]['title']
                           multi[key][ac][yscale].xlabel = Rarr[sim].R['costshared'][origkey][ac][yscale]['xlabel']
                           multi[key][ac][yscale].ylabel = Rarr[sim].R['costshared'][origkey][ac][yscale]['ylabel']                
        
    printv('...done gathering multi-simulation results.', 4, verbose)
    return multi





def gatheroptimdata(D, result, verbose=2):
    """ Return the data for plotting the optimization results. """
    from bunch import Bunch as struct
    from printv import printv
    from numpy import arange
    printv('Gathering optimization results...', 3, verbose)
    
    optim = struct() # These optimization results
    optim.kind = result.kind # Flag for the kind of optimization
    optim.multi = gathermultidata(D, result.Rarr, verbose=2) # Calculate data for displaying standard epidemiological results
    if optim.kind in ['constant', 'timevarying', 'multiyear']:
        optim.outcome = struct() # Plot how the outcome improved with optimization
        optim.outcome.ydata = result.fval.tolist() # Vector of outcomes
        optim.outcome.xdata = arange(len(result.fval.tolist())).tolist() # Vector of iterations
        optim.outcome.ylabel = 'Outcome'
        optim.outcome.xlabel = 'Iteration'
        optim.outcome.title = 'Outcome (initial: %0.0f, final: %0.0f)' % (result.fval[0], result.fval[-1])
    if optim.kind=='constant':
        optim.alloc = []
        titles = ['Original','Optimal']
        for i in range(2): # Original and optimal
            optim.alloc.append(struct())
            optim.alloc[i].piedata = result.allocarr[i][0].tolist() # A vector of allocations, length nprogs, for pie charts
            optim.alloc[i].radardata = struct() # Structure for storing radar plot data
            optim.alloc[i].radardata.best = result.allocarr[i][0].tolist() # 'Best' estimate: the thick line in the radar plot
            optim.alloc[i].radardata.low  = result.allocarr[i][1].tolist() # 'Low' estimate: the 
            optim.alloc[i].radardata.high = result.allocarr[i][2].tolist()
            optim.alloc[i].title = titles[i] # Titles for pies or radar charts
            optim.alloc[i].legend = D.data.meta.progs.short # Program names, length nprogs, for pie and radar
    if optim.kind=='timevarying' or optim.kind=='multiyear':
        optim.alloc = struct() # Allocation structure
        optim.alloc.stackdata = [] # Empty list
        for p in range(D.G.nprogs): # Loop over programs
            optim.alloc.stackdata.append(result.alloc[p].tolist()) # Allocation array, nprogs x npts, for stacked area plots
        optim.alloc.xdata = result.xdata.tolist() # Years
        optim.alloc.xlabel = 'Year'
        optim.alloc.ylabel = 'Spending'
        optim.alloc.title = 'Optimal allocation'
        optim.alloc.legend = D.data.meta.progs.short # Program names, length nprogs
    if optim.kind=='range':
        optim.alloc = struct() # Allocations structure
        optim.alloc.bardata = []
        for b in range(len(result.allocarr)): # Loop over budgets
            optim.alloc.bardata.append(result.allocarr[b].tolist()) # A vector of allocations, length nprogs
        optim.alloc.xdata = result.budgets.tolist() # Vector of budgets
        optim.alloc.xlabels = result.budgetlabels # Budget labels
        optim.alloc.ylabel = 'Spend'
        optim.alloc.title = 'Budget allocations'
        optim.alloc.legend = D.data.meta.progs.short # Program names, length nprogs
        optim.outcome = struct() # Dictionary with names and values
        optim.outcome.bardata = result.fval # Vector of outcomes, length nbudgets
        optim.outcome.xdata = result.budgets.tolist() # Vector of budgets
        optim.outcome.xlabels = result.budgetlabels # Budget labels
        optim.outcome.ylabel = 'Outcome'
        optim.outcome.title = 'Outcomes'

    printv('...done gathering optimization results.', 4, verbose)
    return optim
