def autofit(D, timelimit, startyear=2000, endyear=2015, verbose=2):
    """
    Automatic metaparameter fitting code.
    
    Example usage:
        ipython --pylab # Run Python with Pylab
        ion() # Turn on interactive plotting
        import optima # Run Optima
        F = D.F # Shorten name for fitted parameters
        D = manualfit(D, F) # Run manualfit
        F.force *= 0 # Make a modification
        D = manualfit(D, F) # Rerun manualfit
        D = manualfit(D, F, dosave=True) # If the result is good, save
        
    Version: 2014nov24 by cliffk
    """
    
    from printv import printv
    printv('Running manual fitting...', 1, verbose)
    
    # Update options structure
    from setoptions import setoptions
    D.opt = setoptions(opt=D.opt, startyear=startyear, endyear=endyear)
    
    # Convert data parameters to model parameters
    from makemodelpars import makemodelpars
    D.M = makemodelpars(D.P, D.opt, verbose=verbose)
    
    # Create fitted parameters
    from makefittedpars import makefittedpars
    D.F = makefittedpars(D.G, D.opt, verbose=verbose)
    
    # Run model
    D.S, err = performfit(D, timelimit, verbose=verbose)
    allsims = [D.S]
    
    # Calculate results
    from makeresults import makeresults
    D.R = makeresults(allsims, D, D.opt.quantiles, verbose=verbose)
    
    printv('...done automatic fitting.', 2, verbose)
    return D




    
def performfit(D, timelimit, verbose=2):
    """ 
    Actually run the automatic fitting.

    Version: 2014nov24 by cliffk    
    """
    
    from model import model
    from time import time

    tstart = time()
    elapsed = 0
    iteration = 0
    
    while elapsed<timelimit:
        iteration += 1
        elapsed = time() - tstart
        S = model(D.G, D.M, D.F, D.opt, verbose=verbose)
        print('Iteration: %i Elapsed vs. limit: %f %f' % (iteration, elapsed, timelimit))
        
    err = -1
    
    return S, err