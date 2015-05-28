"""
RUN_OPTIMA

Basic run.

Version: 2015feb01 by cliffk
Modified: 2015may15 by davidkedz
"""


print('WELCOME TO OPTIMA')

from project import Project

projectname = raw_input('Please enter a name for your project: ')

currentproject = Project(projectname)
currentproject.run()

#print('WELCOME TO RUN_OPTIMA')
#
#from time import time
#starttime = time()
#
### Set parameters
#projectname = 'example'
#verbose = 4
#show_wait = False
#nsims = 5
#
#print('\n\n\n1. Making project...')
#from makeproject import Region
#region1 = Region()
#region1.makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)
#region1.getdata()['opt']['nsims'] = nsims # Reset options
#
#print('\n\n\n2. Updating data...')
#from updatedata import updatedata
#region1.setdata(updatedata(region1.getdata(), verbose=verbose))
#
#print('\n\n\n3. Viewing results...')
#from viewresults import viewuncerresults
#viewuncerresults(region1.getdata()['plot']['E'])
#
#print('\n\n\nDONE; elapsed: %f s' % (time()-starttime))