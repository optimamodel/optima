"""
OPTIMA

This function does everything. The basic procedure is as follows:

1. makeproject -- initialize the project file

1. loadspreadsheet -- load the data into a structure
2. data2pars -- convert the data into model parameters
3. setupmodel -- reconcile partnerships and calculate parameters to go into the model
4. model -- actually run the model

Version: 2014nov05 by cliffk
"""
print('WELCOME TO OPTIMA')


## Set parameters
projectname = 'example'
verbose = 10

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname='example', npops=6, nprogs=8, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n\n2. Uploading spreadsheet...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n\n3. Running simulation...')
from runsimulation import runsimulation
D = runsimulation(D, verbose=verbose)

print('\n\n\n4. Making results...')
from epiresults import epiresults
D = epiresults(D, verbose=verbose)

print('\n\n\n4. Viewing results...')
from viewresults import viewresults
D = viewresults(D, whichgraphs={'prevpop':1, 'prevtot':1, 'incipop':1, 'prevtot':1, 'dalypop':1, 'dalytot':1, 'deathpop':1, 'deathtot':1}, verbose=verbose)

#print('\n\n\n4. Loading results...')
#from dataio import loaddata
#D = loaddata('example.prj', verbose=verbose)


print('Done.')
