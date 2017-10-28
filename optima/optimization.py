"""
Functions for running optimizations.

Version: 2017jun04
"""

from optima import OptimaException, Link, Multiresultset, ICER, asd, runmodel, getresults # Main functions
from optima import printv, dcp, odict, findinds, today, getdate, uuid, objrepr, promotetoarray, findnearest, sanitize, inclusiverange # Utilities
from numpy import zeros, empty, arange, maximum, array, inf, isfinite, argmin, argsort, nan, floor, concatenate, exp
from numpy.random import random, seed
from time import time

################################################################################################################################################
### The container class
################################################################################################################################################
class Optim(object):
    ''' An object for storing an optimization '''

    def __init__(self, project=None, name='default', objectives=None, constraints=None, parsetname=None, progsetname=None):
        if project     is None: raise OptimaException('To create an optimization, you must supply a project')
        if parsetname  is None: parsetname  = -1 # If none supplied, assume defaults
        if progsetname is None: progsetname = -1
        if objectives  is None: objectives  = defaultobjectives(project=project,  progsetname=progsetname, verbose=0)
        if constraints is None: constraints = defaultconstraints(project=project, progsetname=progsetname, verbose=0)
        self.name         = name # Name of the optimization, e.g. 'default'
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
            print('WARNING, no results associated with this optimization')
            return None





################################################################################################################################################
### Helper functions
################################################################################################################################################

def defaultobjectives(project=None, progsetname=None, which=None, verbose=2):
    """
    Define default objectives for the optimization. Some objectives are shared
    between outcome and money minimizations, while others are different. However,
    outcome minimization is performed as part of money minimization, so it's useful
    to keep all the keys for both. Still, ugly.

    Version: 2016feb03
    """
    printv('Defining default objectives...', 3, verbose=verbose)

    if which       is None: which = 'outcomes'
    if progsetname is None: progsetname = -1
    
    try:
        defaultbudget = sum(project.progsets[progsetname].getdefaultbudget()[:])
    except:
        defaultbudget = 0.0 # If can't find programs
        printv('defaultobjectives() did not get a project or progset, so setting budget to %0.0f' % defaultbudget, 2, verbose)
        
    objectives = odict() # Dictionary of all objectives
    objectives['which'] = which
    objectives['keys'] = ['death', 'inci', 'daly'] # Define valid keys
    objectives['keylabels'] = odict([('death','Deaths'), ('inci','New infections'), ('daly','DALYs')]) # Define key labels
    if which in ['outcome', 'outcomes']:
        objectives['base']        = None # "Baseline year to compare outcomes to"
        objectives['start']       = 2017 # "Year to begin optimization"
        objectives['end']         = 2030 # "Year to project outcomes to"
        objectives['budget']      = defaultbudget # "Annual budget to optimize"
        objectives['budgetscale'] = [1.] # "Scale factors to apply to budget"
        objectives['deathweight'] = 5    # "Relative weight per death"
        objectives['inciweight']  = 1    # "Relative weight per new infection"
        objectives['dalyweight']  = 0    # "Relative weight per DALY"
        objectives['deathfrac']   = None # Fraction of deaths to get to
        objectives['incifrac']    = None # Fraction of incidence to get to
        objectives['dalyfrac']    = None # Fraction of DALYs to get to
    elif which=='money':
        objectives['base']        = 2015 # "Baseline year to compare outcomes to"
        objectives['start']       = 2017 # "Year to begin optimization"
        objectives['end']         = 2027 # "Year by which to achieve objectives"
        objectives['budget']      = defaultbudget # "Starting budget"
        objectives['deathweight'] = None # "Death weighting"
        objectives['inciweight']  = None # "Incidence weighting"
        objectives['dalyweight']  = None # "Incidence weighting"
        objectives['deathfrac']   = 0.25 # Fraction of deaths to avert
        objectives['incifrac']    = 0.25 # Fraction of incidence to avert
        objectives['dalyfrac']    = 0 # Fraction of DALYs to avert
    else:
        raise OptimaException('"which" keyword argument must be either "outcome" or "money"')

    return objectives


def defaultconstraints(project=None, progsetname=None, which='outcomes', verbose=2):
    """
    Define constraints for minimize outcomes optimization: at the moment, just
    total budget constraints defned as a fraction of current spending. Fixed costs
    are treated differently, and ART is hard-coded to not decrease.

    Version: 2017jun04
    """

    printv('Defining default constraints...', 3, verbose=verbose)

    if progsetname is None: 
        progsetname = -1
        printv('defaultconstraints() did not get a progsetname input, so using default', 3, verbose)
    try:    progset = project.progsets[progsetname]
    except: raise OptimaException('To define constraints, you must supply a program set as an input')

    # If no programs in the progset, return None        
    if not(len(progset.programs)): return None

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
    if 'PMTCT' in constraints['min'].keys():
        constraints['min']['PMTCT'] = 1.0 # By default, don't let ART funding decrease

    return constraints







def constrainbudget(origbudget=None, budgetvec=None, totalbudget=None, budgetlims=None, optiminds=None, tolerance=1e-2, overalltolerance=1.0, outputtype=None, tvsettings=None):
    """ Take an unnormalized/unconstrained budgetvec and normalize and constrain it """
    
    # Handle time-varying optimization if required
    budgetvec, tvcontrolvec, tvenvelope = handletv(budgetvec=budgetvec, tvsettings=tvsettings, optiminds=optiminds)

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
        errormsg = 'Rescaling budget failed (%f != %f)' % (sum(rescaledbudget[:]), totalbudget)
        raise OptimaException(errormsg)

    # Calculate the minimum amount that can be spent on the fixed costs
    rescaledminfixed = dcp(rescaledbudget) # This is the rescaled budget, but with the minimum fixed costs -- should be <= totalbudget
    proginds = arange(len(origbudget)) # Array of all allowable indices
    fixedinds = array([p for p in proginds if p not in optiminds]) # Get the complement of optiminds
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
        errormsg = 'Rescaling budget failed (%f != %f)' % (sum(scaledbudgetvec), optimbudget)
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
        raise OptimaException('Must specify an output type of "odict", "vec", or "full"; you specified "%s"' % outputtype)



def tvfunction(years=None, par=None):
    '''
    Convert a vector of years into a corresponding normalized vector of relative values.
    
    Usage:
        y = tvfunction(range(2000,2030), par=1.5)
    '''
    years = promotetoarray(years) # Make sure it's an array
    x = years-years[0] # Start at zero
    x /= x.max() # Normalize
    y = exp(par*x)
    y /= y.mean()
    return y


def handletv(budgetvec=None, tvsettings=None, optiminds=None):
    ''' Decide if the budget vector includes time-varying information '''
    noptimprogs = len(optiminds) # Number of optimized programs
    ndims = 2 # Semi-hard-code the number of dimensions of the time-varying optimization
    if len(budgetvec)>=ndims*noptimprogs:
        tvcontrolvec = dcp(budgetvec[noptimprogs:ndims*noptimprogs]) # Pull out control vector
        if   len(budgetvec)==(ndims*noptimprogs):   tvenvelope = None # No budget shape
        elif len(budgetvec)==(ndims*noptimprogs+1): tvenvelope = budgetvec[ndims*noptimprogs] # Pull out overall budget shape
        else: raise OptimaException('Length not understood')
        budgetvec = dcp(budgetvec[:noptimprogs]) # Replace the budget vector with the ordinary budget vector
    else:
        tvcontrolvec = None
        tvenvelope = None
    return (budgetvec, tvcontrolvec, tvenvelope)



################################################################################################################################################
### The main meat of the matter
################################################################################################################################################

def outcomecalc(budgetvec=None, which=None, project=None, parsetname=None, progsetname=None, 
                objectives=None, constraints=None, totalbudget=None, optiminds=None, origbudget=None, tvec=None, 
                initpeople=None, outputresults=False, verbose=2, ccsample='best', doconstrainbudget=True, tvsettings=None):
    ''' Function to evaluate the objective for a given budget vector (note, not time-varying) '''

    # Set up defaults
    if which is None: 
        if objectives is not None: which = objectives['which']
        else:                      which = 'outcomes'
    if parsetname  is None: parsetname  = -1
    if progsetname is None: progsetname = -1
    parset  = project.parsets[parsetname] 
    progset = project.progsets[progsetname]
    if objectives  is None: objectives  = defaultobjectives(project=project,  progsetname=progsetname, which=which)
    if constraints is None: constraints = defaultconstraints(project=project, progsetname=progsetname, which=which)
    if totalbudget is None: totalbudget = objectives['budget']
    if origbudget  is None: origbudget  = progset.getdefaultbudget()
    if optiminds   is None: optiminds   = findinds(progset.optimizable())
    if budgetvec   is None: budgetvec   = dcp(origbudget[:][optiminds])
    if type(budgetvec)==odict: budgetvec = dcp(budgetvec[:][optiminds])
    
    # Validate input
    arglist = [budgetvec, which, parset, progset, objectives, totalbudget, constraints, optiminds, origbudget]
    if any([arg is None for arg in arglist]):  # WARNING, this kind of obscures which of these is None -- is that ok? Also a little too hard-coded...
        raise OptimaException('outcomecalc() requires which, budgetvec, parset, progset, objectives, totalbudget, constraints, optiminds, origbudget, tvec as inputs at minimum; argument %i is None' % arglist.index(None))
    if which=='outcome': which='outcomes' # I never remember which it's supposed to be, so let's fix it here
    if which not in ['outcomes','money']:
        errormsg = 'optimize(): "which" must be "outcomes" or "money"; you entered "%s"' % which
        raise OptimaException(errormsg)
    
    # Handle time-varying optimization
    budgetvec, tvcontrolvec, tvenvelope = handletv(budgetvec=budgetvec, tvsettings=tvsettings, optiminds=optiminds)
    
    # Normalize budgetvec and convert to budget -- WARNING, is there a better way of doing this?
    if doconstrainbudget:
        constrainedbudget = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, budgetlims=constraints, optiminds=optiminds, outputtype='odict')
    else:
        constrainedbudget = dcp(origbudget)
        if len(budgetvec)==len(optiminds): constrainedbudget[optiminds] = budgetvec # Assume it's just the optimizable programs
        else:                              constrainedbudget[:]         = budgetvec # Assume it's all programs
        
    # Run model
    if tvsettings is None: # If not running time-varying optimization, it's easy
        paryears = objectives['start']
    else: # Otherwise, it's not easy
        paryears = inclusiverange(start=objectives['start'], stop=objectives['end'], step=tvsettings['tvstep']) # Create the time vector
        for i,ind in enumerate(optiminds): # Loop over the programs and calculate the budget for each
            constrainedbudget[ind] = constrainedbudget[ind]*tvfunction(years=paryears, par=tvcontrolvec[i])
    
    # Get coverage and actual dictionary, in preparation for running
    thiscoverage = progset.getprogcoverage(budget=constrainedbudget, t=paryears, parset=parset, sample=ccsample)
    thisparsdict = progset.getpars(coverage=thiscoverage, t=paryears, parset=parset, sample=ccsample)
    
    # Actually run the model
    if initpeople is None: startyear = None
    else:                  startyear = objectives['start']
    tvec = project.settings.maketvec(start=startyear, end=objectives['end'])
    results = runmodel(pars=thisparsdict, project=project, parsetname=parsetname, progsetname=progsetname, tvec=tvec, initpeople=initpeople, verbose=0, label=project.name+'-optim-outcomecalc', doround=False)

    # Figure out which indices to use
    initialind = findinds(results.tvec, objectives['start'])
    finalind = findinds(results.tvec, objectives['end'])
    if which=='money': baseind = findinds(results.tvec, objectives['base']) # Only used for money minimization
    if which=='outcomes': indices = arange(initialind, finalind) # Only used for outcomes minimization

    ## Here, we split depending on whether it's a outcomes or money minimization:
    if which=='outcomes':
        # Calculate outcome
        outcome = 0 # Preallocate objective value
        rawoutcomes = odict()
        for key in objectives['keys']:
            thisweight = objectives[key+'weight'] # e.g. objectives['inciweight']
            thisoutcome = results.main['num'+key].tot[0][indices].sum() # the instantaneous outcome e.g. objectives['numdeath'] -- 0 is since best
            rawoutcomes['num'+key] = thisoutcome*results.dt
            outcome += thisoutcome*thisweight*results.dt # Calculate objective

        # Output results
        if outputresults:
            results.outcome = outcome
            results.rawoutcomes = rawoutcomes
            results.budgetyears = [objectives['start']] # Use the starting year
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
            results.budgetyears = [objectives['start']] # Use the starting year
            results.budget = constrainedbudget # Convert to budget
            results.targetsmet = targetsmet
            results.target = target
            results.rawoutcomes = final
            output = results
        else:
            summary = 'Baseline: %0.0f %0.0f %0.0f | Target: %0.0f %0.0f %0.0f | Final: %0.0f %0.0f %0.0f' % tuple(baseline.values()+target.values()+final.values())
            output = (targetsmet, summary)
    
    return output









def optimize(optim=None, maxiters=None, maxtime=None, verbose=2, stoppingfunc=None, 
             die=False, origbudget=None, randseed=None, mc=None, label=None, outputqueue=None, *args, **kwargs):
    '''
    The standard Optima optimization function: minimize outcomes for a fixed total budget.
    
    Arguments:
        project = the project file
        optim = the optimization object
        maxiters = how many iterations to optimize for
        maxtime = how many secons to optimize for
        verbose = how much detail to provide
        stoppingfunc = a function called to decide on stopping
        die = whether or not to check things in detail
        origbudget = the budget to start from (if not supplied, use default
        randseed = optionally reset the seed
        mc = how many Monte Carlo seeds to run for (if negative, randomize the start location as well)
        label = a string to append to error messages to make it clear where things went wrong

    Version: 1.4 (2017apr01)
    '''
    
    ## Input validation
    if not kwargs: 
        if not args: kwargs = {}
        else:        kwargs = args[0] # Kwargs can be passed as non-kwargs...horribly confusing, I know
    if optim is None: raise OptimaException('minoutcomes() requires project and optim arguments at minimum')
    project = optim.projectref() # Get the project
    which = optim.objectives['which']
    if which=='outcome': which='outcomes' # I never remember which it's supposed to be, so let's fix it here
    if which not in ['outcomes','money']:
        errormsg = '"which" must be "outcomes" or "money"; you entered "%s"' % which
        raise OptimaException(errormsg)
    printv('Running %s optimization...' % which, 1, verbose)
    
    # Set defaults
    if maxiters is None: maxiters = 1000
    if maxtime is None: maxtime = 3600
    if mc is None: mc = 3
    
    # Optim structure validation
    progset = project.progsets[optim.progsetname] # Link to the original parameter set
    if not(hasattr(optim, 'objectives')) or optim.objectives is None:
        optim.objectives = defaultobjectives(project=project, progsetname=optim.progsetname, which=which, verbose=verbose)
    if not(hasattr(optim, 'constraints')) or optim.constraints is None:
        optim.constraints = defaultconstraints(project=project, progsetname=optim.progsetname, which=which, verbose=verbose)

    # Process inputs
    if not optim.objectives['budget']: # Handle 0 or None 
        try: optim.objectives['budget'] = sum(progset.getdefaultbudget()[:])
        except:  raise OptimaException('Could not get default budget for optimization')
    tvec = project.settings.maketvec(end=optim.objectives['end']) 
    if not progset.readytooptimize():
        detail_costcov = progset.hasallcostcovpars(detail=True)
        detail_covout = progset.hasallcovoutpars(detail=True)
        details = (detail_costcov+detail_covout)
        if len(details):
            errormsg = 'The program set that you provided does not have all the required cost-coverage and/or coverage outcome parameters! Parameters are missing from:\n%s' % details
        else:
            errormsg = 'The program set that you provided does not include any optimizable programs, so optimization cannot be performed.'
        raise OptimaException(errormsg)

    # Run outcomes minimization
    if which=='outcomes':
        multires = minoutcomes(project=project, optim=optim, tvec=tvec, verbose=verbose, maxtime=maxtime, maxiters=maxiters, 
                               origbudget=origbudget, randseed=randseed, mc=mc, label=label, die=die, **kwargs)

    # Run money minimization
    elif which=='money':
        multires = minmoney(project=project, optim=optim, tvec=tvec, verbose=verbose, maxtime=maxtime, maxiters=maxiters, 
                            fundingchange=1.2, randseed=randseed, **kwargs)
    
    # If running parallel, put on the queue; otherwise, return
    if outputqueue is not None:
        outputqueue.put(multires)
        return None
    else:
        return multires




def multioptimize(optim=None, nchains=None, nblocks=None, blockiters=None, 
                  batch=None, mc=None, randseed=None, maxiters=None, maxtime=None, verbose=2, 
                  stoppingfunc=None, die=False, origbudget=None, label=None, **kwargs):
    '''
    Run a multi-chain optimization. See project.optimize() for usage examples, and optimize()
    for kwarg explanation.
    
    Small usage example:
        import optima as op
        import pylab as pl
        P = op.demo(0)
        results = P.optimize(multi=True, nchains=4, blockiters=10, nblocks=2, randseed=1)
        op.pygui(P, toplot=['improvement', 'budgets', 'numinci'])
        pl.figure(); pl.plot(results.multiimprovement.transpose())
    
    You can see how after 10 iterations, the blocks talk to each other, and the optimization
    for each thread restarts from the best solution found for each.
    '''

    # Import dependencies here so no biggie if they fail
    from multiprocessing import Process, Queue
    
    # Set defaults
    if nchains is None:    nchains = 4
    if nblocks is None:    nblocks = 10
    if blockiters is None: blockiters = 10
    if mc is None:         mc = 0
    if abs(mc)>0:
        errormsg = 'Monte Carlo optimization with multithread optimization has not been implemented'
        raise OptimaException(errormsg)
    totaliters = blockiters*nblocks
    fvalarray = zeros((nchains,totaliters+1)) + nan
    
    printv('Starting a parallel optimization with %i threads for %i iterations each for %i blocks' % (nchains, blockiters, nblocks), 2, verbose)
    
    # Loop over the optimization blocks
    for block in range(nblocks):
        
        # Set up the parallel process
        outputqueue = Queue()
        outputlist = empty(nchains, dtype=object)
        processes = []
            
        # Loop over the threads, starting the processes
        for thread in range(nchains):
            blockrand = (block+1)*(2**6-1) # Pseudorandom seeds
            threadrand = (thread+1)*(2**10-1) 
            randtime = int((time()-floor(time()))*1e4)
            if randseed is None: thisseed = (blockrand+threadrand)*randtime # Get a random number based on both the time and the thread
            else:                thisseed = randseed + blockrand+threadrand
            optimargs = (optim, blockiters, maxtime, verbose, stoppingfunc, die, origbudget, thisseed, mc, label, outputqueue, kwargs)
            prc = Process(target=optimize, args=optimargs)
            prc.start()
            processes.append(prc)
        
        # Tidy up: close the threads and gather the results
        for i in range(nchains):
            result = outputqueue.get() # This is needed or else the process never finishes
            outputlist[i] = result # WARNING, this randomizes the order
            if block==0 and i==0: results = dcp(result) # Copy the original results from the first optimization
        for prc in processes:
            prc.join() # Wait for them to finish
        
        # Figure out which one did best
        bestfvalval = inf
        bestfvalind = None
        for i in range(nchains):
            if block==0 and i==0: fvalarray[:,0] = outputlist[i].improvement[0][0] # Store the initial value
            thischain = outputlist[i].improvement[0][1:] # The chain to store the improvement of -- NB, improvement is an odict
            leftbound = block * blockiters + 1
            rightbound = block * blockiters + len(thischain) + 1
            fvalarray[i,leftbound:rightbound] = thischain
            thisbestval = outputlist[i].outcome
            if thisbestval<bestfvalval:
                bestfvalval = thisbestval
                bestfvalind = i
        
        origbudget = outputlist[bestfvalind].budget # Update the budget and use it as the input for the next block -- this is key!
    
    # Assemble final results object from the initial and final run
    finalresults = outputlist[bestfvalind]
    results.improvement[0] = sanitize(fvalarray[bestfvalind,:]) # Store fval vector in normal format
    results.multiimprovement = fvalarray # Store full fval array
    results.outcome = finalresults.outcome
    results.budget = finalresults.budget
    try: results.budgets['Optimal'] = finalresults.budgets['Optimal']
    except: pass
    
    return results





def tvoptimize(project=None, optim=None, tvec=None, verbose=None, maxtime=None, maxiters=1000, origbudget=None, 
               ccsample='best', randseed=None, mc=3, label=None, die=False, tvsettings=None, **kwargs):
    '''
    Run a time-varying optimization. See project.optimize() for usage examples, and optimize()
    for kwarg explanation.
    
    Small usage example:
        import optima as op
        import pylab as pl
        P = op.demo(0)
        results = P.optimize(timevarying=True, randseed=1)
        op.pygui(P, toplot=['improvement', 'budgets', 'numinci'])
        pl.figure(); pl.plot(results.multiimprovement.transpose())
    
    You can see how after 10 iterations, the blocks talk to each other, and the optimization
    for each thread restarts from the best solution found for each.
    '''

    printv('Starting a time-varying optimization...', 1, verbose)
    
    if not isinstance(tvsettings, dict): # Dictionary already supplied: just use
        tvsettings = {'tvtotalbudget': False, # Whether or not to let the budget itself change
                      'tvstep': 1, # NUmber of years per step
                      'asdstep': 0.1, # Default ASD step size
                      'asdlim': 1,} # Minimum/maximum limit
    
    # Do a preliminary non-time-varying optimization
    prelim = optimize(optim=optim, maxtime=maxtime, maxiters=maxiters, verbose=verbose, 
                origbudget=origbudget, ccsample=ccsample, randseed=randseed, mc=mc, label=label, die=die, **kwargs)
    
    # Add in the time-varying component
    origtotalbudget = dcp(optim.objectives['budget']) # Should be a float, but dcp just in case
    totalbudget = origtotalbudget
    optimconstbudget = dcp(prelim.budget)
    origbudget = dcp(prelim.budgets[0]) # OK to do this since if supplied as an argument, will be the same; else, it will be populated here
    project = optim.projectref()

    ## Handle budget and remove fixed costs
    if project is None or optim is None: raise OptimaException('An optimization requires both a project and an optimization object to run')
    parset  = project.parsets[optim.parsetname] # Link to the original parameter set
    progset = project.progsets[optim.progsetname] # Link to the original program set
    
    optimizable = array(progset.optimizable())
    optiminds = findinds(optimizable)
    budgetvec = optimconstbudget[:][optiminds] # Get the original budget vector
    noptimprogs = len(budgetvec) # Number of optimizable programs
    if label is None: label = ''
    
    # Calculate the initial people distribution
    results = runmodel(pars=parset.pars, project=project, parsetname=optim.parsetname, progsetname=optim.progsetname, tvec=tvec, keepraw=True, verbose=0, label=project.name+'-minoutcomes')
    initialind = findinds(results.raw[0]['tvec'], optim.objectives['start'])
    initpeople = results.raw[0]['people'][:,:,initialind] # Pull out the people array corresponding to the start of the optimization -- there shouldn't be multiple raw arrays here

    # Calculate original things
    constrainedbudgetorig, constrainedbudgetvecorig, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=origtotalbudget, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')
    
    # Set up arguments which are shared between outcomecalc and asd
    args = {'which':'outcomes', 
            'project':project, 
            'parsetname':optim.parsetname, 
            'progsetname':optim.progsetname, 
            'objectives':optim.objectives, 
            'constraints':optim.constraints, 
            'totalbudget':origtotalbudget, # Complicated, see below
            'optiminds':optiminds, 
            'origbudget':origbudget, 
            'tvec':tvec, 
            'ccsample':ccsample, 
            'verbose':verbose, 
            'initpeople':initpeople,
            'tvsettings':None} # Complicated; see below
    
    tmpresults = odict()
    tmpimprovements = odict()
    tmpfullruninfo = odict()
    
    # This generates the baseline results
    tmpresults['Baseline']       = outcomecalc(prelim.budgets['Baseline'], outputresults=True, doconstrainbudget=False, **args)
    tmpresults['Non-time-varying'] = outcomecalc(prelim.budgets['Optimal'],  outputresults=True, doconstrainbudget=False, **args)
    for key,result in tmpresults.items(): 
        result.name = key # Update names
        tmpimprovements[key] = [tmpresults[key].outcome] # Hacky, since expects a list

    # Get the total budget & constrain it 
    constrainedbudget, constrainedbudgetvec, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')
    args['totalbudget'] = totalbudget
    args['initpeople'] = initpeople # Set so only runs the part of the optimization required
    
    # Set up budgets to run
    tvbudgetvec = dcp(constrainedbudgetvec)
    tvcontrolvec = zeros(noptimprogs+tvsettings['tvtotalbudget']) # Generate vector of zeros for correct length, including an optional extra one for the total budget
    tvvec = concatenate([tvbudgetvec, tvcontrolvec])
    if randseed is None: randseed = int((time()-floor(time()))*1e4) # Make sure a seed is used
            
    # Actually run the optimizations
    bestfval = inf # Value of outcome
    asdresults = odict()
    key = 'Baseline'
    printv('Running time-varying optimization with maxtime=%s, maxiters=%s' % (maxtime, maxiters), 2, verbose)
    if label: thislabel = '"'+label+'-'+key+'"'
    else: thislabel = '"'+key+'"'
    args['tvsettings'] = tvsettings
    args['origbudget'] = optimconstbudget
    
    xmin = concatenate([zeros(noptimprogs), -tvsettings['asdlim']+dcp(tvcontrolvec)])
    xmax = concatenate([inf+zeros(noptimprogs), tvsettings['asdlim']+dcp(tvcontrolvec)])
    stepbudget = tvsettings['asdstep']*tvbudgetvec
    steptvcontrol = tvsettings['asdstep']+dcp(tvcontrolvec)
    sinitial = concatenate([stepbudget]*2+[steptvcontrol]*2) # Set the step size -- duplicate for +/-
    tvvecnew, fvals, details = asd(outcomecalc, tvvec, args=args, xmin=xmin, xmax=xmax, sinitial=sinitial, maxtime=maxtime, maxiters=maxiters, verbose=verbose, randseed=randseed, label=thislabel, **kwargs)
    budgetvec, tvcontrolvec, tvenvelope = handletv(budgetvec=tvvecnew, tvsettings=tvsettings, optiminds=optiminds)
    constrainedbudgetnew, constrainedbudgetvecnew, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full', tvsettings=tvsettings)
    asdresults[key] = {'budget':tvvecnew, 'fvals':fvals, 'tvcontrolvec':tvcontrolvec}
    if fvals[-1]<bestfval: 
        bestkey = key # Reset key
        bestfval = fvals[-1] # Reset fval
    
    ## Calculate outcomes
    args['initpeople'] = None # Set to None to get full results, not just from strat year
    args['tvsettings'] = None
    new = outcomecalc(asdresults[bestkey]['budget'], outputresults=True, **args)
    new.name = 'Optimal (time-varying)' # Else, say what the budget is
    tmpresults[new.name] = new
    tmpimprovements[new.name] = asdresults[bestkey]['fvals']
    tmpfullruninfo[new.name] = asdresults # Store everything

    ## Output
    multires = Multiresultset(resultsetlist=tmpresults.values(), name='optim-%s' % optim.name)
    for k,key in enumerate(multires.keys): multires.budgetyears[key] = tmpresults[k].budgetyears # WARNING, this is ugly
    multires.improvement = tmpimprovements # Store full function evaluation information -- only use last one
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
    
    # Store optimization settings
    multires.optimsettings = odict([('maxiters',maxiters),('maxtime',maxtime),('mc',mc),('randseed',randseed),('tvsettings',tvsettings)])

    return multires







def minoutcomes(project=None, optim=None, tvec=None, verbose=None, maxtime=None, maxiters=1000, 
                origbudget=None, ccsample='best', randseed=None, mc=3, label=None, die=False, timevarying=None, **kwargs):
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
    
    optimizable = array(progset.optimizable())
    optiminds = findinds(optimizable)
    nonoptiminds = findinds(optimizable==False)
    optimkeys = [key for k,key in enumerate(origbudget.keys()) if optimizable[k]]
    budgetvec = origbudget[:][optiminds] # Get the original budget vector
    nprogs = len(origbudget[:]) # Number of programs total
    noptimprogs = len(budgetvec) # Number of optimizable programs
    xmin = zeros(noptimprogs)
    if label is None: label = ''
    
    # Calculate the initial people distribution
    results = runmodel(pars=parset.pars, project=project, parsetname=optim.parsetname, progsetname=optim.progsetname, tvec=tvec, keepraw=True, verbose=0, label=project.name+'-minoutcomes')
    initialind = findinds(results.raw[0]['tvec'], optim.objectives['start'])
    initpeople = results.raw[0]['people'][:,:,initialind] # Pull out the people array corresponding to the start of the optimization -- there shouldn't be multiple raw arrays here

    # Calculate original things
    constrainedbudgetorig, constrainedbudgetvecorig, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=origtotalbudget, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')
    
    # Set up arguments which are shared between outcomecalc and asd
    args = {'which':'outcomes', 
            'project':project, 
            'parsetname':optim.parsetname, 
            'progsetname':optim.progsetname, 
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
    extremebudgets['Baseline'] = zeros(nprogs)
    for i,p in enumerate(optiminds): extremebudgets['Baseline'][p] = constrainedbudgetvecorig[i] # Must be a better way of doing this :(
    for i in nonoptiminds:           extremebudgets['Baseline'][i] = origbudget[i] # Copy the original budget
    extremebudgets['Zero']     = zeros(nprogs)
    extremebudgets['Infinite'] = origbudget[:]+project.settings.infmoney
    firstkeys = ['Baseline', 'Zero', 'Infinite'] # These are special, store them
    if mc: # Only run these if MC is being run
        for p,prog in zip(optiminds,optimkeys):
            extremebudgets[prog] = zeros(nprogs)
            extremebudgets[prog][p] = sum(constrainedbudgetvecorig)
            for i in nonoptiminds: extremebudgets[prog][p] = origbudget[p] # Copy the original budget
    
    # Run extremes
    extremeresults  = odict()
    extremeoutcomes = odict()
    for key,exbudget in extremebudgets.items():
        if key=='Baseline': 
            args['initpeople'] = None # Do this so it runs for the full time series, and is comparable to the optimization result
            args['totalbudget'] = origbudget[:].sum() # Need to reset this since constraining the budget
            doconstrainbudget = True # This is needed so it returns the full budget odict, not just the budget vector
            inds = optiminds # Reset to only optimizable indices
        else:
            args['initpeople'] = initpeople # Do this so saves a lot of time (runs twice as fast for all the budget scenarios)
            args['totalbudget'] = origtotalbudget
            doconstrainbudget = False
            inds = arange(nprogs)
        extremeresults[key] = outcomecalc(exbudget[inds], outputresults=True, doconstrainbudget=doconstrainbudget, **args)
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
        printv('Outcome for baseline budget (starting point): %0.0f' % extremeoutcomes['Baseline'], 2, verbose)
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
    tmpresults['Baseline'] = extremeresults['Baseline'] # Include un-optimized original
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
            allbudgetvecs['Baseline'] = dcp(constrainedbudgetvec)
            if randseed is None: randseed = int((time()-floor(time()))*1e4) # Make sure a seed is used
            allseeds = [randseed] # Start with current random seed
            if mc: # If MC, run multiple
                if extremeoutcomes[bestprogram] < extremeoutcomes['Baseline']:
                    allbudgetvecs['Program (%s)' % extremebudgets.keys()[bestprogram]] = array([extremebudgets[bestprogram][i] for i in optiminds])  # Include all money going to one program, but only if it's better than the current allocation
                    allseeds.append(randseed+1) # Append a new seed if we're running a program extreme as well
                for i in range(abs(mc)): # For the remainder, do randomizations
                    scalefactorrand = scalefactor*(2**10-1) # Pseudorandomize the seeds
                    mcrand = i*(2**6-1)
                    thisseed = int(randseed + scalefactorrand + mcrand)
                    seed(thisseed)
                    allseeds.append(thisseed)
                    if mc<0: 
                        randbudget = random(noptimprogs)
                        randbudget = randbudget/randbudget.sum()*constrainedbudgetvec.sum()
                        allbudgetvecs['Random %s' % (i+1)] = randbudget
                    else:
                        current = dcp(constrainedbudgetvec)
                        allbudgetvecs['Baseline %s' % (i+1)] = current
                    
            # Actually run the optimizations
            bestfval = inf # Value of outcome
            asdresults = odict()
            for k,key in enumerate(allbudgetvecs.keys()):
                printv('Running optimization "%s" (%i/%i) with maxtime=%s, maxiters=%s' % (key, k+1, len(allbudgetvecs), maxtime, maxiters), 2, verbose)
                if label: thislabel = '"'+label+'-'+key+'"'
                else: thislabel = '"'+key+'"'
                budgetvecnew, fvals, details = asd(outcomecalc, allbudgetvecs[key], args=args, xmin=xmin, maxtime=maxtime, maxiters=maxiters, verbose=verbose, randseed=allseeds[k], label=thislabel, **kwargs)
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
            tmpresults['Optimal'] = dcp(tmpresults['Baseline']) # If zero budget, just copy current and rename
            tmpresults['Optimal'].name = 'Optimal' # Rename name to named name

    ## Output
    multires = Multiresultset(resultsetlist=tmpresults.values(), name='optim-%s' % optim.name)
    for k,key in enumerate(multires.keys): multires.budgetyears[key] = tmpresults[k].budgetyears 
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
    
    # Store optimization settings
    multires.optimsettings = odict([('maxiters',maxiters),('maxtime',maxtime),('mc',mc),('randseed',randseed)])

    return multires






def minmoney(project=None, optim=None, tvec=None, verbose=None, maxtime=None, maxiters=1000, fundingchange=1.2, tolerance=1e-2, ccsample='best', randseed=None, **kwargs):
    '''
    A function to minimize money for a fixed objective. Note that it calls minoutcomes() in the process.

    Version: 2016feb07
    '''

    ## Handle budget and remove fixed costs
    if project is None or optim is None: raise OptimaException('An optimization requires both a project and an optimization object to run')
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
    args = {'which':      'money', 
            'project':    project, 
            'parsetname': optim.parsetname, 
            'progsetname':optim.progsetname, 
            'objectives': optim.objectives, 
            'constraints':optim.constraints, 
            'totalbudget':totalbudget, 
            'optiminds':  optiminds, 
            'origbudget': origbudget, 
            'tvec':       tvec, 
            'ccsample':   ccsample, 
            'verbose':    verbose}


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
    weights = 1.0/(weights[:]+project.settings.eps) # Relative weights are inversely proportional to absolute reductions -- e.g. asking for a reduction of 100 deaths and 400 new infections means 1 death = 4 new infections
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
#        budgetvec1, fvals, details = asd(outcomecalc, budgetvec, args=args, xmin=xmin, maxtime=maxtime, maxiters=maxiters, verbose=verbose, randseed=randseed, **kwargs)
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
        budgetvec3, fvals, details = asd(outcomecalc, budgetvec, args=args, xmin=xmin, maxtime=maxtime, maxiters=maxiters, verbose=verbose, randseed=newrandseed, **kwargs) 
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
            printv('Homing in:\nBudget: %0.0f;\nBaseline funding factor (low, high): %f (%f, %f)\n(%s)\n' % (args['totalbudget'], fundingfactor, lowerlim, upperlim, summary), 2, verbose)
            if targetsmet: upperlim = fundingfactor
            else:          lowerlim = fundingfactor
        constrainedbudget, constrainedbudgetvec, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec5, totalbudget=newtotalbudget*upperlim, budgetlims=optim.constraints, optiminds=optiminds, outputtype='full')

    ## Tidy up -- WARNING, need to think of a way to process multiple inds
    args['totalbudget'] = origtotalbudget
    orig = outcomecalc(origbudgetvec, outputresults=True, **args)
    args['totalbudget'] = newtotalbudget * fundingfactor
    new = outcomecalc(constrainedbudgetvec, outputresults=True, **args)
    orig.name = 'Baseline' # WARNING, is this really the best way of doing it?
    new.name = 'Optimal'
    tmpresults = [orig, new]
    multires = Multiresultset(resultsetlist=tmpresults, name='optim-%s' % optim.name)
    for k,key in enumerate(multires.keys): multires.budgetyears[key] = tmpresults[k].budgetyears 
    optim.resultsref = multires.name # Store the reference for this result
    
    # Store optimization settings
    multires.optimsettings = odict([('maxiters',maxiters),('maxtime',maxtime),('randseed',randseed)])

    return multires



################################################################################################################################################
### ICER calculation
################################################################################################################################################

def icers(name=None, project=None, parsetname=None, progsetname=None, objective=None, 
          startyear=None, endyear=None, budgetratios=None, marginal=None, verbose=2):
    '''
    Calculate ICERs for each program.
    
    Inputs:
        name         = name of the result
        project      = the project object
        parsetname   = name of the parameter set used; default -1
        progsetname  = name of the program set; default -1
        objective    = what to calculate; must be one of 'death', 'inci', 'daly'; 'daly' by default)
        startyear    = the year to start applying the budget and calculating the outcome; default from defaultobjectives()
        endyear      = ditto for end year
        budgetratios = the list of budgets relative to baseline to run; default 10 budgets spanning 0.0 to 2.0
        marginal     = whether to calculate marginal ICERs or relative to baseline; default marginal
        
    Do not call this function directly: see project.icers() for usage example.
    
    Version: 2017jun04
    '''
    
    # Handle inputs
    if type(project).__name__ != 'Project': # Can't compare types directly since can't import Project since not defined yet
        errormsg = 'To calculate ICERs you must supply a project, not "%s"' % type(project)
        raise OptimaException(errormsg)
    
    # Set defaults
    eps = project.settings.eps
    icereps = 1e-9 # A smaller epsilon for ensuring ICER divisions aren't zero
    if marginal     is None: marginal     = True
    if objective    is None: objective    = 'daly'
    if parsetname   is None: parsetname   = -1
    if progsetname  is None: progsetname  = -1
    if budgetratios is None: budgetratios = [0.0, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0]
    budgetratios = array(budgetratios) # Ensure it's an array
    nbudgetratios = len(budgetratios)
    
    # Define objectives
    objectives = defaultobjectives(project=project)
    if startyear is not None: objectives['start'] = startyear # Do not overwrite by default
    if endyear   is not None: objectives['end']   = endyear
    nyears = objectives['end'] - objectives['start'] # Calculate the number of years
    obkeys = objectives['keys']
    if objective not in obkeys:
        errormsg = 'Objective must be one of "%s", not "%s"' % (obkeys, objective)
        raise OptimaException(errormsg)
    for key in obkeys:
        if objective==key: objectives[key+'weight'] = 1.0 # Set weight to 1 if they match
        else:              objectives[key+'weight'] = 0.0 # Set to 0 otherwise
    
    printv('Calculating ICERs for objective "%s" from %i-%i, parset "%s", progset "%s", marginal=%s...' % (objective, objectives['start'], objectives['end'], parsetname, progsetname, marginal), 2, verbose)
    
    # Get budget information
    origbudget    = project.defaultbudget(progsetname, optimizable=False) # Get default budget for optimizable programs
    defaultbudget = project.defaultbudget(progsetname, optimizable=True)  # ...and just for optimizable programs
    keys = defaultbudget.keys() # Get the program keys
    nkeys = len(keys)
    
    # Calculate the initial people distribution
    initresults = runmodel(project=project, parsetname=parsetname, progsetname=progsetname, keepraw=True, verbose=0, label=project.name+'-minoutcomes')
    initialind  = findinds(initresults.raw[0]['tvec'], objectives['start'])
    initpeople  = initresults.raw[0]['people'][:,:,initialind] # Pull out the people array corresponding to the start of the optimization -- there shouldn't be multiple raw arrays here

    # Define arguments that don't change in the loop
    defaultargs = {'which':'outcomes', 'project':project, 'parsetname':parsetname, 'progsetname':progsetname, 'objectives':objectives, 
                   'origbudget':origbudget, 'outputresults':False, 'verbose':verbose, 'doconstrainbudget':False, 'initpeople':initpeople}
    
    # Calculate baseline
    baseliney = outcomecalc(budgetvec=defaultbudget, **defaultargs)
    
    # Define structures for storing results
    rawx    = odict().make(keys=keys, vals=[])
    rawy    = dcp(rawx)
    y       = dcp(rawx)
    icer    = dcp(rawx)
    summary = dcp(rawx)
    
    # Loop over both programs and budget ratios
    count = 0
    for key in keys:
        for budgetratio in budgetratios:
            count += 1
            printv('Running ICER budget %i of %i' % (count, nkeys*nbudgetratios), 2, verbose)
            thisbudget = dcp(defaultbudget)
            thisbudget[key] *= budgetratio
            rawx[key].append(thisbudget[key])
            if budgetratio==1: outcome = baseliney # Don't need to run, just copy this
            else:              outcome = outcomecalc(budgetvec=thisbudget, **defaultargs) # The crux of the matter!! Actually calculate
            rawy[key].append(outcome)
            
    # Calculate y values
    for key in keys:
        baselinex = defaultbudget[key] # Because only looking at one program at a time
        for b in range(nbudgetratios):
            
            # Gather values to use
            thisx = rawx[key][b]
            thisy = rawy[key][b]
            if b>0:    
                lowerx = rawx[key][b-1]
                lowery = rawy[key][b-1]
            else: 
                lowerx = None
                lowery = None
            if b<nbudgetratios-1:
                upperx = rawx[key][b+1]
                uppery = rawy[key][b+1]
            else: 
                upperx = None
                uppery = None
            
            # Calculate estimates by comparing to lower and upper values, and baseline if those fail
            estimates = [] # Start assembling ICER estimates
            if marginal: # Calculate relative to next upper and lower choices
                lower = None
                if lowerx is not None:
                    lowerdiffx = (thisx - lowerx)*nyears
                    lowerdiffy = thisy - lowery
                    lower = -lowerdiffy/(lowerdiffx+eps)
                    estimates.append(lower)
                upper = None
                if upperx is not None:
                    upperdiffx = (thisx - upperx)*nyears
                    upperdiffy = thisy - uppery
                    upper = -upperdiffy/(upperdiffx+eps)
                    estimates.append(upper)
            else: # Calculate relative to baseline only
                if thisx==baselinex:
                    thisx = rawx[key][0] # Assume 0 is 0 budget
                    thisy = rawy[key][0] # Assume 0 is 0 budget
                baselinediffx = (thisx - baselinex)*nyears # To get total cost, need to multiply by the number of years
                baselinediffy = thisy - baseliney
                baselinediff = -baselinediffy/(baselinediffx+eps)
                estimates = [baselinediff]
            
            # Finally, calculate the DALYs per dollar
            thisiecr = array(estimates).mean() # Average upper and lower estimates, if available -- "iecr" is the inverse of an icer
            if thisiecr<0:
                printv('WARNING, ICER for "%s" at budget ratio %0.1f is negative (%0.3e); setting to 0' % (key, budgetratios[b], 1./(thisiecr+icereps)), 1, verbose)
                thisiecr = 0.0;
            y[key].append(thisiecr)
    
    # Convert to arrays
    for key in keys:
        rawx[key] = array(rawx[key])
        rawy[key] = array(rawy[key])
        y[key]    = array(y[key]) 
    
    # Calculate actual ICERs
    for key in keys:
        icer[key] = 1.0/(y[key]+icereps)
    
    # Summarize results
    nearest = findnearest(budgetratios, 1.0)
    for key in keys:
        summary[key] = icer[key][nearest]
    
    # Assemble into results
    results = ICER(name=name, objective=objective, startyear=objectives['start'], endyear=objectives['end'], rawx=rawx, rawy=rawy, x=budgetratios, icer=icer, summary=summary, baseline=baseliney, keys=keys, defaultbudget=defaultbudget, parsetname=parsetname, progsetname=progsetname)
    return results