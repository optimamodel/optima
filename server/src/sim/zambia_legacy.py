"""
RUN_EXAMPLE

Load a project and test data upload.
"""

from dataio import loaddata
from os import path
from runsimulation import runsimulation
from makedatapars import makedatapars

D = loaddata('./projects/zambia-with-new-testing-removed-null-prog.json')
# D = makedatapars(D, verbose=2) # Update parameters
# del D['M']
from updatedata import updatedata
D = updatedata(D)
# if 'M' not in D.keys():

# D['F'] = [D['F'][0]] # Only run a snigle simulation

D = runsimulation(D, verbose=2, makeplot = 1, dosave = False)

from viewresults import viewuncerresults
viewuncerresults(D['plot']['E'],show_wait=True)
