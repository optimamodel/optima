# -*- coding: utf-8 -*-
"""
TESTALL

Run all tests, skipping GUI ones by default (doplot = False).

It runs everything in the same namespace, but deletes variables that get
added along the way. Extremely un-Pythonic, I know.

Version: 2016jan15 by cliffk
"""

## Initialization
from time import time as TIME # Use caps to distinguish 'global' variables
from sys import exc_info
doplot = False # When running all tests, don't try to run the GUIs

## Define master list of tests to run
MASTER = [
'testimports',
'testutils',
'testproject',
'testprograms',
'testmodalities',
'testmodel',
'testscenarios',
'testcalibration',
'testoptimization',
]

## Other tests, for completeness -- not run by default since a subset of the other tests and/or does not make sense to run in batch
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
SUCCEEDED = []
THISSTART = 0
for TEST in MASTER:
    try:
        VARIABLES = locals().keys() # Get the state before the test is ru
        exec(open(TEST+'.py').read()) # Run the test!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if len(SUCCEEDED): THISSTART = SUCCEEDED[-1][1]
        SUCCEEDED.append([TEST, TIME()-STARTTIME-THISSTART])
        for KEY in locals().keys(): # Clean up -- delete any new variables added
            if KEY not in VARIABLES:
                print('       "%s" complete; deleting "%s"' % (TEST, KEY))
                exec('del '+KEY)
    except:
        FAILED.append([TEST, exc_info()[1]])


print('\n'*5)
if len(FAILED):
    print('The following %i/%i tests failed :(' % (len(FAILED), len(MASTER)))
    for FAIL in FAILED: print('  %s: %s' % (FAIL[0], FAIL[1]))
else:
    print('All %i tests passed!!! You are the best!!' % len(MASTER))
    for SUCCESS in SUCCEEDED: print('  %s: %0.1f s' % (SUCCESS[0], SUCCESS[1]))
print('Elapsed time: %0.1f s.' % (TIME()-STARTTIME))