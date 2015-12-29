"""
CALIBRATION

Functions to perform calibration.

Version: 2015dec29 by cliffk
"""

from optima import dcp, perturb

def perturbpars(orig=None, ncopies=5, what='force', span=0.5):
    ''' Function to perturb the parameters to get "uncertainties" '''
    
    parset = dcp(orig) # Copy the original parameter set
    origpars = dcp(parset.pars[0])
    parset.pars = []
    for n in range(ncopies):
        parset.pars.append(dcp(origpars))
    popkeys = origpars['popkeys']
    
    for n in range(ncopies):
        for key in popkeys:
            parset.pars[n]['force'][key] = perturb(n=1, span=span)
    
    return parset