def getcurrentbudget(D, alloc=None, randseed=None):
    """
    Purpose: get the parameters corresponding to a given allocation. If no allocation is specified, this function also estimates the current budget
    Inputs: D, alloc (optional)
    Returns: D
    Version: 2014nov30
    """
    from makeccocs import ccoeqn, cceqn, cc2eqn, cco2eqn, coverage_params, default_convertedccparams, default_convertedccoparams, makesamples
    from numpy import nan, zeros
    from utils import sanitize
    from updatedata import perturb
    
    npts = len(D.opt.partvec) # Number of parameter points

    # Initialise currentbudget if needed
    allocprovided = not(isinstance(alloc,type(None)))
    if not(allocprovided):
        currentbudget = []

    # Initialise currentcoverage and currentnonhivdalys
    currentcoverage = zeros((D.G.nprogs, npts))
    currentnonhivdalysaverted = zeros(npts)

    # Initialise parameter structure (same as D.P)
    for param in D.P.keys():
        if isinstance(D.P[param], dict) and 'p' in D.P[param].keys():
            D.P[param].c = nan+zeros((len(D.P[param].p), npts))

    # Loop over programs
    for prognumber, progname in enumerate(D.data.meta.progs.short):
        
        # Get allocation - either it's been passed in, or we figure it out from the data
        totalcost = alloc[prognumber, :] if allocprovided else sanitize(D.data.costcov.cost[prognumber]).tolist()

        # Extract and sum the number of non-HIV-related DALYs 
        nonhivdalys = D.programs[progname]['nonhivdalys']

        # Extract the converted cost-coverage parameters... or if there aren't any, use defaults (for sim only; FE produces warning)
        convertedccparams = D.programs[progname]['convertedccparams'] if D.programs[progname]['convertedccparams'] else default_convertedccparams
        if randseed>=0: convertedccparams[0][1] = perturb(1,(convertedccparams[2][1]-convertedccparams[1][1])/2, randseed=randseed) - 1 + convertedccparams[0][1]
        currentcoverage[prognumber, :] = cc2eqn(totalcost, convertedccparams[0]) if len(convertedccparams[0])==2 else cceqn(totalcost, convertedccparams[0])

        # TODO -- This should be summed over time anyway... so can make currentcoverage a vector. This was Robyn's intention anyway!
        currentnonhivdalysaverted += nonhivdalys[0]*currentcoverage[prognumber, :]

        # Loop over effects
        for effectnumber, effect in enumerate(D.programs[progname]['effects']):

            # Get population and parameter info
            popname = effect[1]
            parname = effect[0][1]
            
            # Is the affected parameter coverage?
            if parname in coverage_params:
                D.P[parname].c[:] = currentcoverage[prognumber]
            # ... or not?
            else:
                popnumber = D.data.meta.pops.short.index(popname[0]) if popname[0] in D.data.meta.pops.short else 0
                 # Use parameters if there, otherwise give it some predefined ones
                convertedccoparams = effect[4] if len(effect)>4 and len(effect[4])>=4 else default_convertedccoparams
                if randseed>=0:
                    try:
                        convertedccoparams[0][1] = perturb(1,(convertedccoparams[2][1]-convertedccoparams[1][1])/2, randseed=randseed) - 1 + convertedccoparams[0][1]
                        convertedccoparams[-1], convertedccoparams[-2] = makesamples(effect[2], effect[3][0], effect[3][1], effect[3][2], effect[3][3], samplesize=1, randseed=randseed)
                    except:
                        convertedccoparams = default_convertedccoparams
                        print('WARNING, no parameters entered for progname=%s , effectnumber=%s, popname=%s, parname=%s' % (progname, effectnumber, popname, parname))
                    
                D.P[parname].c[popnumber] = cco2eqn(totalcost, convertedccoparams[0]) if len(convertedccparams[0])==2 else ccoeqn(totalcost, convertedccoparams[0])

        if not(allocprovided):
            currentbudget.append(totalcost)
            D.data.meta.progs.currentbudget = currentbudget
            

    return D, currentcoverage, currentnonhivdalysaverted
    
