"""
TEST_MANUALFIT

This function tests that the manual fitting is working.

Version: 2015jan27 by cliffk
"""

defaultpops = [{u'name': u'Female sex workers', u'short_name': u'FSW', u'sexworker': True, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Clients of sex workers', u'short_name': u'Clients', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': True, u'female': False, u'male': True, u'sexwomen': True}]
defaultprogs = [{u'category': u'Prevention', u'short_name': u'Condoms', u'name': u'Condom promotion and distribution', u'parameters': [{u'value': {u'pops': [u''], u'signature': [u'condom', u'reg']}}, {u'value': {u'pops': [u''], u'signature': [u'condom', u'cas']}}]}]

print('WELCOME TO OPTIMA')

## Set parameters
projectname = 'example2'
verbose = 10
nsims = 1


print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname=projectname, pops=defaultpops, progs = defaultprogs, datastart=2000, dataend=2015, verbose=verbose)
D['opt']['nsims'] = nsims # Reset options

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)


print('\n\n\n3. Viewing results...')
whichgraphs = {'prev':[1,1], 'plhiv':[0,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1]}
from viewresults import viewuncerresults
viewuncerresults(D['plot']['E'], whichgraphs=whichgraphs, simstartyear=2000, simendyear=2015, onefig=True, verbose=verbose)


print('\n\n\n4. Setting up manual fitting...')
from numpy import array, zeros


# Change F
F = D['F'][0]
F['force'] = array(F['force']) * 0.5

# Some changes to improve MSM fitting
Plist = [{'name':['const','trans','mmi'], 'data':5e-4}, \
         {'name':['const','trans','mmr'], 'data':1e-3}]

# Artifical change just to demonstrate changing M
tmp = zeros((D['G']['npops'], len(D['opt']['partvec'])))
for p in range(D['G']['npops']): tmp[p,:] = 200+(D['opt']['partvec']-2000)*50
Mlist = [{'name':['numacts','com'], 'data':tmp}]


print('\n\n\n5. Running manual fitting...')
from manualfit import manualfit
D = manualfit(D, F=F, Plist=Plist, Mlist=Mlist, simstartyear=2000, simendyear=2015, verbose=2)


print('\n\n\n6. Viewing results again...')
viewuncerresults(D['plot']['E'], whichgraphs=whichgraphs, simstartyear=2000, simendyear=2015, onefig=True, verbose=verbose)

print('\n\n\nDONE.')
