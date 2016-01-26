"""
Functions for running optimizations.
    
Version: 2016jan24
"""

from optima import OptimaException, Multiresultset, printv, dcp, asd, runmodel, odict, findinds, today, getdate, uuid, objrepr, getresults
from numpy import zeros, arange, array, isnan





class Optim(object):
    ''' An object for storing an optimization '''
    
    def __init__(self, project=None, name='default', which='outcome', objectives=None, constraints=None, parsetname=None, progsetname=None):
        self.name = name # Name of the parameter set, e.g. 'default'
        self.uid = uuid() # ID
        self.project = project # Store pointer for the project, if available
        self.created = today() # Date created
        self.modified = today() # Date modified
        self.which = which # Outcome or money minimization
        self.parsetname = parsetname # Parameter set name
        self.progsetname = progsetname # Program set name
        self.objectives = objectives # List of dicts holding Parameter objects -- only one if no uncertainty
        self.constraints = constraints # List of populations
        if objectives is None: self.objectives = defaultobjectives()
        if constraints is None: self.constraints = 'WARNING, not implemented'
        self.resultsref = None # Store pointer to results
        
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '============================================================\n'
        output += ' Optimization name: %s\n'    % self.name
        output += 'Parameter set name: %s\n'    % self.parsetname
        output += '  Program set name: %s\n'    % self.progsetname
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output
    
    
    def getresults(self):
        ''' A little method for getting the results '''
        if self.resultsref is not None and self.project is not None:
            results = getresults(project=self.project, pointer=self.resultsref)
            return results
        else:
            print('WARNING, no results associated with this parameter set')
            return None




def defaultobjectives(which='outcome', verbose=2):
    """
    Define default objectives for the optimization. Some objectives are shared
    between outcome and money minimizations, while others are different. However,
    outcome minimization is performed as part of money minimization, so it's useful
    to keep all the keys for both. Still, ugly.
    
    Version: 2016jan26
    """

    printv('Defining default objectives...', 3, verbose=verbose)

    objectives = odict() # Dictionary of all objectives
    objectives['start'] = 2017 # "Year to begin optimization"
    objectives['end'] = 2030 # "Year to project outcomes to"
    if which=='outcome':
        objectives['budget'] = 1e6 # "Annual budget to optimize"
        objectives['deathweight'] = 5 # "Death weighting"
        objectives['inciweight'] = 1 # "Incidence weighting"
        objectives['deathsfrac'] = None # Fraction of deaths to get to
        objectives['incifrac'] = None # Fraction of incidence to get to
    elif which=='money':
        objectives['budget'] = None # "Annual budget to optimize"
        objectives['deathweight'] = None # "Death weighting"
        objectives['inciweight'] = None # "Incidence weighting"
        objectives['deathsfrac'] = 0.5 # Fraction of deaths to get to
        objectives['incifrac'] = 0.5 # Fraction of incidence to get to
    else: 
        raise Exception('"which" keyword argument must be either "outcome" or "money"')
    
    return objectives





def objectivecalc(budgetvec=None, project=None, parset=None, progset=None, objectives=None, constraints=None, tvec=None, outputresults=False):
    
    # Validate input
    if any([arg is None for arg in [budgetvec, progset, objectives, constraints, tvec]]):  # WARNING, this kind of obscures which of these is None -- is that ok? Also a little too hard-coded...
        raise OptimaException('objectivecalc() requires a budgetvec, progset, objectives, constraints, and tvec at minimum')
    
    # WARNING -- temp -- normalize budgetvec
    budgetvec *=  objectives['budget']/budgetvec.sum() 
    
    # Convert budgetvec to budget
    budget = progset.getdefaultbudget()
    budget[:] = budgetvec
    
    # Run model
    thiscoverage = progset.getprogcoverage(budget=budget, t=objectives['start'], parset=parset) 
    thisparsdict = progset.getpars(coverage=thiscoverage, t=objectives['start'], parset=parset)
    results = runmodel(pars=thisparsdict, parset=parset, progset=progset, project=project, tvec=tvec, verbose=0)
    
    # Figure out which indices to use
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
        results.budgetvec = budgetvec # WARNING, not sure this should be here
        results.budgetyears = [objectives['start']] # WARNING, this is ugly, should be made less kludgy
        results.budget = progset.getdefaultbudget() # Returns an odict with the correct structure
        for k,key in enumerate(results.budget.keys()):
            results.budget[key] = [budgetvec[k]] # Make this budget value a list so has len()
        return results
    else: 
        return outcome




def minoutcomes(project=None, optim=None, inds=0, maxiters=1000, maxtime=None, verbose=5, stoppingfunc=None, method='asd'):
    
    printv('Running outcomes optimization...', 1, verbose)
    
    if None in [project, optim]: raise OptimaException('minoutcomes() requires project and optim arguments at minimum')
    
    
    
    # Shorten things stored in the optimization -- WARNING, not sure if this is consistent with other functions
    parsetname = optim.parsetname
    progsetname = optim.progsetname
    objectives = optim.objectives
    constraints = optim.constraints 
    
    parset  = project.parsets[parsetname] # Copy the original parameter set
    progset = project.progsets[progsetname] # Copy the original parameter set
    lenparlist = len(parset.pars)
    
    # Process inputs
    if isinstance(inds, (int, float)): inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(lenparlist)
    if max(inds)>lenparlist: raise OptimaException('Index %i exceeds length of parameter list (%i)' % (max(inds), lenparlist+1))
    tvec = project.settings.maketvec(end=objectives['end']) # WARNING, this could be done better most likely
    
    totalbudget = objectives['budget']
    nprogs = len(progset.programs)
    budgetvec = progset.getdefaultbudget()[:]
    if isnan(budgetvec).any():
        budgetlessprograms = array(progset.programs.keys())[isnan(budgetvec)].tolist()
        output = 'WARNING!!!!!!!!!! Not all programs have a budget associated with them.\n A uniform budget will be used instead.\n Programs with no budget are:\n'
        output += '\n'.join(budgetlessprograms)
        print(output)
        budgetvec = zeros(nprogs)+totalbudget/nprogs
    else: budgetvec *= totalbudget/sum(budgetvec) # Rescale
    
    for ind in inds: # WARNING, kludgy -- inds not actually used!!!
        # WARNING, kludge because some later functions expect parset instead of pars
        thisparset = dcp(parset)
        try: thisparset.pars = [parset.pars[ind]] # Turn into a list
        except: raise OptimaException('Could not load parameters %i from parset %s' % (ind, parset.name))
        
        # Calculate limits -- WARNING, kludgy, I guess?
        budgetlower  = zeros(nprogs)
        budgethigher = zeros(nprogs) + totalbudget
        
        args = {'project':project, 'parset':thisparset, 'progset':progset, 'objectives':objectives, 'constraints': constraints, 'tvec': tvec}
        if method=='asd': 
            budgetvecnew, fval, exitflag, output = asd(objectivecalc, budgetvec, args=args, xmin=budgetlower, xmax=budgethigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
        elif method=='simplex':
            from scipy.optimize import minimize
            budgetvecnew = minimize(objectivecalc, budgetvec, args=args).x
        else: raise OptimaException('Optimization method "%s" not recognized: must be "asd" or "simplex"' % method)

    ## Tidy up -- WARNING, need to think of a way to process multiple inds
    orig = objectivecalc(budgetvec, outputresults=True, **args)
    new = objectivecalc(budgetvecnew, outputresults=True, **args)
    orig.name = 'Current allocation' # WARNING, is this really the best way of doing it?
    new.name = 'Optimal allocation'
    tmpresults = [orig, new]
    
    multires = Multiresultset(resultsetlist=tmpresults, name='optimization-%s-%s' % (parsetname, progsetname))
    
    for k,key in enumerate(multires.keys): # WARNING, this is ugly
        
        multires.budgetyears[key] = tmpresults[k].budgetyears
    
    multires.improvement = [output.fval] # Store full function evaluation information -- wrap in list for future multi-runs
    optim.resultsref = multires.uid # Store the reference for this result
    
    return multires
    
    
    
    
    
    
def minmoney(project=None, optim=None, inds=0, maxiters=1000, maxtime=None, verbose=5, stoppingfunc=None, method='asd'):
    
    printv('Running outcomes optimization...', 1, verbose)
    
    if None in [project, optim]: raise OptimaException('minoutcomes() requires project and optim arguments at minimum')
    
    # Shorten things stored in the optimization -- WARNING, not sure if this is consistent with other functions
    parsetname = optim.parsetname
    progsetname = optim.progsetname
    objectives = optim.objectives
    constraints = optim.constraints 
    
    parset  = project.parsets[parsetname] # Copy the original parameter set
    progset = project.progsets[progsetname] # Copy the original parameter set
    lenparlist = len(parset.pars)
    
    # Process inputs
    if isinstance(inds, (int, float)): inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(lenparlist)
    if max(inds)>lenparlist: raise OptimaException('Index %i exceeds length of parameter list (%i)' % (max(inds), lenparlist+1))
    tvec = project.settings.maketvec(end=objectives['end']) # WARNING, this could be done better most likely
    
    
    for ind in inds: # WARNING, kludgy -- inds not actually used!!!
        # WARNING, kludge because some later functions expect parset instead of pars
        thisparset = dcp(parset)
        try: thisparset.pars = [parset.pars[ind]] # Turn into a list
        except: raise OptimaException('Could not load parameters %i from parset %s' % (ind, parset.name))
        
        # Calculate limits -- WARNING, kludgy, I guess?
        budgetlower  = zeros(nprogs)
        budgethigher = zeros(nprogs) + totalbudget
        
        args = {'project':project, 'parset':thisparset, 'progset':progset, 'objectives':objectives, 'constraints': constraints, 'tvec': tvec}
        if method=='asd': 
            budgetvecnew, fval, exitflag, output = asd(objectivecalc, budgetvec, args=args, xmin=budgetlower, xmax=budgethigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
        elif method=='simplex':
            from scipy.optimize import minimize
            budgetvecnew = minimize(objectivecalc, budgetvec, args=args).x
        else: raise OptimaException('Optimization method "%s" not recognized: must be "asd" or "simplex"' % method)

    ## Tidy up -- WARNING, need to think of a way to process multiple inds
    orig = objectivecalc(budgetvec, outputresults=True, **args)
    new = objectivecalc(budgetvecnew, outputresults=True, **args)
    orig.name = 'Current allocation' # WARNING, is this really the best way of doing it?
    new.name = 'Optimal allocation'
    tmpresults = [orig, new]
    
    multires = Multiresultset(resultsetlist=tmpresults, name='optimization-%s-%s' % (parsetname, progsetname))
    
    for k,key in enumerate(multires.keys): # WARNING, this is ugly
        
        multires.budgetyears[key] = tmpresults[k].budgetyears
    
    multires.improvement = [output.fval] # Store full function evaluation information -- wrap in list for future multi-runs
    optim.resultsref = multires.uid # Store the reference for this result
    
    return multires





