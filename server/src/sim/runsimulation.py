"""
RUNSIMULATION
View data and model estimates
Version: 2014oct29
need to change UI


"""

def runsimulation(projectdatafile='example.prj', startyear=2000, endyear=2030, verbose=2):
    if verbose>=1: print('Running simulation...')
    
    # Load data
    from dataio import loaddata, savedata
    D = loaddata(projectdatafile, verbose=verbose)
    
    # Create options structure
    from bunch import Bunch as struct
    options = struct()
    options.startyear = startyear
    options.endyear = endyear
    options.dt = 0.2
    
    from makemodelpars import makemodelpars
    D.Q = makemodelpars(D.P, options, verbose=verbose)
    
    from model import model
    D.sim = model(D.G, D.P, options, verbose=verbose)
    
    savedata(projectdatafile, D, verbose=verbose)
    if verbose>=2: print('  ...done running simulation.')