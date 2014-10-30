"""
MAKEMODELPARS

Calculate all acts and reconcile them between populations.

Version: 2014oct29
"""

def makemodelpars(P, options, verbose=2):
    if verbose>=1: print('Making model parameters...')
    
    from matplotlib.pylab import zeros
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    M = struct()
    M.__doc__ = 'Model parameters to be used directly in the model, calculated from data parameters P.'
    
    tvec = options.tvec # Shorten time vector
    npts = len(tvec) # Number of time points # TODO probably shouldn't be repeated from model.m
    
    
    
    def dpar2mpar(datapar):
        """ Take data parameters and turn them into model parameters """
        npops = len(datapar.p)
        output = zeros((npops,npts))
        for pop in range(npops): output[pop,:] = datapar.p[pop] # TODO: use time!
        return output
    
    ## Epidemilogy parameters -- most are data
    M.popsize = dpar2mpar(P.popsize) # Population size -- TODO: don't take average for this!
    M.hivprev = dpar2mpar(P.hivprev) # Initial HIV prevalence -- TODO: don't take average for this
    M.stiprev = dpar2mpar(P.stiprev) # STI prevalence
    ## TB prevalence @@@
    
    ## Testing parameters -- most are data
    M.hivtest = dpar2mpar(P.hivtest) # HIV testing rates
    M.aidstest = dpar2mpar(P.aidstest) # AIDS testing rates
    
    ## Sexual behavior parameters -- all are parameters so can loop over all
    M.circum = dpar2mpar(P.circum) # Circumcision
    M.numacts = struct()
    M.condom = struct()
    M.numacts.reg = dpar2mpar(P.numactsreg) # ...
    M.numacts.cas = dpar2mpar(P.numactscas) # ...
    M.numacts.com = dpar2mpar(P.numactscom) # ...
    M.numacts.drug = dpar2mpar(P.numinject) # ..
    M.condom.reg = dpar2mpar(P.condomreg) # ...
    M.condom.cas = dpar2mpar(P.condomcas) # ...
    M.condom.com = dpar2mpar(P.condomcom) # ...
    
    ## Drug behavior parameters
    M.ost = dpar2mpar(P.ost)
    M.sharing = dpar2mpar(P.sharing)
    
    ## Matrices can be used directly
    M.pships = P.pships
    M.transit = P.transit
    
    ## Constants...can be used directly -- # TODO should this be copy?
    M.const = P.const
    
    
    ## WARNING need to introduce time!
    def reconcileacts(numacts, popsize, pships):
        from matplotlib.pylab import shape
        npops = shape(numacts)[0]
        popacts = zeros((npops,npts))
        for pop in range(npops):
            popacts[pop] = numacts[pop,:] * popsize[pop,:]
        
        return totalacts
    
    # Calculate number of acts
    totalacts = struct()
    for act in ['reg','cas','com','drug']:
        totalacts[act] = reconcileacts(M.numacts[act], M.popsize, P.pships[act])
    
    
    
    # Reconcile number of acts
    
    # Apply interventions
    
    # Sum matrices

    if verbose>=2: print('  ...done making model parameters.')
    return M
