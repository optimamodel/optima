def manualfit(D, F, startyear=2000, endyear=2015, verbose=2):
    """
    Manual metaparameter fitting code.
    
    Example usage:
        ipython --pylab # Run Python with Pylab
        ion() # Turn on interactive plotting
        import optima # Run Optima
        F = D.F # Shorten name for fitted parameters
        D = manualfit(D, F) # Run manualfit
        F.force *= 0 # Make a modification
        D = manualfit(D, F) # Rerun manualfit
        D = manualfit(D, F, dosave=True) # If the result is good, save
        
    Version: 2014nov24
    """
    
    from printv import printv
    printv('Running manual calibration...', 1, verbose)
    
    # Update options structure
    from setoptions import setoptions
    D.opt = setoptions(opt=D.opt, startyear=startyear, endyear=endyear)
    
    # Convert data parameters to model parameters
    from makemodelpars import makemodelpars
    D.M = makemodelpars(D.P, D.opt, verbose=verbose)
    
    # Run model
    from model import model
    allsims = []
    D.F = F
    D.S = model(D.G, D.M, D.F, D.opt, verbose=verbose)
    allsims.append(D.S)
    
    # Calculate results
    from makeresults import makeresults
    D.R = makeresults(allsims, D, D.opt.quantiles, verbose=verbose)
    
    printv('...done with manual calibration.', 2, verbose)
    return D
