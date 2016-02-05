"""
Functions for running optimizations.
    
Version: 2016feb04
"""

from optima import OptimaException, Multiresultset, Programset, asd, runmodel, getresults, vec2obj # Main functions
from optima import printv, dcp, odict, findinds, today, getdate, uuid, objrepr, isnumber # Utilities
from numpy import zeros, arange, isnan, maximum, array, inf

# Define global parameters that shouldn't really matter
infmoney = 1e9 # Effectively infinite money



class Optim(object):
    ''' An object for storing an optimization '''
    
    def __init__(self, project=None, name='default', which='outcome', objectives=None, constraints=None, parsetname=None, progsetname=None):
        if project is None:     raise OptimaException('To create an optimization, you must supply a project')
        if parsetname is None:  parsetname = 0 # If none supplied, assume defaults
        if progsetname is None: progsetname = 0
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
        if objectives is None: self.objectives = defaultobjectives(progset=project.progsets[progsetname])
        if constraints is None: self.constraints = defaultconstraints(progset=project.progsets[progsetname])
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
        ''' A method for getting the results '''
        if self.resultsref is not None and self.project is not None:
            results = getresults(project=self.project, pointer=self.resultsref)
            return results
        else:
            print('WARNING, no results associated with this parameter set')
            return None




def defaultobjectives(project=None, progset=None, which='outcome', verbose=2):
    """
    Define default objectives for the optimization. Some objectives are shared
    between outcome and money minimizations, while others are different. However,
    outcome minimization is performed as part of money minimization, so it's useful
    to keep all the keys for both. Still, ugly.
    
    Version: 2016feb03
    """

    printv('Defining default objectives...', 3, verbose=verbose)
    
    if type(progset)==Programset:
        defaultbudget = sum(progset.getdefaultbudget()[:])
    if type(project)==Programset: # Not actually a project, but proceed anyway
        defaultbudget = sum(project.getdefaultbudget()[:])
    elif project is not None:
        if progset is None: progset = 0
        defaultbudget = sum(project.progsets[progset].getdefaultbudget()[:])
        printv('defaultobjectives() did not get a progset input, so using default budget of %0.0f' % defaultbudget, 2, verbose)
    else:
        defaultbudget = 1e6 # If can't find programs
        printv('defaultobjectives() did not get a progset input, so using default budget of %0.0f' % defaultbudget, 2, verbose)

    objectives = odict() # Dictionary of all objectives
    objectives['keys'] = ['death', 'inci'] # Define valid keys
    objectives['keylabels'] = {'death':'Deaths', 'inci':'New infections'} # Define key labels
    if which=='outcome':
        objectives['base'] = None # "Baseline year to compare outcomes to"
        objectives['start'] = 2017 # "Year to begin optimization"
        objectives['end'] = 2030 # "Year to project outcomes to"
        objectives['budget'] = defaultbudget # "Annual budget to optimize"
        objectives['deathweight'] = 5 # "Death weighting"
        objectives['inciweight'] = 1 # "Incidence weighting"
        objectives['deathfrac'] = None # Fraction of deaths to get to
        objectives['incifrac'] = None # Fraction of incidence to get to
    elif which=='money':
        objectives['base'] = 2015 # "Baseline year to compare outcomes to"
        objectives['start'] = 2017 # "Year to begin optimization"
        objectives['end'] = 2027 # "Year by which to achieve objectives"
        objectives['budget'] = defaultbudget # "Starting budget"
        objectives['deathweight'] = None # "Death weighting"
        objectives['inciweight'] = None # "Incidence weighting"
        objectives['deathfrac'] = 0.5 # Fraction of deaths to get to
        objectives['incifrac'] = 0.5 # Fraction of incidence to get to
    else: 
        raise OptimaException('"which" keyword argument must be either "outcome" or "money"')
    
    return objectives


def defaultconstraints(project=None, progset=None, which='outcome', verbose=2):
    """
    Define constraints for minimize outcomes optimization: at the moment, just
    total budget constraints defned as a fraction of current spending. Fixed costs
    are treated differently, and ART is hard-coded to not decrease.
    
    Version: 2016feb03
    """

    printv('Defining default objectives...', 3, verbose=verbose)
    
    if type(progset)==Programset: pass
    elif type(project)==Programset: progset = project
    elif project is not None:
        if progset is None: progset = 0
        progset = project.progsets[progset]
        printv('defaultconstraints() did not get a progset input, so using default', 2, verbose)

    else:
        raise OptimaException('To define constraints, you must supply a program set as an input')

    constraints = odict() # Dictionary of all constraints
    constraints['name'] = odict() # Full name
    constraints['min'] = odict() # Minimum budgets
    constraints['max'] = odict() # Maximum budgets
    for prog in progset.programs.values():
        constraints['name'][prog.short] = prog.name
        if prog.optimizable():
            constraints['min'][prog.short] = 0.0
            constraints['max'][prog.short] = None
        else:
            constraints['min'][prog.short] = 1.0
            constraints['max'][prog.short] = 1.0
    if 'ART' in constraints['min'].keys():
        constraints['min']['ART'] = 1.0 # By default, don't let ART funding decrease
    
    return constraints



def outcomecalc(budgetvec=None, project=None, parset=None, progset=None, objectives=None, totalbudget=None, origbudgetdict=None, budgetlims=None, optiminds=None, tvec=None, outputresults=False, debug=False):
    ''' Function to evaluate the objective for a given budget vector (note, not time-varying) '''
    # Validate input
    if any([arg is None for arg in [budgetvec, progset, objectives, totalbudget, origbudgetdict, budgetlims, optiminds, tvec]]):  # WARNING, this kind of obscures which of these is None -- is that ok? Also a little too hard-coded...
        raise OptimaException('outcomecalc() requires a budgetvec, progset, objectives, budgetlims, optiminds, and tvec at minimum')
    
    # Normalize budgetvec and convert to budget -- WARNING, is there a better way of doing this?
    normbudgetvec = constrainbudget(origbudget=budgetvec, total=totalbudget, limits=budgetlims)
    budget = vec2obj(orig=origbudgetdict, newvec=normbudgetvec, inds=optiminds)
    
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
    for key in objectives['keys']:
        thisweight = objectives[key+'weight'] # e.g. objectives['inciweight']
        thisoutcome = results.main['num'+key].tot[0][indices].sum() # the instantaneous outcome e.g. objectives['numdeath'] -- 0 is since best
        outcome += thisoutcome*thisweight*results.dt # Calculate objective

    # Optionally start debugger
    if debug: import traceback; traceback.print_exc(); import pdb; pdb.set_trace()

    if outputresults:
        results.outcome = outcome
        results.budgetvec = budgetvec # WARNING, not sure this should be here
        results.budgetyears = [objectives['start']] # WARNING, this is ugly, should be made less kludgy
        results.budget = vec2obj(orig=origbudgetdict, newvec=budgetvec, inds=optiminds) # Convert to budget
        return results
    else: 
        return outcome


def constrainbudget(origbudget, total=None, limits=None, tolerance=1e-3):
    """ Take an unnormalized/unconstrained budget and normalize and constrain it """
    normbudget = dcp(origbudget)
    
    if total < sum(limits['min']) or total > sum(limits['max']):
        errormsg = 'Budget cannot be constrained since the total %f is outside the low-high limits [%f, %f]' % (total, sum(limits['min']), sum(limits['max']))
        raise OptimaException(errormsg)
    
    # Not strictly needed, but get close to correct answer in one go
    normbudget *= total/float(sum(normbudget)) # Rescale
    
    nprogs = len(normbudget)
    proginds = arange(nprogs)
    limlow = zeros(nprogs, dtype=bool)
    limhigh = zeros(nprogs, dtype=bool)
    for p in proginds:
        if normbudget[p] <= limits['min'][p]:
            normbudget[p] = limits['min'][p]
            limlow[p] = True
        if normbudget[p] >= limits['max'][p]:
            normbudget[p] = limits['max'][p]
            limhigh[p] = True
    
    # Too high
    while sum(normbudget) > total+tolerance:
        overshoot = sum(normbudget) - total
        toomuch = sum(normbudget[~limlow]) / float((sum(normbudget[~limlow]) - overshoot))
        for p in proginds[~limlow]:
            proposed = normbudget[p] / float(toomuch)
            if proposed <= limits['min'][p]:
                proposed = limits['min'][p]
                limlow[p] = True
            normbudget[p] = proposed
        
    # Too low
    while sum(normbudget) < total-tolerance:
        undershoot = total - sum(normbudget)
        toolittle = (sum(normbudget[~limhigh]) + undershoot) / float(sum(normbudget[~limhigh]))
        for p in proginds[~limhigh]:
            proposed = normbudget[p] * toolittle
            if proposed >= limits['max'][p]:
                proposed = limits['max'][p]
                limhigh[p] = True
            normbudget[p] = proposed
    
    return normbudget







def minoutcomes(project=None, optim=None, inds=0, maxiters=1000, maxtime=None, verbose=2, stoppingfunc=None, method='asd'):
    ''' 
    The standard Optima optimization function: minimize outcomes for a fixed total budget.
    
    Version: 1.1 (2016feb03)
    '''
    
    # Begin and check initial inputs
    printv('Running outcomes optimization...', 1, verbose)
    if None in [project, optim]: raise OptimaException('minoutcomes() requires project and optim arguments at minimum')
    
    # Shorten things stored in the optimization -- WARNING, not sure if this is consistent with other functions
    parsetname = optim.parsetname
    progsetname = optim.progsetname
    objectives = optim.objectives
    constraints = optim.constraints 
    
    parset  = project.parsets[parsetname] # Link to the original parameter set
    progset = project.progsets[progsetname] # Link to the original parameter set
    lenparlist = len(parset.pars)
    
    # Process inputs
    if isnumber(inds): inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(lenparlist)
    if max(inds)>lenparlist: raise OptimaException('Index %i exceeds length of parameter list (%i)' % (max(inds), lenparlist+1))
    tvec = project.settings.maketvec(end=objectives['end']) # WARNING, this could be done better most likely
    
    # Handle budget and remove fixed costs
    totalbudget = objectives['budget']
    optiminds = findinds(progset.optimizable())
    fixedinds = findinds(1-array(progset.optimizable()))
    nprogs = len(optiminds) # Only count optimizable programs
    origbudgetdict = dcp(progset.getdefaultbudget())
    budgetvec = dcp(origbudgetdict[:])
    origbudget = sum(budgetvec)
    ratio = totalbudget/origbudget
    
    # Trim out non-optimizable programs and calculate limits
    minlimsvec = constraints['min'][:] # Convert to vector
    minfixedcosts = budgetvec[fixedinds]*minlimsvec[fixedinds]*ratio # Calculate the minimum allowed costs of fixed programs -- scaled to new spending amount
    totalbudget -= minfixedcosts.sum() # Remove fixed costs from budget
    budgetvec = budgetvec[optiminds] # ...then remove them from the vector
    origbudgetvec = dcp(budgetvec) # Store original budget vector
    budgetvec *= totalbudget/sum(budgetvec) # Rescale so the total matches the new total
    
    # Do limits
    budgetlims = odict()
    budgetlims['min'] = zeros(nprogs)
    budgetlims['max'] = zeros(nprogs)
    for p in range(nprogs):
        minfrac = constraints['min'][optiminds[p]]
        maxfrac = constraints['max'][optiminds[p]]
        budgetlims['min'][p] = minfrac * origbudgetvec[p] * ratio # Note: 'constraints' includes non-optimizable programs, must be careful
        if maxfrac is not None: budgetlims['max'][p] = maxfrac * origbudgetvec[p] * ratio
        else:                   budgetlims['max'][p] = inf


    
    for ind in inds: # WARNING, kludgy -- inds not actually used!!!
        # WARNING, kludge because some later functions expect parset instead of pars
        thisparset = dcp(parset)
        try: thisparset.pars = [thisparset.pars[ind]] # Turn into a list
        except: raise OptimaException('Could not load parameters %i from parset %s' % (ind, parset.name))
        
        # Calculate limits -- WARNING, kludgy, I guess?
        budgetlower  = zeros(nprogs)
        budgethigher = zeros(nprogs) + totalbudget
        
        args = {'project':project, 'parset':thisparset, 'progset':progset, 'objectives':objectives, 'totalbudget':totalbudget, 'origbudgetdict':origbudgetdict, 'budgetlims': budgetlims, 'optiminds':optiminds, 'tvec': tvec}
        if method=='asd': 
            budgetvecnew, fval, exitflag, output = asd(outcomecalc, budgetvec, args=args, xmin=budgetlower, xmax=budgethigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
        elif method=='simplex': # WARNING, not fully implemented
            from scipy.optimize import minimize
            budgetvecnew = minimize(outcomecalc, budgetvec, args=args).x
        else: raise OptimaException('Optimization method "%s" not recognized: must be "asd" or "simplex"' % method)

    ## Tidy up -- WARNING, need to think of a way to process multiple inds
    budgetvecnew = constrainbudget(origbudget=budgetvecnew, total=totalbudget, limits=budgetlims) # WARNING, not sure why this is needed, but it is
    orig = outcomecalc(budgetvec, outputresults=True, debug=False, **args)
    new = outcomecalc(budgetvecnew, outputresults=True, debug=False, **args)
    orig.name = 'Current allocation' # WARNING, is this really the best way of doing it?
    new.name = 'Optimal allocation'
    tmpresults = [orig, new]
    
    multires = Multiresultset(resultsetlist=tmpresults, name='minoutcomes-%s-%s' % (parsetname, progsetname))
    
    for k,key in enumerate(multires.keys): # WARNING, this is ugly
        multires.budgetyears[key] = tmpresults[k].budgetyears
    
    multires.improvement = [output.fval] # Store full function evaluation information -- wrap in list for future multi-runs
    optim.resultsref = multires.uid # Store the reference for this result
    
    return multires
    
    
    

## WARNING, should be combined with outcomecal!!!
def moneycalc(budgetvec=None, project=None, parset=None, progset=None, objectives=None, totalbudget=None, origbudgetdict=None, budgetlims=None, optiminds=None, tvec=None, outputresults=False, verbose=2, debug=False):
    ''' Function to evaluate whether or not targets have been met for a given budget vector (note, not time-varying) '''
    # Validate input
    if any([arg is None for arg in [budgetvec, progset, objectives, totalbudget, budgetlims, optiminds, tvec]]):  # WARNING, this kind of obscures which of these is None -- is that ok? Also a little too hard-coded...
        raise OptimaException('moneycalc() requires a budgetvec, progset, objectives, budgetlims, optiminds, and tvec at minimum')
   
   
    # Normalize budgetvec and convert to budget -- WARNING, is there a better way of doing this?
    normbudgetvec = constrainbudget(origbudget=budgetvec, total=objectives['budget'], limits=budgetlims)
    budget = vec2obj(orig=origbudgetdict, newvec=normbudgetvec, inds=optiminds)
    
    # Run model
    thiscoverage = progset.getprogcoverage(budget=budget, t=objectives['start'], parset=parset) 
    thisparsdict = progset.getpars(coverage=thiscoverage, t=objectives['start'], parset=parset)
    results = runmodel(pars=thisparsdict, parset=parset, progset=progset, project=project, tvec=tvec, verbose=0)
    
    # Figure out which indices to use
    baseind = findinds(results.tvec, objectives['base'])
    startind = findinds(results.tvec, objectives['start'])
    if baseind>=startind: 
        baseind = startind-1 # Don't let users specify a baseline after optimization starts
        printv('Warning, baseline year after optimization begins: resetting to last index before budget changes', 2, verbose)
    finalind = findinds(results.tvec, objectives['end'])
    
    # Calculate outcome
    targetsmet = True # Assume success until proven otherwise (since operator is AND, not OR)
    baseline = odict()
    final = odict()
    target = odict()
    targetfrac = odict([(key,objectives[key+'frac']) for key in objectives['keys']]) # e.g. {'inci':objectives['incifrac']} = 0.4 = 40% reduction in incidence
    for key in objectives['keys']:
        thisresult = results.main['num'+key].tot[0] # the instantaneous outcome e.g. objectives['numdeath'] -- 0 is since best
        baseline[key] = float(thisresult[baseind])
        final[key] = float(thisresult[finalind])
        target[key] = float(baseline[key]*(1-targetfrac[key]))
        if final[key] > target[key]: targetsmet = False # Targets are NOT met

    # Optionally debug, since these calculations often go wrong
    if debug: import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
    
    # Output results
    if outputresults:
        results.outcomes = odict([('baseline',baseline), ('final',final), ('target',target), ('targetfrac',targetfrac)])
        results.budgetvec = budgetvec # WARNING, not sure this should be here
        results.budgetyears = [objectives['start']] # WARNING, this is ugly, should be made less kludgy
        results.budget = vec2obj(orig=origbudgetdict, newvec=budgetvec, inds=optiminds) # Convert to budget
        results.targetsmet = targetsmet
        return results
    else: 
        return targetsmet




    
    
    
def minmoney(project=None, optim=None, inds=0, maxiters=1000, maxtime=None, verbose=2, stoppingfunc=None, fundingchange=1.2, tolerance=0.05, debug=False):
    '''
    A function to minimize money for a fixed objective. Note that it calls minoutcomes() in the process.
    
    "fundingchange" specifies the amount by which to increase/decrease the total budget to see if
    objectives are met.
    
    "tolerance" specifies how close the funding amount needs to converge.
    
    Version: 2016feb03
    '''
    
     # Being and check vital inputs    
    printv('Running money optimization...', 1, verbose)
    if None in [project, optim]: raise OptimaException('minoutcomes() requires project and optim arguments at minimum')
    
    # Shorten things stored in the optimization -- WARNING, not sure if this is consistent with other functions
    parsetname = optim.parsetname
    progsetname = optim.progsetname
    objectives = optim.objectives
    constraints = optim.constraints
    
    # Check that objectives were specified appropriately
    for key in objectives['keys']:
        thisfrac = objectives[key+'frac']
        if thisfrac<0 or thisfrac>=1:
            errormsg = 'Fractional reduction in "%s" must be >=0 and <1; actually %f' % (key, thisfrac)
            print(errormsg) # WARNING TEMP
#            raise OptimaException(errormsg) # WARNING TEMP
    
    parset  = project.parsets[parsetname] # Link to the original parameter set
    progset = project.progsets[progsetname] # Link to the original parameter set
    lenparlist = len(parset.pars)
    nprogs = len(progset.programs)
    
    # Process inputs
    if isnumber(inds): inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(lenparlist)
    if max(inds)>lenparlist: raise OptimaException('Index %i exceeds length of parameter list (%i)' % (max(inds), lenparlist+1))
    tvec = project.settings.maketvec(end=objectives['end']) # WARNING, this could be done better most likely
    
    
    ##################################################################################
    ### WARNING, copied from minoutcomes!!!
    
    # Handle budget and remove fixed costs
    progkeys = progset.programs.keys()
    optiminds = findinds(progset.optimizable())
    fixedinds = findinds(1-array(progset.optimizable()))
    nprogs = len(optiminds) # Only count optimizable programs
    origbudgetdict = dcp(progset.getdefaultbudget())
    budgetvec = array(origbudgetdict[:])
    totalbudget = objectives['budget']
    origbudget = sum(budgetvec) # WARNING, correct?
    
    # Error checking
    if isnan(budgetvec).any():
        errormsg = 'Program "%s" does not have any budget' % progkeys[findinds(isnan(budgetvec))]
        raise OptimaException(errormsg)
    
    # Trim out non-optimizable programs and calculate limits
    minlimsvec = constraints['min'][:] # Convert to vector
    minfixedcosts = budgetvec[fixedinds]*minlimsvec[fixedinds]*totalbudget/origbudget # Calculate the minimum allowed costs of fixed programs
    totalbudget -= minfixedcosts.sum() # Remove fixed costs from budget
    budgetvec = budgetvec[optiminds] # ...then remove them from the vector
    origbudgetvec = dcp(budgetvec) # Store original budget vector
    budgetvec *= totalbudget/sum(budgetvec) # Rescale so the total matches the new total
    
    # Do limits
    budgetlims = odict()
    budgetlims['min'] = zeros(nprogs)
    budgetlims['max'] = zeros(nprogs)
    for p in range(nprogs):
        minfrac = constraints['min'][optiminds[p]]
        maxfrac = constraints['max'][optiminds[p]]
        budgetlims['min'][p] = minfrac * origbudgetvec[p] # Note: 'constraints' includes non-optimizable programs, must be careful
        if maxfrac is not None: budgetlims['max'][p] = maxfrac * origbudgetvec[p]
        else:                   budgetlims['max'][p] = infmoney
    
    ##################################################################################
    
    for ind in inds: # WARNING, kludgy -- inds not actually used!!!
        # WARNING, kludge because some later functions expect parset instead of pars
        thisparset = dcp(parset)
        try: thisparset.pars = [thisparset.pars[ind]] # Turn into a list
        except: raise OptimaException('Could not load parameters %i from parset %s' % (ind, parset.name))
        args = {'project':project, 'parset':thisparset, 'progset':progset, 'objectives':objectives, 'totalbudget':totalbudget, 'budgetlims': budgetlims, 'origbudgetdict':origbudgetdict, 'optiminds':optiminds, 'tvec': tvec}

        budgetvec0 = progset.getdefaultbudget()[:][optiminds] # Get the current budget allocation
        budgetvec1 = dcp(budgetvec0)
        budgetlower = zeros(nprogs)
        budgethigher = zeros(nprogs) + budgetvec1.sum() # WARNING, I guess this is ok to start with...
        
        
        ##########################################################################################################################
        ## Loop through different budget options
        ##########################################################################################################################
        
        # First, try infinite money
        targetsmet = moneycalc(budgetvec1+infmoney, **args)
        args['origbudgetdict'] = dcp(origbudgetdict[:]+infmoney)
        if not(targetsmet):
            budgetvecfinal = budgetvec1+infmoney
            printv("Warning, infinite allocation can't meet targets:", 1, verbose)
            if debug: results = moneycalc(budgetvecfinal, outputresults=True, debug=True, **args)
            break
        else:
            printv("Infinite allocation meets targets, as expected; proceeding...", 1, verbose)
        
        # Next, try no money
        targetsmet = moneycalc(budgetvec1/infmoney, **args)
        args['origbudgetdict'] = dcp(origbudgetdict[:]/infmoney)
        if targetsmet:
            budgetvecfinal = budgetvec1/infmoney
            print("Warning, even zero allocation meets targets")
            if debug: results = moneycalc(budgetvecfinal, outputresults=True, debug=True, **args)
            break
        else:
            printv("Zero allocation doesn't meet targets, as expected; proceeding...", 2, verbose)
        
        # If those did as expected, proceed with checking what's actually going on to set objective weights for minoutcomes() function
        args['origbudgetdict'] = dcp(origbudgetdict)
        results = moneycalc(budgetvec1, outputresults=True, **args)
        absreductions = odict() # Absolute reductions requested, for setting weights
        for key in objectives['keys']:
            absreductions[key] = float(results.outcomes['baseline'][key]*objectives[key+'frac']) # e.g. 1000 deaths * 40% reduction = 400 deaths
        weights = dcp(absreductions) # Copy this, since will be modifying it -- not strictly necessary but could come in handy
        weights = 1.0/weights[:] # Relative weights are inversely proportional to absolute reductions -- e.g. asking for a reduction of 100 deaths and 400 new infections means 1 death = 4 new infections
        weights /= weights.min() # Normalize such that the lowest weight is 1; arbitrary, but could be useful
        for k,key in enumerate(objectives['keys']):
           objectives[key+'weight'] = maximum(weights[k],0) # Reset objective weights according to the reduction required -- don't let it go below 0, though
        
        
        ##########################################################################################################################
        ## Now run an optimization on the current budget
        args['totalbudget'] = budgetvec1.sum() # Calculate new total funding
        args['origbudgetdict'] = dcp(origbudgetdict[:]*budgetvec1.sum()/origbudgetvec.sum())
        budgethigher = zeros(nprogs) + totalbudget # Reset funding maximum
        budgetvec2, fval, exitflag, output = asd(outcomecalc, budgetvec1, args=args, xmin=budgetlower, xmax=budgethigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
        
        
        # See if objectives are met
        targetsmet = moneycalc(budgetvec2/infmoney, **args)
        fundingfactor = 1.0
        
        # If targets are met, scale down until they're not -- this loop will be skipped entirely if targets not currently met
        while targetsmet:
            fundingfactor /= fundingchange
            targetsmet = moneycalc(budgetvec2*fundingfactor, **args)
            printv('Current funding factor: %f' % fundingfactor, 4, verbose)
        
        # If targets are not met, scale up until they are -- this will always be run at least once after the previous loop
        while not(targetsmet):
            fundingfactor *= fundingchange
            targetsmet = moneycalc(budgetvec2*fundingfactor, **args)
            printv('Current funding factor: %f' % fundingfactor, 4, verbose)
        
        ##########################################################################################################################
        # Re-optimize based on this fairly close allocation
        budgetvec3 = budgetvec2*fundingfactor # Calculate new budget vector
        args['totalbudget'] = budgetvec3.sum() # Calculate new total funding
        args['origbudgetdict'] = dcp(origbudgetdict[:]*budgetvec2.sum()/origbudgetvec.sum())
        budgethigher = zeros(nprogs) + totalbudget # Reset funding maximum
        budgetvec4, fval, exitflag, output = asd(outcomecalc, budgetvec3, args=args, xmin=budgetlower, xmax=budgethigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
        
        # Check that targets are still met
        targetsmet = moneycalc(budgetvec4, **args)
        if targetsmet: budgetvec5 = dcp(budgetvec4) # Yes, keep them
        else: budgetvec5 = dcp(budgetvec3) # No, go back to previous version that we know worked
                
        # And finally, home in on a solution
        upperlim = 1.0
        lowerlim = 1.0/fundingchange
        while (upperlim-lowerlim>tolerance): # Keep looping until they converge to within "tolerance" of the budget
            fundingfactor = (upperlim+lowerlim)/2
            args['origbudgetdict'] = dcp(origbudgetdict[:]*args['totalbudget']/origbudgetdict[:].sum())
            
            targetsmet = moneycalc(budgetvec5*fundingfactor, **args)
            printv('Current funding factor (low, high): %f (%f, %f)' % (fundingfactor, lowerlim, upperlim), 4, verbose)
            if targetsmet: upperlim=fundingfactor
            else: lowerlim=fundingfactor
        budgetvecfinal = budgetvec5*upperlim # Final budget is new upper limit
        
    ## Tidy up -- WARNING, need to think of a way to process multiple inds
    orig = moneycalc(budgetvec0, outputresults=True, **args)
    new = moneycalc(budgetvecfinal, outputresults=True, **args)
    orig.name = 'Current allocation' # WARNING, is this really the best way of doing it?
    new.name = 'Optimal allocation'
    tmpresults = [orig, new]
    
    multires = Multiresultset(resultsetlist=tmpresults, name='minmoney-%s-%s' % (parsetname, progsetname))
    
    for k,key in enumerate(multires.keys): # WARNING, this is ugly
        multires.budgetyears[key] = tmpresults[k].budgetyears
    
    optim.resultsref = multires.uid # Store the reference for this result
    
    return multires