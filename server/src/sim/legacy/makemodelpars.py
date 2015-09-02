from liboptima.utils import printv
from numpy import zeros, array, exp, shape
eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero


def makemodelpars(P, opt, withwhat='p', verbose=2):
    """
    Prepares model parameters to run the simulation.
    
    Version: 2015jan27
    """

    printv('Making model parameters...', 1, verbose)
    
    M = dict()
    M['tvec'] = opt['partvec'] # Store time vector with the model parameters
    npts = len(M['tvec']) # Number of time points # TODO probably shouldn't be repeated from model.m
    
    
    
    def dpar2mpar(datapar, withwhat, default_withwhat='p', smoothness=5*int(1/opt['dt'])):
        """
        Take parameters and turn them into model parameters
        Set withwhat = p if you want to use the epi data for the parameters
        Set withwhat = c if you want to use the ccoc data for the parameters
        """
        from numpy import isnan
        from liboptima.utils import smoothinterp

        withwhat = withwhat if withwhat in datapar else default_withwhat #if that is not there, then it has to fail anyway
        
        npops = len(datapar[withwhat])
        
        output = zeros((npops,npts))
        for pop in xrange(npops):
            if withwhat=='c' and ~isnan(datapar[withwhat][pop]).all(): # Use cost relationship
                output[pop, :] = datapar[withwhat][pop, :]
            else: # Use parameter
                if 't' in datapar.keys(): # It's a time parameter
                    output[pop,:] = smoothinterp(M['tvec'], datapar['t'][pop], datapar['p'][pop], smoothness=smoothness) # Use interpolation
                else:
                    output[pop,:] = datapar['p'][pop]
                    print('TMP')
        
        return output
    
    
    def grow(popsizes, growth):
        """ Define a special function for population growth, which is just an exponential growth curve """
        npops = len(popsizes)        
        output = zeros((npops,npts))
        for pop in xrange(npops):
            output[pop,:] = popsizes[pop]*exp(growth*(M['tvec']-M['tvec'][0])) # Special function for population growth
            
        return output
    
    
    
    ## Epidemilogy parameters -- most are data
    M['popsize'] = grow(P['popsize'], opt['growth']) # Population size
    M['hivprev'] = P['hivprev'] # Initial HIV prevalence
    M['stiprevulc'] = dpar2mpar(P['stiprevulc'], withwhat) # STI prevalence
    M['stiprevdis'] = dpar2mpar(P['stiprevdis'], withwhat) # STI prevalence
    M['death']  = dpar2mpar(P['death'], withwhat)  # Death rates
    M['tbprev'] = dpar2mpar(P['tbprev'], withwhat) # TB prevalence
    
    ## Testing parameters -- most are data
    M['hivtest'] = dpar2mpar(P['hivtest'], withwhat) # HIV testing rates
    M['aidstest'] = dpar2mpar(P['aidstest'], withwhat)[0] # AIDS testing rates
    M['tx1'] = dpar2mpar(P['numfirstline'], withwhat, smoothness=int(1/opt['dt']))[0] # Number of people on first-line treatment -- 0 since overall not by population
    M['tx2'] = dpar2mpar(P['numsecondline'], withwhat, smoothness=int(1/opt['dt']))[0] # Number of people on second-line treatment
    M['txelig'] = dpar2mpar(P['txelig'], withwhat, smoothness=int(1/opt['dt']))[0] # Treatment eligibility criterion

    ## MTCT parameters
    M['numpmtct'] = dpar2mpar(P['numpmtct'], withwhat)[0]
    M['birth']    = dpar2mpar(P['birth'], withwhat)
    M['breast']   = dpar2mpar(P['breast'], withwhat)[0]  
    
    ## Sexual behavior parameters -- all are parameters so can loop over all
    M['condom']  = dict()
    M['numactsreg'] = dpar2mpar(P['numactsreg'], withwhat) # ...
    M['numactscas'] = dpar2mpar(P['numactscas'], withwhat) # ...
    M['numactscom'] = dpar2mpar(P['numactscom'], withwhat) # ...
    M['numactsinj'] = dpar2mpar(P['numinject'], withwhat) # ..
    M['condom']['reg']  = dpar2mpar(P['condomreg'], withwhat) # ...
    M['condom']['cas']  = dpar2mpar(P['condomcas'], withwhat) # ...
    M['condom']['com']  = dpar2mpar(P['condomcom'], withwhat) # ...
    
    ## Circumcision parameters
    M['circum']    = dpar2mpar(P['circum'], withwhat) # Circumcision percentage
    M['numcircum'] = dpar2mpar(P['numcircum'], withwhat)[0] # Number to be circumcised -- to be populated by the relevant CCOC at non-zero allocations
#    M['numcircum'] = zeros(shape(M['tvec'])) # Number to be circumcised -- to be populated by the relevant CCOC at non-zero allocations
    
    ## Drug behavior parameters
    M['numost'] = dpar2mpar(P['numost'], withwhat)[0]
    M['sharing'] = dpar2mpar(P['sharing'], withwhat)
    
    ## Other intervention parameters (proportion of the populations, not absolute numbers)
    M['prep'] = dpar2mpar(P['prep'], withwhat)
    
    ## Matrices can be used almost directly
    M['pships'] = dict()
    M['transit'] = dict()
    for key in P['pships'].keys(): M['pships'][key] = array(P['pships'][key])
    for key in P['transit'].keys(): M['transit'][key] = array(P['transit'][key])
    
    ## Constants...can be used directly
    M['const'] = P['const']
    
    ## Calculate total acts
    M['totalacts'] = totalacts(M, npts)
    
    ## Program parameters not related to data
    M['propaware'] = zeros(shape(M['hivtest'])) # Initialize proportion of PLHIV aware of their status
    M['txtotal'] = zeros(shape(M['tx1'])) # Initialize total number of people on treatment
    

    printv('...done making model parameters.', 2, verbose)
    return M

def totalacts(M, npts):
    totalacts = dict()
    
    popsize = M['popsize']
    pships = M['pships']

    numacts = dict()
    numacts['reg'] = M['numactsreg']
    numacts['cas'] = M['numactscas']
    numacts['com'] = M['numactscom']
    numacts['inj'] = M['numactsinj']

    for act in pships.keys():
        npops = len(M['popsize'][:,0])
        npop=len(popsize); # Number of populations
        mixmatrix = pships[act]
        symmetricmatrix=zeros((npop,npop));
        for pop1 in xrange(npop):
            for pop2 in xrange(npop):
                symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))

        a = zeros((npops,npops,npts))
        numact = numacts[act]
        for t in xrange(npts):
            a[:,:,t] = reconcileacts(symmetricmatrix.copy(), popsize[:,t], numact[:,t]) # Note use of copy()

        totalacts[act] = a
    
    return totalacts


def reconcileacts(symmetricmatrix,popsize,popacts):

    # Make sure the dimensions all agree
    npop=len(popsize); # Number of populations
    
    for pop1 in xrange(npop):
        symmetricmatrix[pop1,:]=symmetricmatrix[pop1,:]*popsize[pop1];
    
    # Divide by the sum of the column to normalize the probability, then
    # multiply by the number of acts and population size to get total number of
    # acts
    for pop1 in xrange(npop):
        symmetricmatrix[:,pop1]=popsize[pop1]*popacts[pop1]*symmetricmatrix[:,pop1] / float(eps+sum(symmetricmatrix[:,pop1]))
    
    # Reconcile different estimates of number of acts, which must balance
    pshipacts=zeros((npop,npop));
    for pop1 in xrange(npop):
        for pop2 in xrange(npop):
            balanced = (symmetricmatrix[pop1,pop2] * popsize[pop1] + symmetricmatrix[pop2,pop1] * popsize[pop2])/(popsize[pop1]+popsize[pop2]); # here are two estimates for each interaction; reconcile them here
            pshipacts[pop2,pop1] = balanced/popsize[pop2]; # Divide by population size to get per-person estimate
            pshipacts[pop1,pop2] = balanced/popsize[pop1]; # ...and for the other population

    return pshipacts
        
    
