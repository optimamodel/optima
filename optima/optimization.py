"""
Functions for running optimizations.

Version: 2017mar03
"""

from optima import OptimaException, Link, Multiresultset, Programset, asd, runmodel, getresults # Main functions
from optima import printv, dcp, odict, findinds, today, getdate, uuid, objrepr, promotetoarray # Utilities
from numpy import zeros, arange, maximum, array, inf, isfinite, argmin, argsort
from numpy.random import random

################################################################################################################################################
### The container class
################################################################################################################################################
class Optim(object):
    ''' An object for storing an optimization '''

    def __init__(self, project=None, name='default', objectives=None, constraints=None, parsetname=None, progsetname=None):
        if project is None:     raise OptimaException('To create an optimization, you must supply a project')
        if parsetname is None:  parsetname = -1 # If none supplied, assume defaults
        if progsetname is None: progsetname = -1
        if objectives is None:  objectives = defaultobjectives(project=project, progset=progsetname, verbose=0)
        if constraints is None: constraints = defaultconstraints(project=project, progset=progsetname, verbose=0)
        self.name         = name # Name of the parameter set, e.g. 'default'
        self.uid          = uuid() # ID
        self.projectref   = Link(project) # Store pointer for the project, if available
        self.created      = today() # Date created
        self.modified     = today() # Date modified
        self.parsetname   = parsetname # Parameter set name
        self.progsetname  = progsetname # Program set name
        self.objectives   = objectives # List of dicts holding Parameter objects -- only one if no uncertainty
        self.constraints  = constraints # List of populations
        self.resultsref   = None # Store pointer to results


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
        if self.resultsref is not None and self.projectref() is not None:
            results = getresults(project=self.projectref(), pointer=self.resultsref)
            return results
        else:
            print('WARNING, no results associated with this parameter set')
            return None


    def optimize(self, name=None, parsetname=None, progsetname=None, maxiters=1000, maxtime=None, verbose=2, stoppingfunc=None, 
                 method='asd', die=False, origbudget=None, ccsample='best', randseed=None, **kwargs):
        ''' And a little wrapper for optimize() -- WARNING, probably silly to have this at all '''
        if name is None: name='default'
        multires = optimize(which=self.objectives['which'], project=self.projectref(), optim=self, maxiters=maxiters, 
                            maxtime=maxtime, verbose=verbose, stoppingfunc=stoppingfunc, method=method, die=die, 
                            origbudget=origbudget, ccsample=ccsample, randseed=randseed, **kwargs)
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
        except: raise OptimaException('Could not get default budget for optimization')
    elif type(project)==Programset: # Not actually a project, but proceed anyway
        try: defaultbudget = sum(project.getdefaultbudget()[:])
        except: raise OptimaException('Could not get default budget for optimization')
    elif project is not None:
        if progset is None: progset = -1 # Think it's OK to make this the default
        try: defaultbudget = sum(project.progsets[progset].getdefaultbudget()[:])
        except: raise OptimaException('Could not get default budget for optimization')
    else:
        defaultbudget = 0.0 # If can't find programs
        printv('defaultobjectives() did not get a project or progset, so setting budget to %0.0f' % defaultbudget, 2, verbose)
        
    objectives = odict() # Dictionary of all objectives
    objectives['which'] = which
    objectives['keys'] = ['death', 'inci'] # Define valid keys
    objectives['keylabels'] = {'death':'Deaths', 'inci':'New infections'} # Define key labels
    if which in ['outcome', 'outcomes']:
        objectives['base'] = None # "Baseline year to compare outcomes to"
        objectives['start'] = 2017 # "Year to begin optimization"
        objectives['end'] = 2030 # "Year to project outcomes to"
        objectives['budget'] = defaultbudget # "Annual budget to optimize"
        objectives['budgetscale'] = [1.] # "Scale factors to apply to budget"
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
        objectives['deathfrac'] = 0.25 # Fraction of deaths to avert
        objectives['incifrac'] = 0.25 # Fraction of incidence to avert
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
        if progset is None: progset = -1
        progset = project.progsets[progset]
        printv('defaultconstraints() did not get a progset input, so using default', 3, verbose)
    else:
        raise OptimaException('To define constraints, you must supply a program set as an input')

    # If no programs in the progset, return None
    if not(len(progset.programs)): return None
    
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
    if 'PMTCT' in constraints['min'].keys():
        constraints['min']['PMTCT'] = 1.0 # By default, don't let ART funding decrease

    return constraints







def constrainbudget(origbudget=None, budgetvec=None, totalbudget=None, budgetlims=None, optiminds=None, tolerance=1e-2, overalltolerance=1.0, outputtype=None):
    """ Take an unnormalized/unconstrained budgetvec and normalize and constrain it """

    # Prepare this budget for later scaling and the like
    constrainedbudget = dcp(origbudget)
    
    # Handle zeros
    if sum(constrainedbudget[:])==0: constrainedbudget[:] += tolerance
    if sum(budgetvec)==0:            budgetvec[:] += tolerance

    # Calculate the current total budget
    currenttotal = sum(constrainedbudget[:]) # WARNING, assumes it's an odict
    scaleratio = totalbudget/float(currenttotal) # Calculate the ratio between the original budget and the supplied budget

    # Calculate a uniformly scaled budget
    rescaledbudget = dcp(constrainedbudget)
    for key in rescaledbudget.keys(): rescaledbudget[key] *= scaleratio # This is the original budget scaled to the total budget
    if abs(sum(rescaledbudget[:])-totalbudget)>overalltolerance:
        errormsg = 'rescaling budget failed (%f != %f)' % (sum(rescaledbudget[:]), totalbudget)
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
        errormsg = 'rescaling budget failed (%f != %f)' % (sum(scaledbudgetvec), optimbudget)
        raise OptimaException(errormsg)

    # Calculate absolute limits from relative limits
    abslimits = dcp(budgetlims)
    for pind in proginds:
        if abslimits['min'][pind] is None: abslimits['min'][pind] = 0
        if abslimits['max'][pind] is None: abslimits['max'][pind] = inf
    for oi,oind in enumerate(optiminds): # Don't worry about non-optimizable programs at this point -- oi = 0,1,2,3; oind = e.g. 0, 1, 4, 8
        # Fully-relative limits (i.e. scale according to total spend).
        if isfinite(abslimits['min'][oind]): abslimits['min'][oind] *= rescaledbudget[oind]
        if isfinite(abslimits['max'][oind]): abslimits['max'][oind] *= rescaledbudget[oind]
        
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
        for oi,oind in enumerate(optiminds):
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
        for oi,oind in enumerate(optiminds):
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
        errormsg = 'final budget amounts differ (%f != %f)' % (sum(constrainedbudget[:]), totalbudget)
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
        raise OptimaException('must specify an output type of "odict", "vec", or "full"; you specified "%s"' % outputtype)




################################################################################################################################################
### The main meat of the matter
################################################################################################################################################

def outcomecalc(budgetvec=None, which=None, project=None, parset=None, progset=None, parsetname=None, progsetname=None, 
                objectives=None, constraints=None, totalbudget=None, optiminds=None, origbudget=None, tvec=None, 
                initpeople=None, outputresults=False, verbose=2, ccsample='best', doconstrainbudget=True):
    ''' Function to evaluate the objective for a given budget vector (note, not time-varying) '''

    # Set up defaults
    if which is None: which = objectives['which']
    if parsetname is None: parsetname = -1
    if progsetname is None: progsetname = -1
    if parset is None: parset  = project.parsets[parsetname] 
    if progset is None: progset = project.progsets[progsetname] 
    if objectives is None: objectives = defaultobjectives(project=project, progset=progset, which=which)
    if constraints is None: constraints = defaultconstraints(project=project, progset=progset, which=which)
    if totalbudget is None: totalbudget = objectives['budget']
    if origbudget is None: origbudget = progset.getdefaultbudget()
    if optiminds is None: optiminds = findinds(progset.optimizable())
    if budgetvec is None: budgetvec = dcp(origbudget[:][optiminds])
    if type(budgetvec)==odict: budgetvec = dcp(budgetvec[:][optiminds])
    
    # Validate input
    arglist = [budgetvec, which, parset, progset, objectives, totalbudget, constraints, optiminds, origbudget]
    if any([arg is None for arg in arglist]):  # WARNING, this kind of obscures which of these is None -- is that ok? Also a little too hard-coded...
        raise OptimaException('outcomecalc() requires which, budgetvec, parset, progset, objectives, totalbudget, constraints, optiminds, origbudget, tvec as inputs at minimum; argument %i is None' % arglist.index(None))
    if which=='outcome': which='outcomes' # I never remember which it's supposed to be, so let's fix it here
    if which not in ['outcomes','money']:
        errormsg = 'optimize(): "which" must be "outcomes" or "money"; you entered "%s"' % which
        raise OptimaException(errormsg)

    # Normalize budgetvec and convert to budget -- WARNING, is there a better way of doing this?
    if doconstrainbudget:
        constrainedbudget = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, budgetlims=constraints, optiminds=optiminds, outputtype='odict')
    else:
        constrainedbudget = dcp(origbudget)
        constrainedbudget[:] = budgetvec
    
    # Run model
    thiscoverage = progset.getprogcoverage(budget=constrainedbudget, t=objectives['start'], parset=parset, sample=ccsample)
    thisparsdict = progset.getpars(coverage=thiscoverage, t=objectives['start'], parset=parset, sample=ccsample)
    if initpeople is not None:
        tvec = project.settings.maketvec(start=objectives['start'], end=objectives['end'])
    results = runmodel(pars=thisparsdict, project=project, parset=parset, progset=progset, tvec=tvec, initpeople=initpeople, verbose=0, label=project.name+'-optim-outcomecalc')

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









def optimize(which=None, project=None, optim=None, maxiters=1000, maxtime=180, verbose=2, stoppingfunc=None, method='asd', 
             die=False, origbudget=None, ccsample='best', randseed=None, mc=3, label=None, **kwargs):
    '''
    The standard Optima optimization function: minimize outcomes for a fixed total budget.
    
    Arguments:
        which = 'outcome' or 'money'
        project = the project file
        optim = the optimization object
        maxiters = how many iterations to optimize for
        maxtime = how many secons to optimize for
        verbose = how much detail to provide
        stoppingfunc = a function called to decide on stopping
        method = 'asd', currently the only option
        die = whether or not to check things in detail
        origbudget = the budget to start from (if not supplied, use default
        ccsample = which sample of the cost curves to use (deprecated)
        randseed = optionally reset the seed
        mc = how many Monte Carlo iterations to run for (if -1, run other starting points but not MC)
        label = a string to append to error messages to make it clear where things went wrong

    Version: 1.3 (2017mar02)
    '''
    
    ## Input validation
    if which=='outcome': which='outcomes' # I never remember which it's supposed to be, so let's fix it here
    if which not in ['outcomes','money']:
        errormsg = '"which" must be "outcomes" or "money"; you entered "%s"' % which
        raise OptimaException(errormsg)
    if None in [project, optim]: raise OptimaException('minoutcomes() requires project and optim arguments at minimum')
    printv('Running %s optimization...' % which, 1, verbose)
    
    progset = project.progsets[optim.progsetname] # Link to the original parameter set
    
    # optim structure validation
    if not(hasattr(optim, 'objectives')) or optim.objectives is None:
        optim.objectives = defaultobjectives(project=project, progset=progset, which=which, verbose=verbose)
    if not(hasattr(optim, 'constraints')) or optim.constraints is None:
        optim.constraints = defaultconstraints(project=project, progset=progset, which=which, verbose=verbose)

    # Process inputs
    if not optim.objectives['budget']: # Handle 0 or None -- WARNING, temp?
        try: optim.objectives['budget'] = sum(progset.getdefaultbudget()[:])
        except:  raise OptimaException('Could not get default budget for optimization')
    tvec = project.settings.maketvec(end=optim.objectives['end']) # WARNING, this could be done better most likely
    if not progset.readytooptimize():
        detail_costcov = progset.hasallcostcovpars(detail=True)
        detail_covout = progset.hasallcovoutpars(detail=True)
        errormsg = 'The program set that you provided does not have all the required cost-coverage and/or coverage outcome parameters! Parameters are missing from:\n%s' % ((detail_costcov+detail_covout))
        raise OptimaException(errormsg)

    # Run outcomes minimization
    if which=='outcomes':
        multires = minoutcomes(project=project, optim=optim, tvec=tvec, verbose=verbose, maxtime=maxtime, maxiters=maxiters, 
                               origbudget=origbudget, ccsample=ccsample, randseed=randseed, mc=mc, label=label, die=die, **kwargs)

    # Run money minimization
    elif which=='money':
        multires = minmoney(project=project, optim=optim, tvec=tvec, verbose=verbose, maxtime=maxtime, maxiters=maxiters, 
                            fundingchange=1.2, ccsample=ccsample, randseed=randseed, **kwargs)

    return multires






def minoutcomes(project=None, optim=None, name=None, tvec=None, verbose=None, maxtime=None, maxiters=1000, 
                origbudget=None, ccsample='best', randseed=None, mc=3, label=None, die=False, **kwargs):
    ''' Split out minimize outcomes '''

    ## Handle budget and remove fixed costs
    if project is None or optim is None: raise OptimaException('An optimization requires both a project and an optimization object to run')
    parset  = project.parsets[optim.parsetname] # Link to the original parameter set
    progset = project.progsets[optim.progsetname] # Link to the original program set
    origtotalbudget = dcp(optim.objectives['budget']) # Should be a float, but dcp just in case
    if origbudget is not None:
        origbudget = dcp(origbudget)
    else:
        try: origbudget = dcp(progset.getdefaultbudget())
        except: raise OptimaException('Could not get default budget for optimization')
    
    optimizable = progset.optimizable()
    optiminds = findinds(optimizable)
    optimkeys = [key for k,key in enumerate(origbudget.keys()) if optimizable[k]]
    budgetvec = origbudget[:][optiminds] # Get the original budget vector
    nprogs = len(origbudget[:]) # Number of programs total
    noptimprogs = len(budgetvec) # Number of optimizable programs
    xmin = zeros(noptimprogs)
    if label is None: label = ''
    
    # Calculate the initial people distribution
    results = runmodel(pars=parset.pars, project=project, parset=parset, progset=progset, tvec=tvec, keepraw=True, verbose=0, label=project.name+'-minoutcomes')
    initialind = findinds(results.raw[0]['tvec'], optim.objectives['start'])
    initpeople = results.raw[0]['people'][:,:,initialind] # Pull out the people array corresponding to the start of the optimization -- there shouldn't be multiple raw arrays here

    # Calculate original things
    constrainedbudgetorig, constrainedbudgetvecorig, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=origtotalbudget, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')
    
    # Set up arguments which are shared between outcomecalc and asd
    args = {'which':'outcomes', 
            'project':project, 
            'parset':parset, 
            'progset':progset, 
            'objectives':optim.objectives, 
            'constraints':optim.constraints, 
            'totalbudget':origtotalbudget, # Complicated, see below
            'optiminds':optiminds, 
            'origbudget':origbudget, 
            'tvec':tvec, 
            'ccsample':ccsample, 
            'verbose':verbose, 
            'initpeople':initpeople} # Complicated; see below
    
    # Set up extremes
    extremebudgets = odict()
    extremebudgets['Current']    = zeros(nprogs)
    for p in optiminds:  extremebudgets['Current'][p] = constrainedbudgetvecorig[p] # Must be a better way of doing this :(
    extremebudgets['Zero']     = zeros(nprogs)
    extremebudgets['Infinite'] = origbudget[:]+project.settings.infmoney
    firstkeys = ['Current', 'Zero', 'Infinite'] # These are special, store them
    if mc: # Only run these if MC is being run
        for p,prog in zip(optiminds,optimkeys):
            extremebudgets[prog] = zeros(nprogs)
            extremebudgets[prog][p] = sum(constrainedbudgetvecorig)
    
    # Run extremes
    extremeresults  = odict()
    extremeoutcomes = odict()
    for key,exbudget in extremebudgets.items():
        if key=='Current': 
            args['initpeople'] = None # Do this so it runs for the full time series, and is comparable to the optimization result
            args['totalbudget'] = origbudget[:].sum() # Need to reset this since constraining the budget
            doconstrainbudget = True # This is needed so it returns the full budget odict, not just the budget vector
        else:
            args['initpeople'] = initpeople # Do this so saves a lot of time (runs twice as fast for all the budget scenarios)
            args['totalbudget'] = origtotalbudget
            doconstrainbudget = False
        extremeresults[key] = outcomecalc(exbudget, outputresults=True, doconstrainbudget=doconstrainbudget, **args)
        extremeresults[key].name = key
        extremeoutcomes[key] = extremeresults[key].outcome
    if mc: bestprogram = argmin(extremeoutcomes[:][len(firstkeys):])+len(firstkeys) # Don't include no funding or infinite funding examples
    
    # Print out results of the run
    if mc:
        printv('Budget scenario outcomes:', 2, verbose)
        besttoworst = argsort(extremeoutcomes[:])
        besttoworstkeys = [extremeoutcomes.keys()[i] for i in besttoworst]
        longestkey = -1
        for key in firstkeys+besttoworstkeys: longestkey = max(longestkey, len(key)) # Find the longest key
        for key in firstkeys: besttoworstkeys.remove(key) # Remove these from the list
        for key in firstkeys+besttoworstkeys:
            printv(('Outcome for %'+str(longestkey)+'s: %0.0f') % (key,extremeoutcomes[key]), 2, verbose)
    else:
        printv('Outcome for current budget (starting point): %0.0f' % extremeoutcomes['Current'], 2, verbose)
        printv('Outcome for infinite budget (best possible): %0.0f' % extremeoutcomes['Infinite'], 2, verbose)
        printv('Outcome for zero budget (worst possible):    %0.0f' % extremeoutcomes['Zero'], 2, verbose)
    
    # Check extremes -- not quite fair since not constrained but oh well
    if extremeoutcomes['Infinite'] >= extremeoutcomes['Zero']:
        errormsg = 'Infinite funding has a worse or identical outcome to no funding: %s vs. %s' % (extremeoutcomes['Infinite'], extremeoutcomes['Zero'])
        raise OptimaException(errormsg)
    for k,key in enumerate(extremeoutcomes.keys()):
        if extremeoutcomes[key] > extremeoutcomes['Zero']:
            errormsg = 'WARNING, funding for %s has a worse outcome than no funding: %s vs. %s' % (key, extremeoutcomes[key], extremeoutcomes['Zero'])
            if die: raise OptimaException(errormsg)
            else:   print(errormsg)
            
    ## Loop over budget scale factors
    tmpresults = odict()
    tmpimprovements = odict()
    tmpfullruninfo = odict()
    tmpresults['Current'] = extremeresults['Current'] # Include un-optimized original
    scalefactors = promotetoarray(optim.objectives['budgetscale']) # Ensure it's a list
    for scalefactor in scalefactors: 

        # Get the total budget & constrain it 
        totalbudget = origtotalbudget*scalefactor
        constrainedbudget, constrainedbudgetvec, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')
        args['totalbudget'] = totalbudget
        args['initpeople'] = initpeople # Set so only runs the part of the optimization required
        
        # Set up budgets to run
        if totalbudget: # Budget is nonzero, run
            allbudgetvecs = odict()
            allbudgetvecs['Current'] = dcp(constrainedbudgetvec)
            if mc: # If MC, run multiple
                bvzeros = zeros(noptimprogs)
                allbudgetvecs['Uniform'] = bvzeros + constrainedbudgetvec.mean() # Make it uniform
                if extremeoutcomes[bestprogram] < extremeoutcomes['Current']:
                    allbudgetvecs['Program (%s)' % extremebudgets.keys()[bestprogram]] = array([extremebudgets[bestprogram][i] for i in optiminds])  # Include all money going to one program, but only if it's better than the current allocation
                for i in range(mc): # For the remainder, do randomizations
                    randbudget = random(noptimprogs)
                    allbudgetvecs['Random %s' % (i+1)] = randbudget/randbudget.sum()*constrainedbudgetvec.sum()
            
            # Actually run the optimizations
            bestfval = inf # Value of outcome
            asdresults = odict()
            for k,key in enumerate(allbudgetvecs.keys()):
                printv('Running optimization "%s" (%i/%i) with maxtime=%s, maxiters=%s' % (key, k+1, len(allbudgetvecs), maxtime, maxiters), 2, verbose)
                if label: thislabel = '"'+label+'-'+key+'"'
                else: thislabel = '"'+key+'"'
                budgetvecnew, fvals, exitreason = asd(outcomecalc, allbudgetvecs[key], args=args, xmin=xmin, maxtime=maxtime, maxiters=maxiters, verbose=verbose, randseed=randseed, label=thislabel, **kwargs)
                constrainedbudgetnew, constrainedbudgetvecnew, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvecnew, totalbudget=totalbudget, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')
                asdresults[key] = {'budget':constrainedbudgetnew, 'fvals':fvals}
                if fvals[-1]<bestfval: 
                    bestkey = key # Reset key
                    bestfval = fvals[-1] # Reset fval
            
            ## Calculate outcomes
            args['initpeople'] = None # Set to None to get full results, not just from strat year
            new = outcomecalc(asdresults[bestkey]['budget'], outputresults=True, **args)
            if len(scalefactors)==1: new.name = 'Optimal' # If there's just one optimization, just call it optimal
            else: new.name = 'Optimal (%.0f%% budget)' % (scalefactor*100.) # Else, say what the budget is
            tmpresults[new.name] = new
            tmpimprovements[new.name] = asdresults[bestkey]['fvals']
            tmpfullruninfo[new.name] = asdresults # Store everything
        else:
            tmpresults['Optimal'] = dcp(tmpresults['Current']) # If zero budget, just copy current and rename
            tmpresults['Optimal'].name = 'Optimal' # Rename name to named name

    ## Output
    multires = Multiresultset(resultsetlist=tmpresults.values(), name='optim-%s' % new.name)
    for k,key in enumerate(multires.keys): multires.budgetyears[key] = tmpresults[k].budgetyears # WARNING, this is ugly
    multires.improvement = tmpimprovements # Store full function evaluation information -- only use last one
    multires.extremeoutcomes = extremeoutcomes # Store all of these
    multires.fullruninfo = tmpfullruninfo # And the budgets/outcomes for every different run
    multires.outcomes = odict() # Initialize
    for key in tmpimprovements.keys():
        multires.outcomes[key] = tmpimprovements[key][-1] # Get best value
    optim.resultsref = multires.name # Store the reference for this result
    try:
        multires.outcome = multires.outcomes['Optimal'] # Store these defaults in a convenient place
        multires.budget = multires.budgets['Optimal']
    except:
        multires.outcome = None
        multires.budget = None

    return multires






def minmoney(project=None, optim=None, name=None, tvec=None, verbose=None, maxtime=None, maxiters=1000, fundingchange=1.2, tolerance=1e-2, ccsample='best', randseed=None, **kwargs):
    '''
    A function to minimize money for a fixed objective. Note that it calls minoutcomes() in the process.

    Version: 2016feb07
    '''

    ## Handle budget and remove fixed costs
    if project is None or optim is None: raise OptimaException('An optimization requires both a project and an optimization object to run')
    parset  = project.parsets[optim.parsetname] # Link to the original parameter set
    progset = project.progsets[optim.progsetname] # Link to the original parameter set
    totalbudget = dcp(optim.objectives['budget'])
    origtotalbudget = totalbudget
    try: origbudget = dcp(progset.getdefaultbudget())
    except: raise OptimaException('Could not get default budget for optimization')
    optiminds = findinds(progset.optimizable())
    budgetvec = origbudget[:][optiminds] # Get the original budget vector
    origbudgetvec = dcp(budgetvec)
    xmin = zeros(len(budgetvec))

    # Define arguments for ASD
    args = {'which':'money', 
            'project':project, 
            'parset':parset, 
            'progset':progset, 
            'objectives':optim.objectives, 
            'constraints':optim.constraints, 
            'totalbudget':totalbudget, 
            'optiminds':optiminds, 
            'origbudget':origbudget, 
            'tvec':tvec, 
            'ccsample': ccsample, 
            'verbose':verbose}


    ##########################################################################################################################
    ## Loop through different budget options
    ##########################################################################################################################

    terminate = False

    # First, try infinite money
    args['totalbudget'] = project.settings.infmoney
    targetsmet, summary = outcomecalc(budgetvec, **args)
    infinitefailed = False
    if not(targetsmet): 
        terminate = True
        infinitefailed = True
        printv("Infinite allocation can't meet targets:\n%s" % summary, 1, verbose) # WARNING, this shouldn't be an exception, something more subtle
    else: printv("Infinite allocation meets targets, as expected; proceeding...\n(%s)\n" % summary, 2, verbose)

    # Next, try no money
    zerofailed = False
    if not terminate:
        args['totalbudget'] = 1e-3
        targetsmet, summary = outcomecalc(budgetvec, **args)
        if targetsmet: 
            terminate = True
            zerofailed = True
            printv("Even zero allocation meets targets:\n%s" % summary, 1, verbose)
        else: printv("Zero allocation doesn't meet targets, as expected; proceeding...\n(%s)\n" % summary, 2, verbose)

    # If those did as expected, proceed with checking what's actually going on to set objective weights for minoutcomes() function
    args['totalbudget'] = origtotalbudget
    results = outcomecalc(budgetvec, outputresults=True, **args)
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
        if zerofailed:
            constrainedbudgetvec = budgetvec * 0.0
            newtotalbudget = 0.0
            fundingfactor = 0.0
        if infinitefailed:
            fundingfactor = 100 # For plotting, don't make the factor infinite, just very large
            constrainedbudgetvec = budgetvec * fundingfactor
            newtotalbudget = totalbudget * fundingfactor

    else:
        ##########################################################################################################################
        ## Now run an optimization on the current budget
        ##########################################################################################################################
    
        args['totalbudget'] = origtotalbudget # Calculate new total funding
        args['which'] = 'outcomes' # Switch back to outcome minimization -- WARNING, there must be a better way of doing this
#        budgetvec1, fvals, exitreason = asd(outcomecalc, budgetvec, args=args, xmin=xmin, maxtime=maxtime, maxiters=maxiters, verbose=verbose, randseed=randseed, **kwargs)
        budgetvec2 = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=args['totalbudget'], budgetlims=optim.constraints, optiminds=optiminds, outputtype='vec')
    
        # See if objectives are met
        args['which'] = 'money' # Switch back to money minimization
        targetsmet, summary = outcomecalc(budgetvec2, **args)
        fundingfactor = 1.0
    
        # If targets are met, scale down until they're not -- this loop will be skipped entirely if targets not currently met
        while targetsmet:
            fundingfactor /= fundingchange
            args['totalbudget'] = origtotalbudget * fundingfactor
            targetsmet, summary = outcomecalc(budgetvec2, **args)
            printv('Scaling down budget %0.0f: current funding factor: %f (%s)' % (args['totalbudget'], fundingfactor, summary), 2, verbose)
    
        # If targets are not met, scale up until they are -- this will always be run at least once after the previous loop
        while not(targetsmet):
            fundingfactor *= fundingchange
            args['totalbudget'] = origtotalbudget * fundingfactor
            targetsmet, summary = outcomecalc(budgetvec2, **args)
            printv('Scaling up budget %0.0f: current funding factor: %f (%s)' % (args['totalbudget'], fundingfactor, summary), 2, verbose)
    
    
        ##########################################################################################################################
        # Re-optimize based on this fairly close allocation
        ##########################################################################################################################
        args['which'] = 'outcomes'
        newrandseed = None if randseed is None else 2*randseed+1 # Make the random seed different
        budgetvec3, fvals, exitreason = asd(outcomecalc, budgetvec, args=args, xmin=xmin, maxtime=maxtime, maxiters=maxiters, verbose=verbose, randseed=newrandseed, **kwargs) 
        budgetvec4 = constrainbudget(origbudget=origbudget, budgetvec=budgetvec3, totalbudget=args['totalbudget'], budgetlims=optim.constraints, optiminds=optiminds, outputtype='vec')
    
        # Check that targets are still met
        args['which'] = 'money'
        targetsmet, summary = outcomecalc(budgetvec4, **args)
        if targetsmet: budgetvec5 = dcp(budgetvec4) # Yes, keep them
        else: budgetvec5 = dcp(budgetvec2) # No, go back to previous version that we know worked
        newtotalbudget = args['totalbudget'] # WARNING, necessary?
    
        # And finally, home in on a solution
        upperlim = 1.0
        lowerlim = 1.0/fundingchange
        while (upperlim-lowerlim>tolerance) or not(targetsmet): # Keep looping until they converge to within "tolerance" of the budget
            fundingfactor = (upperlim+lowerlim)/2.0
            args['totalbudget'] = newtotalbudget * fundingfactor
            targetsmet, summary = outcomecalc(budgetvec5, **args)
            printv('Homing in:\nBudget: %0.0f;\nCurrent funding factor (low, high): %f (%f, %f)\n(%s)\n' % (args['totalbudget'], fundingfactor, lowerlim, upperlim, summary), 2, verbose)
            if targetsmet: upperlim = fundingfactor
            else:          lowerlim = fundingfactor
        constrainedbudget, constrainedbudgetvec, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec5, totalbudget=newtotalbudget*upperlim, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')

    ## Tidy up -- WARNING, need to think of a way to process multiple inds
    args['totalbudget'] = origtotalbudget
    orig = outcomecalc(origbudgetvec, outputresults=True, **args)
    args['totalbudget'] = newtotalbudget * fundingfactor
    new = outcomecalc(constrainedbudgetvec, outputresults=True, **args)
    orig.name = 'Current' # WARNING, is this really the best way of doing it?
    new.name = 'Optimal'
    tmpresults = [orig, new]
    multires = Multiresultset(resultsetlist=tmpresults, name='optim-%s' % name)
    for k,key in enumerate(multires.keys): multires.budgetyears[key] = tmpresults[k].budgetyears # WARNING, this is ugly
    optim.resultsref = multires.name # Store the reference for this result

    return multires
