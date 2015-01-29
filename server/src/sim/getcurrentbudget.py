def getcurrentbudget(D, alloc=None):
    """
    Purpose: get the parameters corresponding to a given allocation. If no allocation is specified, this function also estimates the current budget
    Inputs: D, alloc (optional)
    Returns: D
    Version: 2014nov30
    """
    from makeccocs import ccoeqn, cceqn, cc2eqn, cco2eqn, coverage_params, default_convertedccparams, default_convertedccoparams  
    from numpy import asarray, nan, isnan, zeros  
    
    npts = len(D.opt.partvec) # Number of parameter points

    # Initialise parameter structure (same as D.P)
    for param in D.P.keys():
        if isinstance(D.P[param], dict) and 'p' in D.P[param].keys():
            D.P[param].c = nan+zeros((len(D.P[param].p), npts))

    # Initialise currentbudget if needed
    allocprovided = not(isinstance(alloc,type(None)))
    if not(allocprovided):
        currentbudget = []

    # Initialise currentcoverage and currentnonhivdalys
    currentcoverage = zeros((D.G.nprogs, npts))
    currentnonhivdalysaverted = zeros(npts)

    # Loop over programs
    for prognumber, progname in enumerate(D.data.meta.progs.short):
        
        # If an allocation has been passed in, we don't need to figure out the program budget
        if allocprovided:
            # totalcost = alloc[prognumber]
            totalcost = alloc[prognumber, :] # Allocation is over time hence a vector rather than constant
        else:
            # Get cost info
            totalcost = D.data.costcov.cost[prognumber]
            totalcost = asarray(totalcost)
            totalcost = totalcost[~isnan(totalcost)]
            totalcost = totalcost[-1]

        # Extract the converted cost-coverage parameters... 
        if D.programs[progname]['convertedccparams']:
            convertedccparams = D.programs[progname]['convertedccparams']
        # ... or if there aren't any, use defaults (for sim only; FE produces warning)
        else:
            convertedccparams = default_convertedccparams

        # Get coverage
        if len(convertedccparams)==2:
            currentcoverage[prognumber, :] = cc2eqn(totalcost, [convertedccparams[0], convertedccparams[1][1]])
        else:
            currentcoverage[prognumber, :] = cceqn(totalcost, [convertedccparams[0], convertedccparams[1][1], convertedccparams[2]]) 

        # Extract and sum the number of non-HIV-related DALYs 
        nonhivdalys = D.programs[progname]['nonhivdalys']
        
        # TODO -- This should be summed over time anyway... so can make currentcoverage a vector. This was Robyn's intention anyway!
        currentnonhivdalysaverted += nonhivdalys[0] * currentcoverage[prognumber, :]

        # Loop over effects
        for effectnumber, effect in enumerate(D.programs[progname]['effects']):

            # Get population info
            popname = effect[1]

            # Get parameter info
            parname = effect[0][1]

            # Is the affected parameter coverage?
            if parname in coverage_params:
                D.P[effect[0][1]].c[:] = currentcoverage[prognumber]

            # ... or not?
            else:
                if popname[0] in D.data.meta.pops.short:
                    popnumber = D.data.meta.pops.short.index(popname[0]) 
                else:
                    popnumber = 0
                if len(effect)>4 and len(effect[4])>=4: #happy path if co_params are actually there
                    # Unpack
                    convertedccoparams = effect[4]
                else:
                    # did not get co_params yet, giving it some defined params TODO @RS @AS do something sensible here:
                    convertedccoparams = default_convertedccoparams
                    
                if len(convertedccparams)==2:
                    y = cco2eqn(totalcost, [convertedccoparams[0], convertedccoparams[1][1], convertedccoparams[2], convertedccoparams[3]])
                else:
                    y = ccoeqn(totalcost, [convertedccoparams[0], convertedccoparams[1][1], convertedccoparams[2], convertedccoparams[3], convertedccoparams[4]])
                D.P[effect[0][1]].c[popnumber] = y


        if not(allocprovided):
            currentbudget.append(totalcost)
            D.data.meta.progs.currentbudget = currentbudget
            

    return D, currentcoverage, currentnonhivdalysaverted
    
