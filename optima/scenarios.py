## Imports
from numpy import append # array, isnan, zeros, shape, argmax, log, polyfit, exp, arange
from optima import dcp, today, odict, printv, findinds #, sanitize, uuid, getdate, smoothinterp

def runscenarios(P, parset, scenlist=None, verbose=2, debug=False):
    """
    Run all the scenarios.
    """
    
    printv('Running scenarios...', 1, verbose)
    
    # Make sure scenarios exist
    if scenlist==None: scenlist = defaultscenarios(parset, verbose=verbose)
    nscenarios = len(scenlist)
    
    # Convert the list of scenarios to the actual parameters to use in the model
    scenparsets = makescenarios(parset,scenlist,verbose=verbose)
    
    # Run scenarios
    allresults = []
    for scenno, scen in enumerate(scenparsets):
        P.addparset(name=scen,parset=scenparsets[scen])
        allresults.append(P.runsim(scen))
        printv('Scenario: %i/%i' % (scenno+1, nscenarios), 2, verbose)
    
    printv('...done running scenarios.', 2, verbose)
    return allresults


def makescenarios(parset,scenlist,verbose=2):
    """ Convert dictionary of scenario parameters into parset to model parameters """

    scenparsets = odict()
    for scenno, scen in enumerate(scenlist):
        
        thisparset = dcp(parset)
        thisparset.modified = today()
        thisparset.name = scen['name']
        npops = len(parset.pars[0]['popkeys'])
        
        for sc in range(len(parset.pars)): # Loop over all parameter sets
            for par in scenlist[scenno]['pars']: # Loop over all parameters being changed
                thispar = thisparset.pars[sc][par['name']]
                if type(par['for'])==tuple: # If it's a partnership...
                    par2 = (par['for'][1],par['for'][0])
                    pops = [par['for'], par2] # This is confusing - for partnership parameters, pops is a list of the two different partnership orderings.
                elif type(par['for'])==int: #... if its a population.
                    pops = range(npops) if par['for'] > npops else [par['for']]
                else: 
                    errormsg = 'Unrecognized population or partnership type.'
                    raise Exception(errormsg)
                for pop in pops:
                    if par['startyear'] < max(thispar.t[pop]):
                        thispar.t[pop] = thispar.t[pop][thispar.t[pop] < par['startyear']]
                        thispar.y[pop] = thispar.y[pop][thispar.t[pop] < par['startyear']]
                    thispar.t[pop] = append(thispar.t[pop], par['startyear'])
                    thispar.y[pop] = append(thispar.y[pop], par['startval']) 
                    if par['endyear']: # Add end year values if supplied
                        thispar.t[pop] = append(thispar.t[pop], par['endyear'])
                        thispar.y[pop] = append(thispar.y[pop], par['endval'])

        scenparsets[scen['name']] = thisparset

    return scenparsets


def defaultscenarios(parset, verbose=2):
    """ Define a list of default scenarios -- only "Current conditions" by default """
    
    scenlist = [odict()]
    
    ## Current conditions
    scenlist[0]['name'] = 'Current conditions'
    scenlist[0]['pars'] = [] # No changes
    
    return scenlist

def getparvalues(parset, par, dt=.2):
    """
    Return the default parameter values from simpars for a given par.
    
    defaultvals = getparvalues(P, parset, scenariolist[1]['pars'][2])
    """
    npops = len(parset.pars[0]['popkeys'])
    simpars = parset.interp(start=par['startyear'], end=par['endyear'], dt=dt)

    original = simpars[par['names'][0]]
    
    if par['pops'] < npops: # It's for a specific population, get the value
        original = original[par['pops'],:]
    else:
        original = original[:,:].mean(axis=0)
    initialindex = findinds(simpars['tvec'],par['startyear'])
    finalindex = findinds(simpars['tvec'],par['endyear'])

    startval = original[initialindex][0]
    endval = original[finalindex][0]
    return [startval, endval]
        
