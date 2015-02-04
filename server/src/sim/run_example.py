"""
RUN_EXAMPLE

Load a project and test data upload.
"""

from dataio import loaddata
from updatedata import updatedata
from os import path

kind = 'sex'
doplot = True

datadir = '../static/'
datafile = kind+'example2.json'
spreadsheetfile = kind+'example.xlsx'
if path.exists(datadir+datafile):
    D = loaddata(datadir+datafile)
    D.G.workbookname = datadir+spreadsheetfile
    D.G.projectfilename = '/tmp/projects/run_example.prj'
#    D = updatedata(D)


### Manually update CCOCs
#D.programs.ART ={'nonhivdalys': [0.0], 'ccparams': [0.99, 0.5, 0.6, 70000000., None, None], 'effects': [[['txrx', 'numfirstline'], [u'Total']]], 'convertedccparams': []}
#D.programs.SBCC={'nonhivdalys': [0.0], 'ccparams': [0.9, 0.1, 0.2, 600000.], 'effects': [[['sex', 'condomreg'], [u'Males 15-49']], [['sex', 'condomreg'], [u'Females 15-49']]], 'convertedccparams': []}



print('\n\n\n4. Running automatic fitting or optimization...')
#from autofit import autofit
#autofit(D, timelimit=30)

from optimize import optimize
D.F = [D.F[0]] # Only run a snigle simulation
optimize(D, maxiters=10)


if doplot:
    print('Viewing results...')
    from viewresults import viewuncerresults
    viewuncerresults(D.plot.E)