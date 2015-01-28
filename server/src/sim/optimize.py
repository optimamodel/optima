from printv import printv
from bunch import Bunch as struct
from copy import deepcopy
from numpy import array, ones, zeros, concatenate

default_simstartyear = 2000
default_simendyear = 2030

def optimize(D, objectives=None, constraints=None, ntimepm=1, timelimit=60, verbose=2):
    """
    Allocation optimization code:
        D is the project data structure
        objectives is a dictionary defining the objectives of the optimization
        constraints is a dictionary defining the constraints on the optimization
        timelimit is the maximum time in seconds to run optimization for
        verbose determines how much information to print.
        
    Version: 2015jan27 by cliffk
    """
    
    # Imports
    from model import model
    from ballsd import ballsd
    from getcurrentbudget import getcurrentbudget
    from makemodelpars import makemodelpars
    from timevarying import timevarying
    printv('Running optimization...', 1, verbose)
    
    # Set up parameter vector for time-varying optimisation...
    stepsize = 100000
    growsize = 0.01
    
    # Set options to update year range
    from setoptions import setoptions
    simstartyear = objectives.get("year").get("start") or default_simstartyear
    simendyear = objectives.get("year").get("end") or default_simendyear
    D.opt = setoptions(D.opt, simstartyear=simstartyear, simendyear=simendyear)
    
    # Make sure objectives and constraints exist
    if not isinstance(objectives, struct):  objectives = defaultobjectives(D, verbose=verbose)
    if not isinstance(constraints, struct): constraints = defaultconstraints(D, verbose=verbose)

    objectives = deepcopy(objectives)
    constraints = deepcopy(constraints)
    
    ntimepm=2 if objectives.timevarying == True else 1

    # Convert weightings from percentage to number
    if objectives.outcome.inci:  objectives.outcome.inciweight  = float(objectives.outcome.inciweight) / 100.0
    if objectives.outcome.daly:  objectives.outcome.dalyweight  = float(objectives.outcome.dalyweight) / 100.0
    if objectives.outcome.death: objectives.outcome.deathweight = float(objectives.outcome.deathweight) / 100.0
    if objectives.outcome.cost:  objectives.outcome.costweight  = float(objectives.outcome.costweight) / 100.0

    for ob in objectives.money.objectives.keys():
        if objectives.money.objectives[ob].use: objectives.money.objectives[ob].by = float(objectives.money.objectives[ob].by) / 100.0

    for prog in objectives.money.costs.keys():
        objectives.money.costs[prog] = float(objectives.money.costs[prog]) / 100.0

    for prog in constraints.decrease.keys():
        if constraints.decrease[prog].use: constraints.decrease[prog].by = float(constraints.decrease[prog].by) / 100.0

    # Run optimization # TODO -- actually implement :)
    nallocs = 1 # WARNING, will want to do this better
    D.A = deepcopy([D.A[0]])
    for alloc in range(nallocs): D.A.append(deepcopy(D.A[0])) # Just copy for now
    D.A[0].label = 'Original'
    D.A[1].label = 'Optimal'
    # preserving the origalloc during the first iteration (because on web, we run this in batches)
    if 'origalloc' not in D.A[0]:
        origalloc = deepcopy(array(D.A[0].alloc))
        D.A[0].origalloc = origalloc
    else:
        origalloc = D.A[0].origalloc
    D.A = D.A[:2] # TODO WARNING KLUDGY

    nprogs = len(origalloc)
    totalspend = sum(origalloc) # Temp # TODO -- set this up for variable budgets
    
    def objectivecalc(optimparams):
        """ Calculate the objective function """

        thisalloc = timevarying(optimparams, ntimepm=ntimepm, nprogs=nprogs, tvec=D.opt.partvec, totalspend=totalspend)        
        newD = deepcopy(D)
        newD, newcov, newnonhivdalysaverted = getcurrentbudget(newD, thisalloc)
        newD.M = makemodelpars(newD.P, newD.opt, withwhat='c', verbose=0)
        S = model(newD.G, newD.M, newD.F[0], newD.opt, verbose=0)
        
        # Obtain value of the objective function
        objective = 0 # Preallocate objective value 
        if objectives.what == 'outcome':
            for ob in ['inci', 'death', 'daly', 'cost']:
                if objectives.outcome[ob]: objective += S[ob].sum() * objectives.outcome[ob + 'weight'] # TODO -- can we do 'daly' and 'cost' like this too??
        else: print('Work to do here') # 'money'
            
        return objective
        
    # Initiate probabilities of parameters being selected
    stepsizes = zeros(nprogs * ntimepm)
    
    # Easy access initial allocation indices and turn stepsizes into array
    ai = range(nprogs)
    gi = range(nprogs,   nprogs*2) if ntimepm >= 2 else []
    si = range(nprogs*2, nprogs*3) if ntimepm >= 3 else []
    ii = range(nprogs*3, nprogs*4) if ntimepm >= 4 else []
    
    # Turn stepsizes into array
    stepsizes[ai] = stepsize
    stepsizes[gi] = growsize if ntimepm > 1 else 0
    stepsizes[si] = stepsize
    stepsizes[ii] = growsize # Not sure that growsize is an appropriate starting point
    
    # Initial values of time-varying parameters
    growthrate = zeros(nprogs)   if ntimepm >= 2 else []
    saturation = origalloc       if ntimepm >= 3 else []
    inflection = ones(nprogs)*.5 if ntimepm >= 4 else []
    
    # Concatonate parameters to be optimised
    optimparams = concatenate((origalloc, growthrate, saturation, inflection))
        
    parammin = concatenate((zeros(nprogs), ones(nprogs)*-1e9))
        
    # Run the optimization algorithm
    optparams, fval, exitflag, output = ballsd(objectivecalc, optimparams, xmin=parammin, absinitial=stepsizes, timelimit=timelimit, verbose=verbose,)
    
    # Update the model
    for i, params in enumerate([origalloc, optparams]):
        alloc = timevarying(params, ntimepm=len(params)/nprogs, nprogs=nprogs, tvec=D.opt.partvec, totalspend=totalspend)            
        D, D.A[i].coverage, D.A[i].nonhivdalysaverted = getcurrentbudget(D, alloc)
        D.M = makemodelpars(D.P, D.opt, withwhat='c', verbose=2)
        D.A[i].S = model(D.G, D.M, D.F[0], D.opt, verbose=verbose)
        D.A[i].alloc = alloc # This is overwriting a vector with a matrix # TODO -- initiate properly in makedatapars
    
    # Calculate results
    from makeresults import makeresults
    for alloc in range(len(D.A)):
        D.A[alloc].R = makeresults(D, [D.A[alloc].S], D.opt.quantiles, verbose=verbose)
    
    # Gather plot data
    from gatherplotdata import gatheroptimdata, gathermultidata
    D.plot.OA = gatheroptimdata(D, D.A, verbose=verbose)
    D.plot.OM = gathermultidata(D, D.A, verbose=verbose)
    
    printv('...done optimizing programs.', 2, verbose)
    return D

def saveoptimization(D, name, objectives, constraints, result = None, verbose=2):
    #save the optimization parameters
    new_optimization = struct()
    new_optimization.name = name
    new_optimization.objectives = objectives
    new_optimization.constraints = constraints
    if result: new_optimization.result = result

    if not "optimizations" in D:
        D.optimizations = [new_optimization]
    else:
        try:
            index = [item.name for item in D.optimizations].index(name)
            D.optimizations[index] = deepcopy(new_optimization)
        except:
            D.optimizations.append(new_optimization)
    return D

def removeoptimization(D, name):
    if "optimizations" in D:
        try:
            index = [item.name for item in D.optimizations].index(name)
            D.optimizations.pop(index)
        except:
            pass
    return D

def defaultobjectives(D, verbose=2):
    """
    Define default objectives for the optimization.
    """

    printv('Defining default objectives...', 3, verbose=verbose)

    ob = struct() # Dictionary of all objectives
    ob.year = struct() # Time periods for objectives
    ob.year.start = 2015 # "Year to begin optimization from"
    ob.year.end = 2020 # "Year to end optimization"
    ob.year.until = 2030 # "Year to project outcomes to"
    ob.what = 'outcome' # Alternative is "money"
    
    ob.outcome = struct()
    ob.outcome.fixed = 1e6 # "With a fixed amount of money available"
    ob.outcome.inci = True # "Minimize cumulative HIV incidence"
    ob.outcome.inciweight = 100 # "Incidence weighting"
    ob.outcome.daly = False # "Minimize cumulative DALYs"
    ob.outcome.dalyweight = 100 # "DALY weighting"
    ob.outcome.death = False # "Minimize cumulative AIDS-related deaths"
    ob.outcome.deathweight = 100 # "Death weighting"
    ob.outcome.cost = False # "Minimize cumulative DALYs"
    ob.outcome.costweight = 100 # "Cost weighting"
    ob.funding = "constant" #that's how it works on FE atm
    
    # Other settings
    ob.timevarying = False # Do not use time-varying parameters
    ob.artcontinue = 1 # No one currently on ART stops
    ob.otherprograms = "remain" # Other programs remain constant after optimization ends
    
    ob.money = struct()
    ob.money.objectives = struct()
    for objective in ['inci', 'incisex', 'inciinj', 'mtct', 'mtctbreast', 'mtctnonbreast', 'deaths', 'dalys']:
        ob.money.objectives[objective] = struct()
        ob.money.objectives[objective].use = False # TIck box: by default don't use
        ob.money.objectives[objective].by = 50 # "By" text entry box: 0.5 = 50% reduction
        ob.money.objectives[objective].to = 0 # "To" text entry box: don't use if set to 0
    ob.money.objectives.inci.use = True # Set incidence to be on by default
    
    ob.money.costs = struct()
    for prog in D.programs.keys():
        ob.money.costs[prog] = 100 # By default, use a weighting of 100%
    
    return ob

def defaultconstraints(D, verbose=2):
    """
    Define default constraints for the optimization.
    """
    
    printv('Defining default constraints...', 3, verbose=verbose)
    
    con = struct()
    con.txelig = 4 # 4 = "All people diagnosed with HIV"
    con.dontstopart = True # "No one who initiates treatment is to stop receiving ART"
    con.decrease = struct()
    for prog in D.programs.keys(): # Loop over all defined programs
        con.decrease[prog] = struct()
        con.decrease[prog].use = False # Tick box: by default don't use
        con.decrease[prog].by = 50 # Text entry box: 0.5 = 50% per year
    
    con.coverage = struct()
    for prog in D.programs.keys(): # Loop over all defined programs
        con.coverage[prog] = struct()
        con.coverage[prog].use = False # Tick box: by default don't use
        con.coverage[prog].level = 0 # First text entry box: default no limit
        con.coverage[prog].year = 2030 # Year to reach coverage level by
        
    return con


def defaultoptimizations(D, verbose=2):
    """ Define a list of default optimizations (one default optimization) """
    
    # Start at the very beginning, a very good place to start :)
    optimizations = [struct()]
    
    ## Current conditions
    optimizations[0].name = 'Default'
    optimizations[0].constraints = defaultconstraints(D, verbose)
    optimizations[0].objectives = defaultobjectives(D, verbose)
    return optimizations


