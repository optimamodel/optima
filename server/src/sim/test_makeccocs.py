""" Test makeccocs code and bring up graphs using default values """

verbose = 4

## Initialize simulation

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname='example', pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n\n3. Running simulation...')
from runsimulation import runsimulation
D = runsimulation(D, startyear=2000, endyear=2015, verbose=verbose)


# Actually run makeccocs
from makeccocs import plotallcurves
try:
    out = plotallcurves(D=D, coparams=[], ccparams=[0.9, 0.2, 800000.0, 7000000.0], progname='SBCC', makeplot = True)
    from matplotlib.pylab import show
    show()
except:
    out = plotallcurves(D=D, coparams=[], ccparams=[0.9, 0.2, 800000.0, 7000000.0], progname='SBCC', makeplot = False)