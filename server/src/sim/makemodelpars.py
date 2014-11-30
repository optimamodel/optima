from printv import printv
from numpy import zeros, array, exp
from bunch import Bunch as struct # Replicate Matlab-like structure behavior
eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero


def makemodelpars(P, opt, withwhat='p', verbose=2):
    """
    Prepares model parameters to run the simulation.
    
    Version: 2014nov05
    """
    
    printv('Making model parameters...', 1, verbose)
    
    M = struct()
    M.__doc__ = 'Model parameters to be used directly in the model, calculated from data parameters P.'
    tvec = opt.tvec # Shorten time vector
    npts = len(tvec) # Number of time points # TODO probably shouldn't be repeated from model.m
    
    
    
    def dpar2mpar(datapar, withwhat):
        """
        Take parameters and turn them into model parameters
        Set withwhat = p if you want to use the epi data for the parameters
        Set withwhat = c if you want to use the ccoc data for the parameters
        """
        from numpy import interp, isnan
        
        npops = len(datapar[withwhat])
        
        if npops>1:
            output = zeros((npops,npts))
            for pop in range(npops):
                if withwhat=='c' and ~isnan(datapar['c'][pop]): # Use cost relationship
                    output[pop,:] = datapar['c'][pop] # TODO: use time!
                else: # Use parameter
                    if 't' in datapar.keys(): # It's a time parameter
                        output[pop,:] = interp(tvec, datapar.t[pop], datapar.p[pop]) # Use interpolation
                    else:
                        output[pop,:] = datapar.p[pop]
                
        else:
            output = zeros(npts)
            try:
                if withwhat=='c' and ~isnan(datapar['c'][0]): # Use cost relationship
                    output[:] = datapar['c'][0] # TODO: use time!
                else: # Use parameter
                    if 't' in datapar.keys(): # It's a time parameter
                        output[:] = interp(tvec, datapar.t[0], datapar.p[0]) # Use interpolation
                    else:
                        output[:] = datapar.p[0]
            except:
                import traceback; traceback.print_exc(); import pdb; pdb.set_trace()

        
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
    M.stiprevulc = dpar2mpar(P.stiprevulc, withwhat) # STI prevalence
    M.stiprevdis = dpar2mpar(P.stiprevdis, withwhat) # STI prevalence
    M.death = dpar2mpar(P.death, withwhat) # Death rates
    ## TB prevalence @@@
    
    ## Testing parameters -- most are data
    M.hivtest = dpar2mpar(P.testrate, withwhat) # HIV testing rates
    M.aidstest = dpar2mpar(P.aidstestrate, withwhat) # AIDS testing rates
    M.tx1 = dpar2mpar(P.numfirstline, withwhat) # Number of people on first-line treatment
    M.tx2 = dpar2mpar(P.numsecondline, withwhat) # Number of people on second-line treatment
    
    ## Sexual behavior parameters -- all are parameters so can loop over all
    M.circum  = dpar2mpar(P.circum, withwhat) # Circumcision
    M.numacts = struct()
    M.condom  = struct()
    M.numacts.reg = dpar2mpar(P.numactsreg, withwhat) # ...
    M.numacts.cas = dpar2mpar(P.numactscas, withwhat) # ...
    M.numacts.com = dpar2mpar(P.numactscom, withwhat) # ...
    M.numacts.inj = dpar2mpar(P.numinject, withwhat) # ..
    M.condom.reg  = dpar2mpar(P.condomreg, withwhat) # ...
    M.condom.cas  = dpar2mpar(P.condomcas, withwhat) # ...
    M.condom.com  = dpar2mpar(P.condomcom, withwhat) # ...
    
    ## Drug behavior parameters
    M.numost = dpar2mpar(P.numost, withwhat)
    M.sharing = dpar2mpar(P.sharing, withwhat)
    
    ## Matrices can be used almost directly
    M.pships = struct()
    M.transit = struct()
    for key in P.pships.keys(): M.pships[key] = array(P.pships[key])
    for key in P.transit.keys(): M.transit[key] = array(P.transit[key])
    
    ## Constants...can be used directly
    M.const = P.const
    
    ## Calculate total acts
    M.totalacts = totalacts(P, M, npts)
    
    # Apply interventions?
    
    # Sum matrices?

    printv('...done making model parameters.', 2, verbose)
    return M

def totalacts(P, M, npts):
    totalacts = struct()
    totalacts.__doc__ = 'Balanced numbers of acts'
    
    popsize = M.popsize
    pships = P.pships

    for act in pships.keys():
        npops = len(M.popsize[:,0])
        npop=len(popsize); # Number of populations
        mixmatrix = array(pships[act])
        symmetricmatrix=zeros((npop,npop));
        for pop1 in range(npop):
            for pop2 in range(npop):
                symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))

        a = zeros((npops,npops,npts))
        numacts = M['numacts'][act]
        for t in range(npts):
            a[:,:,t] = reconcileacts(symmetricmatrix.copy(), popsize[:,t], numacts[:,t]) # Note use of copy()

        totalacts[act] = a
    
    return totalacts


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