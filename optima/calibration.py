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
























def autofit(project=None, name=None, what=None, maxtime=None, niters=100, inds=0):
    ''' 
    Function to automatically fit parameters
    
    Version: 2016jan04 by cliffk
    '''
    
    # Initialization
    parset = dcp(project.parsets[name]) # Copy the original parameter set
    npars = len(parset.pars)
    if what is None: what = ['force'] # By default, automatically fit force-of-infection only
    if type(inds)==int or type(inds)==float: inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(npars)
    if max(inds)>npars: raise Exception('Index %i exceeds length of parameters %i' % (max(inds), npars))
    origpars = dcp(parset.pars)
    parset.pars = [] # Clear out in preparation for fitting
    
    # Populate lists of what to fit
    
    # Loop over each pars
    for ind in inds:
        
        # Get this set of parameters
        try: pars = origpars[ind]
        except: raise Exception('Could not load parameters %i from parset %s' % (ind, parset.name))
        
        # Pull out parameters to fit
        
        
        # Perform fit
        simpars = self.parsets[name].interp(start=project.data['datastart'], end=project.data['dataend'])
        raw = model(simparslist[ind], self.settings) # THIS IS SPINAL OPTIMA
        results = Resultset(self, simparslist, rawlist) # Create structure for storing results
        results.make() # Generate derived results
        
        # Save

    
    return None