def runsimulation(D, startyear=2000, endyear=2030, verbose=2):
    """
    RUNSIMULATION
    View data and model estimates
    
    Version: 2014nov05 by cliffk
    """

    if verbose>=1: print('Running simulation (projectfilename = %s, startyear = %s, endyear = %s)...' % (D.projectfilename, startyear, endyear))
    
    # Create options structure
    from bunch import Bunch as struct
    from matplotlib.pylab import arange
    options = struct()
    options.startyear = startyear
    options.endyear = endyear
    options.dt = 0.1
    options.tvec = arange(options.startyear, options.endyear, options.dt) # Time vector
    
    # Convert data parameters to model parameters
    from makemodelpars import makemodelpars
    D.M = makemodelpars(D.P, options, verbose=verbose)
    
    # Run model
    from model import model
    D.S = model(D.G, D.M, options, verbose=verbose)
    
    # Save output
    from dataio import savedata
    savedata(D.projectfilename, D, verbose=verbose)
    if verbose>=2: print('  ...done running simulation.')
    return D