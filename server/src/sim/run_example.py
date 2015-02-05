"""
TESTSUDAN

Load a project and test data upload.
"""

from dataio import loaddata
from updatedata import updatedata
from os import path

kind = 'sex'
doplot = True

datadir = '../static/'
datafile = kind+'example1.json'
spreadsheetfile = kind+'example.xlsx'
if path.exists(datadir+datafile):
    D = loaddata(datadir+datafile)
    D.G.workbookname = datadir+spreadsheetfile
    D.G.projectfilename = '/tmp/projects/run_example.prj'
    D = updatedata(D)


print('\n\n\n4. Running automatic fitting...')
from autofit import autofit
autofit(D, timelimit=30)


if doplot:
    print('Viewing results...')
    from viewresults import viewuncerresults
    viewuncerresults(D.plot.E)