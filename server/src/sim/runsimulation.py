def uncertainties(Sarray, quantiles):
    """
    Take an array of simulation results and calculate the corresponding uncertainty
    intervals defined by the list quantiles.
    
    Version: 2014nov23 by cliffk
    """
    
    S = Sarray
    
    return S





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
    D.opt = setoptions(D, startyear, endyear)
    
    # Convert data parameters to model parameters
    from makemodelpars import makemodelpars
    D.M = makemodelpars(D.P, D.opt, verbose=verbose)
    
    # Create fitted parameters
    from makefittedpars import makefittedpars
    D.F = makefittedpars()
    
    # Run model
    from model import model
    Sarray = []
    for s in range(D.opt.nsims): # TODO -- parallelize
        tmpS = model(D.G, D.M, D.F[s], D.opt, verbose=verbose)
        Sarray.append(tmpS)
    
    # Calculate statistics
    D.S = uncertainties(Sarray, D.opt.quantiles)
    
    
    # Save output
    from dataio import savedata
    savedata(D.projectfilename, D, verbose=verbose)
    printv('...done running simulation for project %s.' % D.projectfilename, 2, verbose)
    return D