"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2015nov23 by cliffk
"""



## Define tests to run here!!!
tests = [
'makeproject',
'saveload',
'loadspreadsheet',
'runsim',
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


## Project creation test
if 'makeproject' in tests:
    t = tic()
    print('Running make project test...')
    from optima import Project
    P = Project()
    print(P)
    done(t)




## Project save/load test
if 'saveload' in tests:
    t = tic()
    print('Running save/load test...')
    
    from optima import Project, saveobj, loadobj
    from os import remove
    filename = 'testproject.prj'
    
    print('  Checking saving...')
    P = Project()
    saveobj(filename, P)
    
    print('  Checking loading...')
    Q = loadobj(filename)
    
    print('Cleaning up...')
    remove(filename)
    
    done(t)




## Load spreadsheet test
if 'loadspreadsheet' in tests:
    t = tic()
    print('Running loadspreadsheet test...')
    from optima import Project
    
    print('  Create a project from a spreadsheet')
    P = Project(spreadsheet='test.xlsx')
    
    print('  Load a project, then load a spreadsheet')
    Q = Project()
    Q.loadspreadsheet('test.xlsx')
    
    assert Q.data['const']['effcondom'][0]==0.95, 'Condom efficacy not 95% or not being read in properly'
    
    done(t)




## Run simulation test
if 'runsim' in tests:
    t = tic()
    print('Running runsim test...')
    
    from optima import Project
    P = Project(spreadsheet='test.xlsx')
    results = P.runsim('default')
    
    done(t)





print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)