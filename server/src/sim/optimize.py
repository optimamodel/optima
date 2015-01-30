"""
Allocation optimization code:
    D is the project data structure
    objectives is a dictionary defining the objectives of the optimization
    constraints is a dictionary defining the constraints on the optimization
    timelimit is the maximum time in seconds to run optimization for
    verbose determines how much information to print.
    
Version: 2015jan29 by cliffk
"""

from printv import printv
from bunch import Bunch as struct
from copy import deepcopy
from numpy import ones, zeros, concatenate, arange, inf, hstack, argmin
from utils import findinds
from makeresults import makeresults
from timevarying import timevarying
from getcurrentbudget import getcurrentbudget
from model import model
from makemodelpars import makemodelpars
from quantile import quantile

default_simstartyear = 2000
default_simendyear = 2030



def objectivecalc(optimparams, options):
    """ Calculate the objective function """

    thisalloc = timevarying(optimparams, ntimepm=options.ntimepm, nprogs=options.nprogs, tvec=options.D.opt.partvec, totalspend=options.totalspend)        
    newD = deepcopy(options.D)
    newD, newcov, newnonhivdalysaverted = getcurrentbudget(newD, thisalloc)
    newD.M = makemodelpars(newD.P, newD.opt, withwhat='c', verbose=0)
    S = model(newD.G, newD.M, newD.F[0], newD.opt, verbose=0)
    R = makeresults(options.D, allsims=[S], verbose=0)
    
    objective = 0 # Preallocate objective value 
    for key in options.outcomekeys:
        if options.weights[key]>0: # Don't bother unless it's actually used
            if key!='costann': thisobjective = R[key].tot[0][options.indices].sum()
            else: thisobjective = R[key].total.total[0][options.indices].sum() # Special case for costann
            objective += thisobjective * options.weights[key] / float(options.normalizations[key]) * options.D.opt.dt # Calculate objective
        
    return objective
    
    
    
def optimize(D, objectives=None, constraints=None, timelimit=60, verbose=2, name='Default'):
    """ Perform the actual optimization """
    
    # Imports
    
    from ballsd import ballsd
    
    
    printv('Running optimization...', 1, verbose)
    
    # Set up parameter vector for time-varying optimisation...
    stepsize = 100000
    growsize = 0.01
    
    origR = deepcopy(D.R)
    origalloc = D.data.origalloc
    
    # Make sure objectives and constraints exist
    if objectives is None: objectives = defaultobjectives(D, verbose=verbose)
    if constraints is None: constraints = defaultconstraints(D, verbose=verbose)

    objectives = deepcopy(objectives)
    constraints = deepcopy(constraints)
    ntimepm=1 + int(objectives.timevarying) # Either 1 or 2

    # Do percentage normalizations
    for ob in objectives.money.objectives.keys(): 
        if objectives.money.objectives[ob].use: objectives.money.objectives[ob].by = float(objectives.money.objectives[ob].by) / 100.0
    for prog in objectives.money.costs.keys(): 
        objectives.money.costs[prog] = float(objectives.money.costs[prog]) / 100.0
    for prog in constraints.decrease.keys(): 
        if constraints.decrease[prog].use: constraints.decrease[prog].by = float(constraints.decrease[prog].by) / 100.0

    nprogs = len(D.programs)
    totalspend = objectives.outcome.fixed # For fixed budgets
    
    
    ## Define indices, weights, and normalization factors
    initialindex = findinds(D.opt.partvec, objectives.year.start)
    finalindex = findinds(D.opt.partvec, objectives.year.end)
    indices = arange(initialindex,finalindex)
    weights = dict()
    normalizations = dict()
    outcomekeys = ['inci', 'death', 'daly', 'costann']
    if sum([objectives.outcome[key] for key in outcomekeys])>1: # Only normalize if multiple objectives, since otherwise doesn't make a lot of sense
        for key in outcomekeys:
            thisweight = objectives.outcome[key+'weight'] * objectives.outcome[key] / 100.
            weights.update({key:thisweight}) # Get weight, and multiply by "True" or "False" and normalize from percentage
            if key!='costann': thisnormalization = origR[key].tot[0][indices].sum()
            else: thisnormalization = origR[key].total.total[0][indices].sum() # Special case for costann
            normalizations.update({key:thisnormalization})
    else:
        for key in outcomekeys:
            weights.update({key:int(objectives.outcome[key])}) # Weight of 1
            normalizations.update({key:1}) # Normalizatoin of 1
        
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
    
    # Concatenate parameters to be optimised
    optimparams = concatenate((origalloc, growthrate, saturation, inflection))
        
    parammin = concatenate((zeros(nprogs), ones(nprogs)*-1e9))
        
        
        
    
    
    
    ###########################################################################
    ## Constant budget optimization
    ###########################################################################
    if objectives.funding == 'constant' and objectives.timevarying == False:
        
        ## Define options structure
        options = struct()
        options.ntimepm = ntimepm # Number of time-varying parameters
        options.nprogs = nprogs # Number of programs
        options.D = deepcopy(D) # Main data structure
        options.outcomekeys = outcomekeys # Names of outcomes, e.g. 'inci'
        options.weights = weights # Weights for each parameter
        options.indices = indices # Indices for the outcome to be evaluated over
        options.normalizations = normalizations # Whether to normalize a parameter
        options.totalspend = totalspend # Total budget
        
        
        ## Run with uncertainties
        allocarr = []
        fvalarr = []
        for s in range(len(D.F)): # Loop over all available meta parameters
            print('========== Running uncertainty optimization %s of %s... ==========' % (s+1, len(D.F)))
            options.D.F = [D.F[s]] # Loop over fitted parameters
            print('WARNING TODO want to loop over CCOCs too')
            optparams, fval, exitflag, output = ballsd(objectivecalc, optimparams, options=options, xmin=parammin, absinitial=stepsizes, timelimit=timelimit, fulloutput=True, verbose=verbose)
            optparams = optparams / optparams.sum() * options.totalspend # Make sure it's normalized -- WARNING KLUDGY
            allocarr.append(optparams)
            fvalarr.append(output.fval)
        
        ## Find which optimization was best
        bestallocind = -1
        bestallocval = inf
        for s in range(len(fvalarr)):
            if fvalarr[s][-1]<bestallocval:
                bestallocval = fvalarr[s][-1]
                bestallocind = s
        if bestallocind == -1: print('WARNING, best allocation value seems to be infinity!')
        
        # Update the model and store the results
        result = struct()
        result.kind = 'constant'
        result.fval = fvalarr[bestallocind] # Append the best value noe
        result.allocarr = [] # List of allocations
        result.allocarr.append(quantile([origalloc])) # Kludgy -- run fake quantile on duplicated origalloc just so it matches
        result.allocarr.append(quantile(allocarr)) # Calculate allocation arrays 
        labels = ['Original','Optimal']
        result.Rarr = []
        for params in [origalloc, allocarr[bestallocind]]: # CK: loop over original and (the best) optimal allocations
            alloc = timevarying(params, ntimepm=len(params)/nprogs, nprogs=nprogs, tvec=D.opt.partvec, totalspend=totalspend)   
            D, coverage, nonhivdalysaverted = getcurrentbudget(D, alloc)
            D.M = makemodelpars(D.P, D.opt, withwhat='c', verbose=2)
            S = model(D.G, D.M, D.F[0], D.opt, verbose=verbose)
            R = makeresults(D, [S], D.opt.quantiles, verbose=verbose)
            result.Rarr.append(struct()) # Append a structure
            result.Rarr[-1].R = deepcopy(R) # Store the R structure (results)
            result.Rarr[-1].label = labels.pop(0) # Store labels, one at a time
        
        
        
    
    
    ###########################################################################
    ## Time-varying budget optimization
    ###########################################################################
    if objectives.funding == 'constant' and objectives.timevarying == True:
        
        ## Define options structure
        options = struct()
        options.ntimepm = ntimepm # Number of time-varying parameters
        options.nprogs = nprogs # Number of programs
        options.D = deepcopy(D) # Main data structure
        options.outcomekeys = outcomekeys # Names of outcomes, e.g. 'inci'
        options.weights = weights # Weights for each parameter
        options.indices = indices # Indices for the outcome to be evaluated over
        options.normalizations = normalizations # Whether to normalize a parameter
        options.totalspend = totalspend # Total budget
        
        
        ## Run time-varying optimization
        print('========== Running time-varying optimization ==========')
        optparams, fval, exitflag, output = ballsd(objectivecalc, optimparams, options=options, xmin=parammin, absinitial=stepsizes, timelimit=timelimit, fulloutput=True, verbose=verbose)
        optparams = optparams / optparams.sum() * options.totalspend # Make sure it's normalized -- WARNING KLUDGY
        
        # Update the model and store the results
        result = struct()
        result.kind = 'timevarying'
        result.fval = output.fval # Append the objective sequence
        result.Rarr = []
        labels = ['Original','Optimal']
        for params in [origalloc, optparams]: # CK: loop over original and (the best) optimal allocations
            alloc = timevarying(params, ntimepm=len(params)/nprogs, nprogs=nprogs, tvec=D.opt.partvec, totalspend=totalspend) #Regenerate allocation
            D, coverage, nonhivdalysaverted = getcurrentbudget(D, alloc)
            D.M = makemodelpars(D.P, D.opt, withwhat='c', verbose=2)
            S = model(D.G, D.M, D.F[0], D.opt, verbose=verbose)
            R = makeresults(D, [S], D.opt.quantiles, verbose=verbose)
            result.Rarr.append(struct()) # Append a structure
            result.Rarr[-1].R = deepcopy(R) # Store the R structure (results)
            result.Rarr[-1].label = labels.pop(0) # Store labels, one at a time
        result.xdata = S.tvec # Store time data
        result.alloc = alloc[:,0:len(S.tvec)] # Store allocation data, and cut to be same length as time data
        
    
    
    
        
        
        
        
    ###########################################################################
    ## Multiple budgets optimization
    ###########################################################################
    if objectives.funding == 'range':
        
        ## Define options structure
        options = struct()
        options.ntimepm = 1 # Number of time-varying parameters -- always 1 in this case
        options.nprogs = nprogs # Number of programs
        options.D = deepcopy(D) # Main data structure
        options.outcomekeys = outcomekeys # Names of outcomes, e.g. 'inci'
        options.weights = weights # Weights for each parameter
        options.indices = indices # Indices for the outcome to be evaluated over
        options.normalizations = normalizations # Whether to normalize a parameter
        options.totalspend = totalspend # Total budget
        
        ## Run multiple budgets
        budgets = arange(objectives.outcome.budgetrange.minval, objectives.outcome.budgetrange.maxval+objectives.outcome.budgetrange.step, objectives.outcome.budgetrange.step)
        closesttocurrent = argmin(abs(budgets-1)) + 1 # Find the index of the budget closest to current and add 1 since prepend current budget
        nbudgets = len(budgets)
        budgets = hstack([1,budgets]) # Include current budget
        allocarr = [origalloc] # Original allocation
        fvalarr = [objectivecalc(optimparams, options=options)] # Outcome for original allocation
        for b in range(nbudgets):
            print('========== Running budget optimization %s of %s... ==========' % (b+1, nbudgets))
            options.totalspend = totalspend*budgets[b+1] # Total budget, skipping first
            optparams, fval, exitflag, output = ballsd(objectivecalc, optimparams, options=options, xmin=parammin, absinitial=stepsizes, timelimit=timelimit, fulloutput=True, verbose=verbose)
            optparams = optparams / optparams.sum() * options.totalspend # Make sure it's normalized -- WARNING KLUDGY
            allocarr.append(optparams)
            fvalarr.append(fval) # Only need last value
        
        # Update the model and store the results
        result = struct()
        result.kind = objectives.funding
        result.budgets = budgets
        result.budgetlabels = ['Original budget']
        for b in range(nbudgets): result.budgetlabels.append('%i%% budget' % (budgets[b+1]*100.))
            
        result.fval = fvalarr # Append the best value noe
        result.allocarr = allocarr # List of allocations
        labels = ['Original','Optimal']
        result.Rarr = []
        for params in [origalloc, allocarr[closesttocurrent]]: # CK: loop over original and (the best) optimal allocations
            alloc = timevarying(params, ntimepm=len(params)/nprogs, nprogs=nprogs, tvec=D.opt.partvec, totalspend=totalspend)   
            D, coverage, nonhivdalysaverted = getcurrentbudget(D, alloc)
            D.M = makemodelpars(D.P, D.opt, withwhat='c', verbose=2)
            S = model(D.G, D.M, D.F[0], D.opt, verbose=verbose)
            R = makeresults(D, [S], D.opt.quantiles, verbose=verbose)
            result.Rarr.append(struct()) # Append a structure
            result.Rarr[-1].R = deepcopy(R) # Store the R structure (results)
            result.Rarr[-1].label = labels.pop(0) # Store labels, one at a time        
        
        
    
    ## Gather plot data
    from gatherplotdata import gatheroptimdata
    optim = gatheroptimdata(D, result, verbose=verbose)
    if 'optim' not in D.plot: D.plot.optim = [] # Initialize list if required
    D.plot.optim.append(optim) # In any case, append
    
    ## Save optimization to D
    saveoptimization(D, name, objectives, constraints, result, verbose=2)   
    
    printv('...done optimizing programs.', 2, verbose)
    return D











def saveoptimization(D, name, objectives, constraints, result, verbose=2):
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
    ob.outcome.costann = False # "Minimize cumulative DALYs"
    ob.outcome.costannweight = 100 # "Cost weighting"
    ob.outcome.budgetrange = struct() # For running multiple budgets
    ob.outcome.budgetrange.minval = None
    ob.outcome.budgetrange.maxval = None
    ob.outcome.budgetrange.step = None
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


