"""
TESTPWID

Load a project and test data upload.
"""

from dataio import loaddata
from updatedata import updatedata
from os import getcwd, path

datafile = getcwd()+'/pwidtest.json'
if path.exists(datafile):
    D = loaddata(datafile)
    D.G.workbookname = getcwd()+'/PWID_example.xlsx'
    D = updatedata(D)
