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
            symmetricmatrix[:,pop1]=popsize[pop1]*popacts[pop1]*symmetricmatrix[:,pop1]/sum(symmetricmatrix[:,pop1]);
        
        # Reconcile different estimates of number of acts, which must balance
        pshipacts=zeros((npop,npop));
        for pop1 in range(npop):
            for pop2 in range(npop):
                balanced = (symmetricmatrix[pop1,pop2] * popsize[pop1] + symmetricmatrix[pop2,pop1] * popsize[pop2])/(popsize[pop1]+popsize[pop2]); # here are two estimates for each interaction; reconcile them here
                pshipacts[pop2,pop1] = balanced/popsize[pop2]; # Divide by population size to get per-person estimate
                pshipacts[pop1,pop2] = balanced/popsize[pop1]; # ...and for the other population

        return pshipacts
        
    
    # Calculate number of acts
    totalacts = struct()
    for act in ['reg','cas','com','drug']:
        npops = len(M.popsize[:,0])
        totalacts[act] = zeros((npops,npops,npts))
        for t in range(npts):
            totalacts[act][:,:,t] = reconcileacts(P.pships[act], M.popsize[:,t], M.numacts[act][:,t])
        
    
    
    
    # Reconcile number of acts
    
    # Apply interventions
    
    # Sum matrices

    if verbose>=2: print('  ...done making model parameters.')
    return M
