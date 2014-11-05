def manualfit(D, F, startyear=2000, endyear=2015, dosave=False, verbose=2):
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
        
    Version: 2014nov05
    """
    
    from printv import printv
    from bunch import Bunch as struct
    from matplotlib.pylab import arange
    
    ## TODO: don't just copy from runsimulation()
    options = struct()
    options.startyear = startyear
    options.endyear = endyear
    options.dt = 0.1
    options.tvec = arange(options.startyear, options.endyear, options.dt) # Time vector
    
    printv('1. Running simulation...', 1, verbose)
    from model import model
    D.S = model(D.G, D.M, F, options, verbose=2)
    
    printv('2. Making results...', 1, verbose)
    from epiresults import epiresults
    D = epiresults(D, verbose=verbose)
    
    printv('3. Viewing results...', 1, verbose)
    from viewresults import viewresults
    viewresults(D, whichgraphs={'prev':1, 'inci':1, 'daly':1, 'death':1, 'pops':1, 'tot':1}, onefig=True, verbose=verbose)
    
    if dosave:
        from dataio import savedata
        D.F = F
        savedata(D.projectfilename, D, verbose=verbose)
        printv('...done manual fitting.', 2, verbose)
    
    return D
