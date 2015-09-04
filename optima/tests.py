# -*- coding: utf-8 -*-
"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

Version: 2015sep04 by cliffk
"""

##############################################################################
## Initialization
##############################################################################

from utils import tic, toc, blank, pd # analysis:ignore

# Define tests to run
tests = [
#'makespreadsheet',
#'creation',
#'saveload',
#'loadspreadsheet',
'runsim',
]

blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()



##############################################################################
## The tests
##############################################################################

T = tic()


## Spreadsheet creation test
if 'makespreadsheet' in tests:
    from makeworkbook import makeworkbook
    makeworkbook()
    print('Done.')
    blank()
    
    

## Project creation test
if 'creation' in tests:
    print('Running creation test...')
    from project import Project
    P = Project()
    print(P)
    print('Done.')
    blank()




## Project save/load test
if 'saveload' in tests:
    print('Running save/load test...')
    
    from project import Project, loadprj
    filename = 'testproject.prj'
    
    print('  Checking saving...')
    P = Project()
    P.save(filename)
    
    print('  Checking loading...')
    Q = loadprj(filename)
    Q.save()
    Q.reload()
    
    print('  Checking defaults...')
    Z = Project()
    Z.save()
    
    print('Done.')
    blank()




## Load spreadsheet test
if 'loadspreadsheet' in tests:
    print('Running loadspreadsheet test...')
    from project import Project
    
    print('  Create a project from a spreadsheet')
    P = Project(spreadsheet='test.xlsx')
    
    print('  Load a project, then load a spreadsheet')
    Q = Project()
    Q.loadspreadsheet('test.xlsx')
    
    print('Done.')
    blank()




## Load spreadsheet test
if 'runsim' in tests:
    print('Running runsim test...')
    from project import Project
    
    print('  Loading spreadsheet')
    P = Project(spreadsheet='test.xlsx')
    
    print('  Run the simulation')
    Q = Project()
    Q.loadspreadsheet('test.xlsx')
    
    print('Done.')
    blank()







print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)