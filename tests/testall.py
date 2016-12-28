#!/usr/bin/env python

"""
TESTALL

Run all tests, skipping GUI ones by default (doplot = False).

It runs everything in the same namespace, but deletes variables that get
added along the way. Extremely un-Pythonic, I know.

To run everything, either set everything = True below, or at the command line type

./testall everything

Version: 2016jan29 by cliffk
"""

## Initialization
from time import time as TIME # Use caps to distinguish 'global' variables
from sys import exc_info, argv
from glob import glob
import optima as op
import os
EVERYTHING = False # Whether to run all Python scripts in the folder
doplot = False # When running all tests, don't try to run the GUIs -- this must match the name in the script files


## Define master list of tests to run
MASTER = [
'testimports',
'testutils',
'testmakespreadsheet',
'testproject',
'testprograms',
'testmodalities',
'testmodel',
'testscenarios',
'testcalibration',
'testoptimization',
]

## Optionally run everything
if len(argv)>1 and argv[1]=='everything': EVERYTHING = True
if EVERYTHING: # Figure out the path -- adapted from defaults.py
    MASTER = glob(os.sep.join(op.__file__.split(os.sep)[:-2] + ['tests'+os.sep])+'*.py')
else:
    for INDEX in range(len(MASTER)): MASTER[INDEX] += '.py' # Append .py ending
    

## Run the tests in a loop
VARIABLES = []
VERYSTART = TIME()
FAILED = []
SUCCEEDED = []
for TEST in MASTER:
    try:
        VARIABLES = locals().keys() # Get the state before the test is run
        THISSTART = TIME()
        print('\n'*10+'#'*200)
        print('NOW RUNNING: %s' % TEST)
        print('#'*200+'\n'*3)
        exec(open(TEST).read()) # Run the test!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        SUCCEEDED.append({'test':TEST, 'time':TIME()-THISSTART})
        for KEY in locals().keys(): # Clean up -- delete any new variables added
            if KEY not in VARIABLES:
                print('       "%s" complete; deleting "%s"' % (TEST, KEY))
                exec('del '+KEY)
    except:
        FAILED.append({'test':TEST, 'msg':exc_info()[1]})


print('\n'*5)
if len(FAILED):
    print('The following %i/%i tests failed :(' % (len(FAILED), len(MASTER)))
    for FAIL in FAILED: print('  %s: %s' % (FAIL['test'], FAIL['msg']))
else:
    print('All %i tests passed!!! You are the best!!' % len(MASTER))
    for SUCCESS in SUCCEEDED: print('  %s: %0.1f s' % (SUCCESS['test'], SUCCESS['time']))
print('Elapsed time: %0.1f s.' % (TIME()-VERYSTART))