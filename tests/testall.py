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
from sys import exc_info as EXC_INFO, argv as ARGV
from glob import glob as GLOB
import os as OS
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
'testmigrations',
]

## Optionally run everything
if len(ARGV)>1 and ARGV[1]=='everything': EVERYTHING = True
if not EVERYTHING: # If using the master list supplied, just need to append .py ending
    for INDEX in range(len(MASTER)): MASTER[INDEX] += '.py' 
else: # We're using everything
    MASTER = GLOB(OS.path.dirname(OS.path.realpath(__file__))+OS.sep+'*.py') # Figure out the path -- adapted from defaults.py
    try: MASTER.remove(OS.path.realpath(__file__)) # Simple solution if file is in list
    except:
        print('Automatic infinite loop removal failed; trying manual...')
        REMOVED = False # Assume not removed
        for INDEX in range(len(MASTER)): # Loop over all tests
            THISFILE = OS.path.basename(__file__) # Find the name of this file
            if MASTER[INDEX][-len(THISFILE):] == THISFILE: # Check if this index matches
                MASTER.pop(INDEX) # If so, remove it
                REMOVED = True # And report success
        if not REMOVED: raise Exception('Could not find this file, aborting to avoid infinite loop!')

    

## Run the tests in a loop
VARIABLES = []
VERYSTART = TIME()
FAILED = []
SUCCEEDED = []
for TEST in MASTER:
    try:
        THISSTART = TIME()
        VARIABLES = locals().keys() # Get the state before the test is run
        print('\n'*10+'#'*200)
        print('NOW RUNNING: %s' % TEST)
        print('#'*200+'\n'*3)
        exec(open(TEST).read()) # Run the test!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        SUCCEEDED.append({'test':TEST, 'time':TIME()-THISSTART})
        for KEY in locals().keys(): # Clean up -- delete any new variables added
            if KEY not in VARIABLES:
                print('       "%s" complete; deleting "%s"' % (TEST, KEY))
                exec('del '+KEY)
    except:
        FAILED.append({'test':TEST, 'msg':EXC_INFO()[1]})


print('\n'*5)
if len(FAILED):
    print('The following %i/%i tests failed :(' % (len(FAILED), len(MASTER)))
    for FAIL in FAILED: print('  %s: %s' % (FAIL['test'], FAIL['msg']))
else:
    print('All %i tests passed!!! You are the best!!' % len(MASTER))
    for SUCCESS in SUCCEEDED: print('  %s: %0.1f s' % (SUCCESS['test'], SUCCESS['time']))
print('Elapsed time: %0.1f s.' % (TIME()-VERYSTART))