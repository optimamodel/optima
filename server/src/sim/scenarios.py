from bunch import Bunch as struct
from copy import deepcopy

def runscenarios(D, scenariolist=None, verbose=2):
    """
    Allocation optimization code:
        D is the project data structure
        objectives is a dictionary defining the objectives of the optimization
        constraints is a dictionary defining the constraints on the optimization
        timelimit is the maximum time in seconds to run optimization for
        verbose determines how much information to print.
        
    Version: 2014nov24 by cliffk
    """
    
    from model import model
    from printv import printv
    printv('Running scenarios...', 1, verbose)
    
    # Make sure scenarios exist
    if scenariolist==None: scenariolist = defaultscenarios(D, verbose=verbose)
    nscenarios = len(scenariolist)
    
    # Convert the list of scenarios to the actual parameters to use in the model
    scenariopars = makescenarios(D.M, scenariolist, verbose=verbose)
    
    M = []
    for scen in range(nscenarios):
        M.append(deepcopy(D.M)) # Make a copy of the model parameters
        M[scen].update(scenariopars[scen].M) # Update with selected scenario model parameters
    
    
    # Run scenarios # TODO -- actually implement :)
    print('!!! TODO !!!')
    D.scens = [struct()]*nscenarios
    for scen in range(nscenarios):
        D.scens[scen].label = scenariolist[scen].name # Copy name
        D.scens[scen].S = model(D.G, M[scen], D.F[0], D.opt, verbose=verbose) # At the moment, D.F is changing -- but need allocation to change
        printv('Scenario: %i/%i' % (scen, nscenarios), 2, verbose)
    
    # Calculate results
    from makeresults import makeresults
    for scen in range(nscenarios):
        D.scens.R = makeresults(D, [D.scens[scen].S], D.opt.quantiles, verbose=verbose)
    
    # Gather plot data
    from gatherplotdata import gathermultidata
    D.plot.scens = gathermultidata(D, D.scens, verbose=verbose)
    
    printv('...done running scenarios.', 2, verbose)
    return D




def makescenarios(D, scenariolist, verbose=2):
    """ Convert a list of scenario parameters into a list of changes to model parameters """
    from pylab import find, linspace
    
    nscenarios = len(scenariolist)
    scenariopars = [struct()]*nscenarios
    
    # From http://stackoverflow.com/questions/14692690/access-python-nested-dictionary-items-via-a-list-of-keys
    def getnested(nesteddict, maplist): return reduce(lambda d, k: d[k], maplist, nesteddict)
    def setnested(nesteddict, maplist, value): getnested(nesteddict, maplist[:-1])[maplist[-1]] = value
    
    for scen in range(nscenarios):
        scenariopars[scen].name = scenariolist[scen].name
        npars = len(scenariopars[scen].pars)
        scenariopars[scen].M = deepcopy(D.M) # Copy the whole thing...too hard to generate nested dictionaries on the fly
        for par in range(npars):
            thesepars = scenariolist[scen].pars[par] # Shorten name
            original = getnested(scenariopars[scen].M, thesepars.keys)
            initialindex = find(abs(D.opt.tvec - thesepars.startyear)<1e-6)
            finalindex = find(abs(D.opt.tvec - thesepars.startyear)<1e-6)
            initialvalue = original[initialindex] if thesepars.startval == -1 else thesepars.startval 
            finalvalue = original[finalindex] if thesepars.endval == -1 else thesepars.endval
            npts = finalindex-initialindex+1
            newvalues = linspace(initialvalue, finalvalue, npts)
            scenariopars[scen].M[initialvalue:finalvalue+1] = newvalues
            
    return scenariopars




def defaultscenarios(D, verbose=2):
    """ Define a list of default scenarios """
    
    # Start at the very beginning, a very good place to start :)
    scenariolist = [struct()]*2
    
    scenariolist[0].name = 'Current conditions'
    scenariolist[0].pars = [] # No changes
    
    scenariolist[1].name = '100% condom use in KAPs'
    scenariolist[1].pars = [struct()]*4
    # MSM regular condom use
    scenariolist[1].pars[0].keys = ['condom','reg']
    scenariolist[1].pars[0].pop = 0
    scenariolist[1].pars[0].startyear = 2010
    scenariolist[1].pars[0].endyear = 2015
    scenariolist[1].pars[0].startval = -1
    scenariolist[1].pars[0].endval = 1
    # MSM casual condom use
    scenariolist[1].pars[1].keys = ['condom','cas']
    scenariolist[1].pars[1].pop = 0
    scenariolist[1].pars[1].startyear = 2010
    scenariolist[1].pars[1].endyear = 2015
    scenariolist[1].pars[1].startval = -1
    scenariolist[1].pars[1].endval = 1
    # FSW commercial condom use
    scenariolist[1].pars[2].keys = ['condom','com']
    scenariolist[1].pars[2].pop = 1
    scenariolist[1].pars[2].startyear = 2010
    scenariolist[1].pars[2].endyear = 2015
    scenariolist[1].pars[2].startval = -1
    scenariolist[1].pars[2].endval = 1
    # Client commercial condom use
    scenariolist[1].pars[2].keys = ['condom','com']
    scenariolist[1].pars[2].pop = 5
    scenariolist[1].pars[2].startyear = 2010
    scenariolist[1].pars[2].endyear = 2015
    scenariolist[1].pars[2].startval = -1
    scenariolist[1].pars[2].endval = 1
    
    return scenariolist