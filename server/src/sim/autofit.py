def autofit(D, timelimit=60, startyear=2000, endyear=2015, verbose=2):
    """
    Automatic metaparameter fitting code:
        D is the project data structure
        timelimit is the maximum time limit for fitting in seconds
        startyear is the year to begin running the model
        endyear is the year to stop running the model
        verbose determines how much information to print.
        
    Version: 2014nov24 by cliffk
    """
    
    from model import model
    from time import time
    from printv import printv
    printv('Running automatic calibration...', 1, verbose)
    
    # TODO -- actually implement :)
    tstart = time()
    elapsed = 0
    iteration = 0
    while elapsed<timelimit:
        iteration += 1
        elapsed = time() - tstart
        D.S = model(D.G, D.M, D.F[0], D.opt, verbose=verbose)
        printv('Iteration: %i | Elapsed: %f s |  Limit: %f s' % (iteration, elapsed, timelimit), 2, verbose)
        D.S.mismatch = -1 # Mismatch for this simulation
    
    allsims = [D.S]
    
    # Calculate results
    from makeresults import makeresults
    D.R = makeresults(allsims, D, D.opt.quantiles, verbose=verbose)

    # Gather plot data
    from gatherplotdata import gatherepidata
    D.plot.E = gatherepidata(D, verbose=verbose)
    
    printv('...done with automatic calibration.', 2, verbose)
    return D