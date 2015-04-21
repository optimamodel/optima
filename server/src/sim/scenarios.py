## Imports
from copy import deepcopy
from numpy import linspace, ndim
from nested import getnested, setnested
from utils import findinds

def runscenarios(D, scenariolist=None, verbose=2):
    """
    Run all the scenarios. The hard work is actually done by makescenarios, which
    takes the list of scenarios and makes the required changes to the model parameters
    M. Note that if a value is -1, it uses the current value. The code is a little
    ugly since some of it is duplicated between getparvalues() (not used here, but
    used for the GUI) and makescenarios().
        
    Version: 2015jan27 by cliffk
    """
    
    from model import model
    from printv import printv
    printv('Running scenarios...', 1, verbose)
    
    # Make sure scenarios exist
    if scenariolist==None: scenariolist = defaultscenarios(D, verbose=verbose)
    nscenarios = len(scenariolist)
    
    # Convert the list of scenarios to the actual parameters to use in the model
    scenariopars = makescenarios(D, scenariolist, verbose=verbose)
    
    # Run scenarios
    D['scens'] = [dict() for s in xrange(nscenarios)]
    for scen in xrange(nscenarios):
        D['scens'][scen]['scenario'] = deepcopy(scenariolist[scen]) # Copy scenario data
        D['scens'][scen]['label'] = scenariolist[scen]['name'] # Copy name
        D['scens'][scen]['M'] = deepcopy(scenariopars[scen]['M'])
        D['scens'][scen]['S'] = model(D['G'], D['scens'][scen]['M'], D['F'][0], D['opt'], verbose=verbose)
        printv('Scenario: %i/%i' % (scen+1, nscenarios), 2, verbose)
    
    # Calculate results
    from makeresults import makeresults
    for scen in xrange(nscenarios):
        D['scens'][scen]['R'] = makeresults(D, [D['scens'][scen]['S']], D['opt']['quantiles'], verbose=verbose)
    
    # Gather plot data
    from gatherplotdata import gathermultidata
    D['plot']['scens'] = gathermultidata(D, D['scens'], verbose=verbose)
    
    # Clean up -- inefficient, yes!
    for scen in xrange(nscenarios):
        D['scens'][scen].pop('M')
        D['scens'][scen].pop('S')
        D['scens'][scen].pop('R')
    
    printv('...done running scenarios.', 2, verbose)
    return D




def makescenarios(D, scenariolist, verbose=2):
    """ Convert a list of scenario parameters into a list of changes to model parameters """
    nscenarios = len(scenariolist)
    scenariopars = [dict() for s in xrange(nscenarios)]
    for scen in xrange(nscenarios):
        scenariopars[scen]['name'] = scenariolist[scen]['name']
        scenariopars[scen]['M'] = deepcopy(D['M']) # Copy the whole thing...too hard to generate nested dictionaries on the fly
        for par in xrange(len(scenariolist[scen]['pars'])):
            thesepars = scenariolist[scen]['pars'][par] # Shorten name
            data = getnested(scenariopars[scen]['M'], thesepars['names'])
            if ndim(data)>1:
                if thesepars['pops'] < len(data):
                    newdata = data[thesepars['pops']] # If it's more than one dimension, use population data too
                else:
                    newdata = data[:] # Get all populations
            else:
                newdata = data # If it's not, just use the whole thing
            
            # Get current values
            initialindex = findinds(D['opt']['partvec'], thesepars['startyear'])
            finalindex = findinds(D['opt']['partvec'], thesepars['endyear'])
            if thesepars['startval'] == -1:
                if ndim(newdata)==1: initialvalue = newdata[initialindex]
                else: initialvalue = newdata[:,initialindex].mean(axis=0) # Get the mean if multiple populations
            else:
                initialvalue = thesepars['startval']
            if thesepars['endval'] == -1:
                if ndim(newdata)==1: finalvalue = newdata[finalindex]
                else: finalvalue = newdata[:,finalindex].mean() # Get the mean if multiple populations
            else:
                finalvalue = thesepars['endval'] 
            
            # Set new values
            npts = finalindex-initialindex
            newvalues = linspace(initialvalue, finalvalue, npts)
            if ndim(newdata)==1:
                newdata[initialindex:finalindex] = newvalues
                newdata[finalindex:] = newvalues[-1] # Fill in the rest of the array with the last value
                if ndim(data)==1:
                    data = newdata
                else:
                    data[thesepars['pops']] = newdata
            else:
                for p in xrange(len(newdata)):
                    newdata[p,initialindex:finalindex] = newvalues
                    newdata[p,finalindex:] = newvalues[-1] # Fill in the rest of the array with the last value
            
            # Update data
            if ndim(data)>1 and ndim(newdata)==1:
                data[thesepars['pops']] = newdata # Data is multiple populations, but we're only resetting one
            else:
                data = newdata # In all other cases, reset the whole thing (if both are 1D, or if both are 2D

            setnested(scenariopars[scen]['M'], thesepars['names'], data)
                
    return scenariopars




def defaultscenarios(D, verbose=2):
    """ Define a list of default scenarios -- only "Current conditions" by default """
    
    # Start at the very beginning, a very good place to start :)
    scenariolist = [dict()]
    
    ## Current conditions
    scenariolist[0]['name'] = 'Current conditions'
    scenariolist[0]['pars'] = [] # No changes
    
    return scenariolist



def getparvalues(D, scenariopars):
    """
    Return the default parameter values from D['M'] for a given scenario. If a scenariolist
    is defined as above, then call this function using e.g.
    
    defaultvals = getparvalues(D, scenariolist[1]['pars'][2])
    
    Version: 2014dec02 by cliffk
    """
    from numpy import ndim
    original = getnested(D['M'], scenariopars['names'])
    if ndim(original)>1:
        if scenariopars['pops']<len(original):
            original = original[scenariopars['pops']] # If it's a valid population, just use it
        else:
            original = original[:,:].mean(axis=0) # If multiple populations, take the mean along first axis
    initialindex = findinds(D['opt']['partvec'], scenariopars['startyear'])
    finalindex = findinds(D['opt']['partvec'], scenariopars['endyear'])
    startval = original[initialindex].tolist()[0]
    endval = original[finalindex].tolist()[0]
    return [startval, endval]
