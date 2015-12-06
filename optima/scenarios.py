## Imports

from numpy import append, mean # array, isnan, zeros, shape, argmax, log, polyfit, exp, arange
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
#        import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
        printv('Scenario: %i/%i' % (scenno+1, nscenarios), 2, verbose)
    
    printv('...done running scenarios.', 2, verbose)
    return allresults


def makescenarios(parset,scenlist,verbose=2):
    """ Convert dictionary of scenario parameters into parset to model parameters """

    scenparsets = odict()
    for scenno, scen in enumerate(scenlist):
        
        thisparset = dcp(parset)
        thisparset.created = today()
        thisparset.modified = today()
        thisparset.name = scen['name']
        npops = len(parset.pars[0]['popkeys'])
        
        for par in scenlist[scenno]['pars']:
            parname = "".join(par['names'])
            pops = range(npops) if par['pops'] > npops else [par['pops']]
            for pop in pops:
                if par['startyear'] < max(thisparset.pars[0][parname].t[pop]):
                    thisparset.pars[0][parname].t[pop] = thisparset.pars[0][parname].t[pop][thisparset.pars[0][parname].t[pop] < par['startyear']]
                    thisparset.pars[0][parname].y[pop] = thisparset.pars[0][parname].y[pop][thisparset.pars[0][parname].t[pop] < par['startyear']]
                thisparset.pars[0][parname].t[pop] = append(thisparset.pars[0][parname].t[pop], par['startyear'])
                thisparset.pars[0][parname].y[pop] = append(thisparset.pars[0][parname].y[pop], par['startval']) 
                if par['endyear']: # Add end year values if supplied
                    thisparset.pars[0][parname].t[pop] = append(thisparset.pars[0][parname].t[pop], par['endyear'])
                    thisparset.pars[0][parname].y[pop] = append(thisparset.pars[0][parname].y[pop], par['endval'])

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

    if par['names'][0]=='condom': original = simpars[par['names'][0]][par['names'][1]]
    else: original = simpars[par['names'][0]]
    
    if par['pops'] < npops: # It's for a specific population, get the value
        original = original[par['pops'],:]
    else:
        original = original[:,:].mean(axis=0)
    initialindex = findinds(simpars['tvec'],par['startyear'])
    finalindex = findinds(simpars['tvec'],par['endyear'])

    startval = original[initialindex].tolist()[0]
    endval = original[finalindex].tolist()[0]
    return [startval, endval]
        
