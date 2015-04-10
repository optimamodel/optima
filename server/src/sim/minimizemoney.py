"""
Minimize money code...to be combined with optimize.py eventually
    
Version: 2015apr10 by cliffk
"""

from printv import printv
from copy import deepcopy
from numpy import ones, zeros, concatenate, arange, inf
from utils import findinds
from makeresults import makeresults
from timevarying import timevarying
from getcurrentbudget import getcurrentbudget
from model import model
from makemodelpars import makemodelpars
from quantile import quantile
from ballsd import ballsd
from optimize import saveoptimization, defaultobjectives, defaultconstraints, partialupdateM



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
    newD, newcov, newnonhivdalysaverted = getcurrentbudget(newD, thisalloc, randseed=randseed) # Get cost-outcome curves with uncertainty
    newM = makemodelpars(newD['P'], newD['opt'], withwhat='c', verbose=0) # Don't print out
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
    
    tmpplotdata = [] # TEMP
    outcome = 0 # Preallocate objective value 
    for key in options['outcomekeys']:
        if options['weights'][key]>0: # Don't bother unless it's actually used
            if key!='costann': thisoutcome = R[key]['tot'][0][options['outindices']].sum()
            else: thisoutcome = R[key]['total']['total'][0][options['outindices']].sum() # Special case for costann
            tmpplotdata.append(R[key]['tot'][0][options['outindices']]) # TEMP
            outcome += thisoutcome * options['weights'][key] / float(options['normalizations'][key]) * options['D']['opt']['dt'] # Calculate objective
    
    options['tmpbestdata'].append(dict())
    options['tmpbestdata'][-1]['optimparams'] = optimparams
#    options['tmpbestdata'][-1]['opt']ions = options
    options['tmpbestdata'][-1]['R'] = R
#    print options['tmpbestdata'][-1]['optimparams']

    
    return outcome
    
    
    
def minimizemoney(D, objectives=None, constraints=None, maxiters=1000, timelimit=None, verbose=5, name='Default', stoppingfunc = None):
    """ Perform the actual optimization """
    
    printv('Running money minimization...', 1, verbose)
    
    
    # Set up parameter vector for time-varying optimisation...
    stepsize = 100000
    growsize = 0.01

    origR = deepcopy(D['R'])
    origalloc = D['data']['origalloc']
    
    # Make sure objectives and constraints exist, and overwrite using saved ones if available
    if objectives is None: objectives = defaultobjectives(D, verbose=verbose)
    if constraints is None: constraints = defaultconstraints(D, verbose=verbose)

    if not "optimizations" in D: saveoptimization(D, name, objectives, constraints)


    # Do this so if e.g. /100 won't have problems
    objectives = deepcopy(objectives)
    constraints = deepcopy(constraints)
    ntimepm=1 + int(objectives['timevarying'])*int(objectives['funding']=='constant') # Either 1 or 2, but only if funding==constant

    # Handle original allocation
    nprogs = len(origalloc)
    totalspend = objectives['outcome']['fixed'] # For fixed budgets
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
    weights = dict()
    normalizations = dict()
    outcomekeys = ['inci', 'death', 'daly', 'costann']
    if sum([objectives['outcome'][key] for key in outcomekeys])>1: # Only normalize if multiple objectives, since otherwise doesn't make a lot of sense
        for key in outcomekeys:
            thisweight = objectives['outcome'][key+'weight'] * objectives['outcome'][key] / 100.
            weights.update({key:thisweight}) # Get weight, and multiply by "True" or "False" and normalize from percentage
            if key!='costann': thisnormalization = origR[key]['tot'][0][outindices].sum()
            else: thisnormalization = origR[key]['total']['total'][0][outindices].sum() # Special case for costann
            normalizations.update({key:thisnormalization})
    else:
        for key in outcomekeys:
            weights.update({key:int(objectives['outcome'][key])}) # Weight of 1
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
    optimparams = concatenate((origalloc, growthrate, saturation, inflection)) # WARNING, not used for multi-year optimizations
        
    
    
    
    ###########################################################################
    ## Constant budget optimization
    ###########################################################################
    if objectives['funding'] == 'constant' and objectives['timevarying'] == False:
        
        ## Define options structure
        options = dict()
        options['ntimepm'] = ntimepm # Number of time-varying parameters
        options['nprogs'] = nprogs # Number of programs
        options['D'] = deepcopy(D) # Main data structure
        options['outcomekeys'] = outcomekeys # Names of outcomes, e.g. 'inci'
        options['weights'] = weights # Weights for each parameter
        options['outindices'] = outindices # Indices for the outcome to be evaluated over
        options['parindices'] = parindices # Indices for the parameters to be updated on
        options['normalizations'] = normalizations # Whether to normalize a parameter
        options['totalspend'] = totalspend # Total budget
        options['fundingchanges'] = fundingchanges # Constraints-based funding changes
        
        
#        options.tmporigdata = []
        options['tmpbestdata'] = []
#        options.tmperrcount = [0]
#        options.tmperrhist = [None]
        
        
        ## Run with uncertainties
        allocarr = []
        fvalarr = []
        for s in xrange(len(D['F'])): # xrange(len(D['F'])): # Loop over all available meta parameters
            print('========== Running uncertainty optimization %s of %s... ==========' % (s+1, len(D['F'])))
            options['D']['F'] = [deepcopy(D['F'][s])] # Loop over fitted parameters
            
            options['randseed'] = s
            optparams, fval, exitflag, output = ballsd(objectivecalc, optimparams, options=options, xmin=fundingchanges['total']['dec'], xmax=fundingchanges['total']['inc'], absinitial=stepsizes, MaxIter=maxiters, timelimit=timelimit, fulloutput=True, stoppingfunc=stoppingfunc, verbose=verbose)
            optparams[opttrue] = optparams[opttrue] / optparams[opttrue].sum() * (options['totalspend'] - optparams[~opttrue].sum()) # Make sure it's normalized -- WARNING KLUDGY
            allocarr.append(optparams)
            fvalarr.append(output.fval)
        
        ## Find which optimization was best
        bestallocind = -1
        bestallocval = inf
        for s in xrange(len(fvalarr)):
            if fvalarr[s][-1]<bestallocval:
                bestallocval = fvalarr[s][-1]
                bestallocind = s
        if bestallocind == -1: print('WARNING, best allocation value seems to be infinity!')
        
        # Update the model and store the results
        result = dict()
        result['kind'] = 'constant'
        result['fval'] = fvalarr[bestallocind] # Append the best value noe
        result['allocarr'] = [] # List of allocations
        result['allocarr'].append(quantile([origalloc])) # Kludgy -- run fake quantile on duplicated origalloc just so it matches
        result['allocarr'].append(quantile(allocarr)) # Calculate allocation arrays 
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

    printv('...done optimizing programs.', 2, verbose)
    return D