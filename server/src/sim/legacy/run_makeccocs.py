""" Test makeccocs code and bring up graphs using default values """

import argparse
parser = argparse.ArgumentParser(description = "OPTIMA test makeccocs")
parser.add_argument("-w","--wait", help="wait for user input after showing graphs", action="store_true")
parser.add_argument("-p","--plot", help="plot graphs", action="store_true")
parser.add_argument("-v", "--verbose", type=int, default=4, help="increase output verbosity")

args = parser.parse_args()

verbose = args.verbose # 4
makeplot = args.plot
show_wait = args.wait

if show_wait:
    makeplot = False

## Initialize simulation

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname='example', pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n\n3. Running simulation...')
from runsimulation import runsimulation
D = runsimulation(D, verbose=verbose)

# Actually run makeccocs
from plotccocs import plotall
#plotallcco(D=D)
ccparams = {'saturation': 0.9, 
          'coveragelower': 0.15, 
          'coverageupper':0.25, 
          'funding':800000.0, 
          'scaleup':None, 
          'nonhivdalys':None, 
          'cpibaseyear':None,
          'xupperlim':1000000,
          'perperson':None}
plotall(D=D, coparams=[], ccparams=ccparams)
if show_wait:
    from matplotlib.pylab import show
    show()
