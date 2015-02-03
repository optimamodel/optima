"""
TESTSUDAN

Load a project and test data upload.
"""

from dataio import loaddata
from updatedata import updatedata
from os import path

kind = 'sudan'
doplot = True

datadir = '../static/'
datafile = kind+'example.json'
spreadsheetfile = kind+'example.xlsx'
if path.exists(datadir+datafile):
    D = loaddata(datadir+datafile)
    D.G.workbookname = datadir+spreadsheetfile
    D.G.projectfilename = '/tmp/projects/run_example.prj'
    D = updatedata(D)

if doplot:
    print('Viewing results...')
    from viewresults import viewuncerresults
    viewuncerresults(D.plot.E, whichgraphs={'prev':[1,1], 'plhiv':[0,1], 'inci':[0,1], 'force':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1], 'costcum':[1,1]}, simstartyear=2000, simendyear=2015, onefig=True)
