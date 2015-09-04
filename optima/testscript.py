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
#'creation',
'saveload',
#'loadspreadsheet',
]

blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()



##############################################################################
## The tests
##############################################################################

T = tic()

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
    filename = 'testproject.prj'
    from project import Project
    P = Project()
    P.save(filename)
    Q = Project.load(filename)
    print('Done.')
    blank()



## Load spreadsheet test
if 'loadspreadsheet' in tests:
    print('Running loadspreadsheet test...')
    from project import Project
    P = Project(spreadsheet='test.xlsx')
    Q = Project()
    Q.loadspreadsheet('test.xlsx')
    print(P)
    print(Q)
    print('Done.')
    blank()


print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)