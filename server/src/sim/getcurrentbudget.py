def getcurrentbudget(D, alloc=None):
    """
    Purpose: get the parameters corresponding to a given allocation. If no allocation is specified, this function also estimates the current budget
    Inputs: D, alloc (optional)
    Returns: D
    Version: 2014nov30
    """
    from makeccocs import ccoeqn, cceqn, coverage_params
    import numpy as np
    
    # Initialise parameter structure (same as D.P). #TODO make this less ugly
    for param in D.P.keys():
        if isinstance(D.P[param], dict) and 'p' in D.P[param].keys():
            D.P[param].c = np.zeros(np.size(np.array(D.P[param].p),0))
            D.P[param].c[D.P[param].c>=0] = float('nan')

    # Initialise currentbudget if needed
    allocprovided = not(isinstance(alloc,type(None)))
    if not(allocprovided):
        currentbudget = []

    # Loop over programs
    for prognumber, progname in enumerate(D.data.meta.progs.short):
        
        # If an allocation has been passed in, we don't need to figure out the program budget
        if allocprovided:
            totalcost = alloc[prognumber]
        else:
            # Get cost info
            totalcost = D.data.costcov.cost[prognumber]
            totalcost = np.asarray(totalcost)
            totalcost = totalcost[~np.isnan(totalcost)]
            totalcost = totalcost[-1]

        # Loop over effects
        for effectnumber, effectname in enumerate(D.programs[progname]):
            # Get population info
            popname = effectname[1]

            # Get parameter info
            parname = effectname[0][1]
            # Does this affect a specific population within the model?
            if popname[0] in D.data.meta.pops.short and not parname in coverage_params:
                popnumber = D.data.meta.pops.short.index(popname[0]) 
                if len(effectname)>3 and len(effectname[3])>=7: #happy path if co_params are actually there
                    # Unpack
                    saturation, growthrate, xupperlim, muz, stdevz, muf, stdevf = effectname[3][0], effectname[3][1], effectname[3][2], effectname[3][3], effectname[3][4], effectname[3][5], effectname[3][6]
                else: # did not get co_params yet, giving it some defined params TODO @RS @AS do something sensible here:
                    saturation, growthrate, xupperlim, muz, stdevz, muf, stdevf = effectname[3][0], effectname[3][1], effectname[3][2], 0.3, 0.5, 0.7, 0.9

                #   zerosample, fullsample = makesamples(muz, stdevz, muf, stdevf, samplesize=1)
                y = ccoeqn(totalcost, [saturation, growthrate, muz, muf])
                D.P[effectname[0][1]].c[popnumber] = y


            # ... or does it affect all parameters?
            else:
                y = cceqn(totalcost, D.programs[progname][effectnumber][-1][0])
                D.P[effectname[0][1]].c[0] = y

        if not(allocprovided):
            currentbudget.append(totalcost)
            D.data.meta.progs.currentbudget = currentbudget

    return D