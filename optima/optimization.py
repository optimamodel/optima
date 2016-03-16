"""
Functions for running optimizations.

Version: 2016feb07
"""

from optima import OptimaException, Multiresultset, Programset, asd, runmodel, getresults # Main functions
from optima import printv, dcp, odict, findinds, today, getdate, uuid, objrepr, isnumber # Utilities
from numpy import zeros, arange, maximum, array, inf

# Define global parameters that shouldn't really matter
infmoney = 1e9 # Effectively infinite money


## TEMP define a default budget
tmpdefaultbudget = odict({u'MSM programs': 1000.0, u'HTC': 11015092.0, u'VMMC': 3650750.0, u'Other care': 1000, u'PMTCT': 10663079.0, u'SBCC': 1504986.0, u'MGMT': 1000, u'ART': 69209158.0, u'FSW programs': 1000})
tmpdefaultbudget = tmpdefaultbudget.sort([u'PMTCT', u'VMMC', u'SBCC', u'FSW programs', u'MSM programs', u'HTC', u'Other care', u'MGMT', u'ART'])

################################################################################################################################################
### The container class
################################################################################################################################################
class Optim(object):
    ''' An object for storing an optimization '''

    def __init__(self, project=None, name='default', objectives=None, constraints=None, parsetname=None, progsetname=None):
        if project is None:     raise OptimaException('To create an optimization, you must supply a project')
        if parsetname is None:  parsetname = 0 # If none supplied, assume defaults
        if progsetname is None: progsetname = 0
        self.name         = name # Name of the parameter set, e.g. 'default'
        self.uid          = uuid() # ID
        self.project      = project # Store pointer for the project, if available
        self.created      = today() # Date created
        self.modified     = today() # Date modified
        self.parsetname   = parsetname # Parameter set name
        self.progsetname  = progsetname # Program set name
        self.objectives   = objectives # List of dicts holding Parameter objects -- only one if no uncertainty
        self.constraints  = constraints # List of populations
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


    def optimize(self, name=None, parsetname=None, progsetname=None, inds=0, maxiters=1000, maxtime=None, verbose=2, stoppingfunc=None, method='asd', debug=False):
        ''' And a little wrapper for optimize() -- WARNING, probably silly to have this at all '''
        if name is None: name='default'
        multires = optimize(which=self.objectives['which'], project=self.project, optim=self, inds=inds, maxiters=maxiters, maxtime=maxtime, verbose=verbose, stoppingfunc=stoppingfunc, method=method, debug=debug)
        multires.name = 'optim-'+name # Multires might be None if couldn't meet targets
        return multires





################################################################################################################################################
### Helper functions
################################################################################################################################################

def defaultobjectives(project=None, progset=None, which='outcomes', verbose=2):
    """
    Define default objectives for the optimization. Some objectives are shared
    between outcome and money minimizations, while others are different. However,
    outcome minimization is performed as part of money minimization, so it's useful
    to keep all the keys for both. Still, ugly.

    Version: 2016feb03
    """

    printv('Defining default objectives...', 3, verbose=verbose)

    if type(progset)==Programset:
        try: defaultbudget = sum(progset.getdefaultbudget()[:])
        except: defaultbudget = sum(tmpdefaultbudget[:])
    elif type(project)==Programset: # Not actually a project, but proceed anyway
        try: defaultbudget = sum(project.getdefaultbudget()[:])
        except: defaultbudget = sum(tmpdefaultbudget[:])
    elif project is not None:
        if progset is None: progset = 0
        try: defaultbudget = sum(project.progsets[progset].getdefaultbudget()[:])
        except: defaultbudget = sum(tmpdefaultbudget[:])
        printv('defaultobjectives() did not get a progset input, so using default budget of %0.0f' % defaultbudget, 2, verbose)
    else:
        defaultbudget = 1e6 # If can't find programs
        printv('defaultobjectives() did not get a progset input, so using default budget of %0.0f' % defaultbudget, 2, verbose)

    objectives = odict() # Dictionary of all objectives
    objectives['which'] = which
    objectives['keys'] = ['death', 'inci'] # Define valid keys
    objectives['keylabels'] = {'death':'Deaths', 'inci':'New infections'} # Define key labels
    if which in ['outcome', 'outcomes']:
        objectives['base'] = None # "Baseline year to compare outcomes to"
        objectives['start'] = 2017 # "Year to begin optimization"
        objectives['end'] = 2030 # "Year to project outcomes to"
        objectives['budget'] = defaultbudget # "Annual budget to optimize"
        objectives['deathweight'] = 5 # "Relative weight per death"
        objectives['inciweight'] = 1 # "Relative weight per new infection"
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


def defaultconstraints(project=None, progset=None, which='outcomes', verbose=2):
    """
    Define constraints for minimize outcomes optimization: at the moment, just
    total budget constraints defned as a fraction of current spending. Fixed costs
    are treated differently, and ART is hard-coded to not decrease.

    Version: 2016feb03
    """

    printv('Defining default constraints...', 3, verbose=verbose)

    if type(progset)==Programset: pass
    elif type(project)==Programset: progset = project
    elif project is not None:
        if progset is None: progset = 0
        progset = project.progsets[progset]
        printv('defaultconstraints() did not get a progset input, so using default', 2, verbose)

    else:
        raise OptimaException('To define constraints, you must supply a program set as an input')

    constraints = odict() # Dictionary of all constraints -- WARNING, change back to odict!
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







def constrainbudget(origbudget=None, budgetvec=None, totalbudget=None, budgetlims=None, optiminds=None, tolerance=1e-2, overalltolerance=1.0, outputtype=None):
    """ Take an unnormalized/unconstrained budgetvec and normalize and constrain it """

    # Prepare this budget for later scaling and the like
    constrainedbudget = dcp(origbudget)

    # Calculate the current total budget
    currenttotal = sum(constrainedbudget[:]) # WARNING, assumes it's an odict
    scaleratio = totalbudget/float(currenttotal) # Calculate the ratio between the original budget and the supplied budget

    # Calculate a uniformly scaled budget
    rescaledbudget = dcp(constrainedbudget)
    for key in rescaledbudget.keys(): rescaledbudget[key] *= scaleratio # This is the original budget scaled to the total budget
    if abs(sum(rescaledbudget[:])-totalbudget)>overalltolerance:
        errormsg = 'constrainbudget(): rescaling budget failed (%f != %f)' % (sum(rescaledbudget[:]), totalbudget)
        raise OptimaException(errormsg)

    # Calculate the minimum amount that can be spent on the fixed costs
    rescaledminfixed = dcp(rescaledbudget) # This is the rescaled budget, but with the minimum fixed costs -- should be <= totalbudget
    proginds = arange(len(origbudget)) # Array of all allowable indices
    fixedinds = array([p for p in proginds if p not in optiminds]) # WARNING, weird way of getting the complement of optiminds
    minfixed = 0.0
    for ind in fixedinds:
        rescaledminfixed[ind] = rescaledbudget[ind]*budgetlims['min'][ind]
        minfixed += rescaledminfixed[ind]

    # Calculate the total amount available for the optimizable programs
    optimbudget = totalbudget - minfixed
    optimscaleratio = optimbudget/float(sum(budgetvec)) # If totalbudget=sum(origbudget) and fixed cost lower limits are 1, then optimscaleratio=1

    # Scale the supplied budgetvec to meet this available amount
    scaledbudgetvec = dcp(budgetvec*optimscaleratio)
    if abs(sum(scaledbudgetvec)-optimbudget)>overalltolerance:
        errormsg = 'constrainbudget(): rescaling budget failed (%f != %f)' % (sum(scaledbudgetvec), optimbudget)
        raise OptimaException(errormsg)

    # Calculate absolute limits from relative limits
    abslimits = dcp(budgetlims)
    for pind in proginds:
        if abslimits['min'][pind] is None: abslimits['min'][pind] = 0
        if abslimits['max'][pind] is None: abslimits['max'][pind] = inf
    for oi,oind in enumerate(optiminds): # Don't worry about non-optimizable programs at this point -- oi = 0,1,2,3; oind = e.g. 0, 1, 4, 8
        # Fully-relative limits (i.e. scale according to total spend).
        abslimits['min'][oind] *= rescaledbudget[oind]
        abslimits['max'][oind] *= rescaledbudget[oind]

#        # Semi-relative limits. Note: Has issues, but is left here for posterity.
#        if scaleratio<1:
#            abslimits['min'][oind] *= rescaledbudget[oind] # If total budget is less, scale down the lower limit...
#            abslimits['max'][oind] *= origbudget[oind] # ...but keep the upper limit in absolute terms
#        elif scaleratio>=1:
#            abslimits['min'][oind] *= origbudget[oind] # If the total budget is more, keep the absolute original lower limit...
#            abslimits['max'][oind] *= rescaledbudget[oind] # ...but scale up the upper limit

    # Apply constraints on optimizable parameters
    noptimprogs = len(optiminds) # Number of optimizable programs
    limlow = zeros(noptimprogs, dtype=bool)
    limhigh = zeros(noptimprogs, dtype=bool)
    for oi,oind in enumerate(optiminds):
        if scaledbudgetvec[oi] <= abslimits['min'][oind]:
            scaledbudgetvec[oi] = abslimits['min'][oind]
            limlow[oi] = True
        if scaledbudgetvec[oi] >= abslimits['max'][oind]:
            scaledbudgetvec[oi] = abslimits['max'][oind]
            limhigh[oi] = True

    # Too high
    count = 0
    countmax = 1e4
    while sum(scaledbudgetvec) > optimbudget+tolerance:
        count += 1
        if count>countmax: raise OptimaException('Tried %i times to fix budget and failed! (wanted: %g; actual: %g' % (count, optimbudget, sum(scaledbudgetvec)))
        overshoot = sum(scaledbudgetvec) - optimbudget
        toomuch = sum(scaledbudgetvec[~limlow]) / float((sum(scaledbudgetvec[~limlow]) - overshoot))
        for oi,oinds in enumerate(optiminds):
            if not(limlow[oi]):
                proposed = scaledbudgetvec[oi] / float(toomuch)
                if proposed <= abslimits['min'][oind]:
                    proposed = abslimits['min'][oind]
                    limlow[oi] = True
                scaledbudgetvec[oi] = proposed

    # Too low
    while sum(scaledbudgetvec) < optimbudget-tolerance:
        count += 1
        if count>countmax: raise OptimaException('Tried %i times to fix budget and failed! (wanted: %g; actual: %g' % (count, optimbudget, sum(scaledbudgetvec)))
        undershoot = optimbudget - sum(scaledbudgetvec)
        toolittle = (sum(scaledbudgetvec[~limhigh]) + undershoot) / float(sum(scaledbudgetvec[~limhigh]))
        for oi,oinds in enumerate(optiminds):
            if not(limhigh[oi]):
                proposed = scaledbudgetvec[oi] * toolittle
                if proposed >= abslimits['max'][oind]:
                    proposed = abslimits['max'][oind]
                    limhigh[oi] = True
                scaledbudgetvec[oi] = proposed

    # Reconstruct the budget odict using the rescaled budgetvec and the rescaled original amount
    constrainedbudget = dcp(rescaledminfixed) # This budget has the right fixed costs
    for oi,oind in enumerate(optiminds):
        constrainedbudget[oind] = scaledbudgetvec[oi]
    if abs(sum(constrainedbudget[:])-totalbudget)>overalltolerance:
        errormsg = 'constrainbudget(): final budget amounts differ (%f != %f)' % (sum(constrainedbudget[:]), totalbudget)
        raise OptimaException(errormsg)

    # Optionally return the calculated upper and lower limits as well as the original budget and vector
    constrainedbudgetvec = dcp(constrainedbudget[optiminds])
    if outputtype=='odict':
        return constrainedbudget
    elif outputtype=='vec':
        return constrainedbudgetvec
    elif outputtype=='full':
        lowerlim = dcp(abslimits['min'][optiminds])
        upperlim = dcp(abslimits['min'][optiminds])
        return constrainedbudget, constrainedbudgetvec, lowerlim, upperlim
    else:
        raise OptimaException('constrainbudget(): must specify an output type of "odict", "vec", or "full"; you specified "%s"' % outputtype)




################################################################################################################################################
### The main meat of the matter
################################################################################################################################################

def objectivecalc(budgetvec=None, which=None, project=None, parset=None, progset=None, objectives=None, constraints=None, totalbudget=None, optiminds=None, origbudget=None, tvec=None, outputresults=False, debug=False, verbose=2):
    ''' Function to evaluate the objective for a given budget vector (note, not time-varying) '''

    # Validate input
    arglist = [budgetvec, which, parset, progset, objectives, totalbudget, constraints, optiminds, origbudget, tvec]
    if any([arg is None for arg in arglist]):  # WARNING, this kind of obscures which of these is None -- is that ok? Also a little too hard-coded...
        raise OptimaException('outcomecalc() requires which, budgetvec, parset, progset, objectives, totalbudget, constraints, optiminds, origbudget, tvec as inputs at minimum; argument %i is None' % arglist.index(None))
    if which=='outcome': which='outcomes' # I never remember which it's supposed to be, so let's fix it here
    if which not in ['outcomes','money']:
        errormsg = 'optimize(): "which" must be "outcomes" or "money"; you entered "%s"' % which
        raise OptimaException(errormsg)

    # Normalize budgetvec and convert to budget -- WARNING, is there a better way of doing this?
    constrainedbudget = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, budgetlims=constraints, optiminds=optiminds, outputtype='odict')

    # Run model
    thiscoverage = progset.getprogcoverage(budget=constrainedbudget, t=objectives['start'], parset=parset)
    thisparsdict = progset.getpars(coverage=thiscoverage, t=objectives['start'], parset=parset)
    results = runmodel(pars=thisparsdict, project=project, parset=parset, progset=progset, tvec=tvec, verbose=0)

    # Figure out which indices to use
    initialind = findinds(results.tvec, objectives['start'])
    finalind = findinds(results.tvec, objectives['end'])
    if which=='money': baseind = findinds(results.tvec, objectives['base']) # Only used for money minimization
    if which=='outcomes': indices = arange(initialind, finalind) # Only used for outcomes minimization

    ## Here, we split depending on whether it's a outcomes or money minimization:
    if which=='outcomes':
        # Calculate outcome
        outcome = 0 # Preallocate objective value
        for key in objectives['keys']:
            thisweight = objectives[key+'weight'] # e.g. objectives['inciweight']
            thisoutcome = results.main['num'+key].tot[0][indices].sum() # the instantaneous outcome e.g. objectives['numdeath'] -- 0 is since best
            outcome += thisoutcome*thisweight*results.dt # Calculate objective

        # Output results
        if outputresults:
            results.outcome = outcome
            results.budgetyears = [objectives['start']] # WARNING, this is ugly, should be made less kludgy
            results.budget = constrainedbudget # Convert to budget
            output = results
        else:
            output = outcome

    elif which=='money':
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
            if targetfrac[key] is not None:
                target[key] = float(baseline[key]*(1-targetfrac[key]))
                if final[key] > target[key]: targetsmet = False # Targets are NOT met
            else: target[key] = -1 # WARNING, must be a better way of showing no defined objective

        # Output results
        if outputresults:
            results.outcomes = odict([('baseline',baseline), ('final',final), ('target',target), ('targetfrac',targetfrac)])
            results.budgetyears = [objectives['start']] # WARNING, this is ugly, should be made less kludgy
            results.budget = constrainedbudget # Convert to budget
            results.targetsmet = targetsmet
            output = results
        else:
            summary = 'Baseline: %0.0f %0.0f | Target: %0.0f %0.0f | Final: %0.0f %0.0f' % tuple(baseline.values()+target.values()+final.values())
            output = (targetsmet, summary)

    return output









def optimize(which=None, project=None, optim=None, inds=0, maxiters=1000, maxtime=180, verbose=2, stoppingfunc=None, method='asd', debug=False):
    '''
    The standard Optima optimization function: minimize outcomes for a fixed total budget.

    Version: 1.2 (2016feb07)
    '''

    ## Input validation
    if which=='outcome': which='outcomes' # I never remember which it's supposed to be, so let's fix it here
    if which not in ['outcomes','money']:
        errormsg = 'optimize(): "which" must be "outcomes" or "money"; you entered "%s"' % which
        raise OptimaException(errormsg)
    if None in [project, optim]: raise OptimaException('minoutcomes() requires project and optim arguments at minimum')
    printv('Running %s optimization...' % which, 1, verbose)

    # Shorten things stored in the optimization -- WARNING, not sure if this is consistent with other functions
    parset  = project.parsets[optim.parsetname] # Link to the original parameter set
    progset = project.progsets[optim.progsetname] # Link to the original parameter set
    lenparlist = len(parset.pars)

    # Process inputs
    if not optim.objectives['budget']: # Handle 0 or None -- WARNING, temp?
        try: optim.objectives['budget'] = sum(progset.getdefaultbudget()[:])
        except: optim.objectives['budget'] = sum(tmpdefaultbudget[:])
    if isnumber(inds): inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(lenparlist)
    if max(inds)>lenparlist: raise OptimaException('Index %i exceeds length of parameter list (%i)' % (max(inds), lenparlist+1))
    tvec = project.settings.maketvec(end=optim.objectives['end']) # WARNING, this could be done better most likely
    if not progset.readytooptimize():
        detail_costcov = progset.hasallcostcovpars(detail=True)
        detail_covout = progset.hasallcovoutpars(detail=True)
        errormsg = 'The program set that you provided does not have all the required cost-coverage and/or coverage outcome parameters! Parameters are missing from:\n%s' % ((detail_costcov+detail_covout))
        raise OptimaException(errormsg)

    # Run outcomes minimization
    if which=='outcomes':
        multires = minoutcomes(project=project, optim=optim, inds=inds, tvec=tvec, verbose=verbose, maxtime=maxtime, maxiters=maxiters)

    # Run money minimization
    elif which=='money':
        multires = minmoney(project=project, optim=optim, inds=inds, tvec=tvec, verbose=verbose, maxtime=maxtime, maxiters=maxiters, fundingchange=1.2)

    return multires






def minoutcomes(name=None, project=None, optim=None, inds=None, tvec=None, verbose=None, maxtime=None, maxiters=None):
    ''' Split out minimize outcomes '''

    ## Handle budget and remove fixed costs
    parset  = project.parsets[optim.parsetname] # Link to the original parameter set
    progset = project.progsets[optim.progsetname] # Link to the original parameter set
    totalbudget = dcp(optim.objectives['budget'])
    try: origbudget = dcp(progset.getdefaultbudget())
    except: origbudget = dcp(tmpdefaultbudget)
    optiminds = findinds(progset.optimizable())
    budgetvec = origbudget[:][optiminds] # Get the original budget vector
    xmin = zeros(len(budgetvec))

    ## Constrain the budget
    constrainedbudget, constrainedbudgetvec, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')

    ## Actually run the optimization
    # for ind in inds: # WARNING, kludgy -- should be a loop!
    thisparset = dcp(parset) # WARNING, kludge because some later functions expect parset instead of pars
    try: thisparset.pars = [thisparset.pars[inds[0]]] # Turn into a list -- WARNING
    except: raise OptimaException('Could not load parameters %i from parset %s' % (inds, parset.name))
    args = {'which':'outcomes', 'project':project, 'parset':thisparset, 'progset':progset, 'objectives':optim.objectives, 'constraints':optim.constraints, 'totalbudget':totalbudget, 'optiminds':optiminds, 'origbudget':origbudget, 'tvec':tvec, 'verbose':verbose}
    budgetvecnew, fval, exitflag, output = asd(objectivecalc, constrainedbudgetvec, args=args, xmin=xmin, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)

    ## Tidy up -- WARNING, need to think of a way to process multiple inds
    constrainedbudgetnew, constrainedbudgetvecnew, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvecnew, totalbudget=totalbudget, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')
    orig = objectivecalc(constrainedbudgetvec, outputresults=True, debug=False, **args)
    new = objectivecalc(constrainedbudgetvecnew, outputresults=True, debug=False, **args)
    orig.name = 'Current allocation' # WARNING, is this really the best way of doing it?
    new.name = 'Optimal allocation'
    tmpresults = [orig, new]

    # Output
    multires = Multiresultset(resultsetlist=tmpresults, name='optim-%s' % name)
    for k,key in enumerate(multires.keys): multires.budgetyears[key] = tmpresults[k].budgetyears # WARNING, this is ugly
    multires.improvement = [output.fval] # Store full function evaluation information -- wrap in list for future multi-runs
    optim.resultsref = multires.name # Store the reference for this result

    return multires






def minmoney(name=None, project=None, optim=None, inds=None, tvec=None, verbose=None, maxtime=None, maxiters=None, fundingchange=1.2, tolerance=1e-2):
    '''
    A function to minimize money for a fixed objective. Note that it calls minoutcomes() in the process.

    Version: 2016feb07
    '''

    ## Handle budget and remove fixed costs
    parset  = project.parsets[optim.parsetname] # Link to the original parameter set
    progset = project.progsets[optim.progsetname] # Link to the original parameter set
    totalbudget = dcp(optim.objectives['budget'])
    origtotalbudget = totalbudget
    try: origbudget = dcp(progset.getdefaultbudget())
    except: origbudget = dcp(tmpdefaultbudget)
    optiminds = findinds(progset.optimizable())
    budgetvec = origbudget[:][optiminds] # Get the original budget vector
    origbudgetvec = dcp(budgetvec)
    xmin = zeros(len(budgetvec))

    ## Constrain the budget
    thisparset = dcp(parset) # WARNING, kludge because some later functions expect parset instead of pars
    try: thisparset.pars = [thisparset.pars[inds[0]]] # Turn into a list -- WARNING
    except: raise OptimaException('Could not load parameters %i from parset %s' % (inds, parset.name))

    # Define arguments for ASD
    args = {'which':'money', 'project':project, 'parset':thisparset, 'progset':progset, 'objectives':optim.objectives, 'constraints':optim.constraints, 'totalbudget':totalbudget, 'optiminds':optiminds, 'origbudget':origbudget, 'tvec':tvec, 'verbose':verbose}


    ##########################################################################################################################
    ## Loop through different budget options
    ##########################################################################################################################

    terminate = False

    # First, try infinite money
    args['totalbudget'] = 1e9
    targetsmet, summary = objectivecalc(budgetvec, **args)
    if not(targetsmet): 
        terminate = True
        printv("Infinite allocation can't meet targets:\n%s" % summary, 1, verbose) # WARNING, this shouldn't be an exception, something more subtle
    else: printv("Infinite allocation meets targets, as expected; proceeding...", 2, verbose)

    # Next, try no money
    args['totalbudget'] = 1e-3
    targetsmet, summary = objectivecalc(budgetvec, **args)
    if targetsmet: 
        terminate = True
        printv("Even zero allocation meets targets:\n%s" % summary, 1, verbose)
    else: printv("Zero allocation doesn't meet targets, as expected; proceeding...", 2, verbose)

    # If those did as expected, proceed with checking what's actually going on to set objective weights for minoutcomes() function
    args['totalbudget'] = origtotalbudget
    results = objectivecalc(budgetvec, outputresults=True, **args)
    absreductions = odict() # Absolute reductions requested, for setting weights
    for key in optim.objectives['keys']:
        if optim.objectives[key+'frac'] is not None:
            absreductions[key] = float(results.outcomes['baseline'][key]*optim.objectives[key+'frac']) # e.g. 1000 deaths * 40% reduction = 400 deaths
        else:
            absreductions[key] = 1e9 # A very very large number to effectively turn this off -- WARNING, not robust
    weights = dcp(absreductions) # Copy this, since will be modifying it -- not strictly necessary but could come in handy
    weights = 1.0/weights[:] # Relative weights are inversely proportional to absolute reductions -- e.g. asking for a reduction of 100 deaths and 400 new infections means 1 death = 4 new infections
    weights /= weights.min() # Normalize such that the lowest weight is 1; arbitrary, but could be useful
    for k,key in enumerate(optim.objectives['keys']):
       optim.objectives[key+'weight'] = maximum(weights[k],0) # Reset objective weights according to the reduction required -- don't let it go below 0, though

    # If infinite or zero money met objectives, don't bother proceeding
    if terminate:
        constrainedbudgetvec = budgetvec * args['totalbudget']
        newtotalbudget = args['totalbudget']
        fundingfactor = args['totalbudget']

    else:
        ##########################################################################################################################
        ## Now run an optimization on the current budget
        ##########################################################################################################################
    
        args['totalbudget'] = origtotalbudget # Calculate new total funding
        args['which'] = 'outcomes' # Switch back to outcome minimization -- WARNING, there must be a better way of doing this
        budgetvec1, fval, exitflag, output = asd(objectivecalc, budgetvec, args=args, xmin=xmin, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
        budgetvec2 = constrainbudget(origbudget=origbudget, budgetvec=budgetvec1, totalbudget=args['totalbudget'], budgetlims=optim.constraints, optiminds=optiminds, outputtype='vec')
    
        # See if objectives are met
        args['which'] = 'money' # Switch back to money minimization
        targetsmet, summary = objectivecalc(budgetvec2, **args)
        fundingfactor = 1.0
    
        # If targets are met, scale down until they're not -- this loop will be skipped entirely if targets not currently met
        while targetsmet:
            fundingfactor /= fundingchange
            args['totalbudget'] = origtotalbudget * fundingfactor
            targetsmet, summary = objectivecalc(budgetvec2, **args)
            printv('Current funding factor: %f (%s)' % (fundingfactor, summary), 2, verbose)
    
        # If targets are not met, scale up until they are -- this will always be run at least once after the previous loop
        while not(targetsmet):
            fundingfactor *= fundingchange
            args['totalbudget'] = origtotalbudget * fundingfactor
            targetsmet, summary = objectivecalc(budgetvec2, **args)
            printv('Current funding factor: %f (%s)' % (fundingfactor, summary), 2, verbose)
    
    
        ##########################################################################################################################
        # Re-optimize based on this fairly close allocation
        ##########################################################################################################################
        args['which'] = 'outcomes'
        budgetvec3, fval, exitflag, output = asd(objectivecalc, budgetvec, args=args, xmin=xmin, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
        budgetvec4 = constrainbudget(origbudget=origbudget, budgetvec=budgetvec1, totalbudget=args['totalbudget'], budgetlims=optim.constraints, optiminds=optiminds, outputtype='vec')
    
        # Check that targets are still met
        args['which'] = 'money'
        targetsmet, summary = objectivecalc(budgetvec4, **args)
        if targetsmet: budgetvec5 = dcp(budgetvec4) # Yes, keep them
        else: budgetvec5 = dcp(budgetvec2) # No, go back to previous version that we know worked
        newtotalbudget = sum(budgetvec5)
    
        # And finally, home in on a solution
        upperlim = 1.0
        lowerlim = 1.0/fundingchange
        while (upperlim-lowerlim>tolerance): # Keep looping until they converge to within "tolerance" of the budget
            fundingfactor = (upperlim+lowerlim)/2.0
            args['totalbudget'] = newtotalbudget * fundingfactor
            targetsmet, summary = objectivecalc(budgetvec5, **args)
            printv('Current funding factor (low, high): %f (%f, %f)' % (fundingfactor, lowerlim, upperlim), 2, verbose)
            if targetsmet: upperlim = fundingfactor
            else:          lowerlim = fundingfactor
        constrainedbudget, constrainedbudgetvec, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec5, totalbudget=newtotalbudget*upperlim, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')

    ## Tidy up -- WARNING, need to think of a way to process multiple inds
    args['totalbudget'] = origtotalbudget
    orig = objectivecalc(origbudgetvec, outputresults=True, **args)
    args['totalbudget'] = newtotalbudget * fundingfactor
    new = objectivecalc(constrainedbudgetvec, outputresults=True, **args)
    orig.name = 'Current allocation' # WARNING, is this really the best way of doing it?
    new.name = 'Optimal allocation'
    tmpresults = [orig, new]
    multires = Multiresultset(resultsetlist=tmpresults, name='optim-%s' % name)
    for k,key in enumerate(multires.keys): multires.budgetyears[key] = tmpresults[k].budgetyears # WARNING, this is ugly
    optim.resultsref = multires.name # Store the reference for this result

    return multires
