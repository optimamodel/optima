"""
RUN_OPTIMA

Basic run.

Note: Loading will no longer work, without manually coding a directory path for .json files in projectclass.py.
      The hardcoding should be modified eventually but, for now, go to runproject.py in the gpa folder of the analyses repo.
      That will give a better idea of how to run Optima in OOP form.

Version: 2015feb01 by cliffk
Modified: 2015may15 by davidkedz
"""


print('WELCOME TO OPTIMA')

from projectclass import Project

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
#from makeproject import Project
#project1 = Project()
#project1.makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)
#project1.getdata()['opt']['nsims'] = nsims # Reset options
#
#print('\n\n\n2. Updating data...')
#from updatedata import updatedata
#project1.setdata(updatedata(project1.getdata(), verbose=verbose))
#
#print('\n\n\n3. Viewing results...')
#from viewresults import viewuncerresults
#viewuncerresults(project1.getdata()['plot']['E'])
#
#print('\n\n\nDONE; elapsed: %f s' % (time()-starttime))