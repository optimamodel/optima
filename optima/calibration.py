"""
CALIBRATION

Functions to perform calibration.
"""

from optima import dcp, perturb, Parameterset
from numpy import median



def sensitivity(orig=None, ncopies=5, what='force', span=0.5, ind=0):
    ''' 
    Function to perturb the parameters to get "uncertainties".
    
    Inputs:
        orig = parset to perturb
        ncopies = number of perturbed copies of pars to produce
        what = which parameters to perturb
        span = how much to perturb
        ind = index of pars to start from
    Outputs:
        parset = perturbed parameter set with ncopies sets of pars
    
    Version: 2015dec29 by cliffk
    '''
    
    # Validate input
    if span>1 or span<0:
        print('WARNING: span argument must be a scalar in the interval [0,1], resetting...')
        span = median([0,1,span])
    if type(orig)!=Parameterset:
        raise Exception('First argument to sensitivity() must be a parameter set')
    
    # Copy things
    parset = dcp(orig) # Copy the original parameter set
    origpars = dcp(parset.pars[ind])
    parset.pars = []
    for n in range(ncopies):
        parset.pars.append(dcp(origpars))
    popkeys = origpars['popkeys']
    
    if what=='force':
        for n in range(ncopies):
            for key in popkeys:
                parset.pars[n]['force'].y[key] = perturb(n=1, span=span)[0] # perturb() returns array, so need to index -- WARNING, could make more efficient and remove loop
    else:
        raise Exception('Sorry, only "force" is implemented currently')
    
    return parset
























def autofit(project=None, orig=None, what='force', maxtime=None, niters=100, inds=None):
    ''' 
    Function to automatically fit parameters
    
    Inputs:
        orig = parset to perturb
        ncopies = number of perturbed copies of pars to produce
        what = which parameters to perturb
        span = how much to perturb
        ind = index of pars to start from
    Outputs:
        parset = perturbed parameter set with ncopies sets of pars
    
    Version: 2016jan04 by cliffk
    '''
    
    # Validate input
    if inds is None: inds = [0]
    elif type(inds)==int or type(inds)==float: inds = [inds] # # Turn into a list if necessary
    
    # Copy things
    parset = dcp(orig) # Copy the original parameter set
    for ind in inds:
        try: origpars = dcp(parset.pars[ind])
        except:
            errormsg = 'Could not load 
            raise Exception(errormsg)
        parset.pars = []
        for n in range(ncopies):
            parset.pars.append(dcp(origpars))
        popkeys = origpars['popkeys']
        
        if what=='force':
            for n in range(ncopies):
                for key in popkeys:
                    parset.pars[n]['force'].y[key] = perturb(n=1, span=span)[0] # perturb() returns array, so need to index -- WARNING, could make more efficient and remove loop
        else:
            raise Exception('Sorry, only "force" is implemented currently')
    
    return parset