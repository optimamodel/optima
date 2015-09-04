# -*- coding: utf-8 -*-
"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

Version: 2015sep04 by cliffk
"""

##############################################################################
## Initialization
##############################################################################

from utils import tic, toc, blank

# Define tests to run
tests = [
#'creation',
'loadspreadsheet',
]

print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank(3)



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


## Load spreadsheet test
if 'loadspreadsheet' in tests:
    print('Running loadspreadsheet test...')
    from project import Project
    P = Project(spreadsheet='test.xlsx')
    print('Done.')


blank(3)
print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)