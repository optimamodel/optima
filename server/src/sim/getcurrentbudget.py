def getcurrentbudget(D, alloc=None):
    """
    Purpose: get the parameters corresponding to a given allocation. If no allocation is specified, this function also estimates the current budget
    Inputs: D, alloc (optional)
    Returns: D
    Version: 2014nov30
    """
    from makeccocs import ccoeqn, cceqn, coverage_params, default_convertedccparams, default_convertedccoparams
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
        for effectnumber, effect in enumerate(D.programs[progname]['effects']):

            # Get population info
            popname = effect[1]

            # Get parameter info
            parname = effect[0][1]

            # Is the affected parameter coverage?
            if parname in coverage_params:
                if D.programs[progname]['convertedccparams']:
                    convertedccparams = D.programs[progname]['convertedccparams']
                else:
                    convertedccparams = default_convertedccparams
                y = cceqn(totalcost, convertedccparams)
                D.P[effect[0][1]].c[0] = y

            # ... or not?
            else:
                if popname[0] in D.data.meta.pops.short:
                    popnumber = D.data.meta.pops.short.index(popname[0]) 
                else:
                    popnumber = 0

                if len(effect)>4 and len(effect[4])>=4: #happy path if co_params are actually there
                    # Unpack
                    convertedccoparams = effect[4]
                else: # did not get co_params yet, giving it some defined params TODO @RS @AS do something sensible here:
                    convertedccoparams = default_convertedccoparams

                #   zerosample, fullsample = makesamples(muz, stdevz, muf, stdevf, samplesize=1)
                y = ccoeqn(totalcost, convertedccoparams)
                D.P[effect[0][1]].c[popnumber] = y


        if not(allocprovided):
            currentbudget.append(totalcost)
            D.data.meta.progs.currentbudget = currentbudget

    return D