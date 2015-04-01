def getcurrentbudget(D, alloc=None, randseed=None):
    """
    Purpose: get the parameters corresponding to a given allocation. If no allocation is specified, this function also estimates the current budget
    Inputs: D, alloc (optional)
    Returns: D
    Version: 2014nov30
    """
    from makeccocs import ccoeqn, cco2eqn, coverage_params, makesamples
    from numpy import nan, zeros, array
    from utils import sanitize, perturb
    
    npts = len(D['opt']['partvec']) # Number of parameter points
    allocprovided = not(isinstance(alloc,type(None))) # Initialise currentbudget if needed
    currentcoverage = getcurrentcoverage(D=D, alloc=alloc, randseed=randseed) # Get currentcoverage 
    currentnonhivdalysaverted = zeros(npts) # Initialise currentnonhivdalys

    # Initialise parameter structure (same as D['P'])
    for param in D['P'].keys():
        if isinstance(D['P'][param], dict) and 'p' in D['P'][param].keys():
            D['P'][param]['c'] = nan+zeros((len(D['P'][param]['p']), npts))

    # Loop over programs
    for prognumber, progname in enumerate(D['data']['meta']['progs']['short']):
        
        # Get allocation - either it's been passed in, or we figure it out from the data
        totalcost = alloc[prognumber, :] if allocprovided else sanitize(D['data']['costcov']['cost'][prognumber]).tolist()

        # Extract and sum the number of non-HIV-related DALYs 
        nonhivdalys = D['programs'][prognumber]['nonhivdalys']

        # TODO -- This should be summed over time anyway... so can make currentcoverage a vector. This was Robyn's intention anyway!
        currentnonhivdalysaverted += nonhivdalys*currentcoverage[prognumber, :]

        # Loop over effects
        for effectnumber, effect in enumerate(D['programs'][prognumber]['effects']):

            # Get population and parameter info
            popname, parname = effect['popname'], effect['param']
            
            if parname in coverage_params: # Is the affected parameter coverage?
                D['P'][parname]['c'][:] = currentcoverage[prognumber]
            else: # ... or not?
                try: # Get population number...
                    popnumber = D['data']['meta']['pops']['short'].index(popname)
                except: # ... or raise error if it isn't recognised
                    print('Cannot recognise population %s, it is not in %s' % (popname, D['data']['meta']['pops']['short']))
                try: # Use parameters if there...
                    convertedccoparams = effect['convertedccoparams']
                except: # ... otherwise give it some predefined ones
                    convertedccoparams = setdefaultccoparams(progname=progname, param=effect['param'], pop=effect['popname'])
                if randseed>=0:
                    try:
                        convertedccoparams[0][1] = array(perturb(1,(convertedccoparams[2][1]-convertedccoparams[1][1])/2, randseed=randseed)) - 1 + convertedccoparams[0][1]
                        convertedccoparams[-1], convertedccoparams[-2] = makesamples(effect['coparams'], effect['convertedcoparams'][0], effect['convertedcoparams'][1], effect['convertedcoparams'][2], effect['convertedcoparams'][3], randseed=randseed)
                    except:
                        print('Random sampling for CCOCs failed for program %s, makesamples failed with parameters %s.' % (progname, convertedccoparams))

                D['P'][parname]['c'][popnumber] = cco2eqn(totalcost, convertedccoparams[0]) if len(convertedccoparams[0])==4 else ccoeqn(totalcost, convertedccoparams[0])

    return D, currentnonhivdalysaverted
   
################################################################
def getcurrentcoverage(D, alloc=None, randseed=None):
    ''' Get the coverage levels corresponding to a particular allocation '''
    from numpy import zeros_like, array
    from makeccocs import cc2eqn, cceqn
    from utils import perturb
    
    origallocwaslist = 0
    if isinstance(alloc,list): alloc, origallocwaslist = array(alloc), 1
    currentcoverage = zeros_like(alloc)

    for prognumber, progname in enumerate(D['data']['meta']['progs']['short']):
        if D['programs'][prognumber]['effects']:            
            if D['programs'][prognumber]['convertedccparams']:
                convertedccparams = D['programs'][prognumber]['convertedccparams'] 
            else:
                convertedccparams = setdefaultccparams(progname=progname)    
            if randseed>=0: convertedccparams[0][1] = array(perturb(1,(array(convertedccparams[2][1])-array(convertedccparams[1][1]))/2., randseed=randseed)) - 1 + array(convertedccparams[0][1]) 
            currentcoverage[prognumber,] = cc2eqn(alloc[prognumber,], convertedccparams[0]) if len(convertedccparams[0])==2 else cceqn(alloc[prognumber,], convertedccparams[0])        
        else:
            currentcoverage[prognumber,] = array([None]*len(alloc[prognumber,]))
        if origallocwaslist: currentcoverage = currentcoverage.tolist()
            
    return currentcoverage
        
################################################################
def setdefaultccparams(progname=None):
    '''Set default coverage levels. ONLY for use in BE. In FE, if ccocs haven't been defined then the user won't get to this step'''

    # Defaults are stored as [median, lower bound, upperbound]. 
    default_convertedccparams = [[0.8, 4.9e-06], [0.8, 4.7e-06], [0.8, 5.1e-06]]
    print('WARNING: Cost-coverage curve not found for program %s... Using defaults.' % (progname))
    return default_convertedccparams
    
################################################################
def setdefaultccoparams(progname=None, param=None, pop=None):
    '''Set default coverage levels. ONLY for use in BE. In FE, if ccocs haven't been defined then the user won't get to this step'''

    # Defaults are stored as [median, lower bound, upperbound]. 
    default_convertedccoparams = [[0.8, 4.9e-06, 0.4, 0.8, 0], [0.8, 4.7e-06, 5.1e-06, 0.4, 0.8, 0], [0.8, 4.9e-06, 0.4, 0.8, 0]]
    print('WARNING: Cost-outcome curve not found for program %s, parameter %s and population %s... Using defaults.' % (progname, param, pop))
    
    return default_convertedccoparams
