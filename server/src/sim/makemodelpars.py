from printv import printv
from numpy import zeros, array, exp
from bunch import Bunch as struct # Replicate Matlab-like structure behavior
## WARNING need to introduce time!

eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero

def reconcileacts(symmetricmatrix,popsize,popacts):

    # Make sure the dimensions all agree
    npop=len(popsize); # Number of populations
    
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

def makemodelpars(P, opt, verbose=2):
    """
    Prepares model parameters to run the simulation.
    
    Version: 2014nov05
    """
    
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
    
    
    def grow(popsizes, growth):
        """ Define a special function for population growth, which is just an exponential growth curve """
        npops = len(popsizes)        
        output = zeros((npops,npts))
        for pop in range(npops):
            output[pop,:] = popsizes[pop]*exp(growth*(tvec-tvec[0])) # Special function for population growth
            
        return output
    
    
    
    ## Epidemilogy parameters -- most are data
    M.popsize = grow(P.popsize, opt.growth) # Population size
    M.hivprev = P.hivprev # Initial HIV prevalence
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
    
    M.totalacts = struct()
    M.totalacts.__doc__ = 'Balanced numbers of acts'

    popsize = M.popsize

    for act in P.pships.keys():

        npops = len(M.popsize[:,0])

        npop=len(popsize); # Number of populations
    
        # Moved here from reconcileacts()
        # WARNING, NOT SURE ABOUT THIS
        # Make matrix symmetric
        mixmatrix = array(P.pships[act])
        symmetricmatrix=zeros((npop,npop));
        for pop1 in range(npop):
            for pop2 in range(npop):
                symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))

        a = zeros((npops,npops,npts))
        numacts = M.numacts[act]
        for t in range(npts):
            a[:,:,t] = reconcileacts(symmetricmatrix.copy(), popsize[:,t], numacts[:,t]) # Note use of copy()

        M.totalacts[act] = a
    
    # Apply interventions?
    
    # Sum matrices?

    printv('...done making model parameters.', 2, verbose)
    return M
