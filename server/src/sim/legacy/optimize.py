"""
Allocation optimization code:
    D is the project data structure
    objectives is a dictionary defining the objectives of the optimization
    constraints is a dictionary defining the constraints on the optimization
    timelimit is the maximum time in seconds to run optimization for
    verbose determines how much information to print.
    
Version: 2015feb06 by cliffk
"""

from liboptima.utils import printv
from copy import deepcopy
from numpy import ones, zeros, concatenate, arange, inf, hstack, argmin, array, ndim
from liboptima.utils import findinds
from makeresults import makeresults
from timevarying import timevarying, multiyear
from getcurrentbudget import getcurrentbudget
from model import model
from makemodelpars import makemodelpars
from liboptima.quantile import quantile
from liboptima.ballsd import ballsd
from getcurrentbudget import getcoverage

import optima.defaults as defaults



def runmodelalloc(D, thisalloc, origalloc, parindices, randseed, rerunfinancial=False, verbose=2):
    """ Little function to do calculation since it appears so many times """
    newD = deepcopy(D)
    newD = getcurrentbudget(newD, thisalloc, randseed=randseed) # Get cost-outcome curves with uncertainty
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
    
    # Now update things
    newD['M'] = partialupdateM(D['M'], newM, parindices)
    S = model(newD['G'], newD['M'], newD['F'][0], newD['opt'], verbose=verbose)
    R = makeresults(D, allsims=[S], rerunfinancial=rerunfinancial, verbose=0)
    R['debug'] = dict()
    R['debug']['G'] = deepcopy(newD['G'])
    R['debug']['M'] = deepcopy(newD['M'])
    R['debug']['F'] = deepcopy(newD['F'])
    R['debug']['S'] = deepcopy(S)
    R['debug']['newbudget'] = deepcopy(thisalloc)     # Assuming thisalloc is the optimised full budget, it is being stored...
    return R
    
    

def constrainbudget(origbudget, total=None, limits=None):
    """ Take an unnormalized/unconstrained budget and normalize and constrain it """
    normbudget = deepcopy(origbudget)
    
    eps = 1e-3 # Don't try to make an exact match, I don't have that much faith in my algorithm
    
    if total < sum(limits['dec']) or total > sum(limits['inc']):
        raise Exception('Budget cannot be constrained since the total %f is outside the low-high limits [%f, %f]' % (total, sum(limits['dec']), sum(limits['inc'])))
    
    nprogs = len(normbudget)
    proginds = arange(nprogs)
    limlow = zeros(nprogs, dtype=bool)
    limhigh = zeros(nprogs, dtype=bool)
    for p in proginds:
        if normbudget[p] <= limits['dec'][p]:
            normbudget[p] = limits['dec'][p]
            limlow[p] = 1
        if normbudget[p] >= limits['inc'][p]:
            normbudget[p] = limits['inc'][p]
            limhigh[p] = 1
    
    # Too high
    while sum(normbudget) > total+eps:
        overshoot = sum(normbudget) - total
        toomuch = sum(normbudget[~limlow]) / (sum(normbudget[~limlow]) - overshoot)
        for p in proginds[~limlow]:
            proposed = normbudget[p] / toomuch
            if proposed <= limits['dec'][p]:
                proposed = limits['dec'][p]
                limlow[p] = 1
            normbudget[p] = proposed
        
    # Too low
    while sum(normbudget) < total-eps:
        undershoot = total - sum(normbudget)
        toolittle = (sum(normbudget[~limhigh]) + undershoot) / sum(normbudget[~limhigh])
        for p in proginds[~limhigh]:
            proposed = normbudget[p] * toolittle
            if proposed >= limits['inc'][p]:
                proposed = limits['inc'][p]
                limhigh[p] = 1
            normbudget[p] = proposed
    
    return normbudget


def objectivecalc(optimparams, options):
    """ Calculate the objective function """
    origparams = options['D']['data']['origalloc']
    
    # Exclude fixed ['costs'] from the optimization
    opttrue = zeros(len(options['D']['data']['origalloc']))
    for i in xrange(len(options['D']['data']['origalloc'])):
        if len(options['D']['programs'][i]['effects']): opttrue[i] = 1.0
    opttrue = opttrue.astype(bool) # Logical values
    optimparams = constrainbudget(optimparams, total=options['totalspend'], limits=options['fundingchanges']['total'])


    if 'ntimepm' in options.keys():
        thisalloc = timevarying(optimparams, ntimepm=options['ntimepm'], nprogs=options['nprogs'], tvec=options['D']['opt']['partvec'], totalspend=options['totalspend'], fundingchanges=options['fundingchanges']) 
        origalloc = timevarying(origparams, ntimepm=options['ntimepm'], nprogs=options['nprogs'], tvec=options['D']['opt']['partvec'], totalspend=options['totalspend'], fundingchanges=options['fundingchanges']) 
    elif 'years' in options.keys():
        thisalloc = multiyear(optimparams, years=options['years'], totalspends=options['totalspends'], nprogs=options['nprogs'], tvec=options['D']['opt']['partvec']) 
        origalloc = multiyear(origparams, years=options['years'], totalspends=options['totalspends'], nprogs=options['nprogs'], tvec=options['D']['opt']['partvec']) 
    else:
        raise Exception('Cannot figure out what kind of allocation this is since neither options[\'ntimepm\'] nor options[\'years\'] is defined')
    
    R = runmodelalloc(options['D'], thisalloc, origalloc, options['parindices'], options['randseed'], rerunfinancial=False) # Actually run
    
    tmpplotdata = [] # TEMP
    outcome = 0 # Preallocate objective value 
    for key in options['outcomekeys']:
        if options['weights'][key]>0: # Don't bother unless it's actually used
            if key!='costann': thisoutcome = R[key]['tot'][0][options['outindices']].sum()
            else: thisoutcome = R[key]['total']['total'][0][options['outindices']].sum() # Special case for costann
            tmpplotdata.append(R[key]['tot'][0][options['outindices']]) # TEMP
            outcome += thisoutcome * options['weights'][key] / float(options['normalizations'][key]) * options['D']['opt']['dt'] # Calculate objective
    
#    print('DEBUGGING....................................................................................')
#    from matplotlib.pylab import figure, plot, hold, subplot, show, close, pie
#    close('all')
#    if options.tmperrcount[-1]==0:
#        print('Loading original DATA')
#        tmporigplots = deepcopy(tmpplotdata)
#        tmporigpie = deepcopy(optimparams)
#    options.tmperrcount.append(options.tmperrcount[-1]+1)
#    options.tmperrhist.append(outcome)
#    if options.tmperrcount[-1]>=30:
#        figure()
#        subplot(2,2,1); hold(True)
#        for i in xrange(len(tmporigplots)):
#            plot(options['D']['opt']['partvec'][options['outindices']], tmporigplots[i],c=(0,0,0))
#            plot(options['D']['opt']['partvec'][options['outindices']], tmpplotdata[i])
#        subplot(2,2,2)
#        plot(options.tmperrcount, options.tmperrhist)
#        subplot(2,2,3)
#        pie(tmporigpie)
#        subplot(2,2,4)
#        pie(optimparams)
#        show()
    
#    if options.tmperrcount[-1]==0:
#        print('SAVING ORIGINAL DATA')
#        print options.tmporigdata[-1]['optimparams']
#        options.tmporigdata.append(dict())
#        options.tmporigdata[-1]['optimparams'] = optimparams
##        options.tmporigdata[-1]['opt']ions = options
#        options.tmporigdata[-1]['R'] = R
#    print('SAVING BEST DATA') # TEMP
    options['tmpbestdata'].append(dict())
    options['tmpbestdata'][-1]['optimparams'] = optimparams
#    options['tmpbestdata'][-1]['opt']ions = options
    options['tmpbestdata'][-1]['R'] = R
#    print options['tmpbestdata'][-1]['optimparams']

    
    return outcome
    
    
    
def optimize(D, objectives=None, constraints=None, maxiters=1000, timelimit=None, verbose=5, name='Default', stoppingfunc = None, returnresult=False):
    """ Perform the actual optimization """
    from time import sleep
    
    printv('Running optimization...', 1, verbose)
    
    
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
        options['totalspend'] = sum(origalloc) # Total budget
        options['fundingchanges'] = fundingchanges # Constraints-based funding changes
        options['randseed'] = 0
        options['tmpbestdata'] = []
        
        
        
        ## Run original
        objectivecalc(optimparams, options=options)
        
        ## Run with uncertainties
        allocarr = [] # Original allocation
        fvalarr = [] # Outcome for original allocation
        for s in xrange(len(D['F'])): # Loop over all available meta parameters
            print('========== Running uncertainty optimization %s of %s... ==========' % (s+1, len(D['F'])))
            options['D']['F'] = [deepcopy(D['F'][s])] # Loop over fitted parameters
            
            options['randseed'] = s
            options['totalspend'] = totalspend # Total budget
            optparams, fval, exitflag, output = ballsd(objectivecalc, optimparams, options=options, xmin=fundingchanges['total']['dec'], xmax=fundingchanges['total']['inc'], absinitial=stepsizes, MaxIter=maxiters, timelimit=timelimit, fulloutput=True, stoppingfunc=stoppingfunc, verbose=verbose)
            optparams = constrainbudget(optparams, total=totalspend, limits=fundingchanges['total']) # Constrain the budget using the total amount and the total funding changes
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
        result['covnumarr'] = [] # List of coverage levels
        result['covnumarr'].append(getcoverage(D, alloc=result['allocarr'][0].T)['num'].T) # Original coverage
        result['covnumarr'].append(getcoverage(D, alloc=result['allocarr'][-1].T)['num'].T) # Coverage under last-run optimization
        result['covperarr'] = [] # List of coverage levels
        result['covperarr'].append(getcoverage(D, alloc=result['allocarr'][0].T)['per'].T) # Original coverage
        result['covperarr'].append(getcoverage(D, alloc=result['allocarr'][-1].T)['per'].T) # Coverage under last-run optimization
        labels = ['Original','Optimal']
        result['Rarr'] = [dict(), dict()]
        result['Rarr'][0]['R'] = options['tmpbestdata'][0]['R']
        result['Rarr'][1]['R'] = options['tmpbestdata'][bestallocind]['R']
        result['Rarr'][0]['label'] = 'Original'
        result['Rarr'][1]['label'] = 'Optimal'
#        for i,params in enumerate([options.tmpbest, allocarr[bestallocind]]): # CK: loop over original and (the best) optimal allocations
#            if i==1:
#                import traceback; traceback.print_exc(); import pdb; pdb.set_trace() # TEMP
#            sleep(0.1)
#            alloc = timevarying(params, ntimepm=len(params)/nprogs, nprogs=nprogs, tvec=D['opt']['partvec'], totalspend=totalspend, fundingchanges=fundingchanges)   
#            R = runmodelalloc(options['D'], alloc, options['parindices'], options['randseed'], verbose=verbose) # Actually run
#            result['Rarr'].append(dict()) # Append a structure
#            result['Rarr'][-1]['R'] = deepcopy(R) # Store the R structure (results)
#            result['Rarr'][-1]['label'] = labels.pop(0) # Store labels, one at a time
        
        
        
        
        
        
        
        
        
        
        
    
    
    ###########################################################################
    ## Time-varying budget optimization
    ###########################################################################
    if objectives['funding'] == 'constant' and objectives['timevarying'] == True:
        
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
        parammin = concatenate((fundingchanges['total']['dec'], ones(nprogs)*-1e9))  
        parammax = concatenate((fundingchanges['total']['inc'], ones(nprogs)*1e9))  
        options['randseed'] = 1
        
        
        
        ## Run time-varying optimization
        print('========== Running time-varying optimization ==========')
        optparams, fval, exitflag, output = ballsd(objectivecalc, optimparams, options=options, xmin=parammin, xmax=parammax, absinitial=stepsizes, MaxIter=maxiters, timelimit=timelimit, fulloutput=True, stoppingfunc=stoppingfunc, verbose=verbose)
        optparams[opttrue] = optparams[opttrue] / optparams[opttrue].sum() * (options['totalspend'] - optparams[~opttrue].sum())
        
        # Update the model and store the results
        result = dict()
        result['kind'] = 'timevarying'
        result['fval'] = output['fval'] # Append the objective sequence
        result['Rarr'] = []
        labels = ['Original','Optimal']
        for params in [origalloc, optparams]: # CK: loop over original and (the best) optimal allocations
            sleep(0.1)
            alloc = timevarying(params, ntimepm=len(params)/nprogs, nprogs=nprogs, tvec=D['opt']['partvec'], totalspend=totalspend, fundingchanges=fundingchanges) #Regenerate allocation
            R = runmodelalloc(options['D'], alloc, options['parindices'], options['randseed'], verbose=verbose) # Actually run
            result['Rarr'].append(dict()) # Append a structure
            result['Rarr'][-1]['R'] = deepcopy(R) # Store the R structure (results)
            result['Rarr'][-1]['label'] = labels.pop(0) # Store labels, one at a time
        result['xdata'] = R['tvec'] # Store time data
        result['alloc'] = alloc[:,0:len(R['tvec'])] # Store allocation data, and cut to be same length as time data
        
    
    
    
        
    ###########################################################################
    ## Multiple-year budget optimization
    ###########################################################################
    if objectives['funding'] == 'variable':
        
        ## Define options structure
        options = dict()
        
        options['nprogs'] = nprogs # Number of programs
        options['D'] = deepcopy(D) # Main data structure
        options['outcomekeys'] = outcomekeys # Names of outcomes, e.g. 'inci'
        options['weights'] = weights # Weights for each parameter
        options['outindices'] = outindices # Indices for the outcome to be evaluated over
        options['parindices'] = parindices # Indices for the parameters to be updated on
        options['normalizations'] = normalizations # Whether to normalize a parameter
        
        options['randseed'] = None # Death is enough randomness on its own
        options['fundingchanges'] = fundingchanges # Constraints-based funding changes
        
        options['years'] = []
        options['totalspends'] = []
        yearkeys = objectives['outcome']['variable'].keys()
        yearkeys.sort() # God damn I hate in-place methods
        for key in yearkeys: # Stored as a list of years:
            options['years'].append(float(key)) # Convert from string to number
            options['totalspends'].append(objectives['outcome']['variable'][key]) # Append this year
        
        
        
        ## Define optimization parameters
        nyears = len(options['years'])
        optimparams = array(origalloc.tolist()*nyears).flatten() # Duplicate parameters
        parammin = zeros(len(optimparams))
        stepsizes = stepsize + zeros(len(optimparams))
        keys1 = ['year','total']
        keys2 = ['dec','inc']
        abslims = {'dec':0, 'inc':1e9}
        rellims = {'dec':-1e9, 'inc':1e9}
        for key1 in keys1:
            for key2 in keys2:
                options['fundingchanges'][key1][key2] *= nyears # I know this just points to the list rather than copies, but should be fine. I hope
        
        ## Run time-varying optimization
        print('========== Running multiple-year optimization ==========')
        optparams, fval, exitflag, output = ballsd(objectivecalc, optimparams, options=options, xmin=fundingchanges['total']['dec'], xmax=fundingchanges['total']['inc'], MaxIter=maxiters, timelimit=timelimit, fulloutput=True, stoppingfunc=stoppingfunc, verbose=verbose)
        
        # Normalize
        proginds = arange(nprogs)
        optparams = array(optparams)
        for y in xrange(nyears):
            theseinds = proginds+y*nprogs
            optparams[theseinds] *= options['totalspends'][y] / float(sum(optparams[theseinds]))
        optparams = optparams.tolist()
        
        # Update the model and store the results
        result = dict()
        result['kind'] = 'multiyear'
        result['fval'] = output['fval'] # Append the objective sequence
        result['Rarr'] = []
        labels = ['Original','Optimal']
        for params in [origalloc, optparams]: # CK: loop over original and (the best) optimal allocations
            sleep(0.1)
            alloc = multiyear(optimparams, years=options['years'], totalspends=options['totalspends'], nprogs=options['nprogs'], tvec=options['D']['opt']['partvec']) 
            R = runmodelalloc(options['D'], alloc, options['parindices'], options['randseed'], verbose=verbose) # Actually run
            result['Rarr'].append(dict()) # Append a structure
            result['Rarr'][-1]['R'] = deepcopy(R) # Store the R structure (results)
            result['Rarr'][-1]['label'] = labels.pop(0) # Store labels, one at a time
        result['xdata'] = R['tvec'] # Store time data
        result['alloc'] = alloc[:,0:len(R['tvec'])] # Store allocation data, and cut to be same length as time data
        
    
    
    
    
        
        
        
    ###########################################################################
    ## Multiple budgets optimization
    ###########################################################################
    if objectives['funding'] == 'range':
        
        ## Define options structure
        options = dict()
        options['ntimepm'] = 1 # Number of time-varying parameters -- always 1 in this case
        options['nprogs'] = nprogs # Number of programs
        options['D'] = deepcopy(D) # Main data structure
        options['outcomekeys'] = outcomekeys # Names of outcomes, e.g. 'inci'
        options['weights'] = weights # Weights for each parameter
        options['outindices'] = outindices # Indices for the outcome to be evaluated over
        options['parindices'] = parindices # Indices for the parameters to be updated on
        options['normalizations'] = normalizations # Whether to normalize a parameter
        options['fundingchanges'] = fundingchanges # Constraints-based funding changes
        options['totalspend'] = totalspend # Total budget
        options['randseed'] = None
        
        ## Run multiple budgets
        budgets = arange(objectives['outcome']['budgetrange']['minval'], objectives['outcome']['budgetrange']['maxval']+objectives['outcome']['budgetrange']['step'], objectives['outcome']['budgetrange']['step'])
        closesttocurrent = argmin(abs(budgets-1)) + 1 # Find the index of the budget closest to current and add 1 since prepend current budget
        nbudgets = len(budgets)
        budgets = hstack([1,budgets]) # Include current budget
        allocarr = [origalloc] # Original allocation
        fvalarr = [objectivecalc(optimparams, options=options)] # Outcome for original allocation
        for b in xrange(nbudgets):
            print('========== Running budget optimization %s of %s... ==========' % (b+1, nbudgets))
            options['totalspend'] = totalspend*budgets[b+1] # Total budget, skipping first
            optparams, fval, exitflag, output = ballsd(objectivecalc, optimparams, options=options, xmin=fundingchanges['total']['dec'], xmax=fundingchanges['total']['inc'], absinitial=stepsizes, MaxIter=maxiters, timelimit=timelimit, fulloutput=True, stoppingfunc=stoppingfunc, verbose=verbose)
            optparams[opttrue] = optparams[opttrue] / optparams[opttrue].sum() * (options['totalspend'] - optparams[~opttrue].sum())
            allocarr.append(optparams)
            fvalarr.append(fval) # Only need last value

        # Update the model and store the results
        result = dict()
        result['kind'] = objectives['funding']
        result.budgets = budgets
        result.budgetlabels = ['Original budget']
        for b in xrange(nbudgets): result.budgetlabels.append('%i%% budget' % (budgets[b+1]*100./float(budgets[0])))

        result['fval'] = fvalarr # Append the best value
        result['allocarr'] = allocarr # List of allocations
        labels = ['Original','Optimal']
        result['Rarr'] = []
        for params in [origalloc, allocarr[closesttocurrent]]: # CK: loop over original and (the best) optimal allocations
            sleep(0.1)
            alloc = timevarying(params, ntimepm=len(params)/nprogs, nprogs=nprogs, tvec=D['opt']['partvec'], totalspend=totalspend, fundingchanges=fundingchanges)
            R = runmodelalloc(options['D'], alloc, options['parindices'], options['randseed'], verbose=verbose) # Actually run
            result['Rarr'].append(dict()) # Append a structure
            result['Rarr'][-1]['R'] = deepcopy(R) # Store the R structure (results)
            result['Rarr'][-1]['label'] = labels.pop(0) # Store labels, one at a time









    ## Gather plot data
    from gatherplotdata import gatheroptimdata
    plot_result = gatheroptimdata(D, result, verbose=verbose)
    if 'optim' not in D['plot']: D['plot']['optim'] = [] # Initialize list if required
    D['plot']['optim'].append(plot_result) # In any case, append
    
    result_to_save = {'plot': [plot_result]}

    ## Save optimization to D
    D = saveoptimization(D, name, objectives, constraints, result_to_save, verbose=2)

    printv('...done optimizing programs.', 2, verbose)
    
    # This is new code for the OOP structure. Legacy users will not run this line because returnresult is false by default.
    if returnresult:
#        D['result'] = result['Rarr'][-1]['R']
        D['objective'] = result['fval']         # Note: Need to check this rigorously. Optimize is becoming a mess.
        D['optalloc'] = [x for x in optparams]  # This works for default optimisation. It may not for any more-complicated options.
    
    return D



def saveoptimization(D, name, objectives, constraints, result = None, verbose=2):
    #save the optimization parameters
    new_optimization = dict()
    new_optimization['name'] = name
    new_optimization['objectives'] = objectives
    new_optimization['constraints'] = constraints
    if result: new_optimization['result'] = result

    if not "optimizations" in D:
        D['optimizations'] = [new_optimization]
    else:
        try:
            index = [item['name'] for item in D['optimizations']].index(name)
            D['optimizations'][index] = deepcopy(new_optimization)
        except:
            D['optimizations'].append(new_optimization)
    return D

def removeoptimization(D, name):
    if "optimizations" in D:
        try:
            index = [item['name'] for item in D['optimizations']].index(name)
            D['optimizations'].pop(index)
        except:
            pass
    return D

def defaultobjectives(D, verbose=2):
    """
    Define default objectives for the optimization.
    """

    printv('Defining default objectives...', 3, verbose=verbose)

    ob = dict() # Dictionary of all objectives
    ob['year'] = dict() # Time periods for objectives
    ob['year']['start'] = defaults.startenduntil[0] # "Year to begin optimization from"
    ob['year']['end'] = defaults.startenduntil[1] # "Year to end optimization"
    ob['year']['until'] = defaults.startenduntil[2] # "Year to project outcomes to"
    ob['what'] = 'outcome' # Alternative is "['money']"
    
    ob['outcome'] = dict()
    ob['outcome']['fixed'] = sum(D['data']['origalloc']) # "With a fixed amount of ['money'] available"
    ob['outcome']['inci'] = defaults.incidalydeathcost[0] # "Minimize cumulative HIV incidence"
    ob['outcome']['inciweight'] = defaults.incidalydeathcostweight[0] # "Incidence weighting"
    ob['outcome']['daly'] = defaults.incidalydeathcost[1] # "Minimize cumulative DALYs"
    ob['outcome']['dalyweight'] = defaults.incidalydeathcostweight[1] # "DALY weighting"
    ob['outcome']['death'] = defaults.incidalydeathcost[2] # "Minimize cumulative AIDS-related deaths"
    ob['outcome']['deathweight'] = defaults.incidalydeathcostweight[2] # "Death weighting"
    ob['outcome']['costann'] = defaults.incidalydeathcost[3] # "Minimize cumulative DALYs"
    ob['outcome']['costannweight'] = defaults.incidalydeathcostweight[3] # "Cost weighting"
    ob['outcome']['variable'] = [] # No variable budgets by default
    ob['outcome']['budgetrange'] = dict() # For running multiple budgets
    ob['outcome']['budgetrange']['minval'] = None
    ob['outcome']['budgetrange']['maxval'] = None
    ob['outcome']['budgetrange']['step'] = None
    ob['funding'] = "constant" #that's how it works on FE atm

    # Other settings
    ob['timevarying'] = False # Do not use time-varying parameters
    ob['artcontinue'] = 1 # No one currently on ART stops
    ob['otherprograms'] = "remain" # Other programs remain constant after optimization ends

    ob['money'] = dict()
    ob['money']['objectives'] = dict()
    for objective in ['inci', 'incisex', 'inciinj', 'mtct', 'mtctbreast', 'mtctnonbreast', 'death', 'dalys']:
        ob['money']['objectives'][objective] = dict()
        # Checkbox: by default it's False meaning the objective is not applied
        ob['money']['objectives'][objective]['use'] = False
        # If "By" is not active "To" is used. "By" is active by default. 
        ob['money']['objectives'][objective]['by_active'] = True
        # "By" text entry box: 0.5 means a 50% reduction
        ob['money']['objectives'][objective]['by'] = 0.5
        # "To" text entry box: an absolute value e.g. reduce deaths to <500
        ob['money']['objectives'][objective]['to'] = 0
    ob['money']['objectives']['inci']['use'] = True # Set incidence to be on by default

    ob['money']['costs'] = []
    for p in xrange(D['G']['nprogs']):
        ob['money']['costs'].append(100) # By default, use a weighting of 100%

    return ob

def defaultconstraints(D, verbose=2):
    """
    Define default constraints for the optimization.
    """

    printv('Defining default constraints...', 3, verbose=verbose)

    con = dict()
    con['txelig'] = 4 # 4 = "All people diagnosed with HIV"
    con['dontstopart'] = True # "No one who initiates treatment is to stop receiving ART"
    con['yeardecrease'] = []
    con['yearincrease'] = []
    for p in xrange(D['G']['nprogs']): # Loop over all defined programs
        con['yeardecrease'].append(dict())
        con['yeardecrease'][p]['use'] = False # Tick box: by default don't use
        con['yeardecrease'][p]['by'] = 80 # Text entry box: 0.5 = 50% per year
        con['yearincrease'].append(dict())
        con['yearincrease'][p]['use'] = False # Tick box: by default don't use
        con['yearincrease'][p]['by'] = 120 # Text entry box: 0.5 = 50% per year
    con['totaldecrease'] = []
    con['totalincrease'] = []
    for p in xrange(D['G']['nprogs']): # Loop over all defined programs
        con['totaldecrease'].append(dict())
        con['totaldecrease'][p]['use'] = False # Tick box: by default don't use
        con['totaldecrease'][p]['by'] = 50 # Text entry box: 0.5 = 50% per total
        con['totalincrease'].append(dict())
        con['totalincrease'][p]['use'] = False # Tick box: by default don't use
        con['totalincrease'][p]['by'] = 200 # Text entry box: 0.5 = 50% total
    
    con['coverage'] = []
    for p in xrange(D['G']['nprogs']): # Loop over all defined programs
        con['coverage'].append(dict())
        con['coverage'][p]['use'] = False # Tick box: by default don't use
        con['coverage'][p]['level'] = 0 # First text entry box: default no limit
        con['coverage'][p]['year'] = 2030 # Year to reach coverage level by
        
    return con


def defaultoptimizations(D, verbose=2):
    """ Define a list of default optimizations (one default optimization) """
    
    # Start at the very beginning, a very good place to start :)
    optimizations = [dict()]
    
    ## Current conditions
    optimizations[0]['name'] = 'Default'
    optimizations[0]['constraints'] = defaultconstraints(D, verbose)
    optimizations[0]['objectives'] = defaultobjectives(D, verbose)
    return optimizations


def partialupdateM(oldM, newM, indices, setbefore=False, setafter=True):
    """ 
    Update M, but only for certain indices. If setbefore is true, reset all values before indices to new value; similarly for setafter. 
    WARNING: super ugly code!!
    """
    from makemodelpars import totalacts
    output = deepcopy(oldM)
    for key in output.keys():
        if key not in ['transit', 'pships', 'const', 'tvec', 'hivprev', 'totalacts']: # Exclude certain keys that won't be updated
            if hasattr(output[key],'keys'): # It's a dict, loop again
                for key2 in output[key].keys():
                    try:
                        if ndim(output[key][key2])==1:
                            output[key][key2][indices] = newM[key][key2][indices]
                            if setbefore: output[key][key2][:min(indices)] = newM[key][key2][:min(indices)]
                            if setafter: output[key][key2][max(indices):] = newM[key][key2][max(indices):]
                        elif ndim(output[key][key2])==2:
                            output[key][key2][:,indices] = newM[key][key2][:,indices]
                            if setbefore: output[key][key2][:,:min(indices)] = newM[key][key2][:,:min(indices)]
                            if setafter: output[key][key2][:,max(indices):] = newM[key][key2][:,max(indices):]
                        else:
                            raise Exception('%i dimensions for parameter M.%s.%s' % (ndim(output[key][key2][indices]), key, key2))
                    except:
                        print('Could not set indices for parameter M.%s.%s, indices %i-%i' % (key, key2, min(indices), max(indices)))
#                        import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
            else:
                try:
                    if ndim(output[key])==1:
                        output[key][indices] = newM[key][indices]
                        if setbefore: output[key][:min(indices)] = newM[key][:min(indices)]
                        if setafter: output[key][max(indices):] = newM[key][max(indices):]
                    elif ndim(output[key])==2:
                        output[key][:,indices] = newM[key][:,indices]
                        if setbefore: output[key][:,:min(indices)] = newM[key][:,:min(indices)]
                        if setafter: output[key][:,max(indices):] = newM[key][:,max(indices):]
                    else:
                        raise Exception('%i dimensions for parameter M.%s' % (ndim(output[key][indices]), key, key2))
                except:
                    print('Could not set indices for parameter M.%s, indices %i-%i' % (key, min(indices), max(indices)))
#                    import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
    
    output['totalacts'] = totalacts(output, len(output['tvec'])) # Update total acts
    return output
