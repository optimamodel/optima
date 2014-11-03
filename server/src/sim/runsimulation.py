def runsimulation(projectdatafile='example.prj', startyear=2000, endyear=2030, loaddir = '', verbose=2):
    """
    RUNSIMULATION
    View data and model estimates
    Version: 2014oct29
    need to change UI
    """

    if verbose>=1: 
        data = (projectdatafile, startyear, endyear)
        print('Running simulation (projectdatafile = %s, startyear = %s, endyear = %s)...' % data)
    
    # Load data
    from dataio import loaddata, savedata, normalize_file
    projectdatafile = normalize_file(projectdatafile)
    D = loaddata(projectdatafile, verbose=verbose)
    print("D = %s" % D)
    
    # Create options structure
    from bunch import Bunch as struct
    from matplotlib.pylab import arange
    options = struct()
    options.startyear = startyear
    options.endyear = endyear
    options.dt = 0.1
    options.tvec = arange(options.startyear, options.endyear, options.dt) # Time vector
    
    from makemodelpars import makemodelpars
    D.M = makemodelpars(D.P, options, verbose=verbose)
    
    from model import model
    D.sim = model(D.G, D.M, options, verbose=verbose)
    
    savedata(projectdatafile, D, verbose=verbose)
    if verbose>=2: print('  ...done running simulation.')