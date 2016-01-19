"""
Functions for running optimizations.
    
Version: 2016jan18 by cliffk
"""

from optima import printv, dcp, asd, runmodel, odict, findinds
from numpy import zeros, arange



def objectivecalc(budgetvec, project=None, parset=None, progset=None, indices=None, objectives=None, constraints=None):
    
    # Convert budgetvec to budget
    budget = budgetvec
    
    
    # Define years
    start = objectives['start']
    end = objectives['end']
    
    thiscoverage = progset.getprogcoverage(budget=budget, t=start, parset=parset)
    thisparset = progset.getparset(coverage=thiscoverage, t=start, parset=parset)
    results = runmodel(pars=thisparset.pars[0], end=end, verbose=0)
    
    # Calculate outcome
    outcome = 0 # Preallocate objective value 
    for key in ['death', 'inci']:
        thisweight = objectives[key+'weight'] # e.g. objectives['inciweight']
        thisoutcome = results.main['num'+key].tot[indices].sum() # the instantaneous outcome e.g. objectives['numdeath']
        outcome += thisoutcome*thisweight*resuls.dt # Calculate objective

    
    return outcome




def minoutcomes(project=None, name=None, parset=None, progset=None, inds=0, objectives=None, constraints=None, maxiters=1000, maxtime=None, verbose=5, stoppingfunc=None, method='asd'):
    
    printv('Running outcomes optimization...', 1, verbose)
    
    parset  = project.parsets[parset] # Copy the original parameter set
    progset = project.progsets[progset] # Copy the original parameter set
    origparlist = dcp(parset.pars)
    lenparlist = len(origparlist)
    
    # Process inputs
    if isinstance(inds, (int, float)): inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(lenparlist)
    if max(inds)>lenparlist: raise Exception('Index %i exceeds length of parameter list (%i)' % (max(inds), lenparlist+1))
    if objectives is None: objectives = defaultobjectives()
    
    totalbudget = objectives['budget']
    nprogs = len(progset.programs)
    budgetvec = zeros(nprogs)+totalbudget/nprogs
    
    initial = findinds(parset['tvec'], objectives['start'])
    final = findinds(parset['tvec'], objectives['end'])
    indices = arange(initial, final)
    
    for ind in inds:
        try: pars = origparlist[ind]
        except: raise Exception('Could not load parameters %i from parset %s' % (ind, parset.name))
        
        # Calculate limits
        budgetlower  = zeros(nprogs)
        budgethigher = zeros(nprogs) + totalbudget
        
        args = {'project':project, 'parset':pars, 'progset':progset, 'objectives':objectives, 'constraints': constraints, 'indices':indices}
        if method=='asd': 
            budgetvecnew, fval, exitflag, output = asd(objectivecalc, budgetvec, args=args, xmin=budgetlower, xmax=budgethigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
        elif method=='simplex':
            from scipy.optimize import minimize
            budgetvecnew = minimize(objectivecalc, budgetvec, args=args).x
        else: raise Exception('Optimization method "%s" not recognized: must be "asd" or "simplex"' % method)

    
    return budgetvecnew







def defaultobjectives(verbose=2):
    """
    Define default objectives for the optimization.
    """

    printv('Defining default objectives...', 3, verbose=verbose)

    objectives = odict() # Dictionary of all objectives
    objectives['start'] = 2017 # "Year to begin optimization"
    objectives['end'] = 2030 # "Year to project outcomes to"
    objectives['budget'] = 0 # "Annual budget to optimize"
    objectives['deathweight'] = 5 # "Death weighting"
    objectives['inciweight'] = 1 # "Incidence weighting"
    
    return objectives