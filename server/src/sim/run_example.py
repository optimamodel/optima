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
    D = updatedata(D)


### Manually update CCOCs
D.programs.ART ={
'ccparams': [0.9, 0.1, 0.3, 4000000.0, None, 0.0],
 'ccplot': [],
 'convertedccparams': [[16461.856864957979, 1.1299628093576427e-07],
  [16461.856864957979, 5.578588782855242e-08],
  [16461.856864957979, 1.732867951399863e-07]],
 'effects': [[['txrx', 'numfirstline'], [u'Total']]],
 'nonhivdalys': [0.0]}

D.programs.SBCC={
'ccparams': [0.9, 0.1, 0.3, 4000000.0, None, 0.0],
 'ccplot': [],
 'convertedccparams': [[0.9, 1.1299628093576436e-07],
  [0.9, 5.578588782855242e-08],
  [0.9, 1.732867951399863e-07]],
 'effects': [
  [['sex', 'condomreg'],
   [u'Males 15-49'],
   [0.3, 0.5, 0.7, 0.9],
   [0.4, 0.03333333333333333, 0.8, 0.03333333333333335],
   [[0.9, 1.1299628093576436e-07, 0.4, 0.8],
    [0.9, 5.578588782855242e-08, 0.4, 0.8],
    [0.9, 1.732867951399863e-07, 0.4, 0.8]]],
  [['sex', 'condomreg'],
   [u'Females 15-49'],
   [0.3, 0.5, 0.7, 0.9],
   [0.4, 0.03333333333333333, 0.8, 0.03333333333333335],
   [[0.9, 1.1299628093576436e-07, 0.4, 0.8],
    [0.9, 5.578588782855242e-08, 0.4, 0.8],
    [0.9, 1.732867951399863e-07, 0.4, 0.8]]]],
 'nonhivdalys': [0.0]}


print('\n\n\n4. Running automatic fitting or optimization...')
#from autofit import autofit
#autofit(D, timelimit=30)

#from optimize import optimize
#D.F = [D.F[0]] # Only run a snigle simulation
#optimize(D, maxiters=10)


if doplot:
    print('Viewing results...')
    from viewresults import viewuncerresults
    viewuncerresults(D.plot.E)