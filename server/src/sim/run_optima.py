"""
RUN_OPTIMA

Basic run.

Version: 2015feb01 by cliffk
"""


print('WELCOME TO RUN_OPTIMA\n')

from time import time
from makeproject import Region

## Set parameters
verbose = 4
show_wait = False
nsims = 5

cmdinput = ''
cmdinputlist = []

regionlist = []

while(cmdinput != 'q'):
    cmdinputlist = cmdinput.split(None,1)
    if len(cmdinputlist)>1:

        # Is the first word 'load'? Then load a relevant json file named after the rest of the string.
        if cmdinputlist[0] == 'load':
            projectname = cmdinputlist[1]
            starttime = time()
            
            print('\n\n\n1. Making project...')
            regionlist.append(Region())
            regionlist[-1].setname(projectname)
            regionlist[-1].makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)
            regionlist[-1].getdata()['opt']['nsims'] = nsims # Reset options
            
            print('\n\n\n2. Updating data...')
            from updatedata import updatedata
            regionlist[-1].setdata(updatedata(regionlist[-1].getdata(), verbose=verbose))
            
            print('\n\n\n3. Viewing results...')
            from viewresults import viewuncerresults
            viewuncerresults(regionlist[-1].getdata()['plot']['E'])
            
            print('\n\n\nDONE; elapsed: %f s' % (time()-starttime))
            
    print('Regions loaded...')
    if len(regionlist) == 0:
        print('None')
    else:
        for region in regionlist:
            print(region.getname())
    
    print("To load a region titled 'region_name', type: load <region_name>")
    print('To quit, type: q')
    cmdinput = raw_input('Enter command: ')

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