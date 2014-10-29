"""
OPTIMA

This function does everything. The basic procedure is as follows:

1. makeproject -- initialize the project file

1. loadspreadsheet -- load the data into a structure
2. data2pars -- convert the data into model parameters
3. setupmodel -- reconcile partnerships and calculate parameters to go into the model
4. model -- actually run the model

Version: 2014oct29
"""
print('WELCOME TO OPTIMA')


## Set parameters
projectname = 'example'

print('Making project...')
from makeproject import makeproject
spreadsheetname = makeproject(projectname='example', numpopgroups=6, numprograms=8, startyear=2000, endyear=2015)

print('Uploading spreadsheet...')
from updatedata import updatedata
updatedata(projectname='example')

print('Running simulation...')
from runsimulation import runsimulation
runsimulation(projectdatafile='example.mat')

print('Done.')
