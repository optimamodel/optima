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
'makeprograms'
]


##############################################################################
## Initialization -- same for every test script
##############################################################################

from optima import tic, toc, blank, pd # analysis:ignore

if 'doplot' not in locals(): doplot = True

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




#####################################################################################################
if 'makeproject' in tests:
    t = tic()
    print('Running makeproject/runsim test...')
    
    from optima import Project
    P = Project(spreadsheet='test7pops.xlsx')
    results = P.runsim('default')
    
    done(t)




#####################################################################################################
if 'gui' in tests and doplot:
    t = tic()

    print('Running GUI test...')
    from gui import pygui
    pygui(results)
    
    done(t)


#####################################################################################################
if 'makeprograms' in tests:
    t = tic()

    print('Making a default set of program...')
    from defaultprograms import defaultprograms
    defaultprograms = defaultprograms(P)
    
    # Select a few
    
    
    done(t)


print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)