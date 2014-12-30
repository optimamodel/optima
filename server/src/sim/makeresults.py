def makeresults(D, allsims=None, quantiles=None, verbose=2):
    """
    Generate all outputs required for the model:
        Prevalence
        Incidence
        DALYs
        Deaths
        Number of diagnoses
        Number of people on first-line treatment
        Number of people on second-line treatment
    
    For each, calculate for both overall and per population.

    Version: 2014nov24
    """
    
    from numpy import array, concatenate
    from bunch import Bunch as struct
    from printv import printv
    from quantile import quantile
    printv('Calculating results...', 1, verbose)
    if allsims==None: allsims = [D.S] # If not supplied, using sims structure already in D
    
    R = struct()
    R.__doc__ = 'Output structure containing all worthwhile results from the model'
    R.tvec = allsims[0].tvec # Copy time vector
    nsims = len(allsims) # Number of simulations to average over
    if quantiles==None: quantiles = D.opt.quantiles # If no quantiles are specified, just use the default ones
    allpeople = array([allsims[s].people for s in range(nsims)]) # WARNING, might use stupid amounts of memory
    
    for data in ['prev', 'inci', 'daly', 'death', 'tx1', 'tx2', 'dx', 'costcur', 'costfut']:
        R[data] = struct()
        if data[0:4] != 'cost':
            R[data].pops = []
            R[data].tot = []
        else:
            R[data].ann = []
            R[data].cum = []
        
        
        if data=='prev':
            printv('Calculating prevalence...', 3, verbose)
            R.prev.pops = quantile(allpeople[:,1:,:,:].sum(axis=1) / allpeople[:,:,:,:].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
            R.prev.tot = quantile(allpeople[:,1:,:,:].sum(axis=(1,2)) / allpeople[:,:,:,:].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
            
        
        if data=='inci':
            printv('Calculating incidence...', 3, verbose)
            allinci = array([allsims[s].inci for s in range(nsims)])
            R.inci.pops = quantile(allinci, quantiles=quantiles)
            R.inci.tot = quantile(allinci.sum(axis=1), quantiles=quantiles) # Axis 1 is populations
        
        
        if data=='death':
            printv('Calculating deaths...', 3, verbose)
            alldeaths = array([allsims[s].death for s in range(nsims)])
            R.death.pops = quantile(alldeaths, quantiles=quantiles)
            R.death.tot = quantile(alldeaths.sum(axis=1), quantiles=quantiles) # Axis 1 is populations


        if data=='daly':
            printv('Calculating DALYs...', 3, verbose)
            disutils = [D.P.cost.disutil[key] for key in ['acute', 'gt500', 'gt350', 'gt200', 'aids']]
            tmpdalypops = allpeople[:,concatenate([D.G.tx1, D.G.tx2]),:,:].sum(axis=1) * D.P.cost.disutil.tx
            tmpdalytot = allpeople[:,concatenate([D.G.tx1, D.G.tx2]),:,:].sum(axis=(1,2)) * D.P.cost.disutil.tx
            for h in range(len(disutils)): # Loop over health states
                healthstates = array([D.G.undx[h], D.G.dx[h], D.G.fail[h]])
                tmpdalypops += allpeople[:,healthstates,:,:].sum(axis=1) * disutils[h]
                tmpdalytot += allpeople[:,healthstates,:,:].sum(axis=(1,2)) * disutils[h]
            R.daly.pops = quantile(tmpdalypops, quantiles=quantiles)
            R.daly.tot = quantile(tmpdalytot, quantiles=quantiles)
            
        
        if data=='dx':
            printv('Calculating diagnoses...', 3, verbose)
            alldx = array([allsims[s].dx for s in range(nsims)])
            R.dx.pops = quantile(alldx, quantiles=quantiles)
            R.dx.tot = quantile(alldx.sum(axis=1), quantiles=quantiles) # Axis 1 is populations
            
        
        if data=='tx1':
            printv('Calculating number of people on first-line treatment...', 3, verbose)
            R.tx1.pops = quantile(allpeople[:,D.G.tx1,:,:].sum(axis=1), quantiles=quantiles) # Sum over health states
            R.tx1.tot = quantile(allpeople[:,D.G.tx1,:,:].sum(axis=(1,2)), quantiles=quantiles) # Sum over health states and populations
            
        
        if data=='tx2':
            printv('Calculating number of people on second-line treatment...', 3, verbose)
            R.tx2.pops = quantile(allpeople[:,D.G.tx2,:,:].sum(axis=1), quantiles=quantiles) # Sum over health states
            R.tx2.tot = quantile(allpeople[:,D.G.tx2,:,:].sum(axis=(1,2)), quantiles=quantiles) # Sum over health states and populations
        
        
        if data[0:4]=='cost':
            printv('Calculating costs...', 3, verbose)
            from financialanalysis import financialanalysis
            allcosts = []
            for s in range(nsims):
                thesecosts = financialanalysis(D, postyear = D.data.epiyears[-1], S = allsims[s], yscale = 'abs', makeplot = False)
                allcosts.append(thesecosts)
            
            if data=='costcur':
                R.costcur.ann = quantile(array([allcosts[s]['annualhivcosts']['ylinedata'] for s in range(nsims)]), quantiles=quantiles)
                R.costcur.cum = quantile(array([allcosts[s]['cumulhivcosts']['ylinedata'] for s in range(nsims)]), quantiles=quantiles)
            if data=='costfut':
                R.costfut.ann = quantile(array([allcosts[s]['annualhivcostsfuture']['ylinedata'] for s in range(nsims)]), quantiles=quantiles)
                R.costfut.cum = quantile(array([allcosts[s]['cumulhivcostsfuture']['ylinedata'] for s in range(nsims)]), quantiles=quantiles)
            
            R.costshared = thesecosts # TODO think of how to do this better
            

    printv('...done calculating results.', 2, verbose)
    return R