"""
RUNSIMULATION
View data and model estimates
Version: 2014oct29
need to change UI


"""
import os

def runsimulation(projectdatafile='example.prj', startyear=2000, endyear=2030, loaddir = '', verbose=2):
    # todo: it should not overwrite the original file
    if loaddir:
        projectdatafile = os.path.join(loaddir, projectdatafile)
    if verbose>=1: 
        data = (projectdatafile, startyear, endyear)
        print('Running simulation (projectdatafile = %s, startyear = %s, endyear = %s)...' % data)
    
    # Load data
    from dataio import loaddata, savedata
    D = loaddata(projectdatafile, verbose=verbose)
    
    # Create options structure
    from bunch import Bunch as struct
    from matplotlib.pylab import arange
    options = struct()
    options.startyear = startyear
    options.endyear = endyear
    options.dt = 0.2
    options.tvec = arange(options.startyear, options.endyear, options.dt) # Time vector
    
    from makemodelpars import makemodelpars
    D.M = makemodelpars(D.P, options, verbose=verbose)
    
    from model import model
    D.sim = model(D.G, D.M, options, verbose=verbose)
    
    new_file_name = savedata(projectdatafile, D, verbose=verbose)
    if verbose>=2: print('  ...done running simulation.')