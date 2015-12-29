"""
Tests to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Unlike the other test files, these tests are designed to be run sequentially, 
and are not intended to be comprehensive, but rather show the key workflow.

Version: 2015dec29 by cliffk
"""



## Define tests to run here!!!
tests = [
'makeproject',
'gui',
]


##############################################################################
## Initialization
##############################################################################

from optima import tic, toc, blank, pd, odict # analysis:ignore

def done(t=0):
    print('Done.')
    toc(t)
    blank()
    
blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()

doplot = False


##############################################################################
## The tests
##############################################################################

T = tic()




#####################################################################################################
if 'makeproject' in tests:
    t = tic()
    print('Running makeproject/runsim test...')
    
    from optima import Project
    P = Project(spreadsheet='test7pops.xlsx')
    results = P.runsim('default')
    
    done(t)




#####################################################################################################
if 'gui' in tests:
    t = tic()

    print('Running GUI test...')
    from gui import gui
    gui(results)
    
    done(t)


print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)