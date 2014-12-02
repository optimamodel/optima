def getcurrentbudget(D, alloc=None):
    """
    Purpose: get the parameters corresponding to a given allocation. If no allocation is specified, this function also estimates the current budget
    Inputs: D, alloc (optional)
    Returns: D
    Version: 2014nov30
    """
    from makeccocs import ccoeqn, cceqn, makesamples
    import numpy as np
    
    # Initialise parameter structure (same as D.P). #TODO make this less ugly
    for param in D.P.keys():
        if isinstance(D.P[param], dict):
            if 'p' in D.P[param].keys():
                D.P[param].c = np.zeros(np.size(np.array(D.P[param].p),0))
                D.P[param].c[D.P[param].c>=0] = float('nan')


    # Initialise currentbudget if needed
    if alloc==None:
        currentbudget = []

    # Loop over programs
    for progname in D.data.meta.progs.short:
        
        # Get program index 
        prognumber = D.data.meta.progs.short.index(progname) # get program number

        # Loop over effects
        for effectname in D.programs[progname]:

            # Get effect index 
            effectnumber = D.programs[progname].index(effectname)    
            
            # Do this if it's a saturating program
            if D.data.meta.progs.saturating[prognumber]:

                # If an allocation has been passed in, we don't need to figure out the program budget
                if not(alloc==None):
                    totalcost = alloc[prognumber]

                # If an allocation has been passed in, we don't need to figure out the program budget
                else:
                    totalcost = D.data.costcov.cost[prognumber]
                    totalcost = np.asarray(totalcost)
                    totalcost = totalcost[~np.isnan(totalcost)]
                    totalcost = totalcost[-1]


                # Get population info
                popname = effectname[1]
    
                # Is it a population-disaggregated parameter... ?
                if popname[0] in D.data.meta.pops.short:
                    popnumber = D.data.meta.pops.short.index(popname[0]) 
                # ... or not ?
                else:
                    popnumber = 0 

                # Temporary work around for sharing rates # TODO, FIX THIS ASAP, IT'S AWFUL
                if effectname[0][1] == 'sharing':
                    popnumber = 0 
                      
                # Unpack
                muz, stdevz, muf, stdevf, saturation, growthrate = effectname[3][0], effectname[3][1], effectname[3][2], effectname[3][3], effectname[3][4], effectname[3][5]
                zerosample, fullsample = makesamples(muz, stdevz, muf, stdevf, samplesize=1)
                y = ccoeqn(totalcost, [saturation, growthrate, zerosample, fullsample])
                D.P[effectname[0][1]].c[popnumber] = y
                if not(y>=0):
                    import pdb; pdb.set_trace()
                    

            # ... or do this if it's not a saturating program
            else:

                # If an allocation has been passed in, we don't need to figure out the program budget
                if not(alloc==None):
                    totalcost = alloc[prognumber]

                # ... or else we do
                else:
                    unitcost, cov = D.data.costcov.cost[prognumber], D.data.costcov.cov[prognumber] 
                    unitcost, cov = np.asarray(unitcost), np.asarray(cov)
                    unitcost, cov = unitcost[~np.isnan(unitcost)], cov[~np.isnan(cov)]
                    unitcost, cov = unitcost[-1], cov[-1]
                    totalcost = unitcost*cov

                y = cceqn(totalcost, D.programs[progname][effectnumber][-1][0])
                D.P[effectname[0][1]].c[0] = y
                if not(y>=0):
                    import pdb; pdb.set_trace()


        if alloc==None:
            currentbudget.append(totalcost)
            D.data.meta.progs.currentbudget = currentbudget

    return D