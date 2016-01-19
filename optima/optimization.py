"""
Functions for running optimizations.
    
Version: 2016jan18 by cliffk
"""

from optima import printv, dcp, asd, runmodel, odict, findinds, today, getdate, uuid, objectid, objatt, objmeth
from numpy import zeros, arange, array


def objectivecalc(budgetvec, project=None, parset=None, progset=None, objectives=None, constraints=None, tvec=None, outputresults=False):
    
    # Convert budgetvec to budget
    budget = odict()
    for i,key in enumerate(progset.programs.keys()):
        budget[key] = array([budgetvec[i]]) # WARNING, ugly...
    
    # Run model
    thiscoverage = progset.getprogcoverage(budget=budget, t=array([objectives['start']]), parset=parset) # WARNING, shouldn't need array()
    thisparset = progset.getparset(coverage=thiscoverage, t=array([objectives['start']]), parset=parset)
    results = runmodel(pars=thisparset.pars[0], tvec=tvec, verbose=0) # WARNING, should just generate pars, not parset
    
    initial = findinds(results.tvec, objectives['start'])
    final = findinds(results.tvec, objectives['end'])
    indices = arange(initial, final)
    
    # Calculate outcome
    outcome = 0 # Preallocate objective value 
    for key in ['death', 'inci']:
        thisweight = objectives[key+'weight'] # e.g. objectives['inciweight']
        thisoutcome = results.main['num'+key].tot[0][indices].sum() # the instantaneous outcome e.g. objectives['numdeath'] -- 0 is since best
        outcome += thisoutcome*thisweight*results.dt # Calculate objective

    if outputresults:
        results.outcome = outcome
        return results
    else: 
        return outcome




def minoutcomes(project=None, optim=None, inds=0, maxiters=1000, maxtime=None, verbose=5, stoppingfunc=None, method='asd'):
    
    printv('Running outcomes optimization...', 1, verbose)
    
    # Shorten things stored in the optimization -- WARNING, not sure if this is consistent with other functions
    parset = optim.parset
    progset = optim.progset 
    objectives = optim.objectives
    constraints = optim.constraints 
    
    parset  = project.parsets[parset] # Copy the original parameter set
    progset = project.progsets[progset] # Copy the original parameter set
    lenparlist = len(parset.pars)
    
    # Process inputs
    if isinstance(inds, (int, float)): inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(lenparlist)
    if max(inds)>lenparlist: raise Exception('Index %i exceeds length of parameter list (%i)' % (max(inds), lenparlist+1))
    if objectives is None: objectives = defaultobjectives()
    tvec = project.settings.maketvec(end=objectives['end']) # WARNING, this could be done better most likely
    
    totalbudget = objectives['budget']
    nprogs = len(progset.programs)
    budgetvec = zeros(nprogs)+totalbudget/nprogs
    
    for ind in inds:
        # WARNING, kludge because some later functions expect parset instead of pars
        thisparset = dcp(parset)
        try: thisparset.pars = [parset.pars[ind]] # Turn into a list
        except: raise Exception('Could not load parameters %i from parset %s' % (ind, parset.name))
        
        # Calculate limits -- WARNING, kludgy, I guess?
        budgetlower  = zeros(nprogs)
        budgethigher = zeros(nprogs) + totalbudget
        
        args = {'project':project, 'parset':thisparset, 'progset':progset, 'objectives':objectives, 'constraints': constraints, 'tvec': tvec}
        if method=='asd': 
            budgetvecnew, fval, exitflag, output = asd(objectivecalc, budgetvec, args=args, xmin=budgetlower, xmax=budgethigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
        elif method=='simplex':
            from scipy.optimize import minimize
            budgetvecnew = minimize(objectivecalc, budgetvec, args=args).x
        else: raise Exception('Optimization method "%s" not recognized: must be "asd" or "simplex"' % method)

    ## Tidy up
    results = objectivecalc(budgetvecnew, outputresults=True, **args)
    results.budgetorig = budgetvec # Store original allocation
    results.budgetoptim = budgetvecnew # Store new results
    
    import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
    
    return results





def defaultobjectives(verbose=2):
    """
    Define default objectives for the optimization.
    """

    printv('Defining default objectives...', 3, verbose=verbose)

    objectives = odict() # Dictionary of all objectives
    objectives['start'] = 2017 # "Year to begin optimization"
    objectives['end'] = 2030 # "Year to project outcomes to"
    objectives['budget'] = 1e6 # "Annual budget to optimize"
    objectives['deathweight'] = 5 # "Death weighting"
    objectives['inciweight'] = 1 # "Incidence weighting"
    
    return objectives




class Optim(object):
    def __init__(self, name='default', project=None, objectives=None, constraints=None, parset=None, progset=None):
        self.name = name # Name of the parameter set, e.g. 'default'
        self.uid = uuid() # ID
        self.project = project # Store pointer for the project, if available
        self.created = today() # Date created
        self.modified = today() # Date modified
        self.parset = parset # Parameter set name
        self.progset = progset # Program set name
        self.objectives = None # List of dicts holding Parameter objects -- only one if no uncertainty
        self.constraints = None # List of populations
        if objectives is None: self.objectives = defaultobjectives()
        if constraints is None: self.constraints = 'WARNING, not implemented'
        self.results = None # Store pointer to results
        
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = objectid(self)
        output += '============================================================\n'
        output += ' Optimization name: %s\n'    % self.name
        output += 'Parameter set name: %s\n'    % self.parset
        output += '  Program set name: %s\n'    % self.progset
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objatt(self)
        output += '============================================================\n'
        output += objmeth(self)
        output += '============================================================\n'
        return output