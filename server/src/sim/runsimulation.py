def runsimulation(D, startyear=2000, endyear=2030, verbose=2):
    """
    Calculate initial model estimates.
    
    Version: 2014nov26 by cliffk
    """

    from printv import printv
    printv('Running simulation...', 1, verbose)
    dosave = False # Flag for whether or not to save
    
    # Set options to update year range
    from setoptions import setoptions
    D.opt = setoptions(D.opt, startyear=startyear, endyear=endyear)
    
#    print('WARNING should add conditionals here')
#    from makeccocs import makeallccocs
#    D = makeallccocs(D, verbose=verbose)
#    
#    from getcurrentbudget import getcurrentbudget
#    D = getcurrentbudget(D) # TODO Add verbose
    
    # Convert data parameters to model parameters
    if 'M' not in D.keys():
        dosave = True
        from makemodelpars import makemodelpars
        D.M = makemodelpars(D.P, D.opt, verbose=verbose)
    
    # Run model
    from model import model
    allsims = []
    for s in range(len(D.F)): # TODO -- parallelize
        S = model(D.G, D.M, D.F[s], D.opt, verbose=verbose)
        allsims.append(S)
    D.S = allsims[0] # Save one full sim structure for troubleshooting and funsies
    
    # Calculate results
    from makeresults import makeresults
    D.R = makeresults(D, allsims, D.opt.quantiles, verbose=verbose)
    
    # Gather plot data
    from gatherplotdata import gatheruncerdata
    D.plot.E = gatheruncerdata(D, D.R, verbose=verbose)
    
    # Save output
    if dosave:
        from dataio import savedata
        savedata(D.G.projectfilename, D, verbose=verbose)
    
    printv('...done running simulation for project %s.' % D.G.projectfilename, 2, verbose)
    return D