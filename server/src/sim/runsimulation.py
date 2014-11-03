def runsimulation(projectdatafile='example.prj', startyear=2000, endyear=2030, loaddir = '', verbose=2):
    """
    RUNSIMULATION
    View data and model estimates
    
    Version: 2014nov03 by cliffk
    """

    if verbose>=1: print('Running simulation (projectdatafile = %s, startyear = %s, endyear = %s)...' % (projectdatafile, startyear, endyear))
    
    # Load data
    from dataio import loaddata, savedata, fullpath
    projectdatafile = fullpath(projectdatafile)
    D = loaddata(projectdatafile, verbose=verbose)
    
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
    D.sim = model(D.G, D.M, options, verbose=verbose)
    
    # Save output
    savedata(projectdatafile, D, verbose=verbose)
    if verbose>=2: print('  ...done running simulation.')