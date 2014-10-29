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
verbose = 1

print('1. Making project...')
from makeproject import makeproject
spreadsheetname = makeproject(projectname='example', npops=6, nprogs=8, datastart=2000, dataend=2015, verbose=verbose)

print('2. Uploading spreadsheet...')
from updatedata import updatedata
updatedata(projectname='example', verbose=verbose)

print('3. Running simulation...')
from runsimulation import runsimulation
runsimulation(projectdatafile='example.prj', verbose=verbose)

print('4. Loading results...')
from dataio import loaddata
D = loaddata('example.prj', verbose=verbose)


print('Done.')
