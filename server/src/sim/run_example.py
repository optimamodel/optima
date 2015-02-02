"""
TESTSUDAN

Load a project and test data upload.
"""

from dataio import loaddata
from updatedata import updatedata
from os import path

kind = 'pwid'

datadir = '../static/'
datafile = kind+'example.json'
spreadsheetfile = kind+'example.xlsx'
if path.exists(datadir+datafile):
    D = loaddata(datadir+datafile)
    D.G.workbookname = datadir+spreadsheetfile
    D = updatedata(D)
