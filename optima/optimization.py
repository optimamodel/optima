"""
Functions for running optimizations.

Version: 2019dec02
"""

from optima import OptimaException, Link, Multiresultset, ICER, asd, getresults # Main functions
from optima import printv, dcp, odict, findinds, today, getdate, uuid, objrepr, promotetoarray, findnearest, sanitize, inclusiverange # Utilities

from numpy import zeros, ones, empty, arange, array, inf, isfinite, argmin, argsort, nan, floor, concatenate, exp, sqrt, logical_and
from numpy.random import random, seed, randint
from time import time
import optima as op # Used by minmoney, at some point should make syntax consistent

# Import dependencies here so no biggie if they fail
try:    from multiprocessing import Process, Queue
except: Process, Queue = None, None # OK to skip these if batch is False

import six
if six.PY3:
    basestring = str
    unicode = str

################################################################################################################################################
### The container class
################################################################################################################################################
class Optim(object):
    ''' An object for storing an optimization '''

    def __init__(self, project=None, name='default', objectives=None, constraints=None, proporigconstraints=None, absconstraints=None,
                 parsetname=None, progsetname=None, timevarying=None, tvsettings=None, which=None):
        """
        For backwards compatibility, constraints should be proportions of the rescaled budget, whereas proporigconstraints
        should be proportions of the default budget, and absconstraints have absolute contraints.
        """
        if project     is None: raise OptimaException('To create an optimization, you must supply a project')
        if parsetname  is None: parsetname  = -1 # If none supplied, assume defaults
        if progsetname is None: progsetname = -1
        if objectives  is None: objectives  = defaultobjectives(project=project,  progsetname=progsetname, verbose=0, which=which)
        if tvsettings  is None: tvsettings  = defaulttvsettings(timevarying=timevarying) # Create the time-varying settings
        if constraints is None and proporigconstraints is None and absconstraints is None:
            # Preferred is proporigconstraints, which get converted to absolute constraints at the time of optimization
            proporigconstraints = defaultconstraints(project=project, progsetname=progsetname)
        self.name           = name # Name of the optimization, e.g. 'default'
        self.uid            = uuid() # ID
        self.projectref     = Link(project) # Store pointer for the project, if available
        self.created        = today() # Date created
        self.modified       = today() # Date modified
        self.parsetname     = parsetname # Parameter set name
        self.progsetname    = progsetname # Program set name
        self.objectives     = objectives # List of dicts holding Parameter objects -- only one if no uncertainty
        self.constraints    = constraints
        self.absconstraints = absconstraints # Can provide absolute constraints but note that if the default budget changes, these constraints will not update
        self.proporigconstraints = proporigconstraints
        self.tvsettings     = tvsettings # The settings for being time-varying
        self.resultsref     = None # Store pointer to results


    def __repr__(self):
        ''' Print out useful information when called'''
        output = '============================================================\n'
        output += ' Optimization name: %s\n'    % self.name
        output += 'Parameter set name: %s\n'    % self.parsetname
        output += '  Program set name: %s\n'    % self.progsetname
        output += '      Time-varying: %s\n'    % self.tvsettings['timevarying']
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

    def getabsconstraints(self):
        """ Gets the appropriate absolute constraints from the Optim, taking all the constraints, absconstraints and
            proporigconstraints into consideration and choosing the most strict of them for each program at the totalbudget.
        """
        defabsconstraints = defaultabsconstraints(project=self.projectref(),progsetname=self.progsetname)
        if self.absconstraints is None and self.constraints is None and self.proporigconstraints is None:
            return defabsconstraints

        # Convert constraints, absconstraints and proporigconstraints into absconstraints for this totalbudget
        absconstraints = self.absconstraints
        constraints = constraintstoabsconstraints(project=self.projectref(), progsetname=self.progsetname,constraints=self.constraints,totalbudget=self.objectives['budget'])
        proporigconstraints = proporigconstraintstoabsconstraints(project=self.projectref(), progsetname=self.progsetname,proporigconstraints=self.proporigconstraints)

        # Remove Nones
        constrslist = [constr for constr in [absconstraints,constraints,proporigconstraints] if constr is not None]
        # Now get the most strict constraints from all three
        for progname in defabsconstraints['min'].keys():
            defabsconstraints['min'][progname] = max((0,)   + tuple(constrs['min'][progname] for constrs in constrslist if constrs['min'][progname] is not None))
            defabsconstraints['max'][progname] = min((inf,) + tuple(constrs['max'][progname] for constrs in constrslist if constrs['max'][progname] is not None))
            if defabsconstraints['max'][progname] == inf: defabsconstraints['max'][progname] = None
        return defabsconstraints

    def getproporigconstraints(self):
        """ Does the same thing as getabsconstraints, but then converts the absconstraints into proporigconstraints
        """
        return absconstraintstoprogorigconstraints(project=self.projectref(), progsetname=self.progsetname, absconstraints=self.getabsconstraints())

################################################################################################################################################
### Helper functions
################################################################################################################################################

def getprogsetfromproject(project=None, progsetname=None, function='', verbose=2):
    if project is None: raise OptimaException(f'getprogsetfromproject() called from "{function}" must be supplied with a project to get the progset')
    if progsetname is None:
        progsetname = -1
        printv('getprogsetfromproject() did not get a progsetname input, so using default', 3, verbose)
    try:    progset = project.progsets[progsetname]
    except: raise OptimaException('To define constraints, you must supply a program set name as an input')
    return progset

def constraintstoabsconstraints(project=None, progsetname=None,constraints=None,totalbudget=None, verbose=2,eps=0.001):
    if constraints is None: return None
    if totalbudget is None: raise OptimaException('constraintstoabsconstraints() needs the total budget being optimized.')

    progset = getprogsetfromproject(project=project,progsetname=progsetname,function='constraintstoabsconstraints')
    defbudget = progset.getdefaultbudget()
    absconstraints = dcp(constraints)

    for progname in progset.programs.keys():
        if constraints['min'][progname] is not None:
            absconstraints['min'][progname] = constraints['min'][progname] * totalbudget / (sum(defbudget[:])+eps) * defbudget[progname]
        if constraints['max'][progname] is not None:
            absconstraints['max'][progname] = constraints['max'][progname] * totalbudget / (sum(defbudget[:])+eps) * defbudget[progname]
    return absconstraints

def proporigconstraintstoabsconstraints(project=None, progsetname=None,proporigconstraints=None, verbose=2):
    if proporigconstraints is None: return None

    progset = getprogsetfromproject(project=project,progsetname=progsetname,function='proporigconstraintstoabsconstraints')
    defbudget = progset.getdefaultbudget()
    absconstraints = dcp(proporigconstraints)

    for progname in progset.programs.keys():
        if proporigconstraints['min'][progname] is not None:
            absconstraints['min'][progname] = proporigconstraints['min'][progname] * defbudget[progname]
        if proporigconstraints['max'][progname] is not None:
            absconstraints['max'][progname] = proporigconstraints['max'][progname] * defbudget[progname]
    return absconstraints


def constraintstoprogorigconstraints(project=None, progsetname=None,constraints=None,totalbudget=None, verbose=2,eps=0.001):
    if constraints is None: return None
    if totalbudget is None: raise OptimaException('constraintstoprogorigconstraints() needs the total budget being optimized.')

    progset = getprogsetfromproject(project=project,progsetname=progsetname,function='constraintstoprogorigconstraints')
    defbudget = progset.getdefaultbudget()
    proporigconstraints = dcp(constraints)

    for progname in progset.programs.keys():
        if constraints['min'][progname] is not None:
            proporigconstraints['min'][progname] = constraints['min'][progname] * totalbudget / (sum(defbudget[:])+eps)
        if constraints['max'][progname] is not None:
            proporigconstraints['max'][progname] = constraints['max'][progname] * totalbudget / (sum(defbudget[:])+eps)
    return proporigconstraints

def absconstraintstoprogorigconstraints(project=None, progsetname=None,absconstraints=None, verbose=2):
    if absconstraints is None: return None

    progset = getprogsetfromproject(project=project,progsetname=progsetname,function='absconstraintstoprogorigconstraints')
    defbudget = progset.getdefaultbudget()
    proporigconstraints = dcp(absconstraints)

    for progname in progset.programs.keys():
        if defbudget[progname] == 0:  # absolute constraints cannot be turned into proporigconstraints if the origbudget is 0
            proporigconstraints['min'][progname] = 0.0
            proporigconstraints['max'][progname] = None
            continue
        if absconstraints['min'][progname] is not None:
            proporigconstraints['min'][progname] = absconstraints['min'][progname] / defbudget[progname]
        if absconstraints['max'][progname] is not None:
            proporigconstraints['max'][progname] = absconstraints['max'][progname] / defbudget[progname]
    return proporigconstraints

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
    objectives['which']          = which
    objectives['keys']           = ['death', 'inci', 'daly'] # Define valid keys
    objectives['cascadekeys']    = ['propdiag', 'proptreat', 'propsuppressed']
    objectives['keylabels']      = odict({ # Define key labels
                                        'death':          'Deaths', 
                                        'inci':           'New infections', 
                                        'daly':           'DALYs', 
                                        'propdiag':       'Proportion diagnosed',
                                        'proptreat':      'Proportion treated (of those diagnosed)',
                                        'propsuppressed': 'Proportion suppressed (of those treated)'})
    objectives['propdiag']       = 0
    objectives['proptreat']      = 0
    objectives['propsuppressed'] = 0
    objectives['start']          = 2020 # "Year to begin optimization"
    objectives['end']            = 2030 # "Year to project outcomes to"
    objectives['budget']         = defaultbudget # "Annual budget to optimize"
    if which in ['outcome', 'outcomes']:
        objectives['base']        = None # "Baseline year to compare outcomes to"
        objectives['budgetscale'] = [1.] # "Scale factors to apply to budget"
        objectives['deathweight'] = 5    # "Relative weight per death"
        objectives['inciweight']  = 1    # "Relative weight per new infection"
        objectives['dalyweight']  = 0    # "Relative weight per DALY"
        objectives['deathfrac']   = None # Fraction of deaths to get to
        objectives['incifrac']    = None # Fraction of incidence to get to
        objectives['dalyfrac']    = None # Fraction of DALYs to get to
    elif which=='money':
        objectives['base']        = 2015 # "Baseline year to compare outcomes to"
        objectives['deathweight'] = None # "Death weighting"
        objectives['inciweight']  = None # "Incidence weighting"
        objectives['dalyweight']  = None # "Incidence weighting"
        objectives['deathfrac']   = 0.25 # Fraction of deaths to avert
        objectives['incifrac']    = 0.25 # Fraction of incidence to avert
        objectives['dalyfrac']    = 0 # Fraction of DALYs to avert
    else:
        raise OptimaException('"which" keyword argument must be either "outcome" or "money"')

    return objectives


def defaultconstraints(project=None, progsetname=None, verbose=2):
    """
    Define constraints for minimize outcomes optimization: at the moment, just
    total budget constraints defned as a fraction of current spending. Fixed costs
    are treated differently, and ART is hard-coded to not decrease.

    Version: 2017jun04
    """

    printv('Defining default constraints...', 3, verbose=verbose)

    progset = getprogsetfromproject(project=project,progsetname=progsetname,function='defaultconstraints')

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
    fixedkeys = ['ART', 'PMTCT', 'OST']
    for key in fixedkeys:
        if key in constraints['min'].keys():
            constraints['min'][key] = 1.0 # By default, don't let funding decrease

    return constraints

def defaultabsconstraints(project=None, progsetname=None, verbose=2):
    """
    Helper function to get the default absolute constraints for an optimization from the default budget, using the
    defaultconstraints() function above which are relative to the default budget, then getting
    absolute spending values from those.
    Also converts
    Args:
        project: project
        progsetname: progsetname
        verbose: verbosity

    Returns:

    """
    printv('Defining default absolute constraints...', 3, verbose=verbose)

    progset = getprogsetfromproject(project=project,progsetname=progsetname,function='defaultabsconstraints')
    defconstraints = defaultconstraints(project,progsetname,verbose)
    return proporigconstraintstoabsconstraints(project=project,progsetname=progsetname,proporigconstraints=defconstraints,verbose=verbose)

def defaulttvsettings(**kwargs):
    '''
    Make default settings for time-varying optimization.
    
    Can overwritedefaults with kwargs, e.g.
        tvsettings = defaulttvsettings(tvconstrain=False)    
    
    Version: 2017oct29
    '''
    tvsettings = odict()
    tvsettings['timevarying'] = False # By default, do not use time-varying optimization
    tvsettings['tvconstrain'] = True # Whether or not to constrain the budget at each point in time
    tvsettings['tvstep'] = 1.0 # NUmber of years per step
    tvsettings['tvinit'] = None # Optional array with the same length as the budget vector to initialize to; if None, will default to 0
    tvsettings['asdstep'] = 0.1 # Default ASD step size
    tvsettings['asdlim'] = 5.0 # Minimum/maximum limit
    if kwargs: tvsettings.update(kwargs)
    return tvsettings


def calcoptimindsoptimkeys(functionname, prognamelist=None, progset=None, optiminds = None, optimkeys=None, reorderprograms=True, verbose=2):
    """
    A helper function that calculates the optiminds and optimkeys from the progset if it is given.
    It also copies the order of the programs from the keys of the prognamelist to the progset if reorderprograms=True.

    If no progset is given, it ensures the optimkeys and the optiminds are referring to the same programs from the
    prognamelist, preferring to use the optimkeys if they are given.

    Making sure the optiminds match up to the proper location in the dictionary as the optimkeys helps avoid tricky to
    diagnose errors.

    Example usage: (constraints['name'] is an odict with short program names as the keys)
    constraintskeys = constraints['name'].keys() if (constraints is not None) else None
    optiminds, optimkeys = calcoptimindsoptimkeys('thisfunctionsname', prognamelist=constraintskeys, progset=progset,
                                                  optiminds=optiminds, optimkeys=optimkeys, reorderprograms=True, verbose=verbose)
    note in this example optimkeys and optiminds are overriden and progset is reordered to match the order of prognamelist
    """
    if progset is not None:
        if prognamelist is not None and reorderprograms:
            progset.reorderprograms(prognamelist)
        optimizable = array(progset.optimizable())
        optiminds = findinds(optimizable)
        progkeys = array(progset.programs.keys())
        optimkeys = progkeys[optiminds]

    elif prognamelist is not None:
        if optimkeys is not None:
            optimkeys = array(optimkeys)
            if optiminds is not None:
                optiminds = None
                printv(f"Warning: {functionname}() was supplied with both optimkeys and optiminds. Using the optimkeys {optimkeys} not the optiminds as keys are more reliable.", 1, verbose)
        elif optiminds is not None:
            optiminds = array(optiminds)
            progkeys = array(prognamelist)  # Array of all allowable keys
            optimkeys = progkeys[optiminds]
            printv(f"Warning: {functionname}() wasn't supplied with optimkeys and instead was given optiminds. From optiminds {optiminds}, the following optimkeys {optimkeys} have been assumed. For more reliable constraints, use optimkeys.", 1, verbose)
        else:
            errmsg = f"Error: calcoptimindsoptimkeys() called from {functionname} needs either optimkeys or optiminds if no programset is given."
            raise OptimaException(errmsg)

        if optiminds is None:
            optiminds = []
            for i, key in enumerate(prognamelist):
                if key in optimkeys:
                    optiminds.append(i)
            optiminds = array(optiminds)

    else:
        errmsg = f"Error: calcoptimindsoptimkeys() called from {functionname} needs either a progset or an odict with the programs as the keys of the odict, but neither were given."
        raise OptimaException(errmsg)

    return optiminds, optimkeys


def constrainbudget(origbudget=None, budgetvec=None, totalbudget=None, absconstraints=None, scaleupmethod='multiply', optiminds=None, optimkeys=None,
                    tolerance=1e-2, overalltolerance=1.0, outputtype=None, verbose=2, tvsettings=None):
    """ Take an unnormalized/unconstrained budgetvec and normalize and constrain it """
    # Optional printing for debugging
    # print(f'\n\n!?! constrainbudget called with \norigbudget={origbudget},\nbudgetvec={budgetvec},\nscaleupmethod={scaleupmethod},\ntotalbudget={totalbudget},\nabsconstraints={absconstraints},\noptiminds={optiminds},\noptimkeys={optimkeys},'
    #                                                                                               f'\ntolerance={tolerance},\noveralltolerance={overalltolerance},\noutputtype={outputtype},\nverbose={verbose},\ntvsettings={tvsettings}')

    # # Prepare this budget for later scaling and the like
    # origbudgetcopy = dcp(origbudget)
    
    # Handle zeros
    # if sum(origbudgetcopy[:])==0: origbudgetcopy[:] += tolerance
    if sum(budgetvec)==0:            budgetvec[:] += tolerance

    # # Calculate the current total budget
    # currenttotal = sum(origbudgetcopy[:]) # WARNING, assumes it's an odict
    # scaleratio = totalbudget/float(currenttotal) # Calculate the ratio between the original budget and the supplied budget

    # # Calculate a uniformly scaled budget
    # rescaledorigbudget = dcp(origbudgetcopy)
    # for key in rescaledorigbudget.keys(): rescaledorigbudget[key] *= scaleratio # This is the original budget scaled to the total budget
    # if abs(sum(rescaledorigbudget[:])-totalbudget)>overalltolerance:
    #     errormsg = 'Rescaling budget failed (%f != %f)' % (sum(rescaledorigbudget[:]), totalbudget)
    #     raise OptimaException(errormsg)

    # # Calculate the minimum amount that can be spent on the fixed costs
    # rescaledminfixed = dcp(rescaledorigbudget) # This is the rescaled budget, but with the minimum fixed costs -- should be <= totalbudget

    # Get optiminds and optimkeys
    optiminds, optimkeys = calcoptimindsoptimkeys('constrainbudget', prognamelist=origbudget.keys(), progset=None,
                                                  optiminds=optiminds, optimkeys=optimkeys, reorderprograms=False, verbose=verbose)
    progkeys = array(origbudget.keys())  # Array of all allowable keys
    fixedkeys = array([p for p in progkeys if p not in optimkeys]) # Get the complement of optimkeys
    # minfixed = 0.0
    # for key in fixedkeys:
    #     rescaledminfixed[key] = rescaledorigbudget[key]*absconstraints['min'][key]
    #     minfixed += rescaledminfixed[key]

    # Calculate the total amount available for the optimizable programs
    optimbudget = totalbudget - sum(origbudget[fixedkeys])
    optimscaleratio = optimbudget/float(sum(budgetvec)) # If totalbudget=sum(origbudget) and fixed cost lower limits are 1, then optimscaleratio=1

    # Scale the supplied budgetvec to meet this available amount
    if scaleupmethod == 'multiply' or optimscaleratio <= 1:
        scaledbudgetvec = dcp(budgetvec*optimscaleratio)
        # print(f'Rescaling budget with multiply method, scaleupmethod: {scaleupmethod}, optimscaleratio {optimscaleratio}, budgetvec {budgetvec}, scaledbudgetvec {scaledbudgetvec} with sum {sum(scaledbudgetvec)}, optimbudget {optimbudget}')
    else: # scaleupmethod == 'add'
        difference = optimbudget - float(sum(budgetvec))
        scaledbudgetvec = dcp(budgetvec)
        for i,v in enumerate(scaledbudgetvec): scaledbudgetvec[i] += difference/len(budgetvec) # This is the original budget scaled to the total budget
        # print(f'Rescaling budget with addition method, scaleupmethod: {scaleupmethod}, optimscaleratio {optimscaleratio}, budgetvec {budgetvec}, scaledbudgetvec {scaledbudgetvec} with sum {sum(scaledbudgetvec)}, optimbudget {optimbudget}')
    # scaledbudgetvec = dcp(budgetvec*optimscaleratio)
    if abs(sum(scaledbudgetvec)-optimbudget)>overalltolerance:
        errormsg = 'Rescaling budget failed (%f != %f)' % (sum(scaledbudgetvec), optimbudget)
        raise OptimaException(errormsg)

    # Calculate absolute limits from relative limits
    abslimits = dcp(absconstraints)
    for pkey in progkeys:
        if abslimits['min'][pkey] is None: abslimits['min'][pkey] = 0
        if abslimits['max'][pkey] is None: abslimits['max'][pkey] = inf
    # for oi,okey in enumerate(optimkeys): # Don't worry about non-optimizable programs at this point -- oi = 0,1,2,3; oind = e.g. 0, 1, 4, 8
    #     # Fully-relative limits (i.e. scale according to total spend). - consider making relative to origbudget - needs more thought
    #     if isfinite(abslimits['min'][okey]): abslimits['min'][okey] *= rescaledorigbudget[okey] # origbudget[okey]
    #     if isfinite(abslimits['max'][okey]): abslimits['max'][okey] *= rescaledorigbudget[okey] # origbudget[okey]


    ### optimbudget, scaledbudgetvec,rescaledminfixed,totalbudget

    # Apply constraints on optimizable parameters
    noptimprogs = len(optimkeys) # Number of optimizable programs
    limlow = zeros(noptimprogs, dtype=bool)
    limhigh = zeros(noptimprogs, dtype=bool)
    for oi,okey in enumerate(optimkeys):
        if scaledbudgetvec[oi] <= abslimits['min'][okey]:
            scaledbudgetvec[oi] = abslimits['min'][okey]
            limlow[oi] = True
        if scaledbudgetvec[oi] >= abslimits['max'][okey]:
            scaledbudgetvec[oi] = abslimits['max'][okey]
            limhigh[oi] = True

    # Too high
    count = 0
    countmax = 1e4
    while sum(scaledbudgetvec) > optimbudget+tolerance:
        count += 1
        if count>countmax: raise OptimaException('Tried %i times to fix budget and failed! (wanted: %g; actual: %g' % (count, optimbudget, sum(scaledbudgetvec)))
        overshoot = sum(scaledbudgetvec) - optimbudget
        toomuch = sum(scaledbudgetvec[~limlow]) / float((sum(scaledbudgetvec[~limlow]) - overshoot)+tolerance)
        print(f'\n!! count {count} overshoot: {overshoot}, toomuch: {toomuch} == 0 {toomuch ==0},sum(scaledbudgetvec[~limlow]): {sum(scaledbudgetvec[~limlow])} {sum(scaledbudgetvec[~limlow]) < tolerance}, scaledbudgetvec {sum(scaledbudgetvec)}:{scaledbudgetvec}, optimbudget {optimbudget}, abslimits:\n{abslimits}')
        for oi,okey in enumerate(optimkeys):
            if not(limlow[oi]):
                proposed = scaledbudgetvec[oi] / float(toomuch)
                if proposed <= abslimits['min'][okey]:
                    proposed = abslimits['min'][okey]
                    limlow[oi] = True
                scaledbudgetvec[oi] = proposed

    # Too low
    while sum(scaledbudgetvec) < optimbudget-tolerance:
        count += 1
        if count>countmax: raise OptimaException('Tried %i times to fix budget and failed! (wanted: %g; actual: %g' % (count, optimbudget, sum(scaledbudgetvec)))
        undershoot = optimbudget - sum(scaledbudgetvec)
        toolittle = (sum(scaledbudgetvec[~limhigh]) + undershoot) / float(sum(scaledbudgetvec[~limhigh])+tolerance)
        print(f'\n!! count {count} undershoot: {undershoot}, toolittle: {toolittle}, scaledbudgetvec {sum(scaledbudgetvec)}:{scaledbudgetvec}, optimbudget {optimbudget}, abslimits:\n{abslimits}')
        for oi,okey in enumerate(optimkeys):
            if not(limhigh[oi]):
                proposed = scaledbudgetvec[oi] * toolittle
                if proposed >= abslimits['max'][okey]:
                    proposed = abslimits['max'][okey]
                    limhigh[oi] = True
                scaledbudgetvec[oi] = proposed

    print(f'\n!!gooood!! count {count} scaledbudgetvec {sum(scaledbudgetvec)}:{scaledbudgetvec}, optimbudget {optimbudget}, abslimits:\n{abslimits}')

    # Reconstruct the budget odict using the rescaled budgetvec and the rescaled original amount
    constrainedbudget = dcp(origbudget) # This budget has the right fixed costs, TODO check???
    # constrainedbudget = dcp(rescaledminfixed) # This budget has the right fixed costs
    for oi,okey in enumerate(optimkeys):
        constrainedbudget[okey] = scaledbudgetvec[oi]
    if abs(sum(constrainedbudget[:])-totalbudget)>overalltolerance:
        errormsg = 'final budget amounts differ (%f != %f)' % (sum(constrainedbudget[:]), totalbudget)
        raise OptimaException(errormsg)


    # Optionally return the calculated upper and lower limits as well as the original budget and vector
    constrainedbudgetvec = dcp(constrainedbudget[optimkeys])

    # Optional printing for debugging
    lowerlim = dcp(abslimits['min'][optimkeys])
    upperlim = dcp(abslimits['max'][optimkeys])
    # print(f'\n\n!?! constrainbudget returning \nconstrainedbudget: {constrainedbudget},\nconstrainedbudgetvec: {constrainedbudgetvec},\nlowerlim: {lowerlim},\nupperlim: {upperlim}')

    if outputtype=='odict':
        return constrainedbudget
    elif outputtype=='vec':
        return constrainedbudgetvec
    elif outputtype=='full':
        lowerlim = dcp(abslimits['min'][optimkeys])
        upperlim = dcp(abslimits['max'][optimkeys])
        return constrainedbudget, constrainedbudgetvec, lowerlim, upperlim
    else:
        raise OptimaException('Must specify an output type of "odict", "vec", or "full"; you specified "%s"' % outputtype)



def tvfunction(budgetdict=None, years=None, pars=None, optiminds=None, optimkeys=None, tvsettings=None):
    '''
    Convert a odict budget, vector of years, and a vector of parameters (of same
    length as the budget) into a corresponding normalized dictionary of
    arrays.

    This function has not been fully converted to using optimkeys, but since it recalculates the optiminds
    using the optimkeys (if they are available) it should not be an issue.
    '''
    # Get optiminds and optimkeys, even though optimkeys aren't used in this function,
    optiminds, optimkeys = calcoptimindsoptimkeys('tvfunction', prognamelist=budgetdict.keys(), progset=None,
                                                  optiminds=optiminds, optimkeys=optimkeys, reorderprograms=False)

    # Process x-axis
    years = promotetoarray(years) # Make sure it's an array
    x = years-years[0] # Start at zero
    x /= x.max() # Normalize
    npts = len(years) # Number of points to calculate over
    
    # Loop over the budget dictionary and process each one
    output = dcp(budgetdict) # Not sure if this is necessary, but to be on the safe side...
    for i,val in enumerate(output.values()): # Loop over the programs and calculate the budget for each
        if i in optiminds:
            y = exp(pars[i]*x)
            y /= y.mean()
        else:
            y = ones(npts)
        output[i] = output[i]*y

    # Optionally constrain each time point
    if tvsettings and tvsettings['tvconstrain']:
        optimbudget = budgetdict[:][optiminds].sum() # The amount to constrain to
        optimdata = output[:][optiminds,:] # The spending for every optimizable program for every year
        factors = zeros(npts) # List of correction factors
        for pt in range(npts): # Loop over and calculate correction factors
            factors[pt] = optimbudget/optimdata[:,pt].sum()
        for ind in optiminds: # Loop over programs and correct them
            output[ind] = output[ind]*factors # Correct all time points for this program
    
    return output


def separatetv(inputvec=None, optiminds=None, optimkeys=None):
    ''' Decide if the budget vector includes time-varying information '''
    if   optimkeys is not None: noptimprogs = len(optimkeys)
    elif optiminds is not None: noptimprogs = len(optiminds)
    else:
        errmsg = f"separatetv() wasn't supplied with optimkeys or optiminds. Please supply one of these."
        raise OptimaException(errmsg)

    ndims = 2 # Semi-hard-code the number of dimensions of the time-varying optimization
    if len(inputvec)==noptimprogs:
        budgetvec = inputvec
        tvcontrolvec = None
    elif len(inputvec)==ndims*noptimprogs:
        budgetvec = dcp(inputvec[:noptimprogs]) # Replace the budget vector with the ordinary budget vector
        tvcontrolvec = dcp(inputvec[noptimprogs:]) # Pull out control vector
    else:
        errormsg = 'Budget vector must be either length %i or length %i, not %i' % (noptimprogs, ndims*noptimprogs, len(inputvec))
        raise OptimaException(errormsg)
    return (budgetvec, tvcontrolvec)




################################################################################################################################################
### The main meat of the matter
################################################################################################################################################

def outcomecalc(budgetvec=None, which=None, project=None, parsetname=None, progsetname=None, scaleupmethod='multiply',
                objectives=None, absconstraints=None, totalbudget=None, optiminds=None, optimkeys=None, origbudget=None,
                tvec=None, initpeople=None, initprops=None, startind=None, outputresults=False, verbose=2, ccsample='best',
                doconstrainbudget=True, tvsettings=None, tvcontrolvec=None, origoutcomes=None, penalty=1e9, **kwargs):
    ''' Function to evaluate the objective for a given budget vector (note, not time-varying) '''

    # Set up defaults
    if which is None: 
        if objectives is not None: which = objectives['which']
        else:                      which = 'outcomes'
    if parsetname  is None: parsetname  = -1
    if progsetname is None: progsetname = -1
    parset  = project.parsets[parsetname] 
    progset = project.progsets[progsetname]

    # Reorder the programs to match the order of the constraints, and get optiminds and optimkeys
    constraintskeys = absconstraints['name'].keys() if (absconstraints is not None) else None
    optiminds, optimkeys = calcoptimindsoptimkeys('outcomecalc', prognamelist=constraintskeys, progset=progset,
                                                  optiminds=optiminds, optimkeys=optimkeys, reorderprograms=True, verbose=verbose)

    if objectives  is None: objectives  = defaultobjectives(project=project,  progsetname=progsetname, which=which)
    if absconstraints is None: absconstraints = defaultabsconstraints(project=project, progsetname=progsetname)  # Default constraints are in the same order as progset, so the order should be retained
    if totalbudget is None:
        if budgetvec is None: totalbudget = objectives['budget']
        else:                 totalbudget = budgetvec[:].sum() # If a budget vector is supplied
    if origbudget  is None: origbudget  = progset.getdefaultbudget()
    if budgetvec   is None: budgetvec   = dcp(origbudget[:][optiminds])
    if isinstance(budgetvec, dict): budgetvec = dcp(budgetvec[:][optiminds]) # Assuming odict
       
    # Validate input    
    arglist = [budgetvec, which, parset, progset, objectives, totalbudget, absconstraints, optimkeys, origbudget]
    if any([arg is None for arg in arglist]):  # WARNING, this kind of obscures which of these is None -- is that ok? Also a little too hard-coded...
        raise OptimaException('outcomecalc() requires which, budgetvec, parset, progset, objectives, totalbudget, constraints, optimkeys, origbudget, tvec as inputs at minimum; argument %i is None' % arglist.index(None))
    if which=='outcome': which='outcomes' # I never remember which it's supposed to be, so let's fix it here
    if which not in ['outcomes','money']:
        errormsg = 'optimize(): "which" must be "outcomes" or "money"; you entered "%s"' % which
        raise OptimaException(errormsg)
    
    # Handle time-varying optimization -- try pulling out of the budget vector, if required
    if tvcontrolvec is None:
        budgetvec, tvcontrolvec = separatetv(inputvec=budgetvec, optimkeys=optimkeys)
    
    # Normalize budgetvec and convert to budget -- WARNING, is there a better way of doing this?
    if doconstrainbudget:
        # print('constraining budget from outcomecalc')
        constrainedbudget = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, absconstraints=absconstraints, optimkeys=optimkeys, outputtype='odict', scaleupmethod=scaleupmethod)
    else:
        constrainedbudget = dcp(origbudget)
        if len(budgetvec)==len(optimkeys): constrainedbudget[optimkeys] = budgetvec # Assume it's just the optimizable programs
        else:                              constrainedbudget[:]         = budgetvec # Assume it's all programs
        
    # Get the budget array to run
    if tvsettings is None or not tvsettings['timevarying'] or tvcontrolvec is None: # If not running time-varying optimization, it's easy
        paryears = objectives['start']
        budgetarray = dcp(constrainedbudget) # Just copy the constrained budget (may not be an array)
    else: # Otherwise, it's not easy
        paryears = inclusiverange(start=objectives['start'], stop=objectives['end'], step=tvsettings['tvstep']) # Create the time vector
        nyears = len(paryears) # Figure out how many years we're doing this for
        budgetarray = tvfunction(budgetdict=constrainedbudget, years=paryears, pars=tvcontrolvec, optiminds=optiminds, tvsettings=tvsettings)
        if doconstrainbudget and tvsettings['tvconstrain']: # Do additional constraints
            for y in range(nyears):
                budgetvec = budgetarray.fromeach(ind=y, asdict=False)
                constrainedbudget = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, absconstraints=absconstraints, optimkeys=optimkeys, outputtype='odict', scaleupmethod=scaleupmethod)
                budgetarray.toeach(ind=y, val=constrainedbudget[:])
    
    # Get coverage and actual dictionary, in preparation for running
    thiscoverage = progset.getprogcoverage(budget=budgetarray, t=paryears, parset=parset, sample=ccsample)
    thisparsdict = progset.getpars(coverage=thiscoverage, t=paryears, parset=parset, sample=ccsample)
    
    # Figure out which indices to run for and actually run the model
    tvec       = project.settings.maketvec(end=objectives['end'])
    # initpeople = None # Not anymore! # WARNING, unfortunately initpeople is still causing mismatches -- turning off for now despite the large (2.5x) performance penalty
    if initpeople is None: startind = None
    elif startind is None: startind = findnearest(tvec, objectives['start']) # Assume initpeople is from the start of the optimization
    else: pass      # Assume initpeople and startind are corresponding to the same time
    results = project.runsim(pars=thisparsdict, parsetname=parsetname, progsetname=progsetname, coverage=thiscoverage, budget=budgetarray, budgetyears=paryears, tvec=tvec, initpeople=initpeople, initprops=initprops, startind=startind, verbose=0, label=project.name+'-optim-outcomecalc', doround=False, addresult=False, advancedtracking=False, **kwargs)

    # Figure out which indices to use
    initialind = findnearest(results.tvec, objectives['start'])
    finalind   = findnearest(results.tvec, objectives['end'])
    if which=='money': baseind = findnearest(results.tvec, objectives['base']) # Only used for money minimization
    if which=='outcomes': indices = arange(initialind, finalind) # Only used for outcomes minimization
    
    ## Here, we split depending on whether it's a outcomes or money minimization:
    if which=='outcomes':
        # Calculate outcome
        outcome = 0 # Preallocate objective value
        rawoutcomes = odict()

        # Calculate the outcome
        for key in objectives['keys']:
            thisweight = objectives[key+'weight'] # e.g. objectives['inciweight'] #CKCHANGE
            thisoutcome = results.main['num'+key].tot[0][indices].sum() # The instantaneous outcome e.g. main['numdeath'] -- 0 is since best
            rawoutcomes['num'+key] = thisoutcome*results.dt
            outcome += thisoutcome*thisweight*results.dt # Calculate objective
            if origoutcomes and penalty and thisweight>0:
                if rawoutcomes['num'+key]>origoutcomes.rawoutcomes['num'+key]:
                    outcome += penalty # Impose a large penalty if the solution is worse
        
        # Include cascade values
        for key in objectives['cascadekeys']:
            thisweight = objectives[key] # e.g. objectives['proptreat']
            thisoutcome = 1.0 - results.main[key].tot[0][-1] # e.g. main['proptreat'] -- 0 is since best, subtract from 1 to invert, use final value
            rawoutcomes[key] = thisoutcome
            outcome += thisoutcome*thisweight # Calculate objective
            if origoutcomes and penalty and thisweight>0:
                if rawoutcomes[key]>origoutcomes.rawoutcomes[key]:
                    outcome += penalty # Impose a large penalty if the solution is worse

        # Output results
        if outputresults:
            results.outcome = outcome
            results.rawoutcomes = rawoutcomes
            results.budgetyears = [objectives['start']] # Use the starting year
            results.budget = constrainedbudget # Convert to budget
            results.budgets = odict({'outcomecalc':constrainedbudget}) # For plotting
            results.outcomesettings = odict([('objectives', objectives), ('absconstraints', absconstraints), ('tvsettings', tvsettings)])
            
            # Store time-varying part
            if tvsettings and tvsettings['timevarying']:
                results.timevarying = odict() # One-liner: multires.timevarying = odict().makefrom(locals(), ['tvyears', 'tvpars', 'tvbudgets'])
                results.timevarying['tvyears'] = dcp(paryears)
                results.timevarying['tvpars'] = dcp(tvcontrolvec)
                results.timevarying['tvbudgets'] = dcp(budgetarray)
                
            output = results
        else:
            output = outcome

    ## It's money
    elif which=='money':
        # Calculate outcome
        targetsmet = True # Assume success until proven otherwise (since operator is AND, not OR)
        baseline = odict()
        final = odict()
        target = odict()
        targetfrac = odict([(key,objectives[key+'frac']) for key in objectives['keys']]) # e.g. {'inci':objectives['incifrac']} = 0.4 = 40% reduction in incidence
        for key in objectives['keys']:
            thisresult = results.main['num'+key].tot[0] # the instantaneous outcome e.g. objectives['numdeath'] -- 0 is since best #CKCHANGE
            baseline[key] = float(thisresult[baseind])
            final[key] = float(thisresult[finalind])
            if targetfrac[key] is not None:
                target[key] = float(baseline[key]*(1-targetfrac[key]))
                if final[key] > target[key]: targetsmet = False # Targets are NOT met #CKCHANGE
            else: target[key] = -1 # WARNING, must be a better way of showing no defined objective
        
        targetprops = odict([(key,objectives[key]) for key in objectives['cascadekeys']])
        for key in objectives['cascadekeys']:
            thisresult = 1 - results.main[key].tot[0] # the instantaneous outcome e.g. objectives['numdeath'] -- 0 is since best #CKCHANGE
            final[key] = float(thisresult[finalind])
            if objectives[key] is not None:
                target[key] = 1 - objectives[key]
                if final[key] > objectives[key]: targetsmet = False # Targets are NOT met #CKCHANGE
            else: target[key] = -1 # WARNING, must be a better way of showing no defined objective

        # Output results
        if outputresults:
            results.outcomes = odict([('baseline',baseline), ('final',final), ('target',target), ('targetfrac',targetfrac), ('targetprop',targetprops)])
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
    absconstraints = optim.getabsconstraints()

    # Reorder the programs to match the order of the constraints
    if absconstraints is not None: progset.reorderprograms(absconstraints['name'].keys())

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
        
#    print('HII203948III')
#    print(multi)
#    print(nchains)

    # Run outcomes minimization
    if which=='outcomes':
        multires = minoutcomes(project=project, optim=optim, tvec=tvec, verbose=verbose, maxtime=maxtime, maxiters=maxiters, absconstraints=absconstraints,
                               origbudget=origbudget, randseed=randseed, mc=mc, label=label, die=die, stoppingfunc=stoppingfunc, **kwargs)

    # Run money minimization
    elif which=='money':
        multires = minmoney(project=project, optim=optim, tvec=tvec, verbose=verbose, maxtime=maxtime, maxiters=maxiters, 
                            fundingchange=1.2, randseed=randseed, stoppingfunc=stoppingfunc,absconstraints=absconstraints, **kwargs)
    
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
    
    # Set defaults
    if nchains is None:    nchains = 4
    if nblocks is None:    nblocks = 10
    nblocks = 1 #TEMPORARY fix as blocks don't apply constraints properly - TODO fix properly
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
            optim._threadindex = thread # Store the thread index 
            optimargs = (optim, blockiters, maxtime, verbose, stoppingfunc, die, origbudget, thisseed, mc, label, outputqueue, kwargs)
            prc = Process(target=optimize, args=optimargs)
            prc.start()
            processes.append(prc)
        
        # Tidy up: close the threads and gather the results
        for i in range(nchains):
            result = outputqueue.get() # This is needed or else the process never finishes
            threadindex = result.optim._threadindex # To ensure a robust ordering
            outputlist[threadindex] = result
            if block==0 and threadindex==0: origresults = dcp(result) # Copy the original results from the first optimization
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
        
        origbudget = outputlist[bestfvalind].budgets[-1] # Update the budget and use it as the input for the next block -- this is key!
    
    # Assemble final results object from the initial and final run
    results = dcp(outputlist[bestfvalind]) # Use best results as the basis for the output
    results.improvement[0] = sanitize(fvalarray[bestfvalind,:]) # Store fval vector in normal format
    results.multiimprovement = fvalarray # Store full fval array
    try:    results.budgets['Baseline'] = origresults.budgets['Baseline'] # Assume it's called baseline
    except: results.budgets[0]          = origresults.budgets[0] # If that fails, just use the first entry
    
    return results





def tvoptimize(project=None, optim=None, tvec=None, verbose=None, maxtime=None, maxiters=1000, origbudget=None, 
               ccsample='best', randseed=None, mc=3, label=None, die=False, **kwargs):
    '''
    Run a time-varying optimization. See project.optimize() for usage examples, and optimize()
    for kwarg explanation.
    
    Simple example:
        import optima as op
        P = op.demo(0, which='simple'); P.parset().fixprops(False) # Create the project, and allow ART to be optimized
        P.optimize(timevarying=1, mc=0, maxiters=30, randseed=1, tvconstrain=False)
        op.pygui(P)
    
    Version: 2017oct30
    '''

    printv('Preparing to run a time-varying optimization...', 1, verbose)
    
    # Do a preliminary non-time-varying optimization
    optim.tvsettings['timevarying'] = False # Turn off for the first run
    prelim = optimize(optim=optim, maxtime=maxtime, maxiters=maxiters, verbose=verbose, origbudget=origbudget,
                ccsample=ccsample, randseed=randseed, mc=mc, label=label, die=die, keepraw=True, **kwargs)
    rawresults = prelim.raw['Baseline'][0] # Store the raw results; "Baseline" vs. "Optimized" shouldn't matter, and [0] is the first/best run -- not sure if there is a more robut way
    
    # Add in the time-varying component
    origtotalbudget = dcp(optim.objectives['budget']) # Should be a float, but dcp just in case
    totalbudget = origtotalbudget
    optimconstbudget = dcp(prelim.budgets[-1])
    origbudget = dcp(prelim.budgets[0]) # OK to do this since if supplied as an argument, will be the same; else, it will be populated here
    project = optim.projectref()
    absconstraints = optim.getabsconstraints()

    ## Handle budget and remove fixed costs
    progset = project.progsets[optim.progsetname] # Link to the original program set

    # Reorder the programs to match the order of the constraints, and get optiminds and optimkeys
    optiminds, optimkeys = calcoptimindsoptimkeys('tvoptimize', prognamelist=absconstraints['name'].keys(), progset=progset,
                                                  optiminds=None, optimkeys=None, reorderprograms=True, verbose=verbose)

    budgetvec = optimconstbudget[:][optiminds] # Get the original budget vector
    noptimprogs = len(budgetvec) # Number of optimizable programs
    if label is None: label = ''
    
    # Set up arguments which are shared between outcomecalc and asd
    optim.tvsettings['timevarying'] = True # Turn it back on for everything else
    args = {'which':'outcomes', 
            'project':project, 
            'parsetname':optim.parsetname, 
            'progsetname':optim.progsetname, 
            'objectives':optim.objectives, 
            'absconstraints':absconstraints,
            'totalbudget':origtotalbudget, # Complicated, see below
            'optiminds':optiminds, # Redundant, could probably be removed because optimkeys is given
            'optimkeys':optimkeys,
            'origbudget':origbudget, 
            'tvec':tvec, 
            'ccsample':ccsample, 
            'verbose':verbose, 
            'initpeople':None, # For now, run full time series
            'tvsettings':optim.tvsettings} # Complicated; see below
    
    tmpresults = odict()
    tmpimprovements = odict()
    tmpfullruninfo = odict()
    
    # This generates the baseline results
    tmpresults['Baseline']  = outcomecalc(prelim.budgets['Baseline'],  outputresults=True, doconstrainbudget=False, **args)
    tmpresults['Optimized'] = outcomecalc(prelim.budgets['Optimized'], outputresults=True, doconstrainbudget=False, **args)
    for key,result in tmpresults.items(): 
        result.name = key # Update names
        tmpimprovements[key] = [tmpresults[key].outcome] # Hacky, since expects a list
    
    # Set up budgets to run
    tvbudgetvec = dcp(budgetvec)
    tvcontrolvec = zeros(noptimprogs) # Generate vector of zeros for correct length
    tvvec = concatenate([tvbudgetvec, tvcontrolvec])
    if randseed is None: randseed = int((time()-floor(time()))*1e4) # Make sure a seed is used
    args['totalbudget'] = totalbudget
            
    # Set up the optimizations to run
    bestfval = inf # Value of outcome
    asdresults = odict()
    key = 'Baseline'
    printv('Running time-varying optimization with maxtime=%s, maxiters=%s' % (maxtime, maxiters), 2, verbose)
    if label: thislabel = '"'+label+'-'+key+'"'
    else: thislabel = '"'+key+'"'
    xmin = concatenate([zeros(noptimprogs), -optim.tvsettings['asdlim']+dcp(tvcontrolvec)])
    xmax = concatenate([inf+zeros(noptimprogs), optim.tvsettings['asdlim']+dcp(tvcontrolvec)])
    stepbudget = optim.tvsettings['asdstep']*tvbudgetvec # Step size for budgets
    steptvcontrol = optim.tvsettings['asdstep']+dcp(tvcontrolvec) # Step size for TV parameter
    sinitial = concatenate([stepbudget]*2+[steptvcontrol]*2) # Set the step size -- duplicate for +/-
    args['origbudget'] = optimconstbudget
    
    # Set the initial people
    initialind = findinds(rawresults['tvec'], optim.objectives['start'])
    initpeople = rawresults['people'][:,:,initialind] # Pull out the people array corresponding to the start of the optimization -- there shouldn't be multiple raw arrays here
    args['initpeople'] = initpeople
    
    # Now run the optimization
    origoutcomes = outcomecalc(outputresults=True, **args) # Calculate the initial outcome and pass it back in
    args['origoutcomes'] = origoutcomes
    res = asd(outcomecalc, tvvec, args=args, xmin=xmin, xmax=xmax, sinitial=sinitial, maxtime=maxtime, maxiters=maxiters, verbose=verbose, randseed=randseed, label=thislabel, **kwargs)
    tvvecnew, fvals = res.x, res.details.fvals
    budgetvec, tvcontrolvec = separatetv(inputvec=tvvecnew, optimkeys=optimkeys)
    constrainedbudgetnew, constrainedbudgetvecnew, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, absconstraints=absconstraints, optiminds=optiminds, outputtype='full', tvsettings=optim.tvsettings)
    asdresults[key] = {'budget':constrainedbudgetnew, 'fvals':fvals, 'tvcontrolvec':tvcontrolvec}
    if fvals[-1]<bestfval: 
        bestkey = key # Reset key
        bestfval = fvals[-1] # Reset fval
    
    ## Calculate outcomes
    args['initpeople'] = None # Turn off again to get full results
    new = outcomecalc(asdresults[bestkey]['budget'], tvcontrolvec=tvcontrolvec, outputresults=True, **args)
    new.name = 'Time-varying' # Note: could all be simplified
    tmpresults[new.name] = new
    tmpimprovements[new.name] = asdresults[bestkey]['fvals']
    tmpfullruninfo[new.name] = asdresults # Store everything
    
    ## Output
    multires = Multiresultset(resultsetlist=tmpresults.values(), name='optim-%s' % optim.name)
    for k,key in enumerate(multires.keys): multires.budgetyears[key] = tmpresults[k].budgetyears # Copy budget years
    multires.improvement = tmpimprovements # Store full function evaluation information -- only use last one
    multires.fullruninfo = tmpfullruninfo # And the budgets/outcomes for every different run
    multires.outcomes = dcp(multires.outcome) # Copy to more robust place, and...
    optim.resultsref = multires.name # Store the reference for this result
    
    # Store optimization settings
    multires.optimsettings = odict([('maxiters',maxiters),('maxtime',maxtime),('mc',mc),('randseed',randseed),('tvsettings',optim.tvsettings)])

    return multires



def minoutcomes(project=None, optim=None, tvec=None, absconstraints=None, verbose=None, maxtime=None, maxiters=1000,
                origbudget=None, ccsample='best', randseed=None, mc=3, label=None, die=False, timevarying=None, keepraw=False, stoppingfunc=None, **kwargs):
    ''' Split out minimize outcomes '''

    # Optional printing for debugging
    # print(f'!! minoutcomes called with: optim:{optim}, optim.constraints:{optim.constraints}, optim.objectives:{optim.objectives},tvec:{tvec},origbudget:{origbudget},randseed:{randseed},mc:{mc},timevarying:{timevarying},stoppingfunc:{stoppingfunc}')

    ## Handle budget and remove fixed costs
    if project is None or optim is None: raise OptimaException('An optimization requires both a project and an optimization object to run')
    if absconstraints is None: absconstraints = optim.getabsconstraints()
    # print(f'optim:\n{optim}\n{optim.__dict__}')

    parset  = project.parsets[optim.parsetname] # Link to the original parameter set
    progset = project.progsets[optim.progsetname] # Link to the original program set

    # Reorder the programs to match the order of the constraints, and get optiminds and optimkeys
    optiminds, optimkeys = calcoptimindsoptimkeys('minoutcomes', prognamelist=absconstraints['name'].keys(), progset=progset,
                                                  optiminds=None, optimkeys=None, reorderprograms=True, verbose=verbose)

    nonoptiminds = array([i   for i, key in enumerate(progset.programs) if not (i in optiminds)])
    nonoptimkeys = array([key for i, key in enumerate(progset.programs) if not (i in optiminds)])

    origtotalbudget = dcp(optim.objectives['budget']) # Should be a float, but dcp just in case
    if origbudget is not None:
        origbudget = dcp(origbudget)
    else:
        try: origbudget = dcp(progset.getdefaultbudget())
        except: raise OptimaException('Could not get default budget for optimization')

    budgetvec = origbudget[optimkeys] # Get the original budget
    nprogs = len(origbudget[:]) # Number of programs total
    noptimprogs = len(budgetvec) # Number of optimizable programs
    xmin = zeros(noptimprogs)
    if label is None: label = ''

    # Calculate the initial people distribution
    results = project.runsim(pars=parset.pars, parsetname=optim.parsetname, progsetname=optim.progsetname, tvec=tvec, keepraw=True, verbose=0, label=project.name+'-minoutcomes', addresult=False, advancedtracking=True)
    startind = findnearest(results.raw[0]['tvec'], optim.objectives['start']-1) ## !!! -1 is because of parameter interpolation / smoothing from the current parameters to the budget parameters, we have to start a year before the budget starts
    initpeople = results.raw[0]['people'][:,:,startind] # Pull out the people array corresponding to the start of the optimization -- there shouldn't be multiple raw arrays here
    initprops  = results.raw[0]['props'][:,startind,:]  # Need initprops if running with initpeople

    if stoppingfunc and stoppingfunc():
        raise op.CancelException

    # Calculate original things
    # print('constraining budget 1st minoutcomes',*(origbudget,sum(origbudget[:]),budgetvec,sum(budgetvec),origtotalbudget))
    constrainedbudgetorig, constrainedbudgetvecorig, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=origtotalbudget, absconstraints=absconstraints, optimkeys=optimkeys, outputtype='full', verbose=verbose)

    # Set up arguments which are shared between outcomecalc and asd
    args = {'which':      'outcomes', 
            'project':    project, 
            'parsetname': optim.parsetname, 
            'progsetname':optim.progsetname, 
            'objectives': optim.objectives, 
            'absconstraints':absconstraints,
            'totalbudget':origtotalbudget, # Complicated, see below
            'optimkeys':  optimkeys,
            'origbudget': origbudget, 
            'tvec':       tvec, 
            'ccsample':   ccsample, 
            'verbose':    verbose,
            'startind':   startind,
            'initpeople': initpeople, # Complicated; see below
            'initprops':  initprops,
            'keepraw':    keepraw,
            }
    
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
    
    # Set up storage for extreme budgets
    extremeresults  = odict()
    extremeoutcomes = odict()

    for key,exbudget in extremebudgets.items():

        if stoppingfunc and stoppingfunc():
            raise op.CancelException

        doconstrainbudget = False # Budget is specified fully, don't constrain
        if key=='Baseline':
            args['startind']   = None
            args['initpeople'] = None # Do this so it runs for the full time series, and is comparable to the optimization result
            args['initprops']  = None # Do this so it runs for the full time series, and is comparable to the optimization result
            args['totalbudget'] = origbudget[:].sum() # Need to reset this since constraining the budget
        else:
            args['startind']   = startind
            args['initpeople'] = initpeople # Do this so saves a lot of time (runs twice as fast for all the budget scenarios)
            args['initprops'] = initprops   # Need initprops if running with initpeople
            args['totalbudget'] = origtotalbudget
        extremeresults[key] = outcomecalc(exbudget[optiminds], outputresults=True, doconstrainbudget=doconstrainbudget, **args)
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
        # print('constraining budget from minoutcomes scalefactors')
        constrainedbudget, constrainedbudgetvec, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvec, totalbudget=totalbudget, absconstraints=absconstraints, optimkeys=optimkeys, outputtype='full')
        args['totalbudget'] = totalbudget
        args['initpeople']  = initpeople # Reset initpeople
        args['initprops']   = initprops  # Reset initprops
        args['startind']    = startind   # Reset initpeople

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

                if stoppingfunc and stoppingfunc():
                    raise op.CancelException

                printv('Running optimization "%s" (%i/%i) with maxtime=%s, maxiters=%s' % (key, k+1, len(allbudgetvecs), maxtime, maxiters), 2, verbose)
                if label: thislabel = '"'+label+'-'+key+'"'
                else: thislabel = '"'+key+'"'
                # print('constraining to outcomecalc from minoutcomes scalefactors if totalbudget 1')
                origoutcomes = outcomecalc(outputresults=True, **args) # Calculate the initial outcome and pass it back in
                args['origoutcomes'] = origoutcomes
                # print('Passing over to asd')
                res = asd(outcomecalc, allbudgetvecs[key], args=args, xmin=xmin, maxtime=maxtime, maxiters=maxiters, verbose=verbose, randseed=allseeds[k], label=thislabel, stoppingfunc=stoppingfunc, **kwargs)
                budgetvecnew, fvals = res.x, res.details.fvals
                # print('constraining budget from minoutcomes scalefactors if totalbudget 2')
                constrainedbudgetnew, constrainedbudgetvecnew, lowerlim, upperlim = constrainbudget(origbudget=origbudget, budgetvec=budgetvecnew, totalbudget=totalbudget, absconstraints=absconstraints, optimkeys=optimkeys, outputtype='full')
                asdresults[key] = {'budget':constrainedbudgetnew, 'fvals':fvals}
                if fvals[-1]<bestfval: 
                    bestkey = key # Reset key
                    bestfval = fvals[-1] # Reset fval
            
            ## Calculate final outcomes for the full time vector
            args['initpeople'] = None # Set to None to get full results, not just from start year
            args['initprops']  = None
            args['startind']   = None
            new = outcomecalc(asdresults[bestkey]['budget'], outputresults=True, **args)
            
            ## Name and store outputs
            if len(scalefactors)==1: new.name = 'Optimized' # If there's just one optimization, just call it optimal
            else: new.name = 'Optimized (%.0f%% budget)' % (scalefactor*100.) # Else, say what the budget is
            tmpresults[new.name] = new
            tmpimprovements[new.name] = asdresults[bestkey]['fvals']
            tmpfullruninfo[new.name] = asdresults # Store everything
        else:
            tmpresults['Optimized'] = dcp(tmpresults['Baseline']) # If zero budget, just copy current and rename
            tmpresults['Optimized'].name = 'Optimized' # Rename name to named name
            tmpresults['Optimized'].projectref = Link(project) # Restore link

    ## Output
    multires = Multiresultset(resultsetlist=tmpresults.values(), name='optim-%s' % optim.name)
    optim.resultsref = multires.name # Store the reference for this result
    for k,key in enumerate(multires.keys): multires.budgetyears[key] = tmpresults[k].budgetyears 
    multires.improvement = tmpimprovements # Store full function evaluation information -- only use last one
    multires.extremeoutcomes = extremeoutcomes # Store all of these
    multires.fullruninfo = tmpfullruninfo # And the budgets/outcomes for every different run
    multires.outcomes = dcp(multires.outcome) # Initialize
    multires.outcome = multires.outcomes[-1] # Store these defaults in a convenient place
    multires.optim = optim # Store the optimization object as well
    
    
    # Store optimization settings
    multires.optimsettings = odict([('maxiters',maxiters),('maxtime',maxtime),('mc',mc),('randseed',randseed)])

    return multires






def minmoney(project=None, optim=None, tvec=None, verbose=None, maxtime=None, maxiters=1000, absconstraints=None,
             fundingchange=1.2, tolerance=1e-2, ccsample='best', randseed=None, keepraw=False, die=False, 
             n_throws=None, n_success=None, n_refine=None, schedule=None, multi=None, nchains=None, stoppingfunc=None, **kwargs):
    '''
    A function to minimize money for a fixed objective.

    Version: 2019oct14
    '''
    
    ## Handle budget and remove fixed costs
    if project is None or optim is None: raise OptimaException('An optimization requires both a project and an optimization object to run')
    parset = project.parsets[optim.parsetname] # Original parameter set
    parset.fixprops(False) # It doesn't really make sense to minimize money with these fixed
    progset = project.progsets[optim.progsetname] # Link to the original program set
    if absconstraints is None: absconstraints = optim.getabsconstraints()

    # Reorder the programs to match the order of the constraints, and get optiminds and optimkeys
    optiminds, optimkeys = calcoptimindsoptimkeys('minmoney', prognamelist=absconstraints['name'].keys(), progset=progset,
                                                  optiminds=None, optimkeys=None, reorderprograms=True, verbose=verbose)

    totalbudget = dcp(optim.objectives['budget'])
    origtotalbudget = totalbudget
    try: origbudget = dcp(progset.getdefaultbudget())
    except: raise OptimaException('Could not get default budget for optimization')
    budgetvec = origbudget[:][optiminds] # Get the original budget vector
    origbudgetvec = dcp(budgetvec)
    nprogs = len(budgetvec)
    
    # Define arguments for ASD
    args = {'which':      'money', 
            'project':    project, 
            'parsetname': optim.parsetname, 
            'progsetname':optim.progsetname, 
            'objectives': optim.objectives, 
            'absconstraints':absconstraints,
            'optimkeys':  optimkeys,
            'origbudget': origbudget,
            'tvec':       tvec, 
            'ccsample':   ccsample, 
            'verbose':    verbose,
            'keepraw':    keepraw,
            'doconstrainbudget': True,
            }

    #%% Preliminaries
    start = op.tic()
    
    # Set parameters
    if n_throws  is None: n_throws  = max(50 ,nprogs*5) # Number of throws to try on each round
    if n_success is None: n_success = max(20, nprogs*2) # The number of successes needed to terminate the throws
    if n_refine  is None: n_refine  = 200 # The maximum number of refinement steps to take
    if schedule  is None: schedule  = [0.3, 0.6, 0.8, 0.9, 1.0] # The budget amounts to allocate on each round
    if multi     is None: multi     = False
    search_step  = 2.0 # The size of the steps to establish the upper/lower limits for the binary search
    search_tol   = 0.01 # Tolerance of the binary search (maximum difference between upper and lower limits)
    refine_steps = [0.0, 0.5, 0.8, 0.9, 0.95, 0.99]  # During refinement, factor by which to scale programs
    refine_keep  = 0.5 # During refinement, proportion of difference to reallocate to other programs
    factor       = 1e6 # Units to scale printed out budget numbers
    animate      = False # Whether or not to animate at the end
    if animate: import pylab as pl
    
    if multi: printv('Performing parallel money optimization with %s chains...' % nchains, 2, verbose)
    else:     printv('Performing serial money optimization...', 2, verbose)
    seed(randseed)
    
    #%% Definitions
    def distance(target, this):
        ''' Calculate the Euclidean distance to nearest point on the target region. '''
        each_dist = []
        for key in target.keys():
            ax_dist = max(0, this[key]-target[key])
            each_dist.append(ax_dist)
        dist = sqrt(sum(array(each_dist)**2))
        return dist
        
    def met(dist):
        ''' Whether or not the marget is met '''
        if dist > 0:    return False
        elif dist == 0: return True
        else:           raise Exception('Distance should never be negative, but it is %s' % dist)
    
    def outcome_met(budgetvec=None, totalbudget=None, args=None, target=None, scaleupmethod='multiply'):
        ''' Run an outcome calculation and determine if it meets the targets '''
        res = op.outcomecalc(budgetvec, totalbudget=totalbudget, outputresults=True,scaleupmethod=scaleupmethod, **args)
        res_final = res.outcomes['final']
        dist = distance(target, res_final)
        is_met = met(dist)
        return is_met,res_final
    
        
    #%% Preliminary investigations
        
    # Calculate current, infinite, and zero spending
    printv('\n\n', 2, verbose)
    printv('Preliminary investigations...', 2, verbose)
    dists = op.odict()
    movie = []

    # Calculate initial people distribution
    results = project.runsim(pars=parset.pars, parsetname=optim.parsetname, progsetname=optim.progsetname, tvec=tvec, keepraw=True, verbose=0, label=project.name+'-minoutcomes', addresult=False, advancedtracking=True)
    startind = findnearest(results.raw[0]['tvec'], optim.objectives['start']-1) ## !!! -1 is because of parameter interpolation / smoothing from the current parameters to the budget parameters, we have to start a year before the budget starts
    initpeople = results.raw[0]['people'][:,:,startind] # Pull out the people array corresponding to the start of the optimization -- there shouldn't be multiple raw arrays here
    initprops  = results.raw[0]['props'][:,startind,:]  # Need initprops if running with initpeople
    args.update({'startind':startind, 'initpeople':initpeople, 'initprops':initprops})

    results_curr = op.outcomecalc(budgetvec, outputresults=True, **args)
    res_targ = results_curr.outcomes['target']
    res_curr = results_curr.outcomes['final']
    dists['curr'] = distance(res_targ, res_curr)
    curr_met = met(dists['curr'])
    printv('  Current distance: %s' % dists['curr'], 2, verbose)
    
    totalbudget = project.settings.infmoney
    results_inf = op.outcomecalc(budgetvec, totalbudget=totalbudget, outputresults=True, scaleupmethod='add', **args)
    res_inf = results_inf.outcomes['final']
    dists['inf'] = distance(res_targ, res_inf)
    if not met(dists['inf']):
        infinitefailed = True
        errormsg = "Not proceeding with money minimization since even infinite funding can't meet targets:\n%s" % dists['inf']
        if die: raise OptimaException(errormsg)
        else:   printv(errormsg, 1, verbose)
    else:
        infinitefailed = False
        printv('Infinite money check passes (distance 0)', 2, verbose)
    
    totalbudget = 1e-3
    results_zero = op.outcomecalc(budgetvec, totalbudget=totalbudget, outputresults=True, **args)
    res_zero = results_zero.outcomes['final']
    dists['zero'] = distance(res_targ, res_zero)
    if met(dists['zero']):
        zerofailed = True
        errormsg = "Not proceeding with money minimization since even zero funding meets targets:\n%s" % dists['zero']
        if die: raise OptimaException(errormsg)
        else:   printv(errormsg, 1, verbose)
    else:
        zerofailed = False
        printv('Zero money check passes (distance: %s)' % dists['zero'], 2, verbose)
    
    # Plot current, infinite, and zero spending
    movie.append('Preliminaries')
    movie += [res_curr, res_inf, res_zero]
        
    # If infinite or zero money met objectives, don't bother proceeding
    if infinitefailed or zerofailed:
        if zerofailed:
            budgetvec *= 0.0
            totalbudget = 0.0
            fundingfactor = 0.0
        if infinitefailed:
            fundingfactor = 10 # For plotting, don't make the factor infinite, just very large
            budgetvec = 0.0*budgetvec + budgetvec.sum()*fundingfactor
            totalbudget *= fundingfactor
        
    
    # It didn't, proceed with the algorithm
    else:
        #%% Increase/decrease current budget until targets met
        def binary_search(budgetvec=None, totalbudget=None, args=None, target=None, curr_met=None, step=None, tol=None):
            ''' Do a binary search to find a solution to within tol tolerance '''
            printv('Starting binary search from %s...' % (totalbudget/factor), 2, verbose)
            if step is None: step = search_step # Step size to increase/decrease guess
            if tol  is None: tol  = search_tol # How close to get before declaring a solution
            if curr_met is True: 
                upper_lim = totalbudget
                lower_lim = None
            elif curr_met is False:
                upper_lim = None
                lower_lim = totalbudget
            elif curr_met is None:
                upper_lim = None
                lower_lim = None
            else:
                raise OptimaException('Not sure what curr_met is: must be true, false, or None, not %s' % curr_met)
            
            # Find upper and lower limits
            budget_list = []
            result_list = []
            while upper_lim is None:
                totalbudget *= step
                is_met,res = outcome_met(budgetvec=budgetvec, totalbudget=totalbudget, args=args, target=target, scaleupmethod='add')
                printv(f'  Scaling up budget to find upper lim: %s... Success: {is_met}' % (totalbudget/factor), 2, verbose)
                budget_list.append(totalbudget)
                result_list.append(res)        
                if is_met:
                    upper_lim = totalbudget
            while lower_lim is None:
                totalbudget /= step
                is_met,res = outcome_met(budgetvec=budgetvec, totalbudget=totalbudget, args=args, target=target, scaleupmethod='add')
                printv(f'  Scaling down budget to find upper limit: %s... Success: {is_met}' % (totalbudget/factor), 2, verbose)
                budget_list.append(totalbudget)
                result_list.append(res)
                if not is_met:
                    lower_lim = totalbudget # Note, this does NOT meet targets
            
            # Do the binary search
            while (upper_lim/lower_lim) > (1+tol):
                trial = (upper_lim+lower_lim)/2.0
                is_met,res = outcome_met(budgetvec=budgetvec, totalbudget=trial, args=args, target=target, scaleupmethod='add')
                printv(f'  Binary search: %s (%s, %s)... Success: {is_met}' % (trial/factor, lower_lim/factor, upper_lim/factor), 2, verbose)
                budget_list.append(totalbudget)
                result_list.append(res)
                if is_met:
                    upper_lim = trial
                else:
                    lower_lim = trial
            
            printv('Final value: %s' % (upper_lim/factor), 2, verbose)
            return upper_lim, budget_list, result_list # Since we know this meets the targets
          
        
        def binary_choice(budgets=None, totalbudget=None, args=None, target=None, step=None, tol=None):
            ''' Find the best budget '''
            printv('Starting binary choice for %s...' % (totalbudget/factor), 2, verbose)
            if step is None: step = search_step # Step size to increase/decrease guess
            if tol  is None: tol  = search_tol # How close to get before declaring a solution
            upper_lim = totalbudget # Since we know the total budget meets targets
            lower_lim = None
            
            # Find lower limits
            budget_list = []
            result_list = []
            meet_targets = range(len(success_budgets))
            
            while lower_lim is None:
                totalbudget /= step
                printv('  Scaling down budget to find lower lim: %s...' % (totalbudget/factor), 2, verbose)
                still_met = []
                for m,mt in enumerate(meet_targets):
                    budgetvec = budgets[mt]
                    is_met,res = outcome_met(budgetvec=budgetvec, totalbudget=totalbudget, args=args, target=target, scaleupmethod='add')
                    printv(f'    Running %s of %s... Success: {is_met}' % (m+1, len(meet_targets)), 2, verbose)
                    budget_list.append(totalbudget)
                    result_list.append(res)
                    if is_met: still_met.append(mt)
                if len(still_met):
                    meet_targets = still_met # Some are still met, so only check these
                    upper_lim = totalbudget
                else:
                    lower_lim = totalbudget # None are met, this is the lower limit
            # Do the binary search
            while (upper_lim/lower_lim) > (1+tol):
                trial = (upper_lim+lower_lim)/2.0
                printv('  Binary choice: %s (%s/%s)...' % (trial/factor, lower_lim/factor, upper_lim/factor), 2, verbose)
                still_met = []
                for m,mt in enumerate(meet_targets):
                    budgetvec = budgets[mt]
                    is_met,res = outcome_met(budgetvec=budgetvec, totalbudget=trial, args=args, target=target, scaleupmethod='add')
                    printv(f'    Running %s of %s... Success: {is_met}' % (m+1, len(meet_targets)), 2, verbose)
                    budget_list.append(totalbudget)
                    result_list.append(res)
                    if is_met: still_met.append(mt)
                if len(still_met):
                    meet_targets = still_met # Some are still met, so only check these
                    upper_lim = trial
                else:
                    lower_lim = trial

            # Tidy up
            if len(meet_targets)>1:
                printv('Warning, %s budgets still meet targets (expecting 1, but not strictly so)' % len(meet_targets), 2, verbose)
            totalbudget = upper_lim
            new_budgetvec = budgets[meet_targets[0]] # Pull out the best budget vector (expecting only 1 left)
            new_budgetvec /= new_budgetvec.sum()
            new_budgetvec *= totalbudget # Rescale
            
            printv('Final value: %s' % (upper_lim/factor), 2, verbose)
            return totalbudget, new_budgetvec, budget_list, result_list # Since we know this meets the targets
        
        #%% Do the binary search
        printv('\n\n', 2, verbose)
        movie.append('Scale current budget')
        totalbudget,b_list,r_list = binary_search(budgetvec=budgetvec, totalbudget=origtotalbudget, args=args, target=res_targ, curr_met=curr_met)
        for bud,res in zip(b_list,r_list):
            movie.append(res)
            
        #%% Throw n_throws points at current budget level
        printv('\n\n', 2, verbose)
        printv('Throwing...', 2, verbose)
        allocated_budget = op.dcp(budgetvec)
        allocated_budget[:] *= 0
        for p,prop in enumerate(schedule):
            remaining_budget = totalbudget - allocated_budget.sum()
            printv('  Round %s/%s (%s being allocated)' % (p+1, len(schedule), prop), 2, verbose)
            movie.append('Making throw %s' % (p+1))
            success_count = 1
            success_budgets = [budgetvec]
            
            if not multi:
                for t,throw in enumerate(range(n_throws-1)): # -1 since include current budget
                    key = 'Throw %s' % (t+2) # since starting with current
                    vec = random(nprogs)
                    vec /= vec.sum() # Normalize
                    this_budget = op.dcp(allocated_budget) + vec*remaining_budget
                    this_budget /= this_budget.sum()
                    this_budget *= totalbudget
                    results_throw = op.outcomecalc(this_budget, totalbudget=totalbudget, outputresults=True, **args)
                    res_throw = results_throw.outcomes['final']
                    dists[key] = distance(res_targ, res_throw)
                    movie.append(res_throw)
                    if met(dists[key]):
                        success_count += 1
                        success_budgets.append(this_budget)
                    printv('    %s of %s, %s/%s successes' % (key, n_throws, success_count, n_success), 2, verbose)
                    if success_count >= n_success:
                        break
            
            else:
                import sciris as sc # Optional dependency
                allkeys = []
                allvecs = []
                allbudgets = []
                for t,throw in enumerate(range(n_throws-1)): # -1 since include current budget
                    key = 'Throw %s' % (t+2) # since starting with current
                    vec = random(nprogs)
                    vec /= vec.sum() # Normalize
                    this_budget = op.dcp(allocated_budget) + vec*remaining_budget
                    this_budget /= this_budget.sum()
                    this_budget *= totalbudget
                    allkeys.append(key)
                    allvecs.append(vec)
                    allbudgets.append(this_budget)
                parallelargs = sc.dcp(args)
                parallelargs.update({'totalbudget':totalbudget, 'outputresults':True})
                all_results_throws = sc.parallelize(op.outcomecalc, iterarg=allbudgets, kwargs=parallelargs, ncpus=nchains)
                for t,throw in enumerate(range(n_throws-1)): # -1 since include current budget
                    res_throw = all_results_throws[t].outcomes['final']
                    dists[allkeys[t]] = distance(res_targ, res_throw)
                    movie.append(res_throw)
                    if met(dists[allkeys[t]]):
                        success_count += 1
                        success_budgets.append(allbudgets[t])
                    printv('    %s of %s, %s/%s successes' % (allkeys[t], n_throws, success_count, n_success), 2, verbose)
                    if success_count >= n_success:
                        break
            
            # Do the refinement
            printv('Refining throw...', 2, verbose)
            movie.append('Refining throw %s' % (p+1))
            totalbudget, budgetvec, b_list, r_list = binary_choice(budgets=success_budgets, totalbudget=totalbudget, args=args, target=res_targ)
            for bud,res in zip(b_list,r_list):
                movie.append(res)
            
            # Populate and restart
            this_allocation = prop*budgetvec
            allocated_budget[:] = this_allocation # This includes the previous allocation, so we can use = instead of +=
            printv('Total allocated after round %s: %s\nAllocation:\n%s' % (p+1, this_allocation.sum()/factor, this_allocation/factor), 2, verbose)
        
        op.toc(start)
        
        
        #%% Final refinement
        printv('\n\n', 2, verbose)
        printv('Local search...', 2, verbose)
        for r_s,refine_step in enumerate(refine_steps):
            movie.append('Local search %s (%s/%s)' % (refine_step, r_s+1, len(refine_steps)))
            refine_vec = ones(len(budgetvec))
            r = 0
            still_choices = True
            while r <= n_refine and still_choices:
                r += 1
                trial_vec = op.dcp(budgetvec)
                trial_vec = trial_vec.astype('float')   # this should fix dividing by zero giving an error
                choices = op.findinds(logical_and(refine_vec, trial_vec)) # It's not a choice if either is zero
                if not len(choices):
                    still_choices = False
                else:
                    # Choose program and remake vector
                    ind = choices[randint(len(choices))]
                    this_prog = trial_vec[ind]
                    trial_vec[ind] = 0 # Set to zero temporarily
                    new_prog = this_prog*refine_step
                    reallocate = this_prog*(1-refine_step)*refine_keep
                    reallocate_vec = trial_vec / trial_vec.sum() * reallocate   # this line throws an error if the dtype of trial_vec is not float
                    reallocate_vec = op.sanitize(reallocate_vec, replacenans=0) # Ensure in the corner case that 0/0 is replaced with 0
                    trial_vec += reallocate_vec
                    trial_vec[ind] = new_prog
                    trial_budget = trial_vec.sum()
                    
                    # Try it out
                    is_met,res = outcome_met(budgetvec=trial_vec, totalbudget=trial_budget, args=args, target=res_targ, scaleupmethod='add')
                    movie.append(res)
                    
                    printv('', 2, verbose)
                    printv('  Iteration %s/%s' % (r+1, n_refine), 2, verbose)
                    printv('     Choice (choices): %s (%s)' % (ind, choices), 2, verbose)
                    printv('     Original budget:  %s' % (totalbudget/factor), 2, verbose)
                    printv('     New budget:       %s' % (trial_budget/factor), 2, verbose)
                    printv('     Original program: %s' % (this_prog/factor), 2, verbose)
                    printv('     New program:      %s' % (new_prog/factor), 2, verbose)
                    if is_met:
                        printv('   Target still met, keeping...', 2, verbose)
                        budgetvec = trial_vec
                        totalbudget = trial_budget
                        refine_vec[:] = 1 # Reset
                    else:
                        printv('   Target not met, rejecting...', 2, verbose)
                        refine_vec[ind] = 0
            
    
    #%% Tidy up
    op.toc(start)
    newbudget = op.dcp(origbudget)
    newbudget[optiminds] = budgetvec
    
    #%% Animation
    if animate:
        # Plot setup
        pl_ax = {'x':'death','y':'inci'} # "plot axes"
        target_color = (0.1,0.7,0.3)
        
        def init_fig():
            fig = pl.figure(facecolor='w')
            pl.xlabel(pl_ax['x'])
            pl.ylabel(pl_ax['y'])
            pl.fill_between([0,res_targ[pl_ax['x']]], res_targ[pl_ax['y']]*pl.ones(2), color=target_color) # Plot target
            return fig
        
        def plot_point(res, color=None, budget=None, denom=None, marker=None):
            ''' Plot a single budget-outcome point '''
            if marker is None: marker = 'o'
            if denom is None: denom = origtotalbudget
            pl.scatter(res[pl_ax['x']], res[pl_ax['y']], color=color, marker=marker) # Plot current
            return None
        
        def fix_lims():
            ''' Just readjust the axis limits '''
            xl = pl.xlim()
            yl = pl.ylim()
            pl.xlim((0,xl[1]))
            pl.ylim((0,yl[1]))
            return None
        
        def flush(rate=20):
            ''' Flush the current plotting buffer '''
            pl.pause(1/float(rate))
            return None
        
        # Calculate limits
        init_fig()
        xmax = -1
        ymax = -1
        for frame in movie:
            try:
                xmax = max(xmax, frame[pl_ax['x']])
                ymax = max(ymax, frame[pl_ax['y']])
            except:
                pass
        pl.xlim((0,xmax))
        pl.ylim((0,ymax))
        
        # Plot
        npoints = len(movie)
        colors = op.vectocolor(range(npoints))
        title_text = ''
        for i in range(npoints):
            if isinstance(movie[i], basestring):
                title_text = movie[i]
            else:
                plot_point(movie[i], color=colors[i])
            pl.title(title_text + ' (%s/%s)' % (i+1, npoints))
            if not i%10:
                flush()
                
        pl.figure(facecolor='w')
        pl.subplot(1,2,1)
        pl.pie(origbudget[:], labels=origbudget.keys())
        pl.axis('equal')
        pl.title('Original')
        pl.subplot(1,2,2)
        pl.pie(newbudget[:], labels=newbudget.keys())
        pl.axis('equal')
        pl.title('Optimized')
    
    # Impose lower limits only !!! why is this here ???
    for key in absconstraints['min']:
        newbudget[key] = max(newbudget[key], absconstraints['min'][key])
    
    ## Tidy up -- WARNING, need to think of a way to process multiple inds
    args['doconstrainbudget'] = True
    args['initpeople'] = None  # Set to None to get full results, not just from start year
    args['initprops']  = None
    args['startind']   = None
    orig = outcomecalc(origbudgetvec, totalbudget=origtotalbudget,    outputresults=True, **args)
    new  = outcomecalc(newbudget,     totalbudget=newbudget[:].sum(), outputresults=True, **args)
    
    orig.name = 'Baseline' # WARNING, is this really the best way of doing it?
    if   zerofailed:     new.name = 'Zero budget'
    elif infinitefailed: new.name = 'Infinite budget'
    else:                new.name = 'Optimized'
    tmpresults = [orig, new]
    multires = Multiresultset(resultsetlist=tmpresults, name='optim-%s' % optim.name)
    optim.resultsref = multires.name # Store the reference for this result
    for k,key in enumerate(multires.keys): multires.budgetyears[key] = tmpresults[k].budgetyears 
    
    # Store optimization settings
    multires.optimsettings = odict([('maxiters',maxiters),('maxtime',maxtime),('randseed',randseed)])
    multires.optim = optim # Store the optimization object as well
    
    printv('Money minimization complete after %s seconds' % op.toc(start, output=True), 2, verbose)

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
        objective    = what to calculate; must be one of 'death', 'inci'; 'death' by default)
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
    initresults = project.runsim(parsetname=parsetname, progsetname=progsetname, keepraw=True, verbose=0, label=project.name+'-minoutcomes', addresult=False, advancedtracking=False)
    initialind  = findnearest(initresults.raw[0]['tvec'], objectives['start'])
    initpeople  = initresults.raw[0]['people'][:,:,initialind] # Pull out the people array corresponding to the start of the optimization -- there shouldn't be multiple raw arrays here

    # Define arguments that don't change in the loop
    defaultargs = {'which':'outcomes', 'project':project, 'parsetname':parsetname, 'progsetname':progsetname, 'objectives':objectives, 
                   'origbudget':origbudget, 'outputresults':False, 'verbose':verbose, 'doconstrainbudget':False, 'initpeople':initpeople}
    
    # Calculate baseline
    baseliney = outcomecalc(budgetvec=defaultbudget[:], **defaultargs)
    
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
            else:              outcome = outcomecalc(budgetvec=thisbudget[:], **defaultargs) # The crux of the matter!! Actually calculate
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
            
            # Finally, calculate the outcome per dollar
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