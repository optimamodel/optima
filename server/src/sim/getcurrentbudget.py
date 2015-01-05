def getcurrentbudget(D, alloc=None):
    """
    Purpose: get the parameters corresponding to a given allocation. If no allocation is specified, this function also estimates the current budget
    Inputs: D, alloc (optional)
    Returns: D
    Version: 2014nov30
    """
    from makeccocs import ccoeqn, cceqn
    import numpy as np
    
    # Initialise parameter structure (same as D.P). #TODO make this less ugly
    for param in D.P.keys():
        if isinstance(D.P[param], dict):
            if 'p' in D.P[param].keys():
                D.P[param].c = np.zeros(np.size(np.array(D.P[param].p),0))
                D.P[param].c[D.P[param].c>=0] = float('nan')

    # Initialise currentbudget if needed
    allocprovided = not(isinstance(alloc,type(None)))
    if not(allocprovided):
        currentbudget = []

    # Loop over programs
    for progname in D.data.meta.progs.short:
        
        # Get program index 
        prognumber = D.data.meta.progs.short.index(progname) # get program number

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
        for effectname in D.programs[progname]:

            # Get effect index 
            effectnumber = D.programs[progname].index(effectname)    

            # Get population info
            popname = effectname[1]
            
            # Does this affect a specific population within the model?
            if popname[0] in D.data.meta.pops.short:

                popnumber = D.data.meta.pops.short.index(popname[0]) 

                # Unpack
                muz, stdevz, muf, stdevf, saturation, growthrate = effectname[3][0], effectname[3][1], effectname[3][2], effectname[3][3], effectname[3][4], effectname[3][5]
#                zerosample, fullsample = makesamples(muz, stdevz, muf, stdevf, samplesize=1)
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