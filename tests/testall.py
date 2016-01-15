# -*- coding: utf-8 -*-
"""
TESTALL

Run all tests, skipping GUI ones by default (doplot = False).

It runs everything in the same namespace, but deletes variables that get
added along the way. Extremely un-Pythonic, I know.

Version: 2016jan06 by cliffk
"""

## Initialization
from time import time as TIME # Use caps to distinguish 'global' variables
doplot = False # When running all tests, don't try to run the GUIs

## Define master list of tests to run
MASTER = [
'testutils',
'testproject',
'testprograms',
'testmodalities',
'testmodel',
'testscenarios',
'testcalibration',
#'testoptimization',
]

## Other tests, for completeness
OTHER = [
'testgui',
'testworkflow',
]

## Optionally run everything
MASTER += OTHER

## Run the tests in a loop
VARIABLES = []
STARTTIME = TIME()
FAILED = []
for TEST in MASTER:
    try:
        VARIABLES = locals().keys() # Get the state before the test is ru
        exec(open(TEST+'.py').read()) # Run the test!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        for KEY in locals().keys(): # Clean up -- delete any new variables added
            if KEY not in VARIABLES:
                print('       "%s" complete; deleting "%s"' % (TEST, KEY))
                exec('del '+KEY)
    except:
        FAILED.append(TEST)


print('\n'*5)
if len(FAILED):
    print('The following tests failed :(')
    for FAIL in FAILED: print('  %s' % FAIL)
else:
    print('All %i tests passed!!! You are the best!!' % len(MASTER))
print('Elapsed time: %0.1f s.' % (TIME()-STARTTIME))