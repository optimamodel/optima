"""
RUNSIMULATION

Version: 2014oct29



"""

def runsimulation(projectdatafile='example.prj', startyear=2000, endyear=2030, verbose=2):
    if verbose>=1: print('Running simulation...')
    
    # Load data
    from dataio import loaddata, savedata
    D = loaddata(projectdatafile)
    
    # Create options structure
    from bunch import Bunch as struct
    options = struct()
    options.startyear = startyear
    options.endyear = endyear
    options.dt = 0.2
    
    from model import model
    sim = model(D.G, D.P, options)
    
    savedata(projectdatafile, sim)
    if verbose>=2: print('  ...done running simulation.')

## TEMP
runsimulation()