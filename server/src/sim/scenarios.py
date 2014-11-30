## Imports
from bunch import Bunch as struct
from copy import deepcopy
from numpy import linspace, ndim
from nested import getnested, setnested

def runscenarios(D, scenariolist=None, verbose=2):
    """
    Run all the scenarios. The hard work is actually done by makescenarios, which
    takes the list of scenarios and makes the required changes to the model parameters
    M. Note that if a value is -1, it uses the current value. The code is a little
    ugly since some of it is duplicated between getparvalues() (not used here, but
    used for the GUI) and makescenarios().
        
    Version: 2014nov27 by cliffk
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
    D.scens = [struct() for s in range(nscenarios)]
    for scen in range(nscenarios):
        D.scens[scen].scenario = deepcopy(scenariolist[scen]) # Copy scenario data
        D.scens[scen].label = scenariolist[scen].name # Copy name
        D.scens[scen].M = deepcopy(scenariopars[scen].M)
        D.scens[scen].S = model(D.G, D.scens[scen].M, D.F[0], D.opt, verbose=verbose)
        printv('Scenario: %i/%i' % (scen+1, nscenarios), 2, verbose)
    
    # Calculate results
    from makeresults import makeresults
    for scen in range(nscenarios):
        D.scens[scen].R = makeresults(D, [D.scens[scen].S], D.opt.quantiles, verbose=verbose)
    
    # Gather plot data
    from gatherplotdata import gathermultidata
    D.plot.scens = gathermultidata(D, D.scens, verbose=verbose)
    
    printv('...done running scenarios.', 2, verbose)
    return D




def makescenarios(D, scenariolist, verbose=2):
    """ Convert a list of scenario parameters into a list of changes to model parameters """
    nscenarios = len(scenariolist)
    scenariopars = [struct() for s in range(nscenarios)]
    for scen in range(nscenarios):
        scenariopars[scen].name = scenariolist[scen].name
        scenariopars[scen].M = deepcopy(D.M) # Copy the whole thing...too hard to generate nested dictionaries on the fly
        for par in range(len(scenariolist[scen].pars)):
            thesepars = scenariolist[scen].pars[par] # Shorten name
            data = getnested(scenariopars[scen].M, thesepars.names)
            if ndim(data)>1: newdata = data[thesepars.pops] # If it's more than one dimension, use population data too
            else: newdata = data # If it's not, just use the whole thing
            initialindex = find(D.opt.tvec, thesepars.startyear)
            finalindex = find(D.opt.tvec, thesepars.endyear)
            initialvalue = newdata[initialindex] if thesepars.startval == -1 else thesepars.startval 
            finalvalue = newdata[finalindex] if thesepars.endval == -1 else thesepars.endval
            npts = finalindex-initialindex
            newvalues = linspace(initialvalue, finalvalue, npts)
            newdata[initialindex:finalindex] = newvalues
            newdata[finalindex:] = newvalues[-1] # Fill in the rest of the array with the last value
            if ndim(data)>1: data[thesepars.pops] = newdata # If it's multidimensional, only reset this one population
            else: data = newdata # Otherwise, reset the whole thing
            setnested(scenariopars[scen].M, thesepars.names, data)
                
    return scenariopars




def defaultscenarios(D, verbose=2):
    """ Define a list of default scenarios """
    
    # Start at the very beginning, a very good place to start :)
    scenariolist = [struct() for s in range(3)]
    
    scenariolist[0].name = 'Current conditions'
    scenariolist[0].pars = [] # No changes
    
    scenariolist[1].name = '99% condom use in KAPs'
    scenariolist[1].pars = [struct() for s in range(4)]
    # MSM regular condom use
    scenariolist[1].pars[0].names = ['condom','reg']
    scenariolist[1].pars[0].pops = 0
    scenariolist[1].pars[0].startyear = 2000
    scenariolist[1].pars[0].endyear = 2015
    scenariolist[1].pars[0].startval = 0.99
    scenariolist[1].pars[0].endval = 0.99
    # MSM casual condom use
    scenariolist[1].pars[1].names = ['condom','cas']
    scenariolist[1].pars[1].pops = 0
    scenariolist[1].pars[1].startyear = 2000
    scenariolist[1].pars[1].endyear = 2015
    scenariolist[1].pars[1].startval = 0.99
    scenariolist[1].pars[1].endval = 0.99
    # FSW commercial condom use
    scenariolist[1].pars[2].names = ['condom','com']
    scenariolist[1].pars[2].pops = 1
    scenariolist[1].pars[2].startyear = 2000
    scenariolist[1].pars[2].endyear = 2015
    scenariolist[1].pars[2].startval = 0.99
    scenariolist[1].pars[2].endval = 0.99
    # Client commercial condom use
    scenariolist[1].pars[3].names = ['condom','com']
    scenariolist[1].pars[3].pops = 5
    scenariolist[1].pars[3].startyear = 2000
    scenariolist[1].pars[3].endyear = 2015
    scenariolist[1].pars[3].startval = 0.99
    scenariolist[1].pars[3].endval = 0.99
    
    scenariolist[2].name = 'No needle sharing'
    scenariolist[2].pars = [struct()]
    scenariolist[2].pars[0].names = ['sharing']
    scenariolist[2].pars[0].pops = 2
    scenariolist[2].pars[0].startyear = 2000
    scenariolist[2].pars[0].endyear = 2015
    scenariolist[2].pars[0].startval = 0.0
    scenariolist[2].pars[0].endval = 0.0
    
    return scenariolist



def getparvalues(D, scenariopars):
    """
    Return the default parameter values from D.M for a given scenario If a scenariolist
    is defined as above, then call this function using e.g.
    
    defaultvals = getparvalues(D, scenariolist[1].pars[2])
    
    Version: 2014nov27 by cliffk
    """
    from numpy import ndim
    original = getnested(D.M, scenariopars.names)
    if ndim(original)>1: original = original[scenariopars.pops] # If it's more than one dimension, use population data too
    initialindex = find(D.opt.tvec, scenariopars.startyear)
    finalindex = find(D.opt.tvec, scenariopars.endyear)
    startval = original[initialindex]
    endval = original[finalindex]
    return [startval, endval]


def find(val1, val2=None, eps=1e-6):
    """
    Little function to find matches even if two things aren't eactly equal (eg. 
    due to floats vs. ints). If one argument, find nonzero values. With two arguments,
    check for equality using eps. Returns a tuple of arrays if val1 is multidimensional,
    else returns an array.
    
    Examples:
        find(rand(10)<0.5) # e.g. array([2, 4, 5, 9])
        find([2,3,6,3], 6) # e.g. array([2])
    
    Version: 2014nov27 by cliffk
    """
    from numpy import nonzero, array
    if val2==None: # Check for equality
        output = nonzero(val1) # If not, just check the truth condition
    else:
        output = nonzero(abs(array(val1)-val2)<eps) # If absolute difference between the two values is less than a certain amount
    if ndim(val1)==1: # Uni-dimensional
        output = output[0] # Return an array rather than a tuple of arrays if one-dimensional
    return output