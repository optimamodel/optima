def runsimulation(D, startyear=2000, endyear=2030, verbose=2):
    """
    RUNSIMULATION
    Calculate model estimates
    
    Version: 2014nov23 by cliffk
    """

    from printv import printv
    printv('Running simulation...', 1, verbose)
    
    # update options structure
    from setoptions import setoptions
    D.opt = setoptions(opt=D.opt, startyear=startyear, endyear=endyear)
    
    # Convert data parameters to model parameters
    from makemodelpars import makemodelpars
    D.M = makemodelpars(D.P, D.opt, verbose=verbose)
    
    # Create fitted parameters
    from makefittedpars import makefittedpars
    D.F = makefittedpars(D.G, D.opt, verbose=verbose)
    
    # Run model
    from model import model
    allsims = []
    for s in range(D.opt.nsims): # TODO -- parallelize
        S = model(D.G, D.M, D.F[s], D.opt, verbose=verbose)
        allsims.append(S)
    D.S = allsims[0] # Save one full sim structure for troubleshooting and funsies
    
    # Calculate results
    from makeresults import makeresults
    D.R = makeresults(allsims, D, D.opt.quantiles, verbose=verbose)
    
    # Save output
    from dataio import savedata
    savedata(D.projectfilename, D, verbose=verbose)
    printv('...done running simulation for project %s.' % D.projectfilename, 2, verbose)
    return D
