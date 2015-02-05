"""
RUN_EXAMPLE

Load a project and test data upload.
"""

from dataio import loaddata
from os import path

kind = 'sudan'
doplot = True

datadir = '../static/'
datafile = kind+'test2.json'
spreadsheetfile = kind+'example.xlsx'
if path.exists(datadir+datafile):
    D = loaddata(datadir+datafile)
    D.G.workbookname = datadir+spreadsheetfile
    D.G.projectfilename = '/tmp/projects/run_example.prj'


## Randomize allocation
#from numpy.random import rand
#newalloc = rand(len(D.data.origalloc))
#newalloc *= sum(D.data.origalloc) / sum(newalloc)
#D.data.origalloc = newalloc
#
#
#print('\n\n\n4. Running automatic fitting or optimization...')
##from autofit import autofit
##autofit(D, timelimit=30)
#
from optimize import optimize
D.F = [D.F[0]] # Only run a snigle simulation
optimize(D, maxiters=10, verbose=5)
#
#
if doplot:
    print('Viewing results...')
    from viewresults import viewuncerresults
    viewuncerresults(D.plot.E)