# -*- coding: utf-8 -*-
"""
TESTUTILS

A little script for testing various utilities.

Version: 2015nov21 by cliffk
"""


## Define tests to run here!!!
tests = [
'odict',
]



##############################################################################
## Initialization
##############################################################################

from utils import tic, toc, blank, pd # analysis:ignore

def done(t=0):
    print('Done.')
    toc(t)
    blank()
    





blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()




##############################################################################
## The tests
##############################################################################

T = tic()



## Spreadsheet creation test
if 'odict' in tests:
    t = tic()
    print('Running odict tests...')
    from optima import odict
    foo = odict({'ah':3,'boo':4, 'cough':6, 'dill': 8})
    bar = foo.sort() # Sort the list
    assert(bar['boo'] == 4) # Show get item by value
    assert(bar[1] == 4) # Show get item by index
    assert((bar[0:2] == [3,4]).all()) # Show get item by slice
    assert((bar['cough':'dill'] == [6,8]).all()) # Show alternate slice notation
    assert(bar[[2,1]] == [6,4]) # Show get item by list
    bar[3] = [3,4,5] # Show assignment by item
    bar[0:1] = ['the', 'power'] # Show assignment by slice -- NOTE, inclusive slice!!
    bar.rename('cough','chill') # Show rename
    print(bar) # Print results
    done(t)