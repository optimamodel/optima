def getcurrentbudget(D):
    """
    Purpose: get the current budget and the corresponding parameters
    Inputs: D
    Returns: D
    Version: 2014nov28
    """
    from makeccocs import ccoeqn, makesamples
    import numpy as np
    
    # Initialise parameter structure (same as D.P). #TODO make this less ugly
    for param in D.P.keys():
        if isinstance(D.P[param], dict):
            if 'p' in D.P[param].keys():
                D.P[param].c = D.P[param].p.copy()
                D.P[param].c[D.P[param].c>=0] = float('nan')

    # Initialise currentbudget
    currentbudget = []

    # Loop over programs
    for progname in D.data.meta.progs.code:
        
        # Get program index 
        prognumber = D.data.meta.progs.code.index(progname) # get program number

        # Loop over effects
        for effectname in D.programs[progname]:

            # Get effect index 
            effectnumber = D.programs[progname].index(effectname)    
            
            # Do this if it's a saturating program
            if D.data.meta.progs.saturating[prognumber]:
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

            # ... or do this if it's not a saturating program
            else:
                unitcost, cov = D.data.costcov.cost[prognumber], D.data.costcov.cov[prognumber] 
                unitcost, cov = np.asarray(unitcost), np.asarray(cov)
                unitcost, cov = unitcost[~np.isnan(unitcost)], cov[~np.isnan(cov)]
                unitcost, cov = unitcost[-1], cov[-1]
                totalcost = unitcost*cov

                D.P[effectname[0][1]].c[0] = D.programs[progname][effectnumber][-1][0]

        currentbudget.append(totalcost)
        D.data.meta.progs.currentbudget = currentbudget

    return D


