"""
Minimize money code...to be combined with optimize.py eventually
    
Version: 2015may14 by cliffk
"""

from printv import printv
from copy import deepcopy
from numpy import zeros, arange, array
from utils import findinds
from makeresults import makeresults
from timevarying import timevarying
from getcurrentbudget import getcurrentbudget
from model import model
from makemodelpars import makemodelpars
from quantile import quantile
from optimize import saveoptimization, defaultobjectives, defaultconstraints, partialupdateM
from getcurrentbudget import getcoverage
from optimize import optimize



def runmodelalloc(D, optimparams, parindices, randseed, rerunfinancial=False, verbose=2):
    """ Little function to do calculation since it appears so many times """
    newD = deepcopy(D)
    # Exclude fixed costs from the optimization
    opttrue = zeros(len(D['data']['origalloc']))
    for i in xrange(len(D['data']['origalloc'])):
        if len(D['programs'][i]['effects']): opttrue[i] = 1.0
    opttrue = opttrue.astype(bool) # Logical values
    optimparams[opttrue] = optimparams[opttrue] / optimparams[opttrue].sum() * (sum(optimparams) - optimparams[~opttrue].sum()) # Make sure it's normalized -- WARNING KLUDGY

    thisalloc = timevarying(optimparams, ntimepm=1, nprogs=len(optimparams), tvec=D['opt']['partvec'], totalspend=sum(optimparams)) 
    
    newD = getcurrentbudget(newD, thisalloc, randseed=randseed) # Get cost-outcome curves with uncertainty
#    newD, newcov, newnonhivdalysaverted = getcurrentbudget(newD, thisalloc, randseed=randseed) # Get cost-outcome curves with uncertainty
    newM = makemodelpars(newD['P'], newD['opt'], withwhat='c', verbose=0) # Don't print out
    
    # Hideous hack for ART to use linear unit cost
    try:
        from utils import sanitize
        artind = D['data']['meta']['progs']['short'].index('ART')
        currcost = sanitize(D['data']['costcov']['cost'][artind])[-1]
        currcov = sanitize(D['data']['costcov']['cov'][artind])[-1]
        unitcost = currcost/currcov
        newM['tx1'].flat[parindices] = thisalloc[artind]/unitcost
    except:
        print('Attempt to calculate ART coverage failed for an unknown reason')
    
    newD['M'] = partialupdateM(D['M'], newM, parindices)
    S = model(newD['G'], newD['M'], newD['F'][0], newD['opt'], verbose=verbose)
    R = makeresults(D, allsims=[S], rerunfinancial=rerunfinancial, verbose=0)
    R['debug'] = dict()
    R['debug']['G'] = deepcopy(newD['G'])
    R['debug']['M'] = deepcopy(newD['M'])
    R['debug']['F'] = deepcopy(newD['F'])
    R['debug']['S'] = deepcopy(S)
    return R



def objectivecalc(optimparams, options):
    """ Calculate the objective function """


    R = runmodelalloc(options['D'], optimparams, options['parindices'], options['randseed'], rerunfinancial=False) # Actually run
    
    targetsmet = False
    for key in options['targets']:
        if options['targets'][key]['use']: # Don't bother unless it's actually used
            key1 = key
            if key == 'deaths': key1 = 'death'   # Horrible hack to handle bug on the front-end that does not seem to be tracked.
            if key == 'dalys': key1 = 'daly'            
            orig = R[key1]['tot'][0][options['outindices'][0]]
            new = R[key1]['tot'][0][options['outindices'][-1]]
            if options['targets'][key]['by_active']:
                if new < orig*options['targets'][key]['by']:
                    targetsmet = True
                print('For target %s, orig:%f new:%f; met=%s' % (key, orig, new, targetsmet))
            else:
                print('NOT IMPLEMENTED')
    
    options['tmpbestdata'].append(dict())
    options['tmpbestdata'][-1]['optimparams'] = optimparams
    options['tmpbestdata'][-1]['R'] = R
    
    return targetsmet, optimparams
    
    
    
def minimizemoney(D, objectives=None, constraints=None, maxiters=1000, timelimit=None, verbose=5, name='Default', stoppingfunc = None):
    """ Perform the actual optimization """
    
    printv('Running money minimization...', 1, verbose)
    
    
    origalloc = D['data']['origalloc']
    
    # Make sure objectives and constraints exist, and overwrite using saved ones if available
    if objectives is None: objectives = defaultobjectives(D, verbose=verbose)
    if constraints is None: constraints = defaultconstraints(D, verbose=verbose)

    if not "optimizations" in D: saveoptimization(D, name, objectives, constraints)


    # Do this so if e.g. /100 won't have problems
    objectives = deepcopy(objectives)
#    if objectives['money']['objectives']['death']['use']: objectives['outcome']['death'] = True     # Setup death outcome optimisation if need be.
#    if objectives['money']['objectives']['dalys']['use']: objectives['outcome']['daly'] = True      # Setup daly outcome optimisation if need be.
    constraints = deepcopy(constraints)
    ntimepm=1 + int(objectives['timevarying'])*int(objectives['funding']=='constant') # Either 1 or 2, but only if funding==constant

    # Handle original allocation
    nprogs = len(origalloc)
    opttrue = zeros(len(D['data']['origalloc']))
    for i in xrange(len(D['data']['origalloc'])):
        if len(D['programs'][i]['effects']): opttrue[i] = 1.0
    opttrue = opttrue.astype(bool) # Logical values
    
    
    # Define constraints on funding -- per year and total
    fundingchanges = dict()
    keys1 = ['year','total']
    keys2 = ['dec','inc']
    abslims = {'dec':0, 'inc':1e9}
    rellims = {'dec':-1e9, 'inc':1e9}
    smallchanges = {'dec':1.0, 'inc':1.0} # WARNING BIZARRE
    for key1 in keys1:
        fundingchanges[key1] = dict()
        for key2 in keys2:
            fundingchanges[key1][key2] = []
            for p in xrange(nprogs):
                fullkey = key1+key2+'rease'
                this = constraints[fullkey][p] # Shorten name
                if key1=='total':
                    if not(opttrue[p]): # Not an optimized parameter
                        fundingchanges[key1][key2].append(origalloc[p]*smallchanges[key2])
                    elif this['use'] and objectives['funding'] != 'variable': # Don't constrain variable-year-spend optimizations
                        newlim = this['by']/100.*origalloc[p]
                        fundingchanges[key1][key2].append(newlim)
                    else: 
                        fundingchanges[key1][key2].append(abslims[key2])
                elif key1=='year':
                    if this['use'] and objectives['funding'] != 'variable': # Don't constrain variable-year-spend optimizations
                        newlim = this['by']/100.-1 # Relative change in funding
                        fundingchanges[key1][key2].append(newlim)
                    else: 
                        fundingchanges[key1][key2].append(rellims[key2])
    
    ## Define indices, weights, and normalization factors
    initialindex = findinds(D['opt']['partvec'], objectives['year']['start'])
    finalparindex = findinds(D['opt']['partvec'], objectives['year']['end'])
    finaloutindex = findinds(D['opt']['partvec'], objectives['year']['until'])
    parindices = arange(initialindex,finalparindex)
    outindices = arange(initialindex,finaloutindex)
    normalizations = dict()
        
    # Concatenate parameters to be optimised
    optimparams = deepcopy(origalloc)
        
    
    
    
    ###########################################################################
    ## Money minimization optimization
    ###########################################################################
    if 1: # objectives['funding'] == 'constant' and objectives['timevarying'] == False:
        
        ## Define options structure
        options = dict()
        options['ntimepm'] = ntimepm # Number of time-varying parameters
        options['nprogs'] = nprogs # Number of programs
        options['D'] = deepcopy(D) # Main data structure
        options['targets'] = objectives['money']['objectives'] # Names of outcomes, e.g. 'inci'
        options['outindices'] = outindices # Indices for the outcome to be evaluated over
        options['parindices'] = parindices # Indices for the parameters to be updated on
        options['normalizations'] = normalizations # Whether to normalize a parameter
        options['fundingchanges'] = fundingchanges # Constraints-based funding changes
        options['tmpbestdata'] = []
        
        
        ## Run with uncertainties
        allocarr = []
        terminate = False
        for s in xrange(len(D['F'])): # xrange(len(D['F'])): # Loop over all available meta parameters
            print('========== Running uncertainty optimization %s of %s... ==========' % (s+1, len(D['F'])))
            options['D']['F'] = [deepcopy(D['F'][s])] # Loop over fitted parameters
            
            options['randseed'] = s
            
            # Run current allocation for debugging purposes, as this may affect 'options' persistently somehow...
            print('========== Running current allocation to set up baseline ==========')
            targetsmet, optparams = objectivecalc(optimparams, options)            
            
            # Try infinite money
            print('========== Checking if infinite allocation meets targets ==========')
            targetsmet, optparams = objectivecalc(array(optimparams)*1e9, options)
            if not(targetsmet):
                print("DONE: Infinite allocation can't meet targets!")
                break
            
            # Try zero money
            print('========== Checking if zero allocation meets targets ==========')
            targetsmet, optparams = objectivecalc(array(optimparams)*1e-9, options)
            if targetsmet:
                print("DONE: Even zero allocation meets targets!")
                break
            
             # Sneak in an optimisation to begin with so that our baseline multiplied by factors isn't horrible.
            print('========== Initial optimization ==========')            
            tempD = deepcopy(D)
            tempD['data']['origalloc'] = optimparams
            newD = optimize(tempD, objectives=None, constraints=None, maxiters=max(maxiters,20), timelimit=max(timelimit,100), verbose=5, name='tmp_minimizemoney', stoppingfunc = None) # Run default optimization
            optimparams = newD['debugresult']['allocarr'][1][0]  # Copy optimization parameters out of newD
            
            # First, see if it meets targets already
            print('========== Checking if current allocation meets targets ==========')
            targetsmet, optparams = objectivecalc(optimparams, options)
            
            # Halve funding if targets are already met...
            print('========== Halve funding until floor is reached ==========')
            fundingfactor = 1.0
            while targetsmet:
                fundingfactor /= 2
                targetsmet, optparams = objectivecalc(array(optimparams)*fundingfactor, options)
                print('Current funding factor: %f' % fundingfactor)
            
            # Keep doubling funding till targets are met...
            print('========== Doubling funding until ceiling is reached ==========')
            while not(targetsmet):
                fundingfactor *= 2
                targetsmet, optparams = objectivecalc(array(optimparams)*fundingfactor, options)
                print('Current funding factor: %f' % fundingfactor)
            
            
            # Optimize spending
            print('========== Extra optimization ==========')
            tempD = deepcopy(D)
            tempD['data']['origalloc'] = optparams
            newD = optimize(tempD, objectives=None, constraints=None, maxiters=max(maxiters,20), timelimit=max(timelimit,100), verbose=5, name='tmp_minimizemoney', stoppingfunc = None) # Run default optimization
            optimparams = newD['debugresult']['allocarr'][1][0]/fundingfactor  # Copy optimization parameters out of newD


            
            # Now home in on the solution
            print('========== Homing in on solution ==========')
            upperlim = fundingfactor
            lowerlim = fundingfactor/2.
            while (upperlim-lowerlim>0.1): # Keep looping until they converge to within 10% of the budget
                fundingfactor = (upperlim+lowerlim)/2
                targetsmet, optparams = objectivecalc(array(optimparams)*fundingfactor, options)
                print('Current funding factor (low, high): %f (%f, %f)' % (fundingfactor, lowerlim, upperlim))
                if targetsmet: upperlim=fundingfactor
                else: lowerlim=fundingfactor
            if (upperlim-lowerlim<=0.1):    # Just to make sure that the optimal allocation returned is for the goals-meeting upperlim factor!
                targetsmet, optparams = objectivecalc(array(optimparams)*upperlim, options)
            
        
            optparams[opttrue] = optparams[opttrue] / optparams[opttrue].sum() * (sum(optparams) - optparams[~opttrue].sum()) # Make sure it's normalized -- WARNING KLUDGY
            allocarr.append(optparams)
        
        # Update the model and store the results
        result = dict()
        result['kind'] = 'constant'
        result['allocarr'] = [] # List of allocations
        result['allocarr'].append(quantile([origalloc])) # Kludgy -- run fake quantile on duplicated origalloc just so it matches
        result['allocarr'].append(quantile(allocarr)) # Calculate allocation arrays
        result['covnumarr'] = [] # List of coverage levels
        result['covnumarr'].append(getcoverage(D, alloc=result['allocarr'][0].T)['num'].T) # Original coverage
        result['covnumarr'].append(getcoverage(D, alloc=result['allocarr'][-1].T)['num'].T) # Coverage under last-run optimization
        result['covperarr'] = [] # List of coverage levels
        result['covperarr'].append(getcoverage(D, alloc=result['allocarr'][0].T)['per'].T) # Original coverage
        result['covperarr'].append(getcoverage(D, alloc=result['allocarr'][-1].T)['per'].T) # Coverage under last-run optimization
        labels = ['Original','Optimal']
        result['Rarr'] = [dict(), dict()]
        result['Rarr'][0]['R'] = options['tmpbestdata'][0]['R']
        result['Rarr'][1]['R'] = options['tmpbestdata'][-1]['R']
        result['Rarr'][0]['label'] = 'Original'
        result['Rarr'][1]['label'] = 'Optimal'

        
    ## Gather plot data
    from gatherplotdata import gatheroptimdata
    plot_result = gatheroptimdata(D, result, verbose=verbose)
    if 'optim' not in D['plot']: D['plot']['optim'] = [] # Initialize list if required
    D['plot']['optim'].append(plot_result) # In any case, append
    
    result_to_save = {'plot': [plot_result]}

    ## Save optimization to D
    D = saveoptimization(D, name, objectives, constraints, result_to_save, verbose=2)
    
    D['debugresult'] = result

    printv('...done optimizing programs.', 2, verbose)
    return D