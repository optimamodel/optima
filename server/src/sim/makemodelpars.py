def makemodelpars(P, opt, verbose=2):
    """
    Prepares model parameters to run the simulation.
    
    Version: 2014nov05
    """
    
    from printv import printv
    from matplotlib.pylab import zeros, array #, ones
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    printv('Making model parameters...', 1, verbose)
    
    M = struct()
    M.__doc__ = 'Model parameters to be used directly in the model, calculated from data parameters P.'
    tvec = opt.tvec # Shorten time vector
    npts = len(tvec) # Number of time points # TODO probably shouldn't be repeated from model.m
    
    def dpar2mpar(datapar):
        """ Take data parameters and turn them into model parameters """
        npops = len(datapar.p)
        
        if npops>1:
            output = zeros((npops,npts))
            for pop in range(npops):
                output[pop,:] = datapar.p[pop] # TODO: use time!
        else:
            output = zeros(npts)
            output[:] = datapar.p[0] # TODO: use time!
        
        return output
    
    ## Epidemilogy parameters -- most are data
    M.popsize = dpar2mpar(P.popsize) # Population size -- TODO: don't take average for this!
    M.hivprev = dpar2mpar(P.hivprev)[:,0] # Initial HIV prevalence -- only take initial point
    M.stiprevulc = dpar2mpar(P.stiprevulc) # STI prevalence
    M.stiprevdis = dpar2mpar(P.stiprevdis) # STI prevalence
    M.death = dpar2mpar(P.death) # Death rates
    ## TB prevalence @@@
    
    ## Testing parameters -- most are data
    M.hivtest = dpar2mpar(P.testrate) # HIV testing rates
    M.aidstest = dpar2mpar(P.aidstestrate) # AIDS testing rates
    blank = struct()
    blank.p = [0] # WARNING # TODO KLUDGY
    M.tx1 = dpar2mpar(blank)
    M.tx2 = dpar2mpar(blank)
    
    ## Sexual behavior parameters -- all are parameters so can loop over all
    M.circum  = dpar2mpar(P.circum) # Circumcision
    M.numacts = struct()
    M.condom  = struct()
    M.numacts.reg = dpar2mpar(P.numactsreg) # ...
    M.numacts.cas = dpar2mpar(P.numactscas) # ...
    M.numacts.com = dpar2mpar(P.numactscom) # ...
    M.numacts.inj = dpar2mpar(P.numinject) # ..
    M.condom.reg  = dpar2mpar(P.condomreg) # ...
    M.condom.cas  = dpar2mpar(P.condomcas) # ...
    M.condom.com  = dpar2mpar(P.condomcom) # ...
    
    ## Drug behavior parameters
    M.numost = dpar2mpar(P.numost)
    M.sharing = dpar2mpar(P.sharing)
    
    ## Matrices can be used almost directly
    M.pships = struct()
    M.transit = struct()
    for key in P.pships.keys(): M.pships[key] = array(P.pships[key])
    for key in P.transit.keys(): M.transit[key] = array(P.transit[key])
    
    ## Constants...can be used directly -- # TODO should this be copy?
    M.const = P.const
    
    ## WARNING need to introduce time!
    def reconcileacts(mixmatrix,popsize,popacts):
        from matplotlib.pylab import array
        eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero

        # Make sure the dimensions all agree
        npop=len(popsize); # Number of populations
        
        # WARNING, NOT SURE ABOUT THIS
        # Make matrix symmetric
        mixmatrix = array(mixmatrix)
        symmetricmatrix=zeros((npop,npop));
        for pop1 in range(npop):
            for pop2 in range(npop):
                symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))

        # The probability of interaction is dependent on the population size...not
        # sure exactly why this works, but, um, it does :)
        for pop1 in range(npop):
            symmetricmatrix[pop1,:]=symmetricmatrix[pop1,:]*popsize[pop1];
        
        # Divide by the sum of the column to normalize the probability, then
        # multiply by the number of acts and population size to get total number of
        # acts
        for pop1 in range(npop):
            symmetricmatrix[:,pop1]=popsize[pop1]*popacts[pop1]*symmetricmatrix[:,pop1] / float(eps+sum(symmetricmatrix[:,pop1]))
        
        # Reconcile different estimates of number of acts, which must balance
        pshipacts=zeros((npop,npop));
        for pop1 in range(npop):
            for pop2 in range(npop):
                balanced = (symmetricmatrix[pop1,pop2] * popsize[pop1] + symmetricmatrix[pop2,pop1] * popsize[pop2])/(popsize[pop1]+popsize[pop2]); # here are two estimates for each interaction; reconcile them here
                pshipacts[pop2,pop1] = balanced/popsize[pop2]; # Divide by population size to get per-person estimate
                pshipacts[pop1,pop2] = balanced/popsize[pop1]; # ...and for the other population

        return pshipacts
        
    # Calculate number of acts
    M.totalacts = struct()
    M.totalacts.__doc__ = 'Balanced numbers of acts'
    for act in P.pships.keys():
        npops = len(M.popsize[:,0])
        M.totalacts[act] = zeros((npops,npops,npts))
        for t in range(npts):
            M.totalacts[act][:,:,t] = reconcileacts(P.pships[act], M.popsize[:,t], M.numacts[act][:,t])
        
    # Apply interventions?
    
    # Sum matrices?
    
    
    
    

    printv('...done making model parameters.', 2, verbose)
    
    return M
    
